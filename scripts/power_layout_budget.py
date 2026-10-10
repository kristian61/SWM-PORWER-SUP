from pathlib import Path
import json,math,collections,hashlib,subprocess,tempfile,shutil
R=Path(__file__).resolve().parents[1];E=R/'exports/power'
def width(i,t_um,dt,k=.048):
 area=(i/(k*dt**.44))**(1/.725)
 return area/(t_um/25.4)*.0254
def current(w_mm,t_um,dt,k=.048):return k*dt**.44*((w_mm/.0254)*(t_um/25.4))**.725
rho20=1.724e-8;alpha=.00393
copper=[]
for i in [10,13.26,20.5,40]:
 for t in [35,70]:copper.append({'current_A':i,'copper_um':t,'rise_assumption_K':20,'external_width_mm':width(i,t,20)})
trace=[]
for w in [.18,.3,.8,1.8,3,5]:
 t=.00007;l=.05;r=rho20*l/(w*.001*t)
 trace.append({'width_mm':w,'outer_copper_um':70,'external_empirical_20K_current_A':current(w,70,20),'resistance_50mm_20C_mohm':r*1000,'resistance_50mm_80C_mohm':r*(1+alpha*60)*1000,'heat_at10A_50mm20C_W':100*r,'note':'0.18/0.3 mm are signal traces; 10 A heat columns are comparisons only.'})
f=101800;vin=110;vout=99.6;ind=150e-6;d=vout/vin;ripple=vin*d*(1-d)/(ind*f)
budget={'status':'CALCULATED ASSUMPTIONS - NOT HARDWARE TESTED','empirical_model':'I=0.048*DeltaT^0.44*A_mil2^0.725, traditional IPC-2221 external-trace fit; not IPC-2152 qualification','native_outer_copper_um':70,'native_inner_copper_um':35,'board_nominal_thickness_mm':1.6,'width_requirements':copper,'outer_trace_comparisons':trace,'current_limits':{'target_A':10,'native_average_CC_nominal_A':12.5,'native_average_CC_worst_A':13.26,'cycle_peak_worst_A':.110/(.006*.99)+120/(4*ind*f),'inductor_hot_Isat_required_A':25},'ideal_buck_at_nominal':{'Vin_V':vin,'Vout_V':vout,'frequency_Hz':f,'L_H':ind,'duty':d,'ripple_pp_A':ripple,'inductor_rms_A':math.sqrt(100+ripple*ripple/12)},'loss_examples':{'MOSFET_two_path_Rdsmax_25C_10A_W':2*100*.011,'cycle_shunt_6mohm_at10Arms_W':.006*100,'average_shunt_4mohm_at10A_W':.004*100,'hard_switch_overlap_example_40ns_one_path_W':.5*vin*10*40e-9*f,'four_gates_Qg_typ28nC_10V_100percent_switching_W':4*28e-9*10*f,'four_gates_Qg_max35nC_10V_100percent_switching_W':4*35e-9*10*f,'not_included':['Hot Rds(on), diode reverse recovery, Coss/inductor/ESR losses, switching ringing, terminal/via resistance, load transient losses, driver/LDO heating']},'MOSFET_thermal_context':{'RthJC_max_K_per_W':1,'RthJA_example_max_K_per_W':50,'datasheet_testboard':'40 x 40 x 1.5 mm FR4, drain copper 6 cm2, one 70 um layer, vertical in still air. This PCB does not establish these conditions.','qualification':False},'pending':['Independent physical gate/source-loop, routing and Kelvin review despite complete CAD connectivity','MPNs/datasheets for inductor, bulk capacitors, shunts, connectors, bootstrap footprint','Drain copper heat spreading/thermal vias and cooling','Fabricator stackup/copper plating/hole and creepage review','Gate ringing/current sharing and stable compensation measurement','No integrated 0..100 V / 40 A supply']}
(E/'layout_budget.json').write_text(json.dumps(budget,indent=2)+'\n')
j=json.load(open(E/'drc.json'));nc=collections.Counter()
for v in j['unconnected_items']:
 import re
 nets={n for item in v['items'] for n in re.findall(r'\[([^\]]+)\]',item['description'])}
 assert len(nets)==1,nets
 nc[next(iter(nets))]+=1
(E/'remaining_nets.json').write_text(json.dumps(dict(sorted(nc.items())),indent=2)+'\n')
# Negative rule check runs in an isolated copy; original CAD hashes must survive.
D=R/'design/power';protected=[D/'power_phase.kicad_pcb',D/'power_phase.kicad_pro',D/'power_phase.kicad_dru']
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
with tempfile.TemporaryDirectory(prefix='power-hv-negative-',dir='/tmp') as td:
 t=Path(td)
 for p in D.iterdir():
  if p.is_file() and p.suffix in ['.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_sch','.kicad_sym']:shutil.copy2(p,t/p.name)
 for name in ['sym-lib-table','fp-lib-table']:shutil.copy2(D/name,t/name)
 shutil.copytree(D/'PowerPhase.pretty',t/'PowerPhase.pretty')
 with (t/'power_phase.kicad_dru').open('a') as f:f.write('(rule "NEGATIVE TEST HV separation 5 mm" (condition "A.NetClass == \'HV\' || B.NetClass == \'HV\' || A.NetClass == \'Power\' || B.NetClass == \'Power\'") (constraint clearance (min 5.0mm)))\n')
 proc=subprocess.run([str(R/'bin/kicad-env'),'kicad-cli','pcb','drc','--severity-all','--schematic-parity','--exit-code-violations','--format','json','-o',str(t/'negative.json'),str(t/'power_phase.kicad_pcb')],capture_output=True,text=True)
 assert proc.returncode==5,(proc.returncode,proc.stdout,proc.stderr)
 negative=json.load(open(t/'negative.json'))
 caught=[v for v in negative['violations'] if v['type']=='clearance' and 'NEGATIVE TEST HV' in v['description']]
 assert caught,'HV rule is not enforced'
 assert before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected},'Original CAD changed during isolated test'
 proof={'status':'PASS','purpose':'Prove custom HV clearance providers are active; this does not qualify hardware or fabrication performance.','isolated_rule_min_mm':5,'caught_clearance_violations':len(caught),'negative_DRC_exit':proc.returncode,'source_CAD_hashes_unchanged':True,'original_hashes_sha256':before}
 (E/'hv_rule_negative_check.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps({'width_at10A_70um_20K_mm':width(10,70,20),'native_copper_70um_5mm_20K_estimated_A':current(5,70,20),'remaining_nets':dict(nc),'HV_negative_test':proof['caught_clearance_violations']},indent=2))
