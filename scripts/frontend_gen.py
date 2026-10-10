#!/usr/bin/python3
"""Create a chassis wiring draft, not a mains PCB or a qualified PSU.

Module terminals follow the official RSP-3000 spec, pages 9-10.
Module symbols are functional terminal representations, with passive pins;
ERC checks only the authoring and named connections, not module internals.
"""
from pathlib import Path
import csv
import json
import subprocess
import xml.etree.ElementTree as ET
import kicad_helpers as h

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'design' / 'frontend'
E = ROOT / 'exports' / 'frontend'
for folder in (D, E):
    folder.mkdir(parents=True, exist_ok=True)
NAME = 'frontend'
SPEC = 'https://meanwell.com/Upload/PDF/RSP-3000/RSP-3000-SPEC.PDF'


def module_symbol():
    name = 'RSP3000_48_TERMINALS'
    result = [f'(symbol "{name}" (pin_names (offset 1.27)) (in_bom yes) (on_board no)',
              '(property "Reference" "A" (at 0 27.94 0) (effects (font (size 1.27 1.27))))',
              f'(property "Value" "{name}" (at 0 -27.94 0) (effects (font (size 1.27 1.27))))']
    pin_groups = {
        1: [('TB1.1', 'AC/L', 'L', 12.7), ('TB1.2', 'AC/N', 'L', 0),
            ('TB1.3', 'FG', 'L', -12.7), ('+V', '+V', 'R', 12.7),
            ('-V', '-V', 'R', -12.7)],
        2: [('CN2.1', 'RCG', 'L', 19.05), ('CN2.2', 'RC', 'L', 12.7),
            ('CN2.3', 'PV', 'L', 6.35), ('CN2.4', 'PS', 'L', 0),
            ('CN2.5', '-S', 'L', -6.35), ('CN2.6', 'CS', 'L', -12.7),
            ('CN2.7', '-S', 'L', -19.05), ('CN2.8', '+S', 'R', 19.05),
            ('CN3.1', 'P_OK_GND', 'R', 12.7), ('CN3.2', 'P_OK', 'R', 6.35),
            ('CN3.7', 'AUXG', 'R', 0), ('CN3.8', 'AUX12', 'R', -6.35),
            ('CN3.9', 'OLP', 'R', -12.7), ('CN3.10', 'OL-SD', 'R', -19.05)]
    }
    for unit, pins in pin_groups.items():
        result.append(f'(symbol "{name}_{unit}_1" (rectangle (start -20.32 25.4) (end 20.32 -25.4) (stroke (width 0.254) (type default)) (fill (type background)))')
        for number, label, side, y in pins:
            x, angle = (-25.4, 0) if side == 'L' else (25.4, 180)
            result.append(f'(pin passive line (at {x} {y} {angle}) (length 5.08) (name "{label}" (effects (font (size 1.0 1.0)))) (number "{number}" (effects (font (size 0.8 0.8)))))')
        result.append(')')
    return '\n'.join(result) + ')'


(D / 'Frontend.kicad_sym').write_text(
    '(kicad_symbol_lib (version 20241209) (generator "frontend-gen")\n' + module_symbol() + '\n)\n')
system_library = h.library


def library(name):
    return h.parse((D / 'Frontend.kicad_sym').read_text()) if name == 'Frontend' else system_library(name)


h.library = library
all_components, power, control = [], [], []


def add(ref, value, lib, xy, nets, function, status, sheet='power', unit=1, angle=0, source=''):
    c = dict(ref=ref, val=value, lib=lib, xy=xy, nets=nets, unit=unit,
             angle=angle, uuid=h.uid(), description=function, datasheet=source,
             footprint='', on_board=False, label_length=3.81, release=status)
    all_components.append(c)
    (power if sheet == 'power' else control).append(c)
    return c


pending = 'KRAV / FORELØBIG DEL - VARENUMMER OG RATING IKKE FRIGIVET'
add('J1', '230 VAC / 32 A CIRCUIT', 'Connector_Generic:Conn_01x03',
    (30.48, 53.34), {'1': 'AC_L_IN', '2': 'AC_N_IN', '3': 'PE'},
    'Kabinettilslutning: L, N, PE. Indgangstype, kabel og kontakt-rating skal vælges; kredsens 32 A er ikke en komponentrating.', pending)
