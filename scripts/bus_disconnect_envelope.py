#!/usr/bin/env python3
"""Conditional DC-disconnect envelope with fixed R, C, ESR and delay bounds.

No hardware qualification is implied. All internal quantities use SI units.
The source bound is a REQUIREMENT; 134.4 V is NOT a guaranteed RSP transient limit.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def terminal_voltage(vs: float, initial_v: float, r_min: float,
                     capacitance_min: float, esr_max: float, delay_max: float) -> float:
    """No load, lumped ideal capacitance plus ESR. ESL is bounded separately.

    Fixed R must remain present in every ON/precharge state. FET resistance is
    ignored so that its unqualified positive resistance provides no protection.
    """
    total_r = r_min + esr_max
    return vs - (vs - initial_v) * r_min / total_r * math.exp(
        -delay_max / (total_r * capacitance_min))


def deadline(vs: float, initial_v: float, target_v: float, r_min: float,
             capacitance_min: float, esr_max: float) -> float | None:
    """Latest opening time after the stated start; zero means ESR step fails.

    None means no upper deadline is needed in the ideal RC model (vs <= target).
    """
    if vs <= target_v:
        return None
    total_r = r_min + esr_max
    ratio = (vs - initial_v) * r_min / ((vs - target_v) * total_r)
    return max(0.0, total_r * capacitance_min * math.log(ratio))


def pulse(vs: float, initial_v: float, r_min: float, capacitance_f: float,
          esr: float, delay_max: float) -> dict:
    total_r = r_min + esr
    delta = vs - initial_v
    attenuation = math.exp(-delay_max / (total_r * capacitance_f))
    final_cap_v = vs - delta * attenuation
    energy_losses = .5 * capacitance_f * delta**2 * (1 - attenuation**2)
    return {
        "initial_current_a": delta / total_r,
        "current_at_opening_a": delta / total_r * attenuation,
        "initial_Rlimit_power_w": (delta / total_r)**2 * r_min,
        "Rlimit_pulse_energy_j": energy_losses * r_min / total_r,
        "ESR_pulse_energy_j": energy_losses * esr / total_r,
        "cap_energy_gain_j": .5 * capacitance_f * (final_cap_v**2 - initial_v**2),
        "source_energy_j": vs * capacitance_f * (final_cap_v - initial_v),
    }


def evaluate_model(*, source_bound_v: float | None, start_v: float | None,
                   r_min_ohm: float | None, c_min_f: float | None,
                   esr_max_ohm: float | None, delay_max_s: float | None,
                   extra_terminal_peak_max_v: float | None,
                   ceiling_v: float = 120.0) -> dict:
    bounds = {
        "source_bound_v": source_bound_v,
        "start_v": start_v,
        "r_min_ohm": r_min_ohm,
        "c_min_f": c_min_f,
        "esr_max_ohm": esr_max_ohm,
        "delay_max_s": delay_max_s,
        "extra_terminal_peak_max_v": extra_terminal_peak_max_v,
    }
    missing = [name for name, value in bounds.items() if value is None]
    if missing:
        return {"model_valid": False, "model_accepts": False,
                "reason": "Required bound absent: " + ", ".join(missing)}
    if any(isinstance(value, bool) or not isinstance(value,(int,float))
           or not math.isfinite(value) for value in bounds.values()):
        return {"model_valid": False, "model_accepts": False,
                "reason": "Required numeric bound is not finite"}
    if (source_bound_v <= start_v or r_min_ohm <= 0 or c_min_f <= 0
            or delay_max_s < 0 or esr_max_ohm < 0 or extra_terminal_peak_max_v < 0):
        return {"model_valid": False, "model_accepts": False,
                "reason": "Invalid or nonpositive bound"}
    calculated = terminal_voltage(source_bound_v, start_v, r_min_ohm,
                                  c_min_f, esr_max_ohm, delay_max_s)
    total_peak = calculated + extra_terminal_peak_max_v
    return {"model_valid": True, "model_accepts": total_peak < ceiling_v,
            "calculated_RC_terminal_peak_v": calculated,
            "bounded_extra_peak_v": extra_terminal_peak_max_v,
            "calculated_total_peak_v": total_peak,
            "margin_to_ceiling_v": ceiling_v - total_peak,
            "reason": "Conditional mathematical model; physical bounds are not verified"}


def calculate() -> dict:
    r_nominal = .05
    r_tolerance = .05
    r_min, r_max = r_nominal * (1-r_tolerance), r_nominal * (1+r_tolerance)
    c_nominal, c_tolerance = .0022, .20
    c_min, c_max = c_nominal * (1-c_tolerance), c_nominal * (1+c_tolerance)
    esr_requirement = .001
    delay_requirement = 5e-6
    ringing_requirement = 1.0
    ceiling = 120.0
    rc_target = ceiling - ringing_requirement
    trip_nominal = 114.0
    trip_error_requirement = .65
    comparator_ref_example = 2.5
    comparator_overdrive = .005
    nominal_overdrive_referred_to_bus = comparator_overdrive * trip_nominal / comparator_ref_example
    # Round above 0.228V nominal; actual minimum divider gain must support this.
    overdrive_referred_to_bus = .230
    trip_max_start = trip_nominal + trip_error_requirement + overdrive_referred_to_bus
    starts = {"upstream_detected_initial_110v": 110.0,
              "upstream_detected_initial_normal_high_budget": 112.475,
              "protected_trip_max_plus_required_overdrive": trip_max_start}
    faults = [134.4, 150.0, 160.0, 200.0]
    cases = []
    for fault_v in faults:
        for label, initial_v in starts.items():
            d_ideal = deadline(fault_v, initial_v, ceiling, r_min, c_min, 0.0)
            d_reserved = deadline(fault_v, initial_v, rc_target, r_min, c_min,
                                  esr_requirement)
            evaluation = evaluate_model(
                source_bound_v=fault_v, start_v=initial_v, r_min_ohm=r_min,
                c_min_f=c_min, esr_max_ohm=esr_requirement,
                delay_max_s=delay_requirement,
                extra_terminal_peak_max_v=ringing_requirement)
            cases.append({
                "fault_source_v": fault_v,
                "start_case": label,
                "start_v": initial_v,
                "deadline_to_120_ideal_ESR_zero_s": d_ideal,
                "deadline_to_119_ESR_1milliohm_s": d_reserved,
                "additional_delay_margin_at_5us_s": d_reserved-delay_requirement,
                "required_Cmin_for_5us_ESR_1milliohm_to_119_f":
                    c_min * delay_requirement / d_reserved if d_reserved > 0 else None,
                "required_Cnom_if_total_minus20percent_f":
                    c_nominal * delay_requirement / d_reserved if d_reserved > 0 else None,
                "mathematical_evaluation": evaluation,
                "pulse_at_Cmax_and_ESRzero_for_current_energy_screen": pulse(
                    fault_v, initial_v, r_min, c_max, 0.0, delay_requirement),
            })

    conditional = evaluate_model(
        source_bound_v=160.0, start_v=trip_max_start, r_min_ohm=r_min,
        c_min_f=c_min, esr_max_ohm=esr_requirement,
        delay_max_s=delay_requirement,
        extra_terminal_peak_max_v=ringing_requirement)
    complete_model_args = {
        "source_bound_v": 160.0, "start_v": trip_max_start,
        "r_min_ohm": r_min, "c_min_f": c_min, "esr_max_ohm": esr_requirement,
        "delay_max_s": delay_requirement,
        "extra_terminal_peak_max_v": ringing_requirement,
    }
    absent_bound_cases = {}
    for key in complete_model_args:
        args = dict(complete_model_args)
        args[key] = None
        absent_bound_cases[key] = evaluate_model(**args)

    gate_charge_example = 8 * 87e-9  # not max at 160V/large fault current!
    div_cap_nominal = 4.7e-6
    div_cap_total_tolerance = .20
    div_cap_min = div_cap_nominal * (1-div_cap_total_tolerance)
    effective_gate_supply_cap_min = div_cap_min/2
    pulse_screen = []
    # Manufacturer pulse ID is at Tc25C; 25% mismatch is a design assumption.
    for fault_v in faults:
        initial_pulse_a = (fault_v - 110.0) / r_min
        cold_screen_count = math.ceil(initial_pulse_a * 1.25 / 352)
        pulse_screen.append({
            "fault_v": fault_v,
            "peak_current_upper_example_a": initial_pulse_a,
            "parallel_count_per_half_at_352A_25C_and_assumed25percent_mismatch": cold_screen_count,
            "hot_SOA_and_pulse_current_qualified": False,
            "200v_part_under_180v_VDS_design_ceiling_at_source_bound_alone": fault_v < 180,
        })

    # Conditional source-side flywheel loop diverts energy away from protected bus.
    interruption = []
    maximum_working_fault_current = (160.0-110.0)/r_min
    pre_extra_peak = conditional["calculated_RC_terminal_peak_v"]
    allowed_extra_cap_energy = .5*c_min*((pre_extra_peak+ringing_requirement)**2-pre_extra_peak**2)
    for inductance_h in (.1e-6, 1e-6, 10e-6):
        energy = .5*inductance_h*maximum_working_fault_current**2
        interruption.append({
            "inductance_h": inductance_h,
            "current_a": maximum_working_fault_current,
            "energy_j": energy,
            "voltage_if_current_changes_to_zero_in_1us_v": inductance_h*maximum_working_fault_current/1e-6,
            "Rlimit_flywheel_decay_time_constant_s": inductance_h/r_min,
            "protected_cap_v_if_all_energy_injected": math.sqrt(pre_extra_peak**2+2*energy/c_min),
        })

    precharge_nominal = 100.0
    precharge_min = 95.0
    precharge_max = 105.0
    precharge_source_bound = trip_nominal + trip_error_requirement
    precharge_timeout = 2.0
    conditions = {
        "Rmin_over_temperature_age_and_pulses_ohm": None,
        "Cmin_effective_over_voltage_temperature_age_f": None,
        "ESRmax_in_fault_relevant_frequency_range_ohm": None,
        "source_transient_bound_at_actual_NODE_F_v": None,
        "full_loaded_detection_to_opening_max_s": None,
        "terminal_ESL_inductive_extra_peak_bound_v": None,
        "maximum_protected_trip_start_including_overdrive_v": None,
        "hot_switchbank_SOA_qualified": False,
        "resistor_continuous_and_pulse_qualified": False,
        "capacitor_pulse_current_and_terminal_qualified": False,
        "aux_hold_up_and_default_OFF_qualified": False,
        "precharge_flywheel_dump_and_fault_reset_qualified": False,
    }
    physical_limits = {
        "Rmin_over_temperature_age_and_pulses_ohm": ("min",r_min),
        "Cmin_effective_over_voltage_temperature_age_f": ("min",c_min),
        "ESRmax_in_fault_relevant_frequency_range_ohm": ("max",esr_requirement),
        "source_transient_bound_at_actual_NODE_F_v": ("max",160.0),
        "full_loaded_detection_to_opening_max_s": ("max",delay_requirement),
        "terminal_ESL_inductive_extra_peak_bound_v": ("max",ringing_requirement),
        "maximum_protected_trip_start_including_overdrive_v": ("max",trip_max_start),
    }
    qualification_failures = []
    for name,value in conditions.items():
        if name in physical_limits:
            direction,limit = physical_limits[name]
            if (value is None or isinstance(value,bool) or not isinstance(value,(int,float))
                    or not math.isfinite(value) or value < 0):
                qualification_failures.append(name+": verified finite bound absent")
            elif (direction=="min" and value < limit) or (direction=="max" and value > limit):
                qualification_failures.append(name+": verified bound fails requirement")
        elif value is not True:
            qualification_failures.append(name+": not qualified")
    result = {
        "schema_version": 1,
        "status": "CONDITIONAL_DESIGN_ENVELOPE_PHYSICAL_QUALIFICATION_FAIL",
        "units": "SI internally; suffixes identify each output unit",
        "model": "No-load source step, fixed series R, lumped C+ESR; bounded ESL/ringing separately",
        "source_fact_warning": "134.4V is sum of RSP OVP threshold upper endpoints, not a transient bound",
        "design_requirements_NOT_verified": {
            "Rseries_nominal_ohm": r_nominal,
            "Rseries_full_budget_fraction": r_tolerance,
            "Rseries_min_ohm": r_min,
            "Rseries_max_ohm": r_max,
            "Rseries_bypass_permitted": False,
            "Cprotected_nominal_f": c_nominal,
            "Cprotected_full_budget_fraction": c_tolerance,
            "Cprotected_min_f": c_min,
            "Cprotected_max_f": c_max,
            "Cprotected_ESR_max_ohm": esr_requirement,
            "source_transient_bound_at_NODE_F_v": 160.0,
            "total_detection_to_opening_delay_max_s": delay_requirement,
            "extra_terminal_peak_max_v": ringing_requirement,
            "critical_terminal_ceiling_v": ceiling,
            "RC_terminal_target_v": rc_target,
            "fast_OV_nominal_v": trip_nominal,
            "fast_OV_total_error_bound_v": trip_error_requirement,
            "fast_OV_required_5mV_overdrive_bus_equivalent_v": overdrive_referred_to_bus,
            "fast_OV_nominal_5mV_overdrive_bus_equivalent_v_NOT_bound": nominal_overdrive_referred_to_bus,
            "protected_trip_analysis_start_v": trip_max_start,
        },
        "delay_budget_requirements_s": {
            "sense_filter_settle_max_NOT_verified": .5e-6,
            "TLV3501_max_ONLY_given_datasheet_step_conditions": 12e-9,
            "latch_gating_logic_max_NOT_selected": .25e-6,
            "TPSI3050_EN_to_10percent_max_ONLY_given_100pF_conditions": 3e-6,
            "additional_loaded_gate_opening_max_NOT_verified": 1e-6,
            "remaining_budget_NOT_measured": .238e-6,
            "total_requirement_NOT_qualified": delay_requirement,
        },
        "timing_source_facts": {
            "TPSI3050_off_max_under_table_conditions_s": 3e-6,
            "TPSI3050_primary_supply_loss_timeout_typ_s_NO_MAX": 100e-6,
            "TPSI3050_peak_sink_typ_a_NO_MIN": 3.0,
            "TPSI3050_low_driver_resistance_typ_ohm_NO_MAX": 1.7,
            "TLV3501_5mV_overdrive_step_delay_max_s": 12e-9,
            "TLV3501_maximum_NOT_production_tested_characterized": True,
            "TPS3700_HL_typ_s_NO_MAX": 18e-6,
            "TPS3700_LH_typ_s_NO_MAX": 29e-6,
            "TPS3700_startup_max_s": 450e-6,
        },
        "fault_start_cases": cases,
        "conditional_160v_model": conditional,
        "fail_closed_missing_bound_cases": absent_bound_cases,
        "ESR_sensitivity_at_160v_protected_trip_start": [
            {"ESR_ohm": esr,
             "RC_terminal_peak_v": terminal_voltage(160.0, trip_max_start,
                 r_min,c_min,esr,delay_requirement)}
            for esr in (0.0,.001,.002,.005,.020)
        ],
        "continuous_Rseries_budget": [
            {"current_a": current,
             "nominal_drop_v": current*r_nominal,
             "maximum_drop_v": current*r_max,
             "nominal_loss_w": current**2*r_nominal,
             "maximum_loss_w": current**2*r_max}
            for current in (38.28,40.0)
        ],
        "switchbank_screen_NOT_qualification": {
            "candidate": "IPP110N20N3G in common-source back-to-back halves",
            "use": "Switch only; no 40A/20ms linear clamp claim",
            "VDS_rating_v": 200.0,
            "VDS_design_ceiling_requirement_v": 180.0,
            "parallel_count_per_half_working_candidate": 4,
            "total_MOSFETs_working_candidate": 8,
            "pulse_current_assessment": pulse_screen,
            "pair_bank_hot_RDS_estimate_assumes_2x25C_ohm": 2*.011*2/4,
            "pair_bank_hot_loss_estimate_at_40A_w": 40**2*2*.011*2/4,
            "pair_bank_hot_drop_estimate_at_40A_v": 40*2*.011*2/4,
            "Qg_sum_at_datasheet100V44A_conditions_c_NOT_fault_bound": gate_charge_example,
            "Qg_over_3A_typ_sink_estimate_s_NOT_guaranteed": gate_charge_example/3,
            "sum_Ciss_max_at_datasheet_conditions_f_NOT_fixed_load_model": 8*7100e-12,
            "TPSI3050_gate_supply_each_divcap_nominal_requirement_f": div_cap_nominal,
            "each_divcap_min_requirement_f": div_cap_min,
            "gate_supply_series_effective_Cmin_f": effective_gate_supply_cap_min,
            "charge_step_droop_estimate_v_NOT_fault_bound": gate_charge_example/effective_gate_supply_cap_min,
            "loaded_delay_max_verified_s": None,
        },
        "precharge_requirements_and_examples": {
            "Rpre_nominal_ohm": precharge_nominal,
            "Rpre_full_budget_min_ohm": precharge_min,
            "Rpre_full_budget_max_ohm": precharge_max,
            "Rpre_switch_bidirectional_blocking_required": True,
            "Rseries_included_and_never_bypassed": True,
            "Cmax_f": c_max,
            "source_max_before_OV_threshold_v_NOT_fault_bound": precharge_source_bound,
            "pre_OV_peak_current_example_a": precharge_source_bound/(precharge_min+r_min),
            "pre_OV_peak_Rpre_power_example_w": precharge_source_bound**2/precharge_min,
            "normal_110v_energy_to_Rpre_upper_bound_j": .5*c_max*110**2,
            "pre_OV_energy_to_Rpre_upper_example_j": .5*c_max*precharge_source_bound**2,
            "time_to_within1v_at_110v_Rmax_Cmax_s":
                (precharge_max+r_max)*c_max*math.log(110),
            "timeout_requirement_s": precharge_timeout,
            "pre_OV_shorted_load_two_second_energy_to_Rpre_upper_example_j":
                precharge_source_bound**2/precharge_min*precharge_timeout,
            "fault_source_bound_requirement_v": 160.0,
            "fault_branch_detection_to_opening_max_requirement_s": delay_requirement,
            "fault_peak_current_upper_a": 160.0/precharge_min,
            "fault_peak_Rpre_power_upper_w": 160.0**2/precharge_min,
            "fault_5us_extra_energy_Rpre_upper_j": 160.0**2/precharge_min*delay_requirement,
            "before_main_close_delta_v_max": 1.0,
            "ideal_peak_equalization_current_at_1v_delta_a": 1/r_min,
            "DUT_and_power_phases_OFF_until_main_gate_and_voltage_verified": True,
        },
        "aux_loss_hold_up_requirements_example": {
            "independent_BUS_NEG_referenced_logic_aux_required": True,
            "hold_cap_nominal_f": 10e-6,
            "hold_cap_min_f_full_budget": 8e-6,
            "total_held_rail_current_max_requirement_a": .05,
            "AUXUV_must_trip_at_or_above_v": 3.1,
            "TPSI3050_primary_recommended_min_v": 3.0,
            "ideal_held_time_to3v_from3_1v_s": 8e-6*.1/.05,
            "TPSI3050_primary_decoupling_recommended_max_f": 20e-6,
            "primary_loss_100us_typ_NOT_used_as_fast_stop": True,
            "all_aux_current_and_diode_drop_bounds_verified": False,
        },
        "inductive_interruption_cases": interruption,
        "protected_extra_energy_allocation": {
            "before_extra_peak_v": pre_extra_peak,
            "allowed_extra_peak_v": ringing_requirement,
            "extra_energy_if_absorbed_only_by_Cmin_j": allowed_extra_cap_energy,
            "max_L_if_all_1053A_energy_injected_into_C_h":
                2*allowed_extra_cap_energy/maximum_working_fault_current**2,
            "source_side_flywheel_diode_required": "anode NODE_PRE, cathode NODE_F; no selected MPN",
            "source_and_protected_energy_paths_need_separate_qualification": True,
        },
        "actual_qualification_evidence": conditions,
        "physical_limit_acceptance_tests": physical_limits,
        "qualification_gate": {
            "physical_qualification_passes": not qualification_failures,
            "failures": qualification_failures,
            "reason": "Required physical bounds and component qualifications remain absent",
            "fabrication_or_energization_release": False,
            "existing_120v_phase_bus_problem_verified": False,
        },
        "references": ["references/bus-protection-sources.json", "references/sources.json"],
    }
    return result


def render_block_diagram(folder: Path) -> None:
    """Export an illustrative functional diagram; no native CAD claim."""
    import os
    import tempfile
    os.environ.setdefault("MPLCONFIGDIR",str(Path(tempfile.gettempdir())/"bus-disconnect-mpl"))
    os.environ.setdefault("XDG_CACHE_HOME",str(Path(tempfile.gettempdir())/"bus-disconnect-cache"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    figure, axis = plt.subplots(figsize=(14.5,9.5))
    axis.set_xlim(0,14)
    axis.set_ylim(0,10)
    axis.axis("off")
    power, logic, energy = "#175588", "#654484", "#b66517"

    def box(x,y,w,h,label,color=power,fill="#f4f8fb",fontsize=10):
        axis.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.03",
                                     edgecolor=color,facecolor=fill,linewidth=1.5))
        axis.text(x+w/2,y+h/2,label,ha="center",va="center",fontsize=fontsize,
                  color="#172738",linespacing=1.35)

    def line(points,color=power,dashed=False,arrow=False):
        xs,ys=zip(*points)
        axis.plot(xs,ys,color=color,linewidth=1.7,
                  linestyle="--" if dashed else "-",solid_capstyle="round")
        if arrow:
            axis.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle="-|>",
                           mutation_scale=12,color=color,linewidth=1.5,
                           linestyle="--" if dashed else "-"))

    def node(x,y,label):
        axis.plot(x,y,"o",color=power,markersize=4)
        axis.text(x,y+.24,label,ha="center",va="bottom",fontsize=9,color=power)

    axis.text(.25,9.7,"DC-afbryder med fast serieimpedans",fontsize=18,
              fontweight="bold",color="#172738")
    axis.text(.25,9.25,"BETINGET DESIGNFORSLAG — komponenter og hardware er ikke kvalificeret",
              fontsize=11,color="#98500c")
    box(.25,6.6,1.8,1.,"BUS_SRC\n2 × 55 V mål")
    box(2.35,6.6,1.05,1.,"F_DC\nTBD")
    node(3.9,7.1,"NODE_F")
    box(4.5,6.6,1.65,1.,"R_LIMIT\n47,5 mΩ min")
    node(6.7,7.1,"NODE_PRE")
    box(7.3,6.6,2.,1.,"Q_MAIN\n4 + 4 MOS\ncommon source",fontsize=9)
    node(9.9,7.1,"BUS_PROTECTED")
    box(11.1,6.6,2.2,1.,"Effektfaser\nRUN efter MAIN_OK")
    for start,end in [((2.05,7.1),(2.35,7.1)),((3.4,7.1),(3.9,7.1)),
                      ((3.9,7.1),(4.5,7.1)),((6.15,7.1),(6.7,7.1)),
                      ((6.7,7.1),(7.3,7.1)),((9.3,7.1),(9.9,7.1)),
                      ((9.9,7.1),(11.1,7.1))]:
        line([start,end],arrow=True)
    axis.text(2.1,6.15,"NODE_F: højst 160 V\ninkl. source-side ringing",
              fontsize=9,color=power,ha="center",va="top")
    box(7.15,8.15,1.6,.8,"Q_PRE\nseparat OFF-switch",fontsize=9)
    box(9.05,8.15,1.4,.8,"R_PRE\n100 Ω mål",fontsize=9)
    line([(6.7,7.1),(6.7,8.55),(7.15,8.55)],arrow=True)
    line([(8.75,8.55),(9.05,8.55)],arrow=True)
    line([(10.45,8.55),(10.7,8.55),(10.7,7.1)],arrow=True)
    box(4.7,5.05,1.55,.8,"D_FLY\nK venstre / A højre",energy,"#fff7ee",9)
    line([(6.7,7.1),(6.7,5.45),(6.25,5.45)],energy,arrow=True)
    line([(4.7,5.45),(3.9,5.45),(3.9,7.1)],energy,arrow=True)
    axis.text(4.9,4.8,"Returløb over R_LIMIT + indrammet L\nDiode/puls/layout: TBD",
              fontsize=9,color=energy,ha="center",va="top")
    box(9.1,4.35,1.6,1.1,"C_PROTECTED\n1760 µF min\nESR ≤ 1 mΩ",fontsize=9)
    line([(9.9,7.1),(9.9,5.45)])
    line([(9.9,4.35),(9.9,3.75)])
    box(11.1,4.35,2.2,1.1,"Reverse-energy\ndump: TBD",fontsize=9)
    line([(10.8,7.1),(10.8,5.8),(12.2,5.8),(12.2,5.45)],arrow=True)
    line([(12.2,4.35),(12.2,3.75)])
    line([(8.7,3.75),(13.3,3.75)])
    axis.text(13.3,3.5,"BUS_NEG (flydende)",fontsize=9,ha="right",color=power)
    box(.25,1.5,3.4,1.05,"Hurtige TLV3501-funktioner\nSRC/PROT OV + UV\nMåler NODE_F / BUS_PROTECTED",logic,"#f7f3fa",9)
    box(4.05,1.5,2.35,1.05,"AUX_UV + hold-up\nstartup / default OFF",logic,"#f7f3fa",9)
    box(7.,1.5,2.35,1.05,"SET-prioriteret\nhardware faultlatch",logic,"#f7f3fa",9)
    box(10.15,1.5,3.15,1.05,"TPSI3050: primary EN\nisoleret gateforsyning\nVSSS = fælles MOS-source",logic,"#f7f3fa",9)
    line([(3.65,2.),(3.8,2.),(3.8,2.9),(8.18,2.9),(8.18,2.55)],logic,True,True)
    line([(6.4,2.),(7.,2.)],logic,True,True)
    line([(9.35,2.),(10.15,2.)],logic,True,True)
    line([(11.72,2.55),(11.72,3.1),(8.3,3.1),(8.3,6.6)],logic,True,True)
    axis.text(7.1,1.05,"Fault → RUN OFF, begge modul-enable OFF og AC-stop",
              fontsize=10,color=logic)
    axis.text(.25,.5,"Acceptkrav: R/C/ESR + loaded stop ≤ 5 µs + protected ringing ≤ 1 V; samlet peak < 120 V.",
              fontsize=10,color="#172738")
    axis.text(.25,.12,"Ingen native KiCad-/build-ready-påstand. F_DC, R/C-bank, Q_PRE, powerdiode, dump og faultlogic har åbne komponentvalg.",
              fontsize=9,color="#5b6673")
    figure.tight_layout(pad=.9)
    folder.mkdir(parents=True,exist_ok=True)
    for suffix in ("png","svg"):
        figure.savefig(folder/("bus_disconnect_blocks."+suffix),dpi=170,
                       facecolor="white",bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,
                        default=ROOT/"exports/analysis/bus_disconnect_envelope.json")
    parser.add_argument("--diagram",action="store_true",
                        help="Also export illustrative PNG/SVG block diagram next to JSON")
    args=parser.parse_args()
    result=calculate()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,
                                      allow_nan=False)+"\n",encoding="utf-8")
    if args.diagram:
        render_block_diagram(args.output.parent)
    print(f"Wrote {args.output}")
    print("160V conditional RC+ESR+1V reserve model:",
          "PASS" if result["conditional_160v_model"]["model_accepts"] else "FAIL")
    print("Physical qualification: FAIL; no source/R/C/ESR/delay/pulse proof supplied.")


if __name__=="__main__":
    main()
