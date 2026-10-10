#!/usr/bin/python3
"""Four independent sink-controlled phase loops: explicit assumed averaged model.

No LTC3779 device simulation, shared ITH net, measured plant or hardware test.
This file preserves the earlier power_analysis.py and its outputs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
for key, child in [('MPLCONFIGDIR', 'matplotlib'), ('XDG_CACHE_HOME', 'cache')]:
    os.environ.setdefault(key, '/workspace/scratch/kicad-psu-runtime/' + child)
    Path(os.environ[key]).mkdir(parents=True, exist_ok=True)
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

GAIN = 41 * .002  # AMC3302 gain and proposed 2mohm shunt, V/A
VREF = 1.25
RIN, RSER, CPI = 47000., 22000., 22e-9
KP = RSER / RIN
KI = 1 / (RIN * CPI)
SENSOR_TAU = .0001  # proposed 1kohm / 100nF output filter


def frequency_case(gain_A_per_V, plant_tau_s, fs):
    f = np.geomspace(.1, fs / 2, 10000)
    s = 2j * np.pi * f
    # Non-inverting PI: measurement coefficient 1+KP+KI/s; command KP+KI/s.
    loop = GAIN * (1 + KP + KI / s) * gain_A_per_V
    loop /= (1 + s * plant_tau_s) * (1 + s * SENSOR_TAU)
    loop *= np.exp(-s * .5 / fs)
    db = 20 * np.log10(abs(loop))
    ph = np.unwrap(np.angle(loop)) * 180 / np.pi
    crosses = []
    for j in np.flatnonzero(db[:-1] * db[1:] <= 0):
        fraction = -db[j] / (db[j+1] - db[j])
        fc = np.exp(np.log(f[j]) + fraction * np.log(f[j+1] / f[j]))
        margin = 180 + ph[j] + fraction * (ph[j+1] - ph[j])
        crosses.append({'gain_crossover_Hz': float(fc), 'phase_margin_deg': float(margin),
                        'above_fs_div10': bool(fc > fs / 10)})
    return f, db, ph, crosses


def allocate(total, active):
    """No phase may be commanded above10A; failed phase does not silently rebalance."""
    active = np.asarray(active, dtype=bool)
    count = int(active.sum())
    target = np.zeros(4)
    if count:
        target[active] = min(max(total, 0), 10 * count) / count
    assert np.all(target <= 10 + 1e-12)
    return target


def simulate(kind, gain=None, plant_tau=None, duration=2.):
    """Averaged states in A/V/s; no actual PWM, diode or transistor dynamics.

    Local plant: requested current = clip(15 - K*(Vgate-.5),0,13.26).
    Constants15A/.5V are hypothetical local operating-point parameters.
    Gate-to-current sign is negative, and all four gate states are independent.
    """
    gate_gain = np.array(gain if gain is not None else [8., 10., 12., 9.])
    tau = np.array(plant_tau if plant_tau is not None else [.0004, .0005, .0003, .0006])
    dt = min(5e-6, tau.min() / 20, SENSOR_TAU / 20)
    count = int(round(duration / dt)) + 1
    sample_every = max(1, int(100e-6 / dt))
    states = []
    current = np.zeros(4)
    # Composite sensor errors are scenarios; they are not fitted device samples.
    error_gain = np.array([1.003, .997, 1.002, .998])
    offset_V = np.array([.002, -.002, .001, -.001])
    measured = VREF + offset_V
    integral = 5 - measured  # held at full local clamp during guarded OFF
    voltage, outer_v_integral, outer_i_integral = 0., 0., 0.
    fault_latched = False
    max_local_gate = 0.
    for index in range(count):
        t = index * dt
        ready = t >= .02  # hypothetical20ms global power/DIAG qualification
        active = np.ones(4, dtype=bool) if ready else np.zeros(4, dtype=bool)
        if kind == 'system_fault' and t >= 1.6:
            fault_latched = True  # unexpected loss => allOFF, no13.33A redistribution
        if fault_latched:
            active[:] = False
        if kind == 'controlled_three' and t >= .5:
            active[3] = False
        load = 1. if kind == 'system_fault' and .7 <= t < 1.2 else 2.5
        if kind in ('system_fault', 'controlled_three'):
            vset = min(max(t - .02, 0) / .2, 1) * 100
            ilimit = min(40., 10. * active.sum())
            dut_current = voltage / load
            ev, ei = vset - voltage, ilimit - dut_current
            cv = np.clip(.4 * ev + outer_v_integral, 0, ilimit)
            cc = np.clip(ilimit + .1 * ei + outer_i_integral, 0, ilimit)
            total_command = min(cv, cc)
            # Explicit modeled back-calculation anti-windup, not an installed circuit.
            outer_v_integral += dt * (20 * ev + 50 * (total_command - (.4 * ev + outer_v_integral)))
            outer_i_integral += dt * (20 * ei + 50 * (total_command - (ilimit + .1 * ei + outer_i_integral)))
        elif kind == 'low_load':
            total_command = .04 if t > .1 else 0.
            # Project policy: below0.5A whole-system command, high-current stagesOFF.
            # Separate low-current path is required; it is not modeled here.
            if total_command < .5:
                active[:] = False
        else:
            total_command = 40 * min(max(t - .02, 0) / .08, 1)
            dut_current = float(current.sum())
        target = allocate(total_command, active)
        command = VREF + GAIN * target
        measured += dt / SENSOR_TAU * (VREF + GAIN * error_gain * current + offset_V - measured)
        error = measured - command
        gate_raw = measured + KP * error + integral
        gate = np.clip(gate_raw, 0, 5)
        local_request = np.clip(15 - gate_gain * (gate - .5), 0, 13.26)
        local_request[~active] = 0
        current += dt / tau * (local_request - current)
        # Conditional anti-windup is an explicit desired implementation requirement.
        integrate = ((gate_raw > 0) & (gate_raw < 5)) | ((gate_raw >= 5) & (error < 0)) | ((gate_raw <= 0) & (error > 0))
        integral += dt * KI * error * integrate
        integral[~active] = 5 - measured[~active] - KP * error[~active]
        if kind in ('system_fault', 'controlled_three'):
            voltage += dt * (current.sum() - voltage / load) / 384e-6
            voltage = max(voltage, 0)
            dut_current = voltage / load
        else:
            dut_current = float(current.sum())
        max_local_gate = max(max_local_gate, float(gate.max()))
        if index % sample_every == 0:
            states.append([t, *current, float(current.sum()), total_command,
                           voltage, dut_current, int(active.sum()), float(fault_latched)])
    values = np.array(states)
    assert np.all(values[:, 1:5] >= -1e-12)
    assert np.all(values[:, 1:5] <= 13.26 + 1e-9)
    assert np.allclose(values[:, 1:5].sum(axis=1), values[:, 5], atol=1e-9)
    summary = {'case': kind, 'model_only': True, 'dt_s': dt,
               'gate_to_current_gain_A_per_V_assumption': gate_gain.tolist(),
               'plant_time_constants_s_assumption': tau.tolist(),
               'sensor_gain_factors_assumption': error_gain.tolist(),
               'sensor_output_offsets_V_assumption': offset_V.tolist(),
               'max_phase_current_A': values[:, 1:5].max(axis=0).tolist(),
               'max_total_phase_current_A': float(values[:, 5].max()),
               'final_phase_currents_A': values[-1, 1:5].tolist(),
               'final_output_V': float(values[-1, 7]),
               'fault_latched_in_model': fault_latched,
               'anti_windup_and_OFF_tracking_are_assumed_implemented': True,
               'initial_full_clamp_tracking_is_assumed_implemented': True,
               'model_gate_max_V': max_local_gate}
    if kind == 'system_fault':
        for start, end, label in [( .5, .65, 'CV_before_load_step'), (.95, 1.15, 'CC_1ohm'), (1.4, 1.55, 'CV_recovered')]:
            window = values[(values[:, 0] >= start) & (values[:, 0] <= end)]
            summary[label] = {'mean_voltage_V': float(window[:,7].mean()),
                              'mean_DUT_current_A': float(window[:,8].mean()),
                              'mean_phase_currents_A': window[:,1:5].mean(axis=0).tolist()}
    return values, summary


def plot_save(fig, out, name):
    for extension in ['png', 'pdf']:
        fig.savefig(out / (name + '.' + extension), dpi=180, bbox_inches='tight')
    plt.close(fig)


def main(args):
    out = Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    report = {'scope': 'Independent per-phase servo proposal; assumed averaged plant only',
              'hardware_tests': 0, 'LTC3779_device_model': False,
              'integrated_four_phase_hardware_implemented': False,
              'shared_ITH_connection': False,
              'proposed_measurement': {'IC':'AMC3302DWE', 'shunt_ohm':.002,
                    'gain_V_per_V':41, 'nominal_output_differential_V_per_A':GAIN,
                    'linear_input_range_V':[-.05,.05], 'linear_current_range_A':[-25,25],
                    'bandwidth_min_Hz':290000, 'offset_max_25C_V':50e-6,
                    'offset_drift_max_V_per_C':.5e-6, 'gain_error_max_25C_fraction':.002,
                    'gain_drift_max_per_C':35e-6, 'startup_settling_max_s':.0014},
              'PI_study_values': {'input_R_ohm':RIN,'series_R_ohm':RSER,'series_C_F':CPI,
                    'measurement_P_V_per_V':1+KP,'command_P_V_per_V':KP,
                    'integral_per_s':KI,'measurement_filter_tau_s':SENSOR_TAU},
              'assumed_model_parameters': {'switch_frequency_Hz':args.frequency,
                    'sample_delay_s':.5/args.frequency,'actuator_free_current_A':15,
                    'actuator_gate_offset_V':.5,'gate_limits_V':[0,5],
                    'native_average_limit_scenario_A':13.26,
                    'output_C_F_assumption':384e-6,
                    'global_ready_delay_s_assumption':.02,
                    'outer_CV_P_A_per_V':.4,'outer_CV_I_A_per_V_s':20,
                    'outer_CC_P_A_per_A':.1,'outer_CC_I_per_s':20,
                    'outer_backcalculation_per_s':50,
                    'total_current_measurement_is_ideal':True,
                    'load_resistance_scenarios_ohm':[2.5,1]},
              'limitations': ['Gate/ITH/current plant gain and poles are assumed, not LTC3779 specifications.',
                    'The 15A/.5V operating-point model and13.26A clamp are illustrative approximations.',
                    'Actual PWM, buck/boost transition, shared output parasitics and nonlinear MOSFET dynamics are absent.',
                    'Anti-windup, OFF tracking, reset/latch and signal gating require concrete hardware implementation.',
                    'Low-current and active0V function require another stage; this model switches high-current phasesOFF.',
                    'Output capacitor discharge after a load step is ideal and omits ESL; peak is not a physical prediction.'],
              'sources':[]}
    for filename in ['AMC3302.pdf','CSD13381F4.pdf','LTC3779.pdf','OPA192.pdf']:
        p=ROOT/'references'/filename
        report['sources'].append({'file':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    assert np.isclose(GAIN*10,.82)
    assert np.isclose(25*.002,.05)
    assert np.allclose(allocate(40,[1,1,1,0]),[10,10,10,0])
    assert np.allclose(allocate(-1,[1,1,1,1]),[0,0,0,0])
    # Sensor-only bounds: shunt accuracy is a design requirement, not a selected MPN.
    bounds=[]
    for temp_delta in [0,75]:
        gain_bound=.001+.002+temp_delta*(15e-6+35e-6)
        offset_current=(50e-6+temp_delta*.5e-6)/.002
        for total in [.04, .5, 40]:
            each=total/4
            low=(each-offset_current)/(1+gain_bound)
            high=(each+offset_current)/(1-gain_bound)
            bounds.append({'total_command_A':total,'delta_T_from25C_C':temp_delta,
                           'combined_sensor_gain_bound_fraction':gain_bound,
                           'sensor_input_offset_equivalent_A':offset_current,
                           'phase_min_A_if_linear_bipolar_control':float(low),
                           'phase_max_A_if_linear_bipolar_control':float(high),
                           'excludes_diff_amp_reference_command_filter_errors':True})
    report['sensor_only_tolerance_scenarios']=bounds
    fig, ax = plt.subplots(figsize=(9,4.6),layout='constrained')
    phase_command=np.geomspace(.001,10,500)
    for temp_delta in [0,75]:
        gain_bound=.001+.002+temp_delta*(15e-6+35e-6)
        offset_current=(50e-6+temp_delta*.5e-6)/.002
        lower=(phase_command-offset_current)/(1+gain_bound)
        upper=(phase_command+offset_current)/(1-gain_bound)
        ax.fill_between(phase_command,lower,upper,alpha=.25,
                        label=f'Sensor/shunt-scenario, ΔT={temp_delta:g} °C')
    ax.plot(phase_command,phase_command,color='black',linewidth=1,label='Ideel lige strøm')
    ax.axhline(0,color='gray',linestyle=':')
    ax.set_yscale('symlog',linthresh=.1)
    ax.set(xscale='log',xlabel='Ønsket fasestrøm (A)',
           ylabel='Beregnet strømområde (A)',title='Sensoroffset giver ingen præcis milliampere-regulering')
    ax.legend();ax.grid(alpha=.25)
    fig.text(.5,-.02,'Sensor-only bound; opamp/reference/kommando/calibrering udeladt. Negative grænser betyder ikke verificeret sinkdrift.',ha='center',fontsize=8)
    plot_save(fig,out,'phase_balance_sensor_tolerance')
    # Independent loops remove L/valley offsets from ideal DC equality, not sensor errors.
    loop_rows=[]
    fig,ax=plt.subplots(figsize=(9,4.8),layout='constrained')
    for gain in [2.,10.,30.]:
        for tau in [.0001,.0004,.001]:
            f,db,phase,crosses=frequency_case(gain,tau,args.frequency)
            loop_rows.append({'gate_to_current_gain_A_per_V_assumption':gain,
                              'plant_tau_s_assumption':tau,'crossovers':crosses})
            ax.plot([x['gain_crossover_Hz'] for x in crosses],
                    [x['phase_margin_deg'] for x in crosses],'o',label=f'K={gain:g} A/V, τ={tau*1e3:g} ms')
    ax.set(xscale='log',xlabel='Modelcrossover (Hz)',ylabel='Model-fasemargin (grader)',
           title='Individuel servo: følsomhed for ukendt ITH/gate-plant')
    ax.grid(alpha=.25);ax.legend(fontsize=8,ncol=3,loc='best')
    fig.text(.5,-.02,'PI 47 kΩ / 22 kΩ / 22 nF, filter 1 kΩ / 100 nF. Plant er antaget; ingen LTC3779-stabilitetsgodkendelse.',ha='center',fontsize=8)
    plot_save(fig,out,'independent_phase_loop_sensitivity')
    report['loop_sensitivity_scenarios']=loop_rows
    summaries=[]
    for kind in ['forty_amp','system_fault','controlled_three','low_load','clamp_authority']:
        values,summary=simulate('forty_amp' if kind=='clamp_authority' else kind,
                                 gain=[2.,2.,2.,2.] if kind=='clamp_authority' else None)
        summary['case']=kind;summaries.append(summary)
        if kind in ['forty_amp','system_fault','controlled_three']:
            fig,axes=plt.subplots(2,1,figsize=(9,6.8),layout='constrained',sharex=True)
            for n in range(4):axes[0].plot(values[:,0],values[:,n+1],label=f'Fase {n+1}')
            axes[0].axhline(10,color='black',linestyle=':',linewidth=1)
            axes[0].set(ylabel='Fasestrøm (A)',title={'forty_amp':'Fire lokale servoer til 40 A: sensorfejl resterer',
                 'system_fault':'Ydre CV/CC, lastspring og latched samlet shutdown',
                 'controlled_three':'Kontrolleret phase-off: kapacitet reduceres til 30 A'}[kind])
            axes[0].legend();axes[1].plot(values[:,0],values[:,5],label='Sum af fasestrømme')
            axes[1].plot(values[:,0],values[:,6],linestyle='--',label='Fælles strømkommando')
            if kind!='forty_amp':axes[1].plot(values[:,0],values[:,7],label='Udgangsspænding (V)')
            axes[1].set(xlabel='Tid (s)',ylabel='A / V');axes[1].legend()
            for a in axes:a.grid(alpha=.25)
            fig.text(.5,-.02,'Gennemsnitsmodel. Loop/anti-windup/gating/plant er antaget; outputlaststep udelader ESL.',ha='center',fontsize=8)
            plot_save(fig,out,'phase_balance_'+kind)
    report['dynamic_scenarios']=summaries
    report['low_load_policy']={'high_current_stages_OFF_below_total_command_A':.5,
             'phase_shedding_not_claimed_to_provide_precision_mA':True,
             'unexpected_phase_fault_action':'latched allOFF; no automatic reallocation',
             'controlled_three_phase_capacity_A':30}
    # Clamp-authority counterexample: even stable small-signal loops cannot create
    # zero current if the actuator saturates before providing enough ITH sink.
    report['clamp_authority_counterexample']={'assumed_free_current_A':15,
       'assumed_gate_offset_V':.5,'assumed_gate_to_current_gain_A_per_V':2,
       'maximum_gate_V':5,'lowest_controllable_current_with_RUN_enabled_A':6,
       'actual_LTC3779_value':False,'requires_RUN_shutdown_for_lower_current_in_this_scenario':True}
    report['checks']={'passed':['sensor scale and full-scale conversion',
              'allocator capacity and negative-command clamps','nonnegative phase currents',
              'modeled native current ceiling','phase sums','latched allOFF after unexpected fault'],
              'hardware_tests':0}
    fault=next(x for x in summaries if x['case']=='system_fault')
    assert fault['fault_latched_in_model'] and max(fault['final_phase_currents_A'])<1e-6
    (out/'phase_balance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'file':str(out/'phase_balance.json'),'dynamic_scenarios':len(summaries),
                      'hardware_tests':0,'plots':5},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--frequency',type=float,default=101800.)
    p.add_argument('--output-dir',default=str(ROOT/'exports/analysis'))
    args=p.parse_args();assert args.frequency>0
    main(args)
