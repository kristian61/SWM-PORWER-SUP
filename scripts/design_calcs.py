#!/usr/bin/python3
"""Reproduce explicit budgets and ideal buck calculations, not hardware tests."""
from pathlib import Path
import json
import os
runtime = Path('/workspace/scratch/kicad-psu-runtime')
for key, relative in [('MPLCONFIGDIR', 'matplotlib'), ('XDG_CACHE_HOME', 'cache')]:
    os.environ.setdefault(key, str(runtime / relative))
    Path(os.environ[key]).mkdir(parents=True, exist_ok=True)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports' / 'analysis'
OUT.mkdir(parents=True, exist_ok=True)
power_out = 100.0 * 40.0
eta_dc, eta_ac, pf = 0.95, 0.915, 0.95
bus, mains = 110.0, 230.0
inductance, frequency, phases = 150e-6, 101.8e3, 4
power_bus = power_out / eta_dc
power_in = power_bus / eta_ac
valley_max = 0.110 / (0.006 * 0.99)
ripple_max_at_120 = 120.0 / (4 * inductance * frequency)
budget = {
    'scope': 'algebraic design assumptions only; no measured performance',
    'inputs': {'Vout_V': 100, 'Iout_A': 40, 'bus_V': bus,
               'mains_V': mains, 'DC_efficiency_assumption': eta_dc,
               'AC_efficiency_typical_datasheet': eta_ac,
               'power_factor_typical_datasheet': pf,
               'phase_L_H': inductance, 'phase_fs_Hz': frequency,
               'phase_count_hypothesis': phases},
    'power': {'output_W': power_out, 'bus_W': power_bus,
              'AC_input_W': power_in, 'AC_current_A': power_in / (mains * pf),
              'bus_current_A': power_bus / bus, 'module_W': power_bus / 2,
              'DC_loss_W': power_bus - power_out,
              'AC_loss_W': power_in - power_bus,
              'total_heat_W': power_in - power_out},
    'single_phase': {'L_uH': inductance * 1e6, 'frequency_kHz': frequency / 1e3,
                     'buck_ripple_max_at_120V_A_pp': ripple_max_at_120,
                     'worst_valley_A': valley_max,
                     'worst_buck_peak_A': valley_max + ripple_max_at_120,
                     'native_average_limit_nominal_A': 0.05 / 0.004,
                     'native_average_limit_low_A': 0.0475 / (0.004 * 1.01),
                     'native_average_limit_high_A': 0.0525 / (0.004 * 0.99)},
    'OVP': {'module_threshold_low_V': 57.6, 'module_threshold_high_V': 67.2,
            'two_module_threshold_sum_V': 134.4,
            'static_threshold_is_transient_clamp': False,
            'power_prototype_procedural_input_max_V': 120},
    'stored_energy_at_100V_J': {
        '10uF_after_limiter_example': .5 * 10e-6 * 100**2,
        'single_phase_96uF_nominal': .5 * 96e-6 * 100**2,
        'four_96uF_phases_example': .5 * 384e-6 * 100**2,
        '1880uF_original_system_example': .5 * 1880e-6 * 100**2},
}
# Separate conditional addition: the proposed disconnect's fixed resistor and
# switch bank are OUTSIDE the original assumed95% DC-regulator boundary. Solve
# current consistently instead of reusing38.28A after inserting a voltage drop.
protection_model = OUT / 'bus_disconnect_envelope.json'
if protection_model.exists():
    protection = json.loads(protection_model.read_text())
    requirement = protection['design_requirements_NOT_verified']
    switch_R = protection['switchbank_screen_NOT_qualification']['pair_bank_hot_RDS_estimate_assumes_2x25C_ohm']
    additions = []
    for name, rseries in [('nominal_series_R', requirement['Rseries_nominal_ohm']),
                          ('maximum_series_R_budget', requirement['Rseries_max_ohm'])]:
        total_R = rseries + switch_R
        discriminant = bus**2 - 4*total_R*power_bus
        if discriminant <= 0:
            raise RuntimeError('Conditional protected bus cannot supply assumed regulator power')
        current = 2*power_bus/(bus + discriminant**.5)
        delivered_bus = bus-current*total_R
        bus_loss = current**2*total_R
        mains_power = (power_bus+bus_loss)/eta_ac
        additions.append({'case': name, 'fixed_series_R_ohm': rseries,
                          'switchbank_hot_R_assumption_ohm': switch_R,
                          'source_current_A': current, 'regulator_input_V': delivered_bus,
                          'series_resistor_heat_W': current**2*rseries,
                          'switchbank_heat_W': current**2*switch_R,
                          'additional_bus_heat_W': bus_loss,
                          'AC_input_W': mains_power,
                          'AC_current_at230V_PF095_A': mains_power/(mains*pf),
                          'system_heat_including_new_bus_stage_W': mains_power-power_out,
                          'ideal100V_duty': 100/delivered_bus,
                          'buck_only_9167pct_exceeded': 100/delivered_bus > 11/12})
    budget['conditional_bus_disconnect_addition'] = {
        'scope': 'Unimplemented fixed-R plus hot-switchbank estimate; all efficiencies and R bounds unqualified',
        'DC95percent_boundary': 'Original regulator including its own power stage; new bus disconnect loss added separately',
        'not_included': ['Extra auxiliary/fan power not already in module data',
                         'Actual buck/boost efficiency and hot RDS/SOA',
                         'Assembly/contact resistance and dynamic fault energy'],
        'cases': additions}
(OUT / 'design_budget.json').write_text(json.dumps(budget, indent=2) + '\n')
vout = np.linspace(0, 100, 2001)
duty = vout / bus
single = bus * duty * (1 - duty) / (inductance * frequency)
fraction = (phases * duty) % 1
summed = bus * fraction * (1 - fraction) / (phases * inductance * frequency)
fig, ax = plt.subplots(figsize=(9, 4.8), layout='constrained')
ax.plot(vout, single, label='Én ideal buckfase')
ax.plot(vout, summed, label='Idealsum af fire faser med 90° forskydning')
ax.set(xlabel='Udgangsspænding (V)', ylabel='Spolestrømripple (A p-p)',
       title='Beregnet buckripple: 110 V bus, 150 µH, 101,8 kHz')
ax.grid(alpha=.25)
ax.legend(loc='upper left')
fig.text(.5, -.03, 'Referenceformler. Strømfordeling, tolerancer og LTC3779 buck/boost-overgang er ikke medregnet.',
         ha='center', fontsize=8)
fig.savefig(OUT / 'ideal_buck_ripple.png', dpi=180, bbox_inches='tight')
fig.savefig(OUT / 'ideal_buck_ripple.pdf', bbox_inches='tight')
plt.close(fig)
print(json.dumps({'budget': str(OUT / 'design_budget.json'),
                  'AC_current_A': budget['power']['AC_current_A'],
                  'total_heat_W': budget['power']['total_heat_W'],
                  'worst_buck_peak_A': budget['single_phase']['worst_buck_peak_A']}, indent=2))
