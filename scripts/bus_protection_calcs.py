#!/usr/bin/env python3
"""Bounded bus-protection design study; NOT a hardware qualification.

Run from any directory: python3 scripts/bus_protection_calcs.py
The deterministic JSON separates source facts from unverified design assumptions.
All internal calculations use SI units. No simulator/device model is implied.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]


def capacitor_energy(capacitance_f: float, voltage_v: float) -> float:
    return 0.5 * capacitance_f * voltage_v**2


def step_voltage(source_v: float, initial_v: float, resistance_ohm: float,
                 capacitance_f: float, delay_s: float) -> float:
    """Ideal RC step, zero load, no inductance, ideal switch until opening.

    Input source amplitude and impedance are assumptions, NOT RSP fault limits.
    This is not a model of the LTC4366 analog control loop.
    """
    return source_v - (source_v - initial_v) * math.exp(
        -delay_s / (resistance_ohm * capacitance_f))


def clamp_bounds(top_ohm: float, bottom_ohm: float,
                 resistor_tolerance: float = 0.001) -> dict:
    """LTC4366 OUT-FB divider: OUT--top--FB--bottom--BUS_NEG.

    Includes +/-1 uA leakage with worst adverse sign and +/-0.1% resistors.
    Limits 1.193/1.267 V are specified over temperature (Rev F p5).
    """
    top_min = top_ohm * (1 - resistor_tolerance)
    top_max = top_ohm * (1 + resistor_tolerance)
    bottom_min = bottom_ohm * (1 - resistor_tolerance)
    bottom_max = bottom_ohm * (1 + resistor_tolerance)
    return {
        "top_ohm": top_ohm,
        "bottom_ohm": bottom_ohm,
        "resistor_tolerance_fraction": resistor_tolerance,
        "nominal_v": 1.23 * (1 + bottom_ohm / top_ohm),
        "min_v": 1.193 * (1 + bottom_min / top_max) - 1e-6 * bottom_min,
        "max_v": 1.267 * (1 + bottom_max / top_min) + 1e-6 * bottom_max,
        "bottom_resistor_total_power_nominal_w":
            (1.23 / top_ohm)**2 * bottom_ohm,
    }


def calculate() -> dict:
    nominal_bus_v = 110.0
    procedural_ceiling_v = 120.0
    source_threshold_sum_v = 2 * 67.2
    output_w = 100.0 * 40.0
    converter_efficiency = 0.95  # assumed, not measured
    bus_w = output_w / converter_efficiency
    bus_a = bus_w / nominal_bus_v
    normal_static_budget_v = nominal_bus_v * (1 + .01 + .0005 * 25)

    # Bulk caps only. Values for proposed additions are NOT installed on the PCB.
    capacitances = {
        "existing_one_phase_bulk_min": 2 * 47e-6 * .8,
        "four_phase_bulk_min_if_all_connected": 4 * 2 * 47e-6 * .8,
        "hypothetical_470u_bulk_min": 470e-6 * .8,
        "hypothetical_2200u_bulk_min": 2200e-6 * .8,
    }
    trip_nominal_v = 116.0
    trip_uncertainty_v = .65  # explicit example; reference/divider not selected
    # TLV3501 5 mV overdrive at a 2.5 V/116 V divider, not instant at crossing.
    required_overdrive_bus_v = .005 * (116.0 / 2.5)
    timing_start_v = trip_nominal_v + trip_uncertainty_v + required_overdrive_bus_v
    assumed_delays_s = {
        "comparator_12ns_at_5mV_overdrive": 12e-9,
        "sense_filter_assumed": .5e-6,
        "latch_buffer_assumed": .5e-6,
        "TPSI3050_EN_to_VDRV_max_at_100pF": 3e-6,
        "additional_loaded_gate_turnoff_assumed": 1e-6,
    }
    example_delay_s = sum(assumed_delays_s.values())

    cap_cases = []
    for name, capacitance_f in capacitances.items():
        cap_cases.append({
            "case": name,
            "capacitance_min_f": capacitance_f,
            "energy_at_110v_j": capacitor_energy(capacitance_f, nominal_bus_v),
            "energy_at_120v_j": capacitor_energy(capacitance_f, procedural_ceiling_v),
            "reverse_energy_room_110_to_120_j": capacitor_energy(
                capacitance_f, procedural_ceiling_v) - capacitor_energy(
                capacitance_f, nominal_bus_v),
            "time_to_120_at_4kw_regeneration_s":
                (capacitor_energy(capacitance_f, procedural_ceiling_v)
                 - capacitor_energy(capacitance_f, nominal_bus_v)) / output_w,
            "no_load_constant_current_time_to_120_from_timing_start_s": {
                str(current_a): capacitance_f
                * (procedural_ceiling_v - timing_start_v) / current_a
                for current_a in (62.5, 125.0, 500.0)
            },
            "rc_step_134_4v_20milliohm_after_driver_only_v": step_voltage(
                source_threshold_sum_v, timing_start_v, .02, capacitance_f, 3e-6),
            "rc_step_134_4v_20milliohm_after_example_total_v": step_voltage(
                source_threshold_sum_v, timing_start_v, .02,
                capacitance_f, example_delay_s),
        })

    # Illustrative LTC4366 divider; split bottom = 2 x 55.6 kohm.
    clamp = clamp_bounds(1210.0, 2 * 55600.0)
    clamp["normal_55v_each_budget_margin_v"] = clamp["min_v"] - normal_static_budget_v
    clamp["normal_53v_each_budget_margin_v"] = clamp["min_v"] - 106 * (1 + .01 + .0005 * 25)
    clamp["margin_to_120v_at_max_clamp_v"] = procedural_ceiling_v - clamp["max_v"]

    # LTC4366 gate sink min at the datasheet test point; NOT constant-waveform proof.
    assumed_external_gate_charge_c = 200e-9
    assumed_stability_gate_cap_f = 2e-9
    gate_estimate_s = (
        assumed_external_gate_charge_c + assumed_stability_gate_cap_f * 12.0) / .122

    pass_current_a = 40.0
    pass_dissipation_w = (source_threshold_sum_v - clamp["nominal_v"]) * pass_current_a
    pass_cases = [{"duration_s": duration_s,
                   "energy_j": pass_dissipation_w * duration_s}
                  for duration_s in (.001, .005, .02, 1.0)]

    # Only an ON-state illustration; 2x temperature multiplier is an assumption.
    hot_multiplier = 2.0
    fet_on_resistance_ohm = .011 * hot_multiplier
    switch_pair_resistance_ohm = 2 * fet_on_resistance_ohm

    result = {
        "schema_version": 1,
        "status": "UNRESOLVED_NOT_QUALIFIED_NO_FABRICATION_RELEASE",
        "description": "Bounded manufacturer-backed design study, no physical test or SPICE validation",
        "source_facts": {
            "RSP3000_48_ovp_each_range_v": [57.6, 67.2],
            "sum_of_ovp_threshold_upper_limits_v": source_threshold_sum_v,
            "one_module_upper_threshold_plus_other_55v_v": 67.2 + 55.0,
            "ovp_threshold_is_not_transient_ceiling": True,
            "LTC4366_FB_range_v": [1.193, 1.23, 1.267],
            "LTC4366_FB_leakage_abs_max_a": 1e-6,
            "LTC4366_fast_path_delay_max_s": 300e-9,
            "LTC4366_SD_filter_max_s": 1200e-6,
            "LTC4366_gate_fast_sink_min_at_test_point_a": .122,
            "TPSI3050_three_wire_off_delay_max_at_100pF_s": 3e-6,
            "IPP110N20N3G_VDS_min_v": 200.0,
            "IPP110N20N3G_RDS_on_max_25C_10V_ohm": .011,
            "IPP110N20N3G_Qg_max_100V_44A_c": 87e-9,
            "references": "references/bus-protection-sources.json",
        },
        "design_assumptions_and_limits": {
            "existing_phase_procedural_bus_ceiling_v": procedural_ceiling_v,
            "existing_phase_MOSFET_rating_v": 150.0,
            "bulk_cap_tolerance_fraction_assumed": .20,
            "nominal_bus_v": nominal_bus_v,
            "unmeasured_converter_efficiency": converter_efficiency,
            "normal_bus_budget_1percent_plus_25C_tempco_v": normal_static_budget_v,
            "normal_bus_budget_excludes_ripple_and_dynamic_overshoot": True,
            "example_fault_source_v_NOT_guaranteed_max": source_threshold_sum_v,
            "example_fault_source_resistance_ohm_NOT_measured": .02,
            "example_trip_nominal_v_NOT_selected": trip_nominal_v,
            "example_trip_uncertainty_v_NOT_qualified": trip_uncertainty_v,
            "required_5mV_overdrive_referred_to_bus_v": required_overdrive_bus_v,
            "example_timing_start_v": timing_start_v,
            "delay_budget_s": assumed_delays_s,
            "example_total_delay_s_NOT_guaranteed": example_delay_s,
            "fault_charging_currents_a_NOT_source_pulse_limits": [62.5, 125.0, 500.0],
            "LTC4366_estimated_gate_charge_c_NOT_selected": assumed_external_gate_charge_c,
            "LTC4366_gate_cap_f_MIN_stability_not_completed_design": assumed_stability_gate_cap_f,
            "hot_RDS_multiplier_NOT_manufacturer_bound": hot_multiplier,
            "source_output_capacitance_f": None,
            "source_transient_peak_v": None,
            "source_shutdown_time_max_s": None,
        },
        "operating_budget": {
            "output_power_w": output_w,
            "input_bus_power_w": bus_w,
            "input_bus_current_a": bus_a,
        },
        "capacitor_and_time_cases": cap_cases,
        "LTC4366_illustrative_clamp_divider_NOT_selected": clamp,
        "LTC4366_estimated_fast_gate_discharge_NOT_guaranteed_s": gate_estimate_s,
        "LTC4366_estimated_delay_plus_discharge_NOT_guaranteed_s": 300e-9 + gate_estimate_s,
        "linear_pass_stress_examples": {
            "source_v": source_threshold_sum_v,
            "clamp_v": clamp["nominal_v"],
            "current_a": pass_current_a,
            "dissipation_w": pass_dissipation_w,
            "duration_energy_cases": pass_cases,
            "IPP110N20N3G_single_40A_20ms_status": "REJECTED: above 10ms SOA at approximately 20V even Tc25C",
            "IPP110N20N3G_single_40A_5ms_status": "NOT_QUALIFIED: no 5ms SOA curve; 1ms curve does not qualify it",
        },
        "precharge_zero_load_examples": [{
            "capacitance_f": capacitance_f,
            "ideal_linear_charge_energy_110v_from_zero_j": capacitor_energy(capacitance_f, 110),
            "ideal_charge_time_at_1a_to_110v_s": capacitance_f * 110,
            "converter_required_off_during_precharge": True,
        } for capacitance_f in (376e-6, 1760e-6)],
        "source_bulk_energy_unknown_example_only": {
            "assumed_capacitance_f": .001,
            "energy_at_134_4v_j": capacitor_energy(.001, source_threshold_sum_v),
            "additional_energy_110_to_134_4v_j": capacitor_energy(.001, source_threshold_sum_v)
                - capacitor_energy(.001, 110),
        },
        "isolated_bidirectional_switch_on_loss_example": {
            "candidate": "2 x IPP110N20N3G common-source; not released",
            "current_a": 40.0,
            "pair_hot_resistance_assumed_ohm": switch_pair_resistance_ohm,
            "pair_dissipation_assumed_w": 40**2 * switch_pair_resistance_ohm,
            "pair_drop_assumed_v": 40 * switch_pair_resistance_ohm,
        },
        "inductive_interruption_examples": [
            {"loop_inductance_h": inductance_h, "current_a": current_a,
             "energy_j": .5 * inductance_h * current_a**2,
             "voltage_if_current_changes_to_zero_in_1us_v": inductance_h * current_a / 1e-6}
            for inductance_h in (1e-6, 10e-6)
            for current_a in (40.0, 500.0)
        ],
        "regenerative_dump_example_NOT_selected": {
            "dump_voltage_v": 116.0,
            "regenerative_power_w": 4000.0,
            "required_resistance_ohm_at_4kw": 116**2 / 4000,
            "dump_current_a_at_4kw": 4000 / 116,
            "pulse_energy_50ms_j": 4000 * .05,
            "pulse_energy_1s_j": 4000.0,
            "resistor_and_switch_MPN": None,
        },
        "conclusion": {
            "existing_150v_phase_and_120v_ceiling_protection_proven": False,
            "fast_bus_clamp_MOS_SOA_qualified": False,
            "complete_threshold_and_latch_circuit_designed": False,
            "AC_contactor_fuses_emergency_stop_qualified": False,
            "native_schematic_or_PCB_changed_by_this_study": False,
            "next_required": [
                "Bound source transient waveform, output bulk energy and path impedance",
                "Choose protected bus capacitance and independent threshold tolerance budget",
                "Qualify linear-clamp MOSFET SOA at hot case, fault/startup and repetition",
                "Design reverse-energy dump and inductive interruption current paths",
                "Complete hardware latch/shutdown, AC coordination and independent review",
            ],
        },
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=REPO / "exports/analysis/bus_protection.json")
    args = parser.parse_args()
    result = calculate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                      allow_nan=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output.relative_to(REPO) if args.output.is_relative_to(REPO) else args.output}")
    print("Status: unresolved; existing 120 V / 150 V phase protection NOT proven.")


if __name__ == "__main__":
    main()