add('SW1', '2-POLE MAINS SWITCH - TBD', 'Switch:SW_DPST',
    (83.82, 53.34), {'1': 'AC_N_IN', '2': 'AC_N', '3': 'AC_L_IN', '4': 'AC_L'},
    'Afbryder L og N samtidigt. PE må ikke afbrydes. AC/inrush-rating og fabrikant mangler.', pending)
for i, y in [(1, 91.44), (2, 167.64)]:
    add(f'F{i}', 'AC BRANCH FUSE - TBD', 'Device:Fuse',
        (55.88, y - 12.7), {'1': 'AC_L', '2': f'AC_L_M{i}'},
        'Separat grenbeskyttelse til AC/DC-modul; strøm, karakteristik, spænding og brydeevne skal dimensioneres efter modul og installation.', pending, angle=90)
    plus, minus = ('BUS_MID', 'BUS_NEG') if i == 1 else ('BUS_POS', 'BUS_MID')
    module = add(f'A{i}', 'RSP-3000-48 / SVR 55.0 V',
                 'Frontend:RSP3000_48_TERMINALS', (157.48, y),
                 {'TB1.1': f'AC_L_M{i}', 'TB1.2': 'AC_N', 'TB1.3': 'PE', '+V': plus, '-V': minus},
                 'Isoleret 48 V / 62,5 A / 3000 W modul; dokumenteret SVR-trim 43–56 V. Arbejdssetpunkt 55 V; seriekobling og samlet integration kræver kvalifikation.',
                 'OFFICIELT DATABLAD LÆST; SYSTEMINTEGRATION IKKE FRIGIVET', source=SPEC)
    module['module'] = True
    add(f'D{i}', 'REVERSE DIODE >=200 V / IFSM >62.5 A', 'Device:D',
        (259.08, y), {'1': plus, '2': minus},
        'Antiparallel diode på hvert moduls DC-udgang: katode +V, anode −V. Producent-FAQ kræver VRRM over samlet maksimal bus og IFSM over modulstrøm; IFAV, SOA, køling og varenummer mangler.', pending, angle=90)
add('J2', '110 V DC BUS - NOT DUT OUTPUT', 'Connector_Generic:Conn_01x02',
    (350.52, 124.46), {'1': 'BUS_POS', '2': 'BUS_NEG'},
    'Bus til regulator. Ingen laboratorieregulering eller bus-afbryder på dette diagram. Terminaler og busbars skal dimensioneres til mindst 45 A som foreløbigt krav.', pending)

for i, x in [(1, 109.22), (2, 307.34)]:
    plus, minus = ('BUS_MID', 'BUS_NEG') if i == 1 else ('BUS_POS', 'BUS_MID')
    add(f'A{i}', 'RSP-3000-48 / SVR 55.0 V',
        'Frontend:RSP3000_48_TERMINALS', (x, 99.06),
        {'CN2.1': f'M{i}_AUXG', 'CN2.2': f'M{i}_RC',
         'CN2.3': f'M{i}_PV_PS', 'CN2.4': f'M{i}_PV_PS',
         'CN2.5': None, 'CN2.6': None, 'CN2.7': minus, 'CN2.8': plus,
         'CN3.1': f'M{i}_OK_COM', 'CN3.2': f'M{i}_OK',
         'CN3.7': f'M{i}_AUXG', 'CN3.8': f'M{i}_AUX12',
         'CN3.9': f'M{i}_OLP_OLSD', 'CN3.10': f'M{i}_OLP_OLSD'},
        'Fabriksjumpere PV–PS og OLP–OL-SD beholdes. Egen local sense og remote-enable. CN1/CN2 er parallelle internt; brug ét stik. De to modulers signaljord må ikke forbindes.',
        'DATABLADSPINOUT KONTROLLERET; EKSTERN STYRING UAFSLUTTET',
        sheet='control', unit=2, source=SPEC)
    add(f'R{i}', '1k / 1% / >=0.25 W', 'Device:R',
        (x, 160.02), {'1': f'M{i}_AUX12', '2': f'M{i}_RC'},
        'Egen AUX12 til RC gennem 1 kΩ, ifølge fabrikantens default-OFF eksempel 3.2C. Ved nominelle 12 V og 1 kΩ er effekten 144 mW; endelig rating skal medtage tolerancer. AUX er kun til styrefunktion, ikke gate/fan-forsyning.',
        'VÆRDI FRA OFFICIELT EKSEMPEL; ENDELIG MODSTANDSSERIE MANGLER',
        sheet='control', angle=90, source=SPEC)
    add(f'K{i}', 'ISOLATED NO CONTACT - ENABLE', 'Switch:SW_SPST',
        (x, 193.04), {'1': f'M{i}_RC', '2': f'M{i}_AUXG'},
        'Potentialfri normalt åben kontakt; lukket aktiverer modulet, åben slukker. Symbol viser kun kontaktfunktionen; relæspole, driver, fail-safe og kontakt/isolation-rating er endnu ikke valgt.',
        pending, sheet='control')
