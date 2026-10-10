#!/usr/bin/python3
"""Small-signal study for a separate, UNIMPLEMENTED post-bulk current stage.

This is neither a transistor device model nor a KiCad compensation release.
Plant transconductance and gate pole are deliberately swept assumptions. INA190
A3 bandwidth is a typical datasheet value, not a guaranteed fault response.
"""
from pathlib import Path
import hashlib
import json
import os
cache = Path('/workspace/scratch/kicad-psu-runtime/cache')
cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('XDG_CACHE_HOME', str(cache))
os.environ.setdefault('MPLCONFIGDIR', str(cache / 'matplotlib'))
import numpy as np
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'exports/analysis'
OUT.mkdir(parents=True, exist_ok=True)
frequency = np.geomspace(.01, 1e6, 15000)
s = 2j*np.pi*frequency
sensor_pole = 35000.0
zero = 1000.0
rolloff = 10000.0
time = np.linspace(0, .6, 6001)
records = []
plt.figure(figsize=(8.1, 4.6))

for resistance, maximum, color in [(1., .02, '#1565c0'), (.1, .2, '#e65100')]:
    sensor_gain = 100*resistance
    # Limit the maximum-gm ideal integrator crossover to about100Hz. This
    # deliberately slow trial does not provide fast short-circuit protection.
    integral = 2*np.pi*100/(2*sensor_gain)
    for gm in [.05, .2, 1., 2.]:
        for gate_pole in [100., 1000., 20000.]:
            controller = integral/s*(1+s/(2*np.pi*zero))/(1+s/(2*np.pi*rolloff))
            plant = gm/(1+s/(2*np.pi*gate_pole))
            sensor_tf = sensor_gain/(1+s/(2*np.pi*sensor_pole))
            loop = controller*plant*sensor_tf
            crossings = np.flatnonzero((abs(loop[:-1]) >= 1) & (abs(loop[1:]) < 1))
            if len(crossings) != 1:
                raise RuntimeError('Expected exactly one unity crossing in this assumed plant')
            i = int(crossings[0])
            ratio = -np.log(abs(loop[i])) / (np.log(abs(loop[i+1]))-np.log(abs(loop[i])))
            fc = float(np.exp(np.log(frequency[i]) + ratio*np.log(frequency[i+1]/frequency[i])))
            phase = np.unwrap(np.angle(loop))*180/np.pi
            margin = float(180+phase[i]+ratio*(phase[i+1]-phase[i]))
            denominator = np.polymul([1/(2*np.pi*rolloff), 1], [1/(2*np.pi*gate_pole), 1])
            denominator = np.polymul(denominator, [1/(2*np.pi*sensor_pole), 1])
            denominator = np.polymul(denominator, [1, 0])
            loop_num = integral*gm*sensor_gain*np.array([1/(2*np.pi*zero), 1])
            closed_den = np.polyadd(denominator, loop_num)
            current_num = integral*gm*sensor_gain*np.polymul([1/(2*np.pi*zero), 1], [1/(2*np.pi*sensor_pole), 1])
            poles = np.roots(closed_den)
            if not np.all(poles.real < 0):
                raise RuntimeError('Unstable assumed current-stage case')
            _, response = signal.step(signal.TransferFunction(current_num, closed_den), T=time)
            outside = np.flatnonzero(abs(response-1) > .01)
            settling = float(time[outside[-1]+1]) if len(outside) and outside[-1]+1 < len(time) else None
            records.append({'range_max_A': maximum, 'shunt_ohm': resistance,
                            'assumed_gm_A_per_V': gm, 'assumed_gate_pole_Hz': gate_pole,
                            'controller_integral_per_s': integral,
                            'controller_proportional_V_per_V': integral/(2*np.pi*zero),
                            'unity_crossover_Hz': fc, 'phase_margin_deg': margin,
                            'closed_loop_poles_per_s': [[float(p.real), float(p.imag)] for p in poles],
                            'normalized_step_peak': float(max(response)),
                            'small_signal_1pct_settling_s': settling})
            if resistance == 1 and gate_pole == 100:
                plt.plot(time*1000, response, label=f'gm={gm:g} A/V; gatepole100Hz')

plt.xlabel('Tid efter lille strømkommandotrinsændring / ms')
plt.ylabel('Normaliseret ekstra strøm')
plt.title('Antaget efterfølgende lavstrømstrin – ikke en komponent-SPICE-model')
plt.grid(alpha=.25)
plt.legend(fontsize=8)
plt.tight_layout()
for extension in ['png', 'pdf']:
    plt.savefig(OUT / ('low_current_loop_assumed_plant.'+extension), dpi=170)
plt.close()

result = {'scope': 'Assumed linear small-signal post-bulk current stage; not implemented',
          'hardware_tests_performed': False, 'transistor_device_model': False,
          'implemented_in_CAD': False,
          'sensor_bandwidth_Hz': sensor_pole, 'sensor_bandwidth_status': 'INA190A3 TYPICAL ONLY, SBOS863D p6',
          'controller_zero_Hz': zero, 'controller_rolloff_Hz': rolloff,
          'minimum_phase_margin_deg': min(r['phase_margin_deg'] for r in records),
          'maximum_1pct_settling_s': max(r['small_signal_1pct_settling_s'] for r in records if r['small_signal_1pct_settling_s'] is not None),
          'cases': records,
          'energy_bypass_warning': 'A capacitor after the pass element can discharge directly into DUT; current-loop stability cannot prevent this.',
          'excluded': ['Large signal startup, OFF tracking, saturation, anti-windup and CV/CC handover',
                       'Transistor gm dependence on bias/temperature, high-side drive and SOA',
                       'Guaranteed sensor delay, enable settling, noise, offset and fault clamp',
                       'Physical disconnection, interlock, reverse blocking and shorted pass element',
                       'Load capacitance/inductance, cable parasitics and sensor placement'],
          'source_sha256': hashlib.sha256((ROOT/'references/INA190.pdf').read_bytes()).hexdigest()}
assert len(records) == 24
assert result['minimum_phase_margin_deg'] > 45
(OUT/'low_current_loop.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k: result[k] for k in ['scope', 'minimum_phase_margin_deg', 'maximum_1pct_settling_s']}, indent=2))
