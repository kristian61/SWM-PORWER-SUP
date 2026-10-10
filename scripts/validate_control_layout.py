#!/usr/bin/python3
"""Independently verify the routed card and prove its HV DRC rule is active."""
from pathlib import Path
import os, hashlib, json, shutil, subprocess, tempfile, datetime
ROOT=Path(__file__).resolve().parents[1]
for key,rel in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:
    os.environ.setdefault(key,str(ROOT/'.runtime/kicad'/rel))
from check_inventory import check
D=ROOT/'design/control';E=ROOT/'exports/control'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
protected=[D/f'control.{ext}' for ext in ['kicad_pcb','kicad_pro','kicad_dru']]
before={str(p.relative_to(ROOT)):digest(p) for p in protected}
base=[str(ROOT/'bin/kicad-env'),'kicad-cli']
subprocess.run(base+['sch','erc','--severity-all','--exit-code-violations','--format','json','-o',str(E/'erc_routed.json'),str(D/'control.kicad_sch')],check=True)
subprocess.run(base+['pcb','drc','--severity-all','--schematic-parity','--exit-code-violations','--format','json','-o',str(E/'drc_routed.json'),str(D/'control.kicad_pcb')],check=True)
inventory=check('Styrekort','control','control','control.csv')
with tempfile.TemporaryDirectory(prefix='control-hv-negative-') as td:
    t=Path(td)
    for path in protected:shutil.copy2(path,t/path.name)
    rules=t/'control.kicad_dru';old=rules.read_text()
    assert old.count('(min 3.0mm)')==1,'Expected one explicit 3 mm HV rule'
    rules.write_text(old.replace('(min 3.0mm)','(min 100.0mm)'))
    result=subprocess.run(base+['pcb','drc','--severity-all','--exit-code-violations','--format','json','-o',str(E/'drc_negative_hv.json'),str(t/'control.kicad_pcb')],check=False)
    negative=json.loads((E/'drc_negative_hv.json').read_text())
    violations=[v for v in negative['violations'] if v['type']=='clearance']
    assert result.returncode==5 and violations,'HV negative control did not fail on clearance'
after={str(p.relative_to(ROOT)):digest(p) for p in protected}
assert before==after,'Negative test altered a protected source file'
summary={'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'ERC_all_severities':'PASS',
         'DRC_all_severities_with_schematic_parity':'PASS',
         'inventory':inventory,
         'HV_rule_negative_control':{'status':'PASS','changed_rule_mm':100,
             'exit_code':result.returncode,'clearance_violations':len(violations)},
         'original_source_hashes':before,'original_sources_unchanged':True,
         'hardware_tests':'NOT PERFORMED','fabrication_release':False}
(E/'layout_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
old=json.loads((E/'summary.json').read_text())
if not (E/'summary_pre_route.json').exists():
    old['stage']='Generator placement before routing; historical, not current PCB'
    (E/'summary_pre_route.json').write_text(json.dumps(old,indent=2)+'\n')
route=json.loads((E/'routing_summary.json').read_text())
old.update({'time_utc':summary['time_utc'],'stage':'Current routed native PCB validation',
            'erc_violations':0,'drc_violations':0,'drc_types':{},'drc_unconnected':0,
            'drc_parity':0,'tracks':route['copper_objects'],
            'source_report':'exports/control/layout_validation.json',
            'scope':'CAD consistency for experimental single-phase control; no hardware functionality or complete PSU'})
(E/'summary.json').write_text(json.dumps(old,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
