#!/usr/bin/python3
"""One isolated phase sensor + PI/sink study. No PCB or existing project edits."""
from pathlib import Path
from copy import deepcopy
import csv,json,subprocess,sys,shutil,tempfile,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts'))
import kicad_helpers as h
D=Path(__file__).resolve().parent;NAME='phase_sensor_study';LIB='PhaseBalanceStudy'
parts=[];rows=[];TI='https://www.ti.com/lit/ds/symlink/'
spec=[('1','DCDC_OUT','power_out'),('2','DCDC_HGND','power_in'),('3','HLDO_IN','power_in'),('4','NC','passive'),('5','HLDO_OUT','power_out'),('6','INP','input'),('7','INN','input'),('8','HGND','power_in'),('16','DCDC_IN','power_in'),('15','DCDC_GND','power_in'),('14','DIAG','open_collector'),('13','LDO_OUT','power_out'),('12','VDD','power_in'),('11','OUTP','output'),('10','OUTN','output'),('9','GND','power_in')]
s=['(symbol "AMC3302DWE" (pin_names (offset 1.27)) (in_bom yes) (on_board yes)','(property "Reference" "U" (at 0 24.13 0) (effects (font (size 1.27 1.27))))','(property "Value" "AMC3302DWE" (at 0 -24.13 0) (effects (font (size 1.27 1.27))))','(symbol "AMC3302DWE_0_1" (rectangle (start -8.89 22.86) (end 8.89 -22.86) (stroke (width 0.254) (type default)) (fill (type background))))','(symbol "AMC3302DWE_1_1"']
for i,(no,name,typ) in enumerate(spec):
 x,y,a=(-12.7,19.05-5.08*i,0) if i<8 else (12.7,19.05-5.08*(i-8),180)
 s.append(f'(pin {typ} line (at {x} {y} {a}) (length 3.81) (name "{name}" (effects (font (size 1 1)))) (number "{no}" (effects (font (size 1 1)))))')
items=['\n'.join(s)+'))']
amp=deepcopy(h.resolved('Amplifier_Operational:LM324'));old=amp[1];amp[1]='OPA4192'
for su in h.children(amp,'symbol'):su[1]='OPA4192'+su[1][len(old):]
for prop in h.children(amp,'property'):
 if prop[1]=='Value':prop[2]='OPA4192'
items.append(h.emit(amp))
(D/(LIB+'.kicad_sym')).write_text('(kicad_symbol_lib (version 20241209) (generator "phase_sensor_study")\n'+'\n'.join(items)+'\n)\n')
orig=h.library
h.library=lambda name:h.parse((D/(LIB+'.kicad_sym')).read_text()) if name==LIB else orig(name)
def add(ref,val,lib,nets,xy,desc,fp='',source='',unit=1,board=True,status='STUDY VALUE / FINAL MPN OR LAYOUT REVIEW PENDING'):
 parts.append(dict(ref=ref,val=val,lib=lib,nets=nets,xy=xy,description=desc,footprint=fp,datasheet=source,unit=unit,on_board=board))
 if ref.startswith('#'):return
 if ref not in {r['Reference'] for r in rows}:rows.append(dict(Reference=ref,Value=val,Quantity=1,Footprint=fp,Description=desc,Source=source,Release_status=status,Study_channels=1,Four_phase_required_quantity=4))