add('J3', 'TWO ISOLATED P_OK CONTACTS', 'Connector_Generic:Conn_01x04',
    (198.12, 228.6), {'1': 'M1_OK_COM', '2': 'M1_OK', '3': 'M2_OK_COM', '4': 'M2_OK'},
    'Hvert moduls P_OK-relækontakt. Fabrikantgrænse 20 V, 500 mA, 10 W. Et OK-signal ved cirka 80 % er ikke dokumentation for en præcis 55 V bus. Ekstern statusmåling mangler.', pending, sheet='control')

root, child = h.uid(), h.uid()
(D / (NAME + '.kicad_pro')).write_text(json.dumps(
    {'meta': {'filename': NAME + '.kicad_pro', 'version': 1}}, indent=2) + '\n')
libs = sorted({c['lib'].split(':')[0] for c in all_components})
(D / 'sym-lib-table').write_text('(sym_lib_table (version 7)\n' + '\n'.join(
    f'(lib (name "{lib}") (type "KiCad") (uri "' +
    ('${KIPRJMOD}/Frontend.kicad_sym' if lib == 'Frontend' else '${KICAD9_SYMBOL_DIR}/' + lib + '.kicad_sym') +
    '") (options "") (descr "Chassis draft symbols"))' for lib in libs) + '\n)\n')

h.write_schematic(D / (NAME + '.kicad_sch'), power, project=NAME, root_uuid=root,
    title='ISOLATED FRONT-END - CHASSIS WIRING DRAFT',
    comments=['2 x RSP-3000-48 set to 55 V; nominal 110 V bus',
              'No mains PCB; no fabrication release; final protections pending',
              'FG and cabinet to PE; floating BUS_NEG is NOT PE',
              'Modules have independent local controls and sense'],
    sheets=[dict(name='Independent module enable and sense', file='control.kicad_sch',
                 xy=(139.7, 228.6), size=(111.76, 30.48), uuid=child)],
    texts=[dict(xy=(15.24, 17.78), text='CHASSIS WIRING DRAFT: purchased isolated modules, not a 230 V PCB.\n110 V bus feeds a separate regulator; it is NOT the DUT output.'),
           dict(xy=(292.1, 68.58), size=1.1, text='Each output: 55 V nominal.\nBUS_MID links A1 +V to A2 -V.\nNever connect BUS_MID to PE.\nDiode K to own +V, A to own -V.'),
           dict(xy=(284.48, 167.64), size=1.1, text='Module OVP: 57.6..67.2 V each.\nThreshold sum upper: 134.4 V.\nThis is NOT a transient clamp.\nBUS_OVP, disconnect, inrush and\nall-module fault logic missing.'),
           dict(xy=(15.24, 213.36), size=1.1, text='AC wiring, fuses, switch, protective earth and busbars require final rated parts.\nNo full-load, isolation, thermal or fault test has been performed.\nThe power prototype procedural input maximum 120 V is NOT guaranteed by module OVP.')])
h.write_schematic(D / 'control.kicad_sch', control, project=NAME,
    root_uuid=child, instance_path='/' + root + '/' + child,
    title='RSP-3000 INDEPENDENT ENABLE / SENSE',
    comments=['Spec remote-enable example 3.2C; contact open = OFF',
              'PV-PS and OLP-OLSD denote retained factory jumpers',
              'NO common AUXG, CS, remote sense or RC between modules'],
    texts=[dict(xy=(15.24, 17.78), text='Keep each module control on its own local output reference.\nThe ENABLE contact symbols are requirements: coil/drivers and hardware fault interlock are missing.'),
           dict(xy=(25.4, 43.18), text='A1 lower module'), dict(xy=(228.6, 43.18), text='A2 upper module'),
           dict(xy=(15.24, 261.62), size=1.1, text='AUX12: 12 V / 100 mA control-only per module. No direct common MCU wiring.\nP_OK isolated contacts do not replace separate voltage, OVP, OTP and full bus supervision.\nCN2.5 (-S duplicate) and CN2.6 (CS parallel-current-share) intentionally unused.')])

