#!/usr/bin/python3
"""Independently compare exported KiCad inventories against BOM and PCB.

This checks the delivery's references, values, footprints and terminal nets.
It does not turn an unrouted board into a passing DRC or validate regulation.
"""
from pathlib import Path
import csv
import datetime
import json
import xml.etree.ElementTree as ET
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = [('Målekort', 'measurement', 'measurement', 'measurement.csv'),
            ('Effektfase', 'power', 'power_phase', 'power-phase.csv'),
            ('Netdel', 'frontend', 'frontend', 'frontend.csv')]
if (ROOT / 'bom/control.csv').exists():
    PROJECTS.append(('Styrekort', 'control', 'control', 'control.csv'))


def check(board_name, directory, stem, bom_name):
    xml = ET.parse(ROOT / 'exports' / directory / (stem + '.xml')).getroot()
    schematic = {}
    for comp in xml.findall('./components/comp'):
        ref = comp.attrib['ref']
        if ref.startswith('#'):
            continue
        schematic[ref] = (comp.findtext('value'), comp.findtext('footprint') or '')
    with (ROOT / 'bom' / bom_name).open(encoding='utf-8-sig', newline='') as source:
        rows = list(csv.DictReader(source))
    if len({row['Reference'] for row in rows}) != len(rows):
        raise RuntimeError(f'{board_name}: duplicate BOM references')
    # These exact references describe external Kelvin shunts, not omitted PCB
    # parts. All other references must still match the exported schematic.
    external_requirements = {'SHUNT_EXT', 'SHUNT_EXTERNAL'}
    offboard = [row for row in rows if row['Reference'] in external_requirements]
    bom = {row['Reference']: row for row in rows if row not in offboard}
    if set(bom) != set(schematic):
        raise RuntimeError(f'{board_name}: schematic/BOM reference mismatch')
    for ref, (value, footprint) in schematic.items():
        row = bom[ref]
        if value != row['Value']:
            raise RuntimeError(f'{board_name}:{ref}: schematic/BOM value mismatch')
        if footprint and footprint != row['Footprint']:
            raise RuntimeError(f'{board_name}:{ref}: schematic/BOM footprint mismatch')
        if int(row['Quantity']) != 1:
            raise RuntimeError(f'{board_name}:{ref}: per-reference quantity must be one')
    result = {'project': board_name, 'inventory': 'PASS',
              'schematic_components': len(schematic), 'offboard_requirements': len(offboard)}
    pcb = ROOT / 'design' / directory / (stem + '.kicad_pcb')
    if pcb.exists():
        board = pcbnew.LoadBoard(str(pcb))
        physical = {fp.GetReference(): (fp.GetValue(),
                    str(fp.GetFPID().GetLibNickname()) + ':' + str(fp.GetFPID().GetLibItemName()))
                    for fp in board.GetFootprints()}
        if physical != schematic:
            raise RuntimeError(f'{board_name}: schematic/PCB refs, values or footprints differ')
        sch_pins = {(node.attrib['ref'], node.attrib['pin']): net.attrib['name']
                    for net in xml.findall('./nets/net') for node in net.findall('node')
                    if not node.attrib['ref'].startswith('#')}
        pads = {}
        physical_numbered_pads = 0
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if not pad.GetNumber():
                    continue
                key = (fp.GetReference(), pad.GetNumber())
                # Some packages expose several physical pads with one logical
                # pin number. Check each pad, rather than allowing the last
                # duplicate to hide a differently assigned earlier pad.
                if sch_pins.get(key) != pad.GetNetname():
                    raise RuntimeError(f'{board_name}:{key}: physical pad-net mismatch')
                pads[key] = pad.GetNetname()
                physical_numbered_pads += 1
        if pads != sch_pins:
            raise RuntimeError(f'{board_name}: schematic/PCB pin-net mismatch')
        result.update({'PCB_pin_net_comparison': 'PASS', 'logical_pads': len(pads),
                       'physical_numbered_pads': physical_numbered_pads,
                       'track_objects': len(list(board.GetTracks()))})
    else:
        result['PCB'] = 'not applicable; offboard chassis wiring only'
    return result


if __name__ == '__main__':
    summary = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'checks': [check(*project) for project in PROJECTS],
               'scope': 'inventory/logical pin consistency only; see each DRC and hardware status'}
    out = ROOT / 'exports/verification/inventory.json'
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
