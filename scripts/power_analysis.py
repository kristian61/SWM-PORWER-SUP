#!/usr/bin/python3
"""Reproducible engineering sensitivity models; not a device or hardware model.

Run with /usr/bin/python3. Values derived from the BOM are accompanied by
explicit scenario assumptions. No LTC3779 current-command gain is inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path('/workspace/scratch/kicad-psu-runtime')
for name, folder in [('MPLCONFIGDIR', 'matplotlib'), ('XDG_CACHE_HOME', 'cache')]:
    os.environ.setdefault(name, str(RUNTIME / folder))
    Path(os.environ[name]).mkdir(parents=True, exist_ok=True)

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def buck_ripple(vin: float, vout: float, inductance: float, frequency: float) -> float:
    assert vin > 0 and 0 <= vout <= vin and inductance > 0 and frequency > 0
    d = vout / vin
    return vin * d * (1 - d) / (inductance * frequency)


def waveforms(vin, vout, current, inductance, frequency, phases=1, samples=32768):
    """Ideal CCM triangular currents, including potentially negative valleys."""
    assert phases >= 1 and isinstance(phases, int) and current >= 0
    x = np.arange(samples) / samples
    d = vout / vin
    delta = buck_ripple(vin, vout, inductance, frequency)
    input_current = np.zeros(samples)
    output_current = np.zeros(samples)
    for n in range(phases):
        p = (x - n / phases) % 1
        if d == 0 or d == 1:
            i = np.full(samples, current)
        else:
            i = np.where(p < d, current - delta / 2 + delta * p / d,
                         current + delta / 2 - delta * (p - d) / (1 - d))
        input_current += np.where(p < d, i, 0)
        output_current += i
    input_ac = input_current - input_current.mean()
    output_ac = output_current - output_current.mean()
    return x, input_ac, output_ac


def capacitor_metrics(vin, vout, current, inductance, frequency, phases,
                      capacitance, esr):
    _, icin, icout = waveforms(vin, vout, current, inductance, frequency, phases)
    dt = 1 / (frequency * len(icout))
    vc = np.cumsum(icout) * dt / capacitance
    vc -= vc.mean()
    voltage = vc + esr * icout
    return {
        'phase_count_ideal': phases,
        'phase_ripple_A_pp': buck_ripple(vin, vout, inductance, frequency),
        'input_capacitor_bank_Irms_A': float(np.sqrt(np.mean(icin**2))),
        'output_capacitor_bank_Irms_A': float(np.sqrt(np.mean(icout**2))),
        'output_current_sum_ripple_A_pp': float(np.ptp(icout)),
        'capacitive_voltage_ripple_V_pp': float(np.ptp(vc)),
        'with_ESR_voltage_ripple_V_pp': float(np.ptp(voltage)),
        'output_bank_effective_C_F_assumption': capacitance,
        'output_bank_ESR_ohm_assumption': esr,
        'output_bank_ESR_heat_W': float(np.mean(icout**2) * esr),
    }


def mosfet_losses(vin, vout, current, inductance, frequency, hot_multiplier,
                  edge_sum_s, qrr_C=46e-9):
    """Buck topology only: Q1/Q2 switch, Q4 passes current, Q3 is off.

    Hard-switch overlap and V*Qrr are reference scalings, not guarantees.
    Coss/ESL, ringing, snubbers and controller quiescent losses are excluded.
    """
    d = vout / vin
    delta = buck_ripple(vin, vout, inductance, frequency)
    square = current**2 + delta**2 / 12
    rdson = .011 * hot_multiplier
    losses = {
        'Q1_conduction_W': square * rdson * d,
        'Q2_conduction_W': square * rdson * (1 - d),
        'Q3_conduction_W': 0.0,
        'Q4_conduction_W': square * rdson,
        'Q1_hard_switch_overlap_W': .5 * vin * current * frequency * edge_sum_s,
        'reverse_recovery_reference_scaling_W': vin * qrr_C * frequency,
        'two_deadtime_diode_intervals_W': 2 * 60e-9 * .88 * current * frequency,
        'two_gates_drive_W': 2 * 35e-9 * 10 * frequency,
    }
    losses['modeled_subtotal_W'] = sum(losses.values())
    losses['thermal_multiplier_assumption'] = hot_multiplier
    losses['rise_plus_fall_time_s_assumption'] = edge_sum_s
    losses['Qrr_C_reference_scaling'] = qrr_C
    losses['Q1_assigned_heat_W'] = (losses['Q1_conduction_W'] +
                                  losses['Q1_hard_switch_overlap_W'] +
                                  losses['reverse_recovery_reference_scaling_W'])
    losses['Q2_assigned_heat_W'] = (losses['Q2_conduction_W'] +
                                  losses['two_deadtime_diode_intervals_W'])
    losses['Q4_assigned_heat_W'] = losses['Q4_conduction_W']
    return losses


def common_valley_currents(total_current, ripple, shunts, offsets_V):
    """Solve shared valley sense command with hypothetical comparator offsets."""
    shunts, offsets_V, ripple = map(np.asarray, (shunts, offsets_V, ripple))
    sense = (total_current - np.sum(ripple / 2) -
             np.sum(offsets_V / shunts)) / np.sum(1 / shunts)
    valley = (sense + offsets_V) / shunts
    average = valley + ripple / 2
    assert np.isclose(average.sum(), total_current, atol=1e-10)
    return float(sense), valley, average


def compensation(s, resistance=1e4, series_cap=10e-9, parallel_cap=100e-12):
    return 1 / (1 / (resistance + 1 / (s * series_cap)) + s * parallel_cap)


def output_impedance(s, load, capacitance, esr):
    return load * (1 + s * esr * capacitance) / (1 + s * capacitance * (load + esr))


def crossover_rows(frequency, loop):
    gain = 20 * np.log10(np.abs(loop))
    phase = np.unwrap(np.angle(loop)) * 180 / np.pi
    results = []
    for index in np.flatnonzero(gain[:-1] * gain[1:] <= 0):
        fraction = -gain[index] / (gain[index + 1] - gain[index])
        logfc = np.log10(frequency[index]) + fraction * np.log10(frequency[index+1] / frequency[index])
        pc = phase[index] + fraction * (phase[index+1] - phase[index])
        results.append({'gain_crossover_Hz': float(10**logfc),
                        'phase_margin_degrees_in_assumed_model': float(180 + pc)})
    return results


def save_plot(fig, out, name):
    fig.savefig(out / f'{name}.png', dpi=180, bbox_inches='tight')
    fig.savefig(out / f'{name}.pdf', bbox_inches='tight')
    plt.close(fig)


def analyse(args):
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    vin, fs, inductance = args.bus, args.frequency, args.inductance_uH * 1e-6
    assert 100 <= vin <= 120 and 50e3 <= fs <= 600e3 and inductance > 0
    report = {
        'scope': 'Analytical ideal-buck and assumed averaged-plant sensitivity studies only',
        'actual_hardware_tests': 0,
        'LTC3779_device_simulation': False,
        'four_phase_system_implemented': False,
        'inputs': {'bus_V': vin, 'frequency_Hz': fs, 'phase_inductance_H': inductance,
                   'phase_target_current_A': 10, 'ideal_phase_count_hypothesis': 4},
        'manufacturer_data': {
            'BSC110N15NS5': {'revision': '2.6, 2022-11-07', 'page': '3-4',
                'Rds_max_10V_25C_ohm': .011, 'Qg_max_C': 35e-9,
                'Qg_typ_C': 28e-9, 'Qgd_max_C': 9e-9, 'Qgd_typ_C': 5.8e-9,
                'tr_typ_s': 3.3e-9, 'tf_typ_s': 2.9e-9,
                'Qrr_typ_C': 46e-9, 'Qrr_max_C': 92e-9,
                'RthetaJC_max_K_per_W': 1, 'Tj_max_C': 150,
                'gate_test': '75V, 38A, VGS0..10V; timing with external RG=3ohm',
                'Qrr_test': '75V, 38A, diF/dt=100A/us; NOT a 110V/10A specification',
                'RthetaJA_test_K_per_W': 50,
                'RthetaJA_test': '40x40x1.5mm vertical FR4, 6cm2 drain Cu, 70um, still air'},
            'LTC3779': {'gm_typ_S': .0015, 'gate_deadtime_typ_s': 60e-9,
                        'maximum_buck_valley_threshold_V': [.070, .090, .110],
                        'threshold_range_is_matching_specification': False,
                        'buck_only_max_duty': .9167},
        },
        'sources': [],
        'limitations': [
            'Buck/boost transition, pulse skipping, DCM and actual LTC3779 sampling are absent.',
            'Qrr/timing/charge values have different manufacturer test points; extrapolation is illustrative.',
            'No actual inductor DCR/core model, capacitor ESR/ESL/lifetime or PCB thermal model exists.',
            'Current-command gain, inner current-loop pole and delay are assumed, not identified LTC3779 data.',
            'Modeled loss subtotal excludes Coss/Eoss, ringing, snubbers, copper/connectors and quiescent losses.',
            'Shared ITH/V5 startup and failed-phase pin-limit problem remains unsolved.',
            'Fault discharge ignores ESL and nonlinear DUT behavior; it is an energy illustration.',
        ],
    }
    for filename in ['BSC110N15NS5.pdf', 'LTC3779.pdf']:
        path = ROOT / 'references' / filename
        report['sources'].append({'file': str(path.relative_to(ROOT)),
                                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    # Verify dimensional/end-point properties against independent limits.
    assert buck_ripple(vin, 0, inductance, fs) == 0
    assert buck_ripple(vin, vin, inductance, fs) == 0
    assert np.isclose(buck_ripple(vin, vin / 2, inductance, fs), vin / (4 * inductance * fs))
    assert np.isclose(buck_ripple(vin, vin / 2, 2 * inductance, fs),
                      .5 * buck_ripple(vin, vin / 2, inductance, fs))
    capacitor_rows = []
    for vout, phases, c_scale, esr_phase in itertools.product([5., 55., 99.6], [1, 4], [.5, 1.], [.02, .1]):
        capacitance, esr = phases * 96e-6 * c_scale, esr_phase / phases
        row = capacitor_metrics(vin, vout, 10, inductance, fs, phases, capacitance, esr)
        row['Vout_V'] = vout
        row['effective_C_fraction_scenario'] = c_scale
        capacitor_rows.append(row)
    # Triangle RMS and capacitive pp identities are independent checks on sampled integration.
    test = capacitor_metrics(vin, vin / 2, 10, inductance, fs, 1, 96e-6, 0)
    ripple = buck_ripple(vin, vin / 2, inductance, fs)
    assert np.isclose(test['output_capacitor_bank_Irms_A'], ripple / np.sqrt(12), rtol=1e-7)
    assert np.isclose(test['capacitive_voltage_ripple_V_pp'], ripple / (8 * fs * 96e-6), rtol=1e-7)
    cancelled = capacitor_metrics(vin, vin / 2, 10, inductance, fs, 4, 384e-6, .01)
    assert cancelled['output_current_sum_ripple_A_pp'] < 1e-9
    report['capacitor_scenarios'] = capacitor_rows

    voltage = np.linspace(.1, 100, 401)
    figures, axes = plt.subplots(2, 1, figsize=(9, 7.3), layout='constrained')
    for phases, label in [(1, 'Én fase / 10 A'), (4, 'Fire ideelle faser / 40 A')]:
        cinrms, voutripple = [], []
        for value in voltage:
            row = capacitor_metrics(vin, value, 10, inductance, fs, phases,
                                    phases * 96e-6, .05 / phases)
            cinrms.append(row['input_capacitor_bank_Irms_A'])
            voutripple.append(1000 * row['with_ESR_voltage_ripple_V_pp'])
        axes[0].plot(voltage, cinrms, label=label)
        axes[1].plot(voltage, voutripple, label=label)
    axes[0].set(ylabel='Inputbankens AC-strøm (A RMS)',
                title=f'Ideel CCM-ripple, {vin:g} V bus, {inductance*1e6:g} µH, {fs/1000:g} kHz')
    axes[1].set(xlabel='Udgangsspænding (V)', ylabel='Udgangsripple (mV p-p)')
    for ax in axes:
        ax.grid(alpha=.25); ax.legend()
    figures.text(.5, -.02, '96 µF og 50 mΩ per fase er scenarier. Ens faser/90° clocks antages; transition er udeladt.', ha='center', fontsize=8)
    save_plot(figures, out, 'capacitor_ripple_scenarios')

    losses = []
    for vout, hot, edge in itertools.product([5., 55., 99.6], [1., 1.5, 2.], [6.2e-9, 40e-9, 100e-9]):
        row = mosfet_losses(vin, vout, 10, inductance, fs, hot, edge)
        row['Vout_V'] = vout
        losses.append(row)
    report['MOSFET_buck_loss_scenarios'] = losses
    # Per-device equivalent thermal resistance is a scenario, not the PCB's RthetaJA.
    thermal_rows = []
    worst = mosfet_losses(vin, 99.6, 10, inductance, fs, 2., 100e-9, 92e-9)
    for rtheta, ambient in itertools.product([5., 15., 50.], [25., 50.]):
        thermal_rows.append({'equivalent_Rtheta_JA_K_per_W_assumption': rtheta,
                            'ambient_C_assumption': ambient,
                            'Q1_fixed_hot_factor_estimated_Tj_C': ambient + rtheta * worst['Q1_assigned_heat_W'],
                            'Q2_fixed_hot_factor_estimated_Tj_C': ambient + rtheta * worst['Q2_assigned_heat_W'],
                            'Q4_fixed_hot_factor_estimated_Tj_C': ambient + rtheta * worst['Q4_assigned_heat_W'],
                            'temperature_was_not_solved_from_actual_Rds_curve': True})
    report['MOSFET_thermal_scenarios'] = thermal_rows
    report['MOSFET_sensitivity_reference'] = worst
    report['inductor_scenarios'] = []
    for dcr, core_loss, rtheta in itertools.product([.005, .02, .05], [1., 3., 8.], [3., 10.]):
        delta = buck_ripple(vin, vin / 2, inductance * .8, fs)
        rms = np.sqrt(10**2 + delta**2 / 12)
        copper = rms**2 * dcr
        report['inductor_scenarios'].append({
            'DCR_ohm_assumption': dcr, 'core_loss_W_assumption': core_loss,
            'thermal_resistance_K_per_W_assumption': rtheta,
            'phase_rms_A': float(rms), 'ripple_A_pp_at_L_minus20_percent': delta,
            'copper_loss_W': float(copper), 'total_modeled_loss_W': float(copper + core_loss),
            'temperature_rise_C': float(rtheta * (copper + core_loss)),
            'selected_manufacturer_part': None,
        })
    current = np.linspace(0, 20.5, 300)
    fig, ax = plt.subplots(figsize=(9, 4.8), layout='constrained')
    for hot, edge, label in [(1., 6.2e-9, '25 °C Rmax / 6,2 ns kildetest'),
                              (1.5, 40e-9, '1,5 × Rmax / 40 ns scenario'),
                              (2., 100e-9, '2 × Rmax / 100 ns scenario')]:
        values = [mosfet_losses(vin, 99.6, i, inductance, fs, hot, edge)['modeled_subtotal_W'] for i in current]
        ax.plot(current, values, label=label)
    ax.set(xlabel='Fasens middelstrøm (A)', ylabel='Beregnet delsum (W)',
           title='MOSFET-tab i idealiseret buckdrift; delsum med gateeffekt')
    ax.grid(alpha=.25); ax.legend()
    fig.text(.5, -.02, 'Coss, ringing, snubber, kobber og transition mangler. Kurverne er ikke en effektivitetsmåling.', ha='center', fontsize=8)
    save_plot(fig, out, 'mosfet_loss_scenarios')

    # Offset range is explicitly hypothetical, NOT the 70..110mV max-limit range.
    example_l = inductance * np.array([.8, .9, 1.1, 1.2])
    example_rs = .006 * np.array([.99, 1.01, .99, 1.01])
    hypothetical_offsets = np.array([.003, .001, -.001, -.003])
    share_rows = []
    for value in [5., 55., 99.6]:
        rp = np.array([buck_ripple(vin, value, el, fs) for el in example_l])
        command, valley, average = common_valley_currents(40., rp, example_rs, hypothetical_offsets)
        share_rows.append({'Vout_V': value, 'shared_sense_command_V': command,
                           'inductances_H': example_l.tolist(), 'shunts_ohm': example_rs.tolist(),
                           'comparator_offsets_V_hypothetical': hypothetical_offsets.tolist(),
                           'valley_currents_A': valley.tolist(), 'average_currents_A': average.tolist(),
                           'peak_currents_A': (valley + rp).tolist(),
                           'maximum_phase_deviation_from_10A_percent': float(np.max(np.abs(average - 10)) * 10)})
    report['four_phase_counterexamples'] = share_rows
    sweeps = []
    for offset_mv in [0, 1, 3, 5]:
        extrema = []
        for l_signs, r_signs, o_signs in itertools.product(itertools.product([-1, 1], repeat=4),
                                                         itertools.product([-1, 1], repeat=4),
                                                         itertools.product([-1, 1], repeat=4)):
            ls = inductance * (1 + .2 * np.array(l_signs))
            rs = .006 * (1 + .01 * np.array(r_signs))
            rp = np.array([buck_ripple(vin, vin / 2, el, fs) for el in ls])
            _, _, avg = common_valley_currents(40., rp, rs, offset_mv * 1e-3 * np.array(o_signs))
            extrema.append([avg.min(), avg.max()])
        sweeps.append({'hypothetical_offset_bound_mV': offset_mv,
                       'phase_min_A': float(np.min(np.array(extrema)[:, 0])),
                       'phase_max_A': float(np.max(np.array(extrema)[:, 1])),
                       'corners_checked': len(extrema),
                       'L_tolerance_scenario_fraction': .2, 'shunt_tolerance_fraction': .01})
    report['four_phase_corner_sweeps'] = sweeps
    fig, ax = plt.subplots(figsize=(9, 4.7), layout='constrained')
    for n, row in enumerate(share_rows):
        ax.bar(np.arange(4) + (n - 1) * .24, row['average_currents_A'], .24, label=f"{row['Vout_V']:g} V ud")
    ax.axhline(10, color='black', linewidth=1, linestyle='--')
    ax.set(xticks=np.arange(4), xticklabels=['Fase 1', 'Fase 2', 'Fase 3', 'Fase 4'],
           ylabel='Beregnet middelstrøm (A)', ylim=(8.5, 11.5),
           title='Fælles valley-kommando giver ikke automatisk ens fasestrøm')
    ax.legend(); ax.grid(axis='y', alpha=.25)
    fig.text(.5, -.02, 'L −20/−10/+10/+20 %, shunt ±1 %, tænkt comparatoroffset +3/+1/−1/−3 mV. Ingen matching-specifikation.', ha='center', fontsize=8)
    save_plot(fig, out, 'phase_sharing_counterexample')

    f = np.geomspace(.1, fs / 2, 10000)
    s = 2j * np.pi * f
    zc = compensation(s)
    zc4 = compensation(s, 2500., 40e-9, 400e-12)
    assert np.allclose(zc4, zc / 4, rtol=1e-12)
    cases = [
        ('Ki=5 A/V, C=96 µF', 5., 96e-6, 1., 1.),
        ('Ki=20 A/V, C=96 µF', 20., 96e-6, 1., 1.),
        ('Ki=80 A/V, C=96 µF', 80., 96e-6, 1., 1.),
        ('Ki=20 A/V, C=48 µF', 20., 48e-6, 1., 1.),
        ('Fire gm / én RC (uskalering)', 20., 96e-6, 4., 1.),
    ]
    fig, axes = plt.subplots(2, 1, figsize=(9, 7.2), layout='constrained', sharex=True)
    loops = []
    for label, ki, cap, gm_scale, zc_scale in cases:
        inner_pole, delay, load, beta = fs / 10, .5 / fs, 10., 1 / 83
        plant = ki * output_impedance(s, load, cap, .05) / (1 + s / (2 * np.pi * inner_pole))
        loop = .0015 * gm_scale * zc * zc_scale * beta * plant * np.exp(-s * delay)
        rows = crossover_rows(f, loop)
        for row in rows:
            row['crosses_above_fs_divided_by_10'] = row['gain_crossover_Hz'] > fs / 10
        loops.append({'label': label, 'Ki_A_per_V_assumption': ki,
                      'C_F_assumption': cap, 'gm_multiplier': gm_scale,
                      'inner_current_loop_pole_Hz_assumption': inner_pole,
                      'sample_delay_s_assumption': delay,
                      'load_ohm_assumption': load, 'ESR_ohm_assumption': .05,
                      'crossovers': rows})
        axes[0].semilogx(f, 20 * np.log10(np.abs(loop)), label=label)
        axes[1].semilogx(f, np.unwrap(np.angle(loop)) * 180 / np.pi)
    for ax in axes:
        ax.axvline(fs / 10, color='gray', linestyle=':', linewidth=1)
        ax.grid(which='both', alpha=.2)
    axes[0].axhline(0, color='black', linewidth=1)
    axes[1].axhline(-180, color='black', linewidth=1)
    axes[0].set(ylabel='Loop gain (dB)', title='Gennemsnitsmodel med antaget strøm-loop; følsomhed')
    axes[1].set(ylabel='Fase (grader)', xlabel='Frekvens (Hz)')
    axes[0].legend(fontsize=8, loc='lower left')
    fig.text(.5, -.02, 'Ki/pol/delay er tænkte parametre. Dette er hverken LTC3779 SPICE eller verificeret CV/CC-stabilitet.', ha='center', fontsize=8)
    save_plot(fig, out, 'loop_sensitivity_assumed_plant')
    report['assumed_voltage_loop_scenarios'] = loops
    # Equivalent scaled ideal four-phase plant reproduces one-phase normalized loop.
    single_plant = 20 * output_impedance(s, 10, 96e-6, .05)
    four_plant = 80 * output_impedance(s, 2.5, 384e-6, .0125)
    assert np.allclose(single_plant, four_plant, rtol=1e-12)
    assert np.allclose(.0015 * zc * single_plant, .006 * zc4 * four_plant, rtol=1e-12)
    report['ideal_gm_RC_scaling_verified'] = {
        'one_gm_S': .0015, 'four_gm_S': .006,
        'one_R_ohm': 1e4, 'equivalent_four_R_ohm': 2500,
        'one_series_C_F': 10e-9, 'equivalent_four_series_C_F': 40e-9,
        'one_shunt_C_F': 100e-12, 'equivalent_four_shunt_C_F': 400e-12,
        'equivalence_is_small_signal_algebra_only': True,
    }

    # Experimental control card: R8=20k, R9=10k, C8=1nF. This approximation
    # applies ONLY with the sink diode forward-biased and sufficient clamp
    # authority. Its dynamic gain is not specified by the device datasheet.
    cc_cases = [(5., 10., 96e-6, 1e-9), (20., 10., 96e-6, 1e-9),
                (80., 10., 96e-6, 1e-9), (20., 1., 96e-6, 1e-9),
                (20., 10., 48e-6, 1e-9), (20., 10., 96e-6, 10e-9),
                (20., 10., 96e-6, 100e-9)]
    cc_rows = []
    fig, axes = plt.subplots(2, 1, figsize=(9, 7.2), layout='constrained', sharex=True)
    for ki, load, cap, pi_cap in cc_cases:
        pi = (1e4 + 1 / (s * pi_cap)) / 2e4
        load_current_plant = ki * output_impedance(s, load, cap, .05) / load
        load_current_plant /= 1 + s / (2 * np.pi * (fs / 10))
        loop = .05 * pi * load_current_plant * np.exp(-s * .5 / fs)
        label = f'Ki={ki:g}, last={load:g} Ω, Cout={cap*1e6:g} µF, Cpi={pi_cap*1e9:g} nF'
        crossovers = crossover_rows(f, loop)
        for row in crossovers:
            row['crosses_above_fs_divided_by_10'] = row['gain_crossover_Hz'] > fs / 10
        cc_rows.append({'label': label, 'Ki_A_per_V_assumption': ki,
                        'load_ohm_assumption': load, 'C_F_assumption': cap,
                        'sensor_V_per_A': .05, 'PI_input_R_ohm': 2e4,
                        'PI_series_R_ohm': 1e4, 'PI_series_C_F': pi_cap,
                        'diode_is_assumed_active': True,
                        'ITH_clamp_authority_is_assumed_sufficient': True,
                        'crossovers': crossovers})
        axes[0].semilogx(f, 20 * np.log10(np.abs(loop)), label=label)
        axes[1].semilogx(f, np.unwrap(np.angle(loop)) * 180 / np.pi)
    for ax in axes:
        ax.axvline(fs / 10, color='gray', linestyle=':', linewidth=1)
        ax.grid(which='both', alpha=.2)
    axes[0].axhline(0, color='black', linewidth=1)
    axes[1].axhline(-180, color='black', linewidth=1)
    axes[0].set(ylabel='CC loop gain (dB)', title='Aktiv CC-gren i antaget plant; PI-værdier er startværdier')
    axes[1].set(ylabel='Fase (grader)', xlabel='Frekvens (Hz)')
    axes[0].legend(fontsize=8, loc='lower left')
    fig.text(.5, -.02, 'Ideal opamp/diode-clamp; windup, CC/CV-skift og faktisk ITH-gain er udeladt. Ingen stabilitetsgodkendelse.', ha='center', fontsize=8)
    save_plot(fig, out, 'cc_loop_sensitivity_assumed_plant')
    report['assumed_CC_active_branch_scenarios'] = cc_rows

    # Capacitor discharge to an illustrative resistor; no claim about actual DUT peak.
    fault_voltage, fault_c, fault_r, delay = 5., 384e-6, .5, 100e-6
    source_before, source_after = .1, .01
    t = np.linspace(0, 2e-3, 4001)
    at_delay = source_before * fault_r + (fault_voltage - source_before * fault_r) * np.exp(-delay / (fault_r * fault_c))
    vfault = np.where(t <= delay,
                     source_before * fault_r + (fault_voltage - source_before * fault_r) * np.exp(-t / (fault_r * fault_c)),
                     source_after * fault_r + (at_delay - source_after * fault_r) * np.exp(-(t - delay) / (fault_r * fault_c)))
    fault_current = vfault / fault_r
    assert np.isclose(vfault[0], fault_voltage)
    assert np.all(vfault >= source_after * fault_r)
    initial_energy = .5 * fault_c * fault_voltage**2
    bus_c, returned_energy = 384e-6, 1.
    report['fault_energy_scenarios'] = {
        'capacitor_discharge': {'initial_V': fault_voltage, 'C_F_assumption': fault_c,
            'fault_R_ohm_assumption': fault_r, 'initial_capacitor_energy_J': initial_energy,
            'initial_ideal_resistive_current_A': fault_voltage / fault_r,
            'source_A_before_delay': source_before, 'source_A_after_delay': source_after,
            'delay_s_assumption': delay, 'R_C_time_constant_s': fault_r * fault_c,
            'ESL_omitted': True, 'physical_DUT_peak_predicted': False},
        '100V_four_nominal_output_banks_energy_J': .5 * 384e-6 * 100**2,
        'bus_returned_energy': {'bus_initial_V': vin, 'bus_C_F_assumption': bus_c,
            'returned_energy_J_assumption': returned_energy,
            'bus_final_V_if_no_sink': float(np.sqrt(vin**2 + 2 * returned_energy / bus_c)),
            'energy_to_raise_bus_to_120V_J': float(.5 * bus_c * (120**2 - vin**2)),
            'Mean_Well_sink_capacity_assumed': False},
    }
    fig, axes = plt.subplots(2, 1, figsize=(9, 6), layout='constrained', sharex=True)
    axes[0].plot(t * 1e6, vfault); axes[0].set(ylabel='Udgangsspænding (V)', title='Illustration: 5 V / 384 µF afleverer energi efter lastfejl')
    axes[1].plot(t * 1e6, fault_current, label='Ideel resistiv laststrøm')
    axes[1].axhline(source_after, color='black', linestyle='--', label='10 mA efterfølgende kildestrøm')
    axes[1].set(ylabel='Laststrøm (A)', xlabel='Tid fra fejl (µs)'); axes[1].legend()
    for ax in axes:
        ax.grid(alpha=.25); ax.axvline(delay * 1e6, color='gray', linestyle=':')
    fig.text(.5, -.02, 'Tænkt 0,5 Ω last / 100 µs reaktionstid. ESL og DUT-nonlinearitet mangler; peak er ikke en hardwareforudsigelse.', ha='center', fontsize=8)
    save_plot(fig, out, 'fault_capacitor_energy')

    report['checks'] = {
        'passed': ['buck endpoints and units/scaling', 'triangle RMS and integrated voltage identity',
                   'ideal four-phase cancellation at D=0.5', 'phase-current sums equal 40A',
                   'parallel RC/gm equivalence', 'scaled output-plant equivalence',
                   'fault initial voltage and discharge bound'],
        'actual_hardware_tests': 0,
    }
    (out / 'power_analysis.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'report': str(out / 'power_analysis.json'), 'hardware_tests': 0,
                      'plots': 6, 'corner_cases_per_offset': 4096,
                      'analytical_checks': len(report['checks']['passed'])}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bus', type=float, default=110., help='Bus voltage, 100..120V')
    parser.add_argument('--frequency', type=float, default=101800., help='Switch frequency in Hz')
    parser.add_argument('--inductance-uH', type=float, default=150., help='Inductance per phase in uH')
    parser.add_argument('--output-dir', default=str(ROOT / 'exports' / 'analysis'))
    analyse(parser.parse_args())
