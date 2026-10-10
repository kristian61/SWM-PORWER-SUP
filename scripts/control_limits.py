#!/usr/bin/python3
"""Check static control bounds from actual BOM values; no transient model."""
from pathlib import Path
import csv, json, math, re

ROOT=Path(__file__).resolve().parents[1]
with (ROOT/'bom/control.csv').open(newline='') as source:
    parts={r['Reference']:r for r in csv.DictReader(source)}
def resistance(ref):
    value=parts[ref]['Value']
    match=re.match(r'(\d+(?:\.\d+)?)([kM]?)',value)
    if not match:raise ValueError(value)
    return float(match[1])*{'':1,'k':1e3,'M':1e6}[match[2]]

def transfer(vfb,vcmd,reference=2.5):
    # All averaging-network resistors are 1 MOhm. Includes actual passive
    # VMID loading, rather than assuming an unloaded 1.25 V reference.
    assert all(math.isclose(resistance('R'+str(i)),1e6) for i in [1,2,3,4,16,17,18,19,20,21])
    inj=vfb+vcmd
    midpoint=(300*reference+inj)/602
    extra=(7*vfb-5*vcmd-2*midpoint)/(6e6)
    vout=83*vfb-82*vcmd+820e3*extra
    return {'VFB_V':vfb,'VCMD_V':vcmd,'INJ_NODE_V':inj,
            'VMID_V':midpoint,'VDIFF_V':midpoint,'VOUT_V':vout}

divider_pairs=[(11,12),(14,15),(26,27),(28,29),(30,31),
               (32,33),(34,35),(36,37),(38,39),(40,41)]
nominal_load=sum(2.5/(resistance('R'+str(a))+resistance('R'+str(b)))
                 for a,b in divider_pairs)+2.5/resistance('R5')
midpoint=transfer(1.2,0)['VMID_V']
nominal_load+=(1.25-midpoint)/resistance('R14')
bias=resistance('R13')
assert math.isclose(bias,2490),'Review the brownout budget if R13 changes'

# Deliberately broader than 25 C initial accuracy: 1% reference envelope,
# 1% bias resistor, 0.1% divider resistors, 5% unspecified R5 and 0.5 uA
# extra input/loading allowance. These are conservative design assumptions.
high_reference=2.525
worst_load=nominal_load*(high_reference/2.5)/.999
worst_load+=high_reference*(1/(resistance('R5')*.95)-1/resistance('R5'))+.5e-6
threshold_low=4.65*.98
remaining=(threshold_low-high_reference)/(bias*1.01)-worst_load
assert remaining>65e-6,'LM4040 minimum-current reserve missing before AUX fault'

windows={}
for name,a,b in [('VCMD_HI',26,27),('ISET_LO',28,29),('ISET_HI',30,31),
                 ('IMON_LO',32,33),('VDIFF_LO',34,35),('VDIFF_HI',36,37)]:
    top,bottom=resistance('R'+str(a)),resistance('R'+str(b))
    nom=2.5*bottom/(top+bottom)
    # Comparator max offset over -40..125 C, plus worst 20 nA input bias
    # and nominal-divider tolerances. Command-source accuracy is excluded.
    delta=.0055+20e-9*(top*bottom/(top+bottom))
    low=2.4975*(bottom*.999)/(top*1.001+bottom*.999)-delta
    high=2.5025*(bottom*1.001)/(top*.999+bottom*1.001)+delta
    windows[name]={'nominal_V':nom,'low_bound_V':low,'high_bound_V':high,
                   'scope':'25 C reference initial accuracy plus full-temperature comparator offset; not full system bound'}

cold=[]
for cmd in [0.,.6,1.2]:
    a,b=transfer(0,cmd)['VOUT_V'],transfer(1,cmd)['VOUT_V']
    fb=-a/(b-a)
    state=transfer(fb,cmd);cold.append(state)
    assert abs(state['VOUT_V'])<1e-10
    assert windows['VDIFF_LO']['high_bound_V']<state['VDIFF_V']<windows['VDIFF_HI']['low_bound_V']
    assert .1>windows['IMON_LO']['high_bound_V']

report={
    'scope':'Static KCL and arithmetic tolerance checks only; not startup/rail-off/loop simulation',
    'hardware_tests':0,
    'R13_bias_ohm':bias,
    'reference_nominal_load_A_at_VCMD0':nominal_load,
    'reference_nominal_shunt_current_A_at_AUX5V':(5-2.5)/bias-nominal_load,
    'reference_nominal_shunt_current_A_at_AUX4p75V':(4.75-2.5)/bias-nominal_load,
    'conservative_brownout_scenario':{'AUX_threshold_low_V':threshold_low,
        'reference_upper_assumption_V':high_reference,'bias_resistor_upper_ohm':bias*1.01,
        'load_upper_A':worst_load,'remaining_shunt_A':remaining,
        'LM4040_required_minimum_A':65e-6,'reserve_A':remaining-65e-6},
    'windows':windows,
    'ISET_low_window_equivalent_current_A':{
        key:(windows['ISET_LO'][key]-.1)/.05 for key in ['nominal_V','low_bound_V','high_bound_V']},
    'cold_output_zero_static_states':cold,
    'CV_nominal_examples':[transfer(1.2,cmd) for cmd in [0,.004914,1.153876,1.2]],
    'ENABLE_default_V':2.5e-6/(1/1e4+1/1e5),
    'ENABLE_armed_V_with_internal_pullup':(5/1e4+2.5e-6)/(1/1e4+1/1e4+1/1e5),
    'not_checked':['AUX rail backfeed','opamp saturation and startup timing',
                   'actual loop dynamics','bus protection','complete fault coverage'],
}
out=ROOT/'exports/analysis/control_limits.json'
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'reference_load_uA':nominal_load*1e6,
                  'brownout_remaining_uA':remaining*1e6,'output':str(out)},indent=2))
