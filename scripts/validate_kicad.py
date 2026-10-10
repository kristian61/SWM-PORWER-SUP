#!/usr/bin/python3
"""Run KiCad checks and independently compare every schematic pin with PCB pads."""
from pathlib import Path
import datetime
import json
import subprocess
import shutil
import tempfile
import xml.etree.ElementTree as ET

import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'design' / 'measurement' / 'measurement'
OUT = ROOT / 'exports' / 'verification'
OUT.mkdir(parents=True, exist_ok=True)
WRAPPER = ROOT / 'bin' / 'kicad-env'


def run(*args):
    result = subprocess.run([str(WRAPPER), 'kicad-cli', *map(str, args)],
                            cwd=ROOT, text=True, capture_output=True)
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip())
    result.check_returncode()


if __name__ == '__main__':
    run('sch', 'erc', '--severity-all', '--exit-code-violations', '--format', 'json',
        '-o', OUT / 'erc.json', BASE.with_suffix('.kicad_sch'))
    run('sch', 'export', 'netlist', '--format', 'kicadxml',
        '-o', OUT / 'netlist.xml', BASE.with_suffix('.kicad_sch'))
    run('pcb', 'drc', '--severity-all', '--all-track-errors', '--schematic-parity',
        '--exit-code-violations', '--format', 'json', '-o', OUT / 'drc.json',
        BASE.with_suffix('.kicad_pcb'))

    # Prove that HV rules execute, using an impossible temporary spacing.
    # This catches lost netclass assignments, disabled severities and wrong units.
    with tempfile.TemporaryDirectory(prefix='psu-hv-rule-', dir='/tmp') as scratch:
        folder = Path(scratch)
        for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_sch'):
            shutil.copy2(BASE.with_suffix(suffix), folder / ('measurement' + suffix))
        for name in ('sym-lib-table', 'fp-lib-table'):
            shutil.copy2(BASE.parent / name, folder / name)
        rules = (folder / 'measurement.kicad_dru').read_text()
        if rules.count('(min 3.0mm)') != 1:
            raise RuntimeError('Missing unique HV spacing rule with explicit units.')
        (folder / 'measurement.kicad_dru').write_text(
            rules.replace('(min 3.0mm)', '(min 100.0mm)')
        )
        report = folder / 'activation.json'
        probe = subprocess.run(
            [str(WRAPPER), 'kicad-cli', 'pcb', 'drc', '--format', 'json',
             '--exit-code-violations', '-o', str(report),
             str(folder / 'measurement.kicad_pcb')],
            cwd=ROOT, text=True, capture_output=True,
        )
        detected = [item for item in json.loads(report.read_text())['violations']
                    if item['type'] == 'clearance'
                    and 'HV copper separation' in item['description']]
        if not probe.returncode or not detected:
            raise RuntimeError('HV rule activation failed negative control.')
        activation = {'result': 'PASS', 'temporary_minimum_mm': 100,
                      'detected_HV_violations': len(detected),
                      'temporary_DRC_exit': probe.returncode,
                      'original_project_modified': False}
        (OUT / 'hv-rule-activation.json').write_text(
            json.dumps(activation, indent=2) + '\n'
        )

    xml = ET.parse(OUT / 'netlist.xml').getroot()
    schematic_components = {
        comp.attrib['ref']: comp.findtext('value')
        for comp in xml.findall('./components/comp')
    }
    schematic_pins = {
        (node.attrib['ref'], node.attrib['pin']): net.attrib['name']
        for net in xml.findall('./nets/net') for node in net.findall('node')
    }
    board = pcbnew.LoadBoard(str(BASE.with_suffix('.kicad_pcb')))
    pcb_components = {
        fp.GetReference(): fp.GetValue() for fp in board.GetFootprints()
    }
    pcb_pins = {
        (fp.GetReference(), pad.GetNumber()): pad.GetNetname()
        for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNumber()
    }
    if schematic_components != pcb_components:
        raise RuntimeError('Schematic component references/values differ from PCB.')
    if schematic_pins != pcb_pins:
        mismatches = [
            {'ref': ref, 'pin': pin, 'schematic': schematic_pins.get((ref, pin)),
             'pcb': pcb_pins.get((ref, pin))}
            for ref, pin in sorted(set(schematic_pins) | set(pcb_pins))
            if schematic_pins.get((ref, pin)) != pcb_pins.get((ref, pin))
        ]
        raise RuntimeError(f'Pin/net mismatch: {mismatches}')
    version = subprocess.check_output(
        [str(WRAPPER), 'kicad-cli', 'version'], cwd=ROOT, text=True
    ).strip()
    result = {
        'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'kicad_version': version,
        'target': 'passive measurement board only',
        'components': len(schematic_components),
        'connected_pads': len(schematic_pins),
        'nets': len(set(schematic_pins.values())),
        'erc': 'passed with all severities',
        'drc': 'passed with all severities and schematic parity',
        'independent_pin_net_comparison': 'passed',
        'HV_rule_activation_negative_control': 'passed',
        'hardware_tests': 'not performed',
        'power_stage_4kW': 'not designed or validated',
    }
    (OUT / 'summary.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)
                                      + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
