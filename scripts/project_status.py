#!/usr/bin/python3
"""Collect current CAD evidence and explicitly separate unqualified hardware.

Run check_inventory.py after the final PCB changes, then run this script before
rendering and packaging. This aggregator does not run ERC, DRC or hardware tests.
"""
from pathlib import Path
import datetime
import hashlib
import json
import csv

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text())


def erc_findings(relative):
    return sum(len(sheet.get('violations', [])) for sheet in read(relative)['sheets'])


def cad_report(name, directory, stem, erc, drc=None):
    record = {'name': name, 'erc_report': erc,
              'erc_findings': erc_findings(erc),
              'hardware_tests_performed': False,
              'fabrication_released': False}
    if drc:
        result = read(drc)
        record.update(drc_report=drc,
                      geometry_findings=len(result['violations']),
                      missing_connections=len(result['unconnected_items']),
                      schematic_parity_findings=len(result['schematic_parity']))
        record['cad_pass'] = not any(record[key] for key in
                                    ('erc_findings', 'geometry_findings',
                                     'missing_connections', 'schematic_parity_findings'))
    else:
        record.update(pcb='not applicable; chassis wiring only',
                      cad_pass=record['erc_findings'] == 0)
    record['source_sha256'] = {}
    native_suffixes = {'.kicad_pro', '.kicad_sch', '.kicad_pcb', '.kicad_dru',
                       '.kicad_sym', '.kicad_mod'}
    for path in sorted((ROOT / 'design' / directory).rglob('*')):
        if path.is_file() and (path.suffix in native_suffixes or path.name in {'sym-lib-table', 'fp-lib-table'}):
            record['source_sha256'][str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return record


if __name__ == '__main__':
    inventory = read('exports/verification/inventory.json')
    projects = [
        cad_report('Målekort', 'measurement', 'measurement',
                   'exports/verification/erc.json', 'exports/verification/drc.json'),
        cad_report('Effektfase', 'power', 'power_phase',
                   'exports/power/erc.json', 'exports/power/drc.json'),
        cad_report('Netdel', 'frontend', 'frontend', 'exports/frontend/erc.json'),
        cad_report('Styrekort', 'control', 'control',
                   'exports/control/erc_routed.json', 'exports/control/drc_routed.json'),
    ]
    for project in projects:
        matching = next(row for row in inventory['checks'] if row['project'] == project['name'])
        if matching['inventory'] != 'PASS':
            raise RuntimeError('Inventory failed: '+project['name'])
        project['inventory_report'] = 'exports/verification/inventory.json'
        project['inventory'] = matching
    power = read('exports/power/layout_summary.json')
    power_project = next(p for p in projects if p['name'] == 'Effektfase')
    if power['track_objects'] != power_project['inventory']['track_objects']:
        raise RuntimeError('Power inventory is stale; run check_inventory.py after PCB handoff')
    if power['unconnected_items'] != power_project['missing_connections']:
        raise RuntimeError('Power layout summary and DRC disagree')
    analysis = [
        ('Effektbudget', 'exports/analysis/design_budget.json',
         'Nominal efficiency/power-factor assumptions; no measured efficiency.'),
        ('Statiske styregrænser', 'exports/analysis/control_limits.json',
         'Ideal DC KCL and explicit tolerance assumptions; no dynamic rail-off validation.'),
        ('Tab, ripple, strømfordeling og loop', 'exports/analysis/power_analysis.json',
         'Analytical/ideal buck and assumed plant models; no LTC3779 device simulation.'),
        ('Lavstrøm og 0 V / 0 A', 'exports/analysis/low_current.json',
         'Unimplemented candidate range/stage and energy budgets; no hardware precision guarantee.'),
        ('Busbeskyttelse', 'exports/analysis/bus_protection.json',
         'Fault/transient and SOA scenarios; no selected/qualified 120 V protection circuit.'),
        ('Uafhængige fasestrømservoer', 'exports/analysis/phase_balance.json',
         'Native one-channel study and assumed averaged four-phase model; not integrated hardware.'),
        ('Separat lavstrøms-loop', 'exports/analysis/low_current_loop.json',
         '24 assumed linear plant cases; no transistor SPICE model, compensation release or fast fault qualification.'),
        ('Betinget fysisk busafbrydelse', 'exports/analysis/bus_disconnect_envelope.json',
         'RC/ESR/delay envelope with required hard bounds; switch SOA and actual source/parts are unqualified.'),
    ]
    calculations = []
    for title, relative, scope in analysis:
        path = ROOT / relative
        read(relative)
        calculations.append({'name': title, 'report': relative, 'scope': scope,
                             'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    study = read('exports/control/studies/summary.json')
    if not study['BOM_XML_refs_values_footprints_match'] or study['ERC_violations_all_severities']:
        raise RuntimeError('Phase study inventory/ERC is not clean')
    status = {
        'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'INCOMPLETE DESIGN DRAFT; NOT A COMPLETE 0-100 V / 40 A PSU',
        'requirements': {'input_VAC': 230, 'input_circuit_A': 32,
                         'voltage_range_V': [0, 100], 'current_range_A': [0, 40],
                         'continuous_output_W': 4000, 'isolated_floating_output': True},
        'projects': projects, 'calculations': calculations,
        'automation_source_sha256': {
            str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((ROOT/'scripts').glob('*'))
            if path.is_file() and path.suffix in {'.py', '.cpp', '.json'}},
        'CAD_main_projects_pass': all(project['cad_pass'] for project in projects),
        'critical_component_matrix': {
            'report': 'bom/critical-components.csv',
            'rows': sum(1 for _ in csv.DictReader((ROOT/'bom/critical-components.csv').open(encoding='utf-8-sig'))),
            'procurement_released': False},
        'main_BOM_rows': sum(1 for _ in csv.DictReader((ROOT/'bom/current-draft.csv').open(encoding='utf-8-sig'))),
        'phase_study_BOM_rows': sum(1 for _ in csv.DictReader((ROOT/'bom/phase-balancing-study.csv').open(encoding='utf-8-sig'))),
        'native_phase_study': {'schematic': 'design/control/studies/phase_sensor_study.kicad_sch',
                               'checks': 'exports/control/studies/summary.json',
                               'ERC_findings': study['ERC_violations_all_severities'],
                               'BOM_XML_refs_values_footprints_match': True,
                               'expected_pin_nodes_checked': study['expected_pin_nodes_checked'],
                               'integrated_in_routed_PCBs': False,
                               'hardware_released': False},
        'physical_tests_performed': False, 'fabrication_released': False,
        'remaining': [
            'Qualify RSP-3000-48 series/floating operation and chassis/mains integration.',
            'Resolve 134.4 V module OVP threshold budget versus 120 V regulator procedure limit before power testing.',
            'Independently review power gate/source loops, Kelvin routing, current return and thermal implementation despite CAD PASS.',
            'Select/verify exact power inductors, capacitors, shunts, diodes, terminals, fuses, auxiliary supplies and cooling.',
            'Implement and qualify phase sharing and phase/rail fault behavior for continuous 40 A.',
            'Integrate CV/CC, validate startup, rail-off and command/feedback faults; implement independent output disconnect.',
            'Implement post-bulk precision low-current limiting, range interlock and defined output discharge/0 V behavior.',
            'Validate control loops, transient/ringing/SOA, short circuit, efficiency, temperature, isolation and EMC on hardware.',
        ],
    }
    destination = ROOT / 'exports/verification/project_status.json'
    destination.write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'report': str(destination),
                      'cad': [{key: p[key] for key in ('name', 'cad_pass', 'erc_findings')}
                              | ({'missing_connections': p['missing_connections']} if 'missing_connections' in p else {})
                              for p in projects],
                      'hardware_tests_performed': False}, ensure_ascii=False, indent=2))