R='Resistor_SMD:R_0603_1608Metric';C='Capacitor_SMD:C_0603_1608Metric'
add('U1','AMC3302DWE',LIB+':AMC3302DWE',{'1':'ISO_DC','2':'HGND','3':'ISO_DC','4':'HGND','5':'ISO_LDO','6':'INP','7':'INN','8':'HGND','9':'PGND','10':'OUTN','11':'OUTP','12':'AUX5','13':'LV_DC','14':'DIAG','15':'PGND','16':'LV_DC'},(55.88,68.58),'TI SBASA11B p3 exact16pin map. High-sideHGND followsVOUT_COMMON;low-sidePGNDisfloatingPSUsecondary.Notmainsisolation.','Package_SO:SOIC-16W_7.5x10.3mm_P1.27mm',TI+'amc3302.pdf',status='MANUFACTURER PINOUT VERIFIED; STUDY ONLY / NO PCB')
add('SH1','2m 0.1% / >=3W / 4-terminal','Device:R',{'1':'PHASE_OUT','2':'VOUT_COMMON'},(20.32,106.68),'Externalphasebranchshuntrequirement:>=25A,>=200Vworking,<=15ppm/C.FinalMPN/Kelvinassemblypending.Existing4mohmIAVGshuntremainsseparate.',board=False)
res=[('R1','10 0.1%','PHASE_OUT','INP','Matchedpositiveinputfilter.'),('R2','10 0.1%','VOUT_COMMON','INN','Matchednegativeinputfilter;HGNDindependentKelvinpath.'),('R3','0 / EMI FB TBD','VOUT_COMMON','HGND','Independenthigh-sidegroundKelvinlink;EMIferriteselectionpending.'),('R4','47k','AUX5','DIAG','DIAGopen-drainpullup;externalfaultlatchrequired.'),('R5','10k 0.01% ratio','OUTP','DIFF_POS','Differenceamplifierpositiveinput.'),('R6','10k 0.01% ratio','VREF','DIFF_POS','Offsetinput;matchednetworkrequired.'),('R7','10k 0.01% ratio','OUTN','DIFF_NEG','Differenceamplifiernegativeinput.'),('R8','10k 0.01% ratio','VMON_RAW','DIFF_NEG','Feedback:VMON=OUTP-OUTN+VREF.'),('R9','1k','VMON_RAW','VMON','Averagefilterwith100nF;1.59kHzinitialpole.'),('R10','47k','ICMD','PI_NEG','PIcommandinput;ICMD=1.25+0.082*targetA.'),('R11','22k','PI_DRIVE','PI_CAP','PIseriesR,studyvalueonly.'),('R12','100','PI_DRIVE','CLAMP_GATE','Gatechargingresistance;edge/ringingreviewpending.'),('R13','100k','CLAMP_GATE','PGND','DefaultgateOFF;RUNmustseparatelydefaultOFF.'),('R14','470','ITH_LOCAL','CLAMP_DRAIN','ITHsinkR;authorityunverified.Noexternalpositivesource.'),('R15','100k','ICMD','PGND','OpencommanddrivesclampbutmustalsogiveRUNshutdownthroughseparateguard.'),('R16','10k','RUN_LOCAL','PGND','LocalRUNdefaultOFF.Noenablelogicimplementedhere.')]
for i,(ref,val,a,b,desc) in enumerate(res):add(ref,val,'Device:R',{'1':a,'2':b},(17.78+35.56*(i%10),167.64+35.56*(i//10)),desc,R)
caps=[('C1','100nF 50V','ISO_DC','HGND','HLDOinputdecoupling.'),('C2','1uF 25V','ISO_DC','HGND','IsolatedDC/DCbulk.'),('C3','1nF 50V','ISO_DC','HGND','IsolatedDC/DCfastdecoupling.'),('C4','100nF 50V','LV_DC','PGND','Onlylow-sideLDO/DCinputdecoupling:noexternalload.'),('C5','100nF 50V','ISO_LDO','HGND','High-sideLDOdecoupling.'),('C6','1nF 50V','ISO_LDO','HGND','High-sideLDOfastdecoupling.'),('C7','1uF 25V','AUX5','PGND','Low-sideVDDbulk.'),('C8','1nF 50V','AUX5','PGND','Low-sideVDDfastdecoupling.'),('C9','10nF 50V C0G','INP','INN','Inputdifferentialfilter~796kHz.'),('C10','100nF 50V','VMON','PGND','Outputaveragefilter1.59kHz.'),('C11','22nF 50V C0G','PI_CAP','PI_NEG','IntegratingC;anti-windup/resetnotimplemented.'),('C12','100nF 50V','AUX5','PGND','OPA4192localbypass.')]
for i,(ref,val,a,b,desc) in enumerate(caps):add(ref,val,'Device:C',{'1':a,'2':b},(17.78+30.48*i,228.6),desc,C,TI+'amc3302.pdf' if i<9 else '')
ampunits=[(1,{'1':'VMON_RAW','2':'DIFF_NEG','3':'DIFF_POS'},(160.02,63.5),'Difference/offsetconverter.'),(2,{'7':'PI_DRIVE','6':'PI_NEG','5':'VMON'},(246.38,63.5),'Highcurrent=>gateup=>ITHsink=>phasestromdown.Dynamicsunverified.'),(3,{'8':'VREF','9':'VREF','10':'VREF_IN'},(332.74,63.5),'Buffersexternalqualified1.25Vreference.'),(4,{'14':'SPARE','13':'SPARE','12':'PGND'},(332.74,119.38),'Unusedchannelgroundfollower;noexternalload.'),(5,{'4':'AUX5','11':'PGND'},(375.92,119.38),'5Vdomainneeds4.5Vminimumandseparatesupervisor.')]
for unit,nets,xy,desc in ampunits:add('U2','OPA4192PW',LIB+':OPA4192',nets,xy,desc,'Package_SO:TSSOP-14_4.4x5mm_P0.65mm',TI+'opa192.pdf',unit=unit,status='MANUFACTURER FAMILY PINOUT VERIFIED; PI DYNAMICS UNVALIDATED')
add('Q1','CSD13381F4 / LANDPATTERN TBD','Transistor_FET:2N7002',{'1':'CLAMP_GATE','2':'PGND','3':'CLAMP_DRAIN'},(246.38,116.84),'TI12VN-FETcandidate,8Vgateabsolute.G1/S2/D3mappingderivedfromdatasheetpackageviews;independentphysicalmapping/landpatternreviewpending.OnlysinksITH.',source=TI+'csd13381f4.pdf',status='MANUFACTURER ELECTRICAL DATA VERIFIED; PHYSICAL PIN/LANDPATTERN REVIEW PENDING')
add('J1','PHASE OUTPUT / COMMON OUTPUT','Connector_Generic:Conn_01x02',{'1':'PHASE_OUT','2':'VOUT_COMMON'},(45.72,129.54),'Externalpower/shuntinterface:>=25A>=200VterminalMPNpending.',board=False)
add('J2','AUX5 / PGND / REF1V25 / ICMD','Connector_Generic:Conn_01x04',{'1':'AUX5','2':'PGND','3':'VREF_IN','4':'ICMD'},(144.78,116.84),'Qualifiedfloating-secondarysupply/reference/perphasecommand.NotPE.','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical')
add('J3','ITH / RUN / DIAG / PGND','Connector_Generic:Conn_01x04',{'1':'ITH_LOCAL','2':'RUN_LOCAL','3':'DIAG','4':'PGND'},(180.34,116.84),'ExternalguardedRUNdriver/latchedshutdownnotdrawn.NeverjoinITHbetweenphases.','Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical')
for idx,net in enumerate(['PHASE_OUT','VOUT_COMMON','HGND','AUX5','DIAG','OUTP','OUTN','VMON','ICMD','PI_DRIVE','ITH_LOCAL','RUN_LOCAL'],1):add('TP'+str(idx),net,'Connector:TestPoint',{'1':net},(20.32+20.32*(idx-1),269.24),'Studytestpoint;HV/HGNDdifferentialmeasurement.NoPCB.','TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm')
for idx,net in enumerate(['AUX5','PGND','HGND'],1):add('#FLG'+str(idx),'PWR_FLAG','power:PWR_FLAG',{'1':net},(355.6+12.7*(idx-1),27.94),'Externallyvalidpower/referenceflag.',board=False)
# Give the delivered BOM readable Danish functions; source/provenance fields stay exact.
descriptions={
 'U1':'Isoleret phasesensor med intern DC/DC. HGND følger den fælles positive udgang; PGND er den flydende sekundærretur. Originalt TI-pinout verificeret.',
 'U2':'OPA4192: A konverterer OUTP-OUTN til 1,25 V offset; B regulerer lokal strøm via PI og NMOS; C buffer referencen; D er ubrugt follower. PI-stabilitet er uverificeret.',
 'SH1':'Ekstern 2 mΩ fireterminal-shunt pr. fase, 0,1 %, mindst 3 W, mindst 25 A, højst 15 ppm/°C og mindst 200 V arbejdsrating som krav. MPN og Kelvin-montage mangler.',
 'Q1':'Lokal 12 V N-MOSFET-kandidat til ITH-sink. Gate tåler højst 8 V. Fysisk G1/S2/D3-mapping er afledt af TI-views og kræver uafhængigt review; landpattern mangler.',
 'J1':'Power-/shuntgrænseflade til én fases outputgren og fælles VOUT. Endeligt stik eller busbar med mindst 25 A og 200 V rating mangler.',
 'J2':'Eksternt kvalificeret AUX5, PGND, 1,25 V reference og individuel strømkommando. PGND tilhører flydende sekundærside.',
 'J3':'Kun denne fases ITH, RUN, DIAG og PGND. RUN-guard og fejllåsning er ikke tegnet; ITH må aldrig deles med andre faser.',
 'R1':'Matchet 10 Ω filter i positiv Kelvin-sensevej.',
 'R2':'Matchet 10 Ω filter i negativ Kelvin-sensevej; HGND har separat retur til shunten.',
 'R3':'Separat HGND-Kelvinlink; 0 Ω i studiet. Eventuel EMI-ferrit og dens DC-modstand skal verificeres.',
 'R4':'47 kΩ pull-up for AMC3302s aktive-lave DIAG; ekstern latched fault-overvågning kræves.',
 'R5':'10 kΩ i differensforstærkerens positive input; matchet ratio-netværk med R6-R8 kræves.',
 'R6':'10 kΩ fra bufferet 1,25 V reference til positivt input.',
 'R7':'10 kΩ fra OUTN til inverterende differensinput.',
 'R8':'10 kΩ differensfeedback; giver VMON_RAW = OUTP - OUTN + 1,25 V ved ideelle ratioer.',
 'R9':'1 kΩ til strøm-feedbackfilter; C10 giver omtrent 1,59 kHz pol.',
 'R10':'47 kΩ fra lokal ICMD til PI-input; ICMD = 1,25 + 0,082 × ønsket fasestrøm i A.',
 'R11':'22 kΩ seriegren i lokal PI; startværdi til studie.',
 'R12':'100 Ω serie på NMOS-gate; gateforløb og opampstabilitet skal verificeres.',
 'R13':'100 kΩ gate-pulldown; gate er lav uden AUX5. RUN skal uafhængigt være slukket.',
 'R14':'470 Ω mellem lokal ITH og NMOS-drain. Kan kun trække ITH ned; faktisk clampmyndighed er ukendt.',
 'R15':'100 kΩ ICMD-pulldown ved åben kommando. Kommando-guard skal samtidig holde RUN lav.',
 'R16':'10 kΩ lokal RUN-pulldown; controllerens 2,5 µA giver omtrent 25 mV før hysterese.',
 'C9':'10 nF differentialt inputfilter med R1/R2; omtrent 796 kHz ideal pol.',
 'C10':'100 nF outputfilter med R9; dæmper switchripple, omtrent 1,59 kHz pol.',
 'C11':'22 nF PI-integrator. Anti-windup og OFF-tracking/reset er endnu ikke implementeret.',
 'C12':'100 nF lokal OPA4192-forsyningsafkobling.'}
for ref in ['C1','C2','C3','C4','C5','C6','C7','C8']:
 descriptions[ref]='AMC3302-afkobling efter originalt TI-datablad figur 9-1; endeligt capacitor-MPN og effektiv kapacitet mangler.'
for idx in range(1,13):descriptions['TP'+str(idx)]='Studietestpunkt for '+rows[next(i for i,r in enumerate(rows) if r['Reference']=='TP'+str(idx))]['Value']+'. HV/HGND kræver passende differentialmåling; der findes intet studie-PCB.'
for row in rows:row['Description']=descriptions.get(row['Reference'],row['Description'])
for p in parts:
 if p['ref'] in descriptions:p['description']=descriptions[p['ref']]
h.write_schematic(D/(NAME+'.kicad_sch'),parts,project=NAME,title='STUDY ONLY: ONE PHASE SENSOR / ITH SINK',comments=['No PCB; no integrated four-phase hardware','Independent ITH / SS / V5 required for each phase','Anti-windup, RUN guard and fault latch missing'],texts=[dict(xy=(12.7,22.86),text='STUDY ONLY: one of four independent sensor / servo channels.\nExternal RUN latch / command gating / PI tracking REQUIRED; not implemented here.'),dict(xy=(109.22,149.86),text='Positive current -> OUTP - OUTN rises -> VMON rises -> PI gate rises -> Q1 sinks local ITH.\nHGND follows VOUT_COMMON near 100 V. PGND is floating secondary return. Never join HGND and PGND.')])
h.symbol_tables(D,{p['lib'] for p in parts if not p['lib'].startswith(LIB+':')})
table=(D/'sym-lib-table').read_text().rstrip()
(D/'sym-lib-table').write_text(table[:-1]+f'\n(lib (name "{LIB}") (type "KiCad") (uri "{chr(36)}{{KIPRJMOD}}/{LIB}.kicad_sym") (options "") (descr "Schematic-onlyphasebalance study"))\n)\n')
fields=['Reference','Value','Quantity','Footprint','Description','Source','Release_status','Study_channels','Four_phase_required_quantity']
with (ROOT/'bom/phase-balancing-study.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
def run(*args):return subprocess.run([str(ROOT/'bin/kicad-env'),'kicad-cli',*map(str,args)],text=True,capture_output=True)
for mode,target in [('pdf',D/(NAME+'.pdf')),('netlist',D/(NAME+'.xml'))]:
 extra=['--format','kicadxml'] if mode=='netlist' else []
 r=run('sch','export',mode,*extra,'-o',target,D/(NAME+'.kicad_sch'))
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
# KiCad9 does not load local lookup tables for a project-less standalone file.
# A disposable project container verifies the exact same schematic/library;
# it is never added to the existing control project or delivered as a new project.
with tempfile.TemporaryDirectory(prefix='phase-balance-erc-',dir='/tmp') as scratch:
 temporary=Path(scratch)
 for name in [NAME+'.kicad_sch',LIB+'.kicad_sym','sym-lib-table']:shutil.copy2(D/name,temporary/name)
 (temporary/(NAME+'.kicad_pro')).write_text('{}\n')
 r=run('sch','erc','--severity-all','--format','json','-o',D/'erc.json',temporary/(NAME+'.kicad_sch'))
 if r.returncode:raise RuntimeError(r.stdout+r.stderr)
tree=ET.parse(D/(NAME+'.xml'))
actual={}
for net in tree.findall('./nets/net'):
 for n in net.findall('node'):actual[(n.get('ref'),n.get('pin'))]=net.get('name')
expected={(p['ref'],no):net for p in parts if not p['ref'].startswith('#') for no,net in p['nets'].items()}
assert all(actual.get(key)==net for key,net in expected.items()),[(k,v,actual.get(k)) for k,v in expected.items() if actual.get(k)!=v]
net_components={c.get('ref'):(c.findtext('value') or '',c.findtext('footprint') or '') for c in tree.findall('./components/comp') if not c.get('ref').startswith('#')}
listed_components={r['Reference']:(r['Value'],r['Footprint']) for r in rows}
assert net_components==listed_components,{'XML_only':list(set(net_components)-set(listed_components)),'BOM_only':list(set(listed_components)-set(net_components)),'mismatches':[(r,v,listed_components.get(r)) for r,v in net_components.items() if listed_components.get(r)!=v]}
sensor_datasheet_pinmap={'1':'DCDC_OUT','2':'DCDC_HGND','3':'HLDO_IN','4':'NC','5':'HLDO_OUT','6':'INP','7':'INN','8':'HGND','9':'GND','10':'OUTN','11':'OUTP','12':'VDD','13':'LDO_OUT','14':'DIAG','15':'DCDC_GND','16':'DCDC_IN'}
assert {p['number']:p['name'] for p in h.pins(LIB+':AMC3302DWE')}==sensor_datasheet_pinmap
erc_data=json.loads((D/'erc.json').read_text())
violations=[v for sheet in erc_data['sheets'] for v in sheet.get('violations',[])]
assert not violations,violations
report={'scope':'single-channel schematic-only study; no PCB; not integrated four-phase hardware','component_refs':len(rows),'BOM_XML_refs_values_footprints_match':True,'virtual_refs_excluded':['#FLG1','#FLG2','#FLG3'],'expected_pin_nodes_checked':len(expected),'ERC':erc_data,'ERC_violations_all_severities':len(violations),'ERC_container':'identical standalone file copied to temporary /tmp project; local lookup table enabled','hardware_tests':0,'unimplemented':['RUN enable logic','command/DIAG fault latch','anti-windup','PI OFF tracking/reset','phase fail-stop','clock gating'],'AMC_sensor_pinmap_verified':True,'FET_physical_pin_and_landpattern_independent_review':'pending'}
(D/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
exports=ROOT/'exports/control/studies';exports.mkdir(parents=True,exist_ok=True)
for filename in [NAME+'.pdf',NAME+'.xml','summary.json','erc.json']:shutil.copy2(D/filename,exports/filename)
print(json.dumps({'components':len(rows),'pin_nodes':len(expected),'files':str(D),'PCB':False}))
