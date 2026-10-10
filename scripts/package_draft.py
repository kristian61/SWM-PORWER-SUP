#!/usr/bin/python3
"""Collect both draft boards, their Danish parts list and source provenance."""
from pathlib import Path
import csv
import hashlib
import json
import zipfile
import argparse
import datetime

ROOT = Path(__file__).resolve().parents[1]


def function(board, ref, description=''):
    if board in ('Netdel', 'Styrekort'):
        if not description:
            raise ValueError(f'Missing component description for {board}:{ref}')
        return description
    if board == 'Målekort':
        if ref in ('R1', 'R2', 'R3', 'R5', 'R6', 'R7'):
            return 'Øverste modstandskæde i 40:1 spændingsdeler; 0,1 %, mindst 100 V arbejdsrating og 0,25 W.'
        if ref in ('R4', 'R8'):
            return 'Bundmodstand i spændingsdeler; 0,1 %, mindst 0,125 W. Åben modstand kræver separat fejlbeskyttelse.'
        if ref in ('R9', 'R10'):
            return 'Seriemodstand i spændingsmålefilter.'
        if ref in ('R11', 'R12'):
            return 'Seriemodstand i Kelvin-strømmålefilter.'
        if ref in ('C1', 'C2'):
            return '10 nF spændingsmålefilter; C0G/NP0, ±5 %, 50 V. Omtrent 1,48 kHz inklusive delerens impedans.'
        if ref == 'C3':
            return '10 nF differentialfilter; C0G/NP0, ±5 %, 50 V. Omtrent 7,96 kHz med to 1 kΩ modstande.'
        if ref == 'SHUNT_EXT':
            return 'Ekstern 1 mΩ fireterminal-shunt; mindst 10 W og 50 A DC. Ikke en monteret kortkomponent.'
        if ref.startswith('TP'):
            return 'Testpad; net og forventet spænding findes i docs/manual.md. TP1/TP2 kan have høj spænding.'
        return {'J1': 'OUT+/OUT− senseindgang, ingen belastningsstrøm.',
                'J2': 'Ekstern Kelvin-shunt og flydende AGND-reference.',
                'J3': 'Analoge måleudgange; ingen ADC, forstærker, isolation eller aktiv beskyttelse.'}[ref]
    groups = {
        'U1': 'LTC3779 fire-switch buck/boost-controller; fast spændingsfeedback i dette udkast.',
        'L1': 'Ekstern 150 µH spole; mindst 15 A rms og varm mætningsstrøm 25 A som krav. Fabrikat mangler.',
        'J1': 'Indgang fra isoleret DC-kilde; foreløbige terminaler, fabrikant/rating mangler.',
        'J2': 'Fast 99,6 V nominelt output; 10 A udviklingsmål, ikke fysisk verificeret.',
        'J3': 'Ekstern isoleret 12 V hjælpeforsyning.',
        'J4': 'Enable, sync, PGOOD og flydende PGND; PGOOD pull-up er cirka 5,5 V.',
        'R5': 'Forbinder NDRV med DRVCC og deaktiverer ekstern pass-regulator.',
        'R6': 'RUN-pulldown; default shutdown.', 'R7': 'Enable-seriemodstand.',
        'R8': 'Holder ubrugt PLLIN lav.', 'R9': 'Programmerer cirka 101,8 kHz.',
        'R10': 'PGOOD pull-up til V5, cirka 5,5 V.',
        'R19': 'VOUTSNS-forbindelse til output-MOSFETens drain PREOUT.',
        'R26': 'Startværdi for ITH-kompensation; loop-stabilitet mangler.',
        'C9': 'DRVCC-afkobling.', 'C10': 'V5-afkobling.',
        'C11': '12 V hjælpeafkobling.', 'C12': 'Soft start; cirka 24 ms til 1,2 V.',
        'C15': '220 pF differentialt filter for cycle-strømmåling.',
        'C16': 'Differentialt filter for intern middelstrømsmåling.',
        'C17': 'Startværdi i seriekompensation ved ITH.',
        'C18': 'Højfrekvent ITH-kompensationskondensator.',
    }
    if ref in groups:
        return groups[ref]
    if ref.startswith('TP'):
        return 'Testpad; se docs/power-phase.md for net, fortegn, reference og forventet waveform.'
    if ref.startswith('Q'):
        return 'BSC110N15NS5: fabrikantdatablad og pinout verificeret, 150 V og højst 11 mΩ ved 10 V / 25 °C. Layout, oversving og termik er endnu uverificeret.'
    if ref in ('D1', 'D2'):
        return 'Bootstrap-ladediode DFLS1200-7; 1 A / 200 V fra ADI-reference, eget datablad mangler.'
    n = int(ref[1:])
    if ref.startswith('R'):
        if n <= 2:
            return 'To 12 mΩ i parallel giver 6 mΩ hurtig lavside-shunt; Kelvin-routing kræves.'
        if n <= 4:
            return 'To 8 mΩ i parallel giver 4 mΩ output-shunt og nominelt 12,5 A fast middelstrømsloft.'
        if 11 <= n <= 14:
            return 'Gate-jumper; endelig modstand bestemmes efter switching-, ringing- og tabsmåling.'
        if n in (15, 16):
            return '100 Ω Kelvin-filter til hurtig cycle-strømmåling.'
        if n in (17, 18):
            return 'Middelstrømsfilter; forskellige værdier kompenserer nominelle pin-biasstrømme.'
        if n in (20, 21, 22):
            return 'Fast feedbackdeler: 820 kΩ / 10 kΩ giver 99,6 V nominelt med 1,2 V reference.'
        if n in (23, 24, 25):
            return 'VINOV-deler, nominelt 129 V med bred comparator-tolerance; ingen præcis uafhængig OVP.'
    if ref.startswith('C'):
        if n <= 4:
            return '47 µF / 200 V bulk-kondensator; serie, ESR, ripple, temperatur og mekanisk footprint mangler endeligt valg.'
        if 5 <= n <= 8:
            return 'Lokal 1 µF / 250 V X7R-afkobling fra ADI-reference; DC-bias reducerer effektiv kapacitet.'
        if n in (13, 14):
            return 'Bootstrap-kondensator mellem BOOST og respektiv switch-node.'
    raise ValueError(f'Missing Danish function for {board}:{ref}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--metadata-only', action='store_true',
                        help='refresh combined BOM/provenance before rendering the manual')
    args = parser.parse_args()
    sources = [('Målekort', 'measurement.csv'), ('Effektfase', 'power-phase.csv'),
               ('Netdel', 'frontend.csv')]
    if (ROOT / 'bom' / 'control.csv').exists():
        sources.append(('Styrekort', 'control.csv'))
    target = ROOT / 'bom' / 'current-draft.csv'
    rows = 0
    with target.open('w', encoding='utf-8-sig', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['Kort', 'Reference', 'Værdi', 'Antal', 'Footprint',
                         'Funktion', 'Kilde', 'Status'])
        for board, filename in sources:
            with (ROOT / 'bom' / filename).open(newline='', encoding='utf-8') as source:
                for row in csv.DictReader(source):
                    writer.writerow([board, row['Reference'], row['Value'],
                                     row['Quantity'], row['Footprint'],
                                     function(board, row['Reference'], row['Description']),
                                     row.get('Source', 'Se docs/manual.md'),
                                     row['Release_status']])
                    rows += 1
    urls = {
        'LTC3895.pdf': 'https://www.analog.com/media/en/technical-documentation/data-sheets/3895fa.pdf',
        'UCC21520.pdf': 'https://www.ti.com/lit/ds/symlink/ucc21520.pdf',
        'LTC3779.pdf': 'https://www.analog.com/media/en/technical-documentation/data-sheets/ltc3779.pdf',
        'LTC3779_DC2456AF.pdf': 'https://www.analog.com/media/en/technical-documentation/user-guides/DC2456AF.PDF',
        'LTC3779_DC2456A4_schematic.pdf': 'https://www.analog.com/media/en/technical-documentation/user-guides/DC2456A-4-SCH.PDF',
    }
    # Merge independently retrieved manufacturer metadata; retain a precise
    # official URL and hash for each original rather than relying on filenames.
    metadata_files = sorted((ROOT / 'references').glob('*.source.json'))
    metadata_files += [p for p in sorted((ROOT / 'references').glob('*sources.json'))
                       if p.name != 'sources.json']
    for path in metadata_files:
        records = json.loads(path.read_text())
        if isinstance(records, dict):
            records = records.get('sources', [records])
        for record in records:
            filename = record.get('file') or record.get('pdf_file')
            url = record.get('official_url') or record.get('download_url') or record.get('url')
            if filename and url:
                urls[filename] = url
    provenance = []
    for filename, url in urls.items():
        data = (ROOT / 'references' / filename).read_bytes()
        if filename.lower().endswith('.pdf') and not data.startswith(b'%PDF-'):
            raise ValueError(f'{filename} is not a PDF')
        provenance.append({'file': filename, 'official_url': url,
                           'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    (ROOT / 'references' / 'sources.json').write_text(
        json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    if args.metadata_only:
        print(json.dumps({'component_rows': rows, 'sources': len(provenance)}, indent=2))
        raise SystemExit(0)
    required = ['README.md', 'exports/manual_da.pdf', 'docs/final-status.md',
                'bom/current-draft.csv', 'bom/critical-components.csv',
                'bom/phase-balancing-study.csv', 'references/sources.json',
                'exports/verification/project_status.json',
                'exports/verification/inventory.json',
                'exports/power/reproduction_check.json',
                'exports/control/studies/summary.json',
                'design/control/studies/phase_sensor_study.kicad_sch']
    for directory, stem in [('measurement', 'measurement'), ('power', 'power_phase'),
                             ('control', 'control'), ('frontend', 'frontend')]:
        required.extend(f'design/{directory}/{stem}.{ext}' for ext in ['kicad_pro', 'kicad_sch'])
        required.append(f'exports/{directory}/{stem}.pdf')
        if directory != 'frontend':
            required.extend(f'design/{directory}/{stem}.{ext}' for ext in ['kicad_pcb', 'kicad_dru'])
    for name in ['design_budget', 'control_limits', 'power_analysis', 'low_current',
                  'low_current_loop', 'bus_protection', 'phase_balance', 'bus_disconnect_envelope']:
        required.append(f'exports/analysis/{name}.json')
    for relative in required:
        if not (ROOT / relative).is_file():
            raise FileNotFoundError('Required delivery file missing: '+relative)
    if not (ROOT/'exports/manual_da.pdf').read_bytes().startswith(b'%PDF-'):
        raise RuntimeError('Manual is not a PDF')
    status = json.loads((ROOT/'exports/verification/project_status.json').read_text())
    if rows != 206 or status['main_BOM_rows'] != rows:
        raise RuntimeError('Main BOM/status row count mismatch')
    if not status['CAD_main_projects_pass']:
        raise RuntimeError('Current main CAD checks do not pass')
    for project in status['projects']:
        for relative, digest in project['source_sha256'].items():
            if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != digest:
                raise RuntimeError('CAD status is stale for '+relative)
    for relative, digest in status['automation_source_sha256'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest() != digest:
            raise RuntimeError('Automation status is stale for '+relative)
    for calculation in status['calculations']:
        if hashlib.sha256((ROOT/calculation['report']).read_bytes()).hexdigest() != calculation['sha256']:
            raise RuntimeError('Calculation status is stale: '+calculation['report'])
    archive = ROOT / 'exports' / 'psu_design_draft.zip'
    report_path = ROOT / 'exports/verification/delivery_check.json'
    files = 0
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(ROOT.rglob('*')):
            relative = path.relative_to(ROOT)
            if not path.is_file() or any(part in ('.git', '.runtime', '__pycache__')
                                         for part in relative.parts):
                continue
            if path.suffix in ('.zip', '.kicad_prl', '.lck'):
                continue
            if path == report_path:
                continue
            bundle.write(path, Path(ROOT.name) / relative)
            files += 1
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('ZIP integrity check failed')
        checked = {}
        for relative in required:
            archived = bundle.read(str(Path(ROOT.name)/relative))
            digest = hashlib.sha256(archived).hexdigest()
            if digest != hashlib.sha256((ROOT/relative).read_bytes()).hexdigest():
                raise RuntimeError('Archive payload differs: '+relative)
            checked[relative] = digest
    report = {'time_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS', 'scope': 'Required source files, fresh CAD hashes, BOM count, PDF signature and ZIP integrity; no hardware qualification',
              'archive': str(archive.relative_to(ROOT)), 'files_including_this_report': files+1,
              'main_BOM_rows': rows, 'critical_matrix_rows': status['critical_component_matrix']['rows'],
              'phase_study_BOM_rows': status['phase_study_BOM_rows'],
              'required_payload_sha256': checked,
              'ZIP_CRC_check': 'PASS', 'physical_tests_performed': False,
              'fabrication_released': False}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    with zipfile.ZipFile(archive, 'a', compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.write(report_path, Path(ROOT.name)/report_path.relative_to(ROOT))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('Final ZIP integrity check failed after adding report')
    print(json.dumps({'archive': str(archive), 'files': files+1,
                      'component_rows': rows, 'bytes': archive.stat().st_size}, indent=2))
