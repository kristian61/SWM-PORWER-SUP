#!/usr/bin/python3
"""Bounds for a separate, unimplemented low-current output range.

INA190 Rev D values are read from the original TI PDF. These calculations
are not an INA190 circuit simulation, a safety qualification or hardware tests.
"""
from pathlib import Path
import json
import math
import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports/analysis'
OUT.mkdir(parents=True, exist_ok=True)

# Table 6.5 specifies VOS at VS=1.8 V, VIN+=12 V, VREF=VS/2.
# Add bounds for changing those conditions; do not reuse 15 uV alone at 5 V.
offset_terms = {
    'offset_25C_uV': 15.0,
    'supply_change_1p8_to_5V_uV': (5.0-1.8)*5.0,
    'common_mode_change_12_to_0V_uV': 12*10**(-132/20)*1e6,
    'reference_change_2p5_to_0p2V_uV': (2.5-0.2)*4.0,
    'offset_drift_for_50C_change_uV': 80e-3*50,
}
offset_bound = sum(offset_terms.values())*1e-6
gain = 100.0  # INA190A3; not a high-side sensor for 100 V.
ratio_bound = .003 + 7e-6*50 + .001 + 25e-6*50
ranges = []
for resistance, maximum in [(1.0, .02), (.1, .2)]:
    examples = []
    for current in [.001, .005, .01, maximum]:
        if current > maximum:
            continue
        # 1 mV command/reference uncertainty is an explicit scenario,
        # not a selected DAC specification. Include OPA4192 25 uV offset.
        bound = offset_bound/resistance + current*ratio_bound
        bound += (1e-3+25e-6)/(gain*resistance)
        examples.append({'actual_current_A': current,
                         'arithmetic_error_bound_A': bound,
                         'relative_bound_percent': 100*bound/current})
    ranges.append({'shunt_requirement_ohm': resistance,
                   'gain_V_per_V': gain, 'range_max_A': maximum,
                   'sensor_V_at_range_max': .2+gain*resistance*maximum,
                   'shunt_drop_V_at_range_max': resistance*maximum,
                   'shunt_loss_W_at_range_max': resistance*maximum**2,
                   'hypothetical_40A_shunt_loss_W': resistance*40**2,
                   'examples': examples})

energies = [{'capacitance_uF': c*1e6, 'voltage_V': v,
             'stored_energy_J': .5*c*v*v}
            for c in [1e-6, 96e-6, 384e-6]
            for v in [5., 100.]]
discharge = [{'C_uF': c*1e6, 'R_ohm': 10_000,
              'initial_voltage_V': 100., 'target_voltage_V': .1,
              'ideal_time_s': 10_000*c*math.log(100/.1),
              'resistor_initial_W': 100**2/10_000}
             for c in [1e-6, 96e-6]]

assert abs(ranges[0]['sensor_V_at_range_max']-2.2) < 1e-12
assert abs(ranges[1]['sensor_V_at_range_max']-2.2) < 1e-12
assert ranges[0]['examples'][0]['relative_bound_percent'] < 7
assert math.isclose(.5*96e-6*100**2, .48, rel_tol=1e-12)
assert discharge[1]['ideal_time_s'] > discharge[0]['ideal_time_s']

result = {
    'scope': 'bounds for unimplemented low-current ranges; no hardware tests',
    'candidate': 'INA190A3IDDFR, low-side; 1 or 0.1 ohm external Kelvin shunt',
    'implemented_in_existing_control': False,
    'sensor_reference_V_assumption': .2,
    'datasheet_limits': {'common_mode_V': [-.2, 40.],
                          'supply_V': [1.7, 5.5],
                          'gain_error_A3_max_fraction': .003},
    'offset_terms': offset_terms,
    'combined_input_offset_bound_uV': offset_bound*1e6,
    'gain_and_shunt_ratio_bound_fraction': ratio_bound,
    'assumed_shunt': {'tolerance_fraction': .001,
                     'temperature_coefficient_ppm_per_C': 25,
                     'temperature_change_C': 50,
                     'manufacturer_part': 'NOT SELECTED'},
    'assumed_command_and_reference_uncertainty_V': .001,
    'ranges': ranges,
    'energy': energies,
    'discharge': discharge,
    'linear_pass_short_scenarios_W': {
        '100V_20mA': 100*.02, '100V_200mA': 100*.2},
    'missing': ['post-bulk pass element with DC/pulse SOA',
                'range interlock and fault-rated bypass/disconnect',
                'independent load voltage supervision',
                'loop design, output-capacitor choice, dynamics and calibration'],
}
(OUT/'low_current.json').write_text(json.dumps(result, indent=2)+'\n')
pdf = ROOT/'references/INA190.pdf'
metadata = [{'file': pdf.name,
             'official_url': 'https://www.ti.com/lit/ds/symlink/ina190.pdf',
             'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest(),
             'document': 'SBOS863D, revised November 2019',
             'usage': 'Unimplemented low-current architecture study'}]
(ROOT/'references/low-current-sources.json').write_text(json.dumps(metadata, indent=2)+'\n')
print(json.dumps({'input_offset_bound_uV': offset_bound*1e6,
                  'output': str(OUT/'low_current.json')}, indent=2))