# Keep module property text outside the rectangles on both sheets.
for file in (D / (NAME + '.kicad_sch'), D / 'control.kicad_sch'):
    doc = h.parse(file.read_text())
    for sym in h.children(doc, 'symbol'):
        lib = h.sub(sym, 'lib_id')
        if lib is None:
            continue
        at = h.sub(sym, 'at')
        for prop in h.children(sym, 'property'):
            if lib[1] == 'Frontend:RSP3000_48_TERMINALS' and prop[1] in ('Reference', 'Value'):
                p = h.sub(prop, 'at')
                p[2] = h.Atom(str(float(at[2]) + (-30.48 if prop[1] == 'Reference' else 30.48)))
            if lib[1] == 'Switch:SW_DPST' and prop[1] in ('Reference', 'Value'):
                h.sub(prop, 'at')[2] = h.Atom(str(float(at[2]) + (-10.16 if prop[1] == 'Reference' else 10.16)))
            if lib[1] == 'Device:D' and prop[1] == 'Value':
                h.sub(prop, 'at')[2] = h.Atom(str(float(at[2]) + 12.7))
    file.write_text(h.emit(doc) + '\n')


def cli(*args):
    subprocess.run([str(ROOT / 'bin/kicad-env'), 'kicad-cli', *map(str, args)], check=True)


cli('sch', 'export', 'netlist', '--format', 'kicadxml', '-o', E / 'frontend.xml', D / (NAME + '.kicad_sch'))
cli('sch', 'export', 'pdf', '-o', E / 'frontend.pdf', D / (NAME + '.kicad_sch'))
cli('sch', 'export', 'svg', '-o', E / 'schematic_svg', D / (NAME + '.kicad_sch'))
cli('sch', 'erc', '--severity-all', '--exit-code-violations', '--format', 'json', '-o', E / 'erc.json', D / (NAME + '.kicad_sch'))
raw_nets = {net.attrib['name']: {(node.attrib['ref'], node.attrib['pin']) for node in net.findall('node')}
            for net in ET.parse(E / 'frontend.xml').findall('./nets/net')}
declared_nc = {(c['ref'], pin) for c in all_components for pin, net in c['nets'].items() if net is None}
nc_nets = {name: pins for name, pins in raw_nets.items() if name.startswith('unconnected-')}
assert all(len(pins) == 1 for pins in nc_nets.values()), 'A declared no-connect has an unexpected connection'
assert set().union(*nc_nets.values()) == declared_nc, 'Exported no-connect pins differ from declared no-connects'
actual = {name: pins for name, pins in raw_nets.items() if name not in nc_nets}
expected = {}
for c in all_components:
    for pin, net in c['nets'].items():
        if net is not None:
            expected.setdefault(net, set()).add((c['ref'], pin))
assert actual == expected, 'Exported frontend terminal connections differ from intended connections'
unique = {}
for c in all_components:
    unique.setdefault(c['ref'], c)
with (ROOT / 'bom/frontend.csv').open('w', encoding='utf-8', newline='') as out:
    writer = csv.writer(out)
    writer.writerow(['Reference', 'Value', 'Footprint', 'Quantity', 'Description', 'Source', 'Release_status'])
    for c in unique.values():
        writer.writerow([c['ref'], c['val'], 'CHASSIS / OFFBOARD - NO PCB', 1,
                         c['description'], c['datasheet'], c['release']])
(E / 'summary.json').write_text(json.dumps(
    {'scope': 'Unqualified chassis wiring draft, purchased isolated modules only',
     'components': len(unique), 'terminal_connections': sum(map(len, expected.values())),
     'erc': 'passed; passive functional module pins, not module internal validation',
     'terminal_netlist_comparison': 'passed', 'pcb': 'not applicable; no mains PCB',
     'nominal_bus_V': 110, 'module_OVP_sum_upper_V': 134.4,
     'hardware_tests': 'not performed', 'fabrication_release': False}, indent=2) + '\n')
print('Generated chassis wiring draft; no mains PCB or manufacturing release.')
