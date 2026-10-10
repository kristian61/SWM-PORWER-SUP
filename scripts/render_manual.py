#!/usr/bin/python3
"""Render the Danish draft manual using locally installed ReportLab."""
from pathlib import Path
import html
import re
import textwrap
import csv
import json
import subprocess
import datetime
from zoneinfo import ZoneInfo
import os

cache_directory = Path('/workspace/scratch/kicad-psu-runtime/cache')
cache_directory.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('XDG_CACHE_HOME', str(cache_directory))

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, Image,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
font_dir = Path('/usr/share/fonts/truetype/dejavu')
for name, filename in [('DejaVu', 'DejaVuSans.ttf'),
                       ('DejaVu-Bold', 'DejaVuSans-Bold.ttf'),
                       ('DejaVu-Mono', 'DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
pdfmetrics.registerFontFamily('DejaVu', normal='DejaVu', bold='DejaVu-Bold')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle('BodyDA', fontName='DejaVu', fontSize=9,
                         leading=13, spaceAfter=6))
styles.add(ParagraphStyle('CellDA', fontName='DejaVu', fontSize=7.3,
                         leading=10, spaceAfter=0))
styles.add(ParagraphStyle('CodeDA', fontName='DejaVu-Mono', fontSize=7,
                         leading=10, spaceAfter=8))
for name, size, leading in [('Title', 20, 26), ('Heading1', 15, 21),
                             ('Heading2', 12, 17), ('Heading3', 10, 14)]:
    styles[name].fontName = 'DejaVu-Bold'
    styles[name].fontSize = size
    styles[name].leading = leading


def inline(value):
    value = html.escape(value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'`([^`]+)`', r'<font name="DejaVu-Mono">\1</font>', value)
    return value


def parse_markdown(path):
    lines = path.read_text(encoding='utf-8').splitlines()
    result = []
    cursor = 0
    while cursor < len(lines):
        line = lines[cursor]
        if not line.strip():
            cursor += 1
            continue
        if line.startswith('```mermaid'):
            # The standalone PNG illustrates this block in the printable
            # manual; retain editable Mermaid source in Markdown only.
            cursor += 1
            while cursor < len(lines) and not lines[cursor].startswith('```'):
                cursor += 1
            cursor += 1
            continue
        figure = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', line)
        if figure:
            image_path = (path.parent / figure[2]).resolve()
            image_path.relative_to(ROOT)
            illustration = Image(str(image_path))
            illustration._restrictSize(174*mm, 215*mm)
            result.extend([illustration, Paragraph(inline(figure[1]), styles['CellDA']), Spacer(1, 8)])
            cursor += 1
            continue
        if line.startswith('```'):
            cursor += 1
            code = []
            while cursor < len(lines) and not lines[cursor].startswith('```'):
                code.extend(textwrap.wrap(lines[cursor], 98,
                                          replace_whitespace=False) or [''])
                cursor += 1
            result.append(Preformatted('\n'.join(code), styles['CodeDA']))
            cursor += 1
            continue
        if line.startswith('|'):
            rows = []
            while cursor < len(lines) and lines[cursor].startswith('|'):
                cells = [cell.strip() for cell in lines[cursor].strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', cell) for cell in cells):
                    rows.append([Paragraph(inline(cell), styles['CellDA'])
                                 for cell in cells])
                cursor += 1
            ncols = len(rows[0])
            fractions = {2: [0.30, 0.70], 3: [0.23, 0.25, 0.52],
                         4: [0.20, 0.20, 0.30, 0.30]}.get(ncols)
            widths = [174*mm*f for f in fractions] if fractions else [174*mm/ncols]*ncols
            table = Table(rows, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e7eef7')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#a5b0bf')),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ]))
            result.extend([table, Spacer(1, 7)])
            continue
        heading = re.match(r'^(#{1,3})\s+(.+)', line)
        if heading:
            result.append(Paragraph(inline(heading[2]),
                                    styles[f'Heading{len(heading[1])}']))
            cursor += 1
            continue
        if re.match(r'^(?:- |\d+\. )', line):
            result.append(Paragraph(inline(line), styles['BodyDA']))
            cursor += 1
            continue
        paragraph = [line]
        cursor += 1
        while cursor < len(lines) and lines[cursor].strip() and not re.match(
            r'^(?:#|\||```|- |\d+\. )', lines[cursor]
        ):
            paragraph.append(lines[cursor])
            cursor += 1
        result.append(Paragraph(inline(' '.join(paragraph)), styles['BodyDA']))
    return result


def footer(canvas, document):
    canvas.saveState()
    canvas.setFont('DejaVu', 7)
    canvas.setFillColor(colors.HexColor('#475569'))
    canvas.drawString(18*mm, 12*mm,
                      'Konstruktionsudkast – komplet 4 kW-strømforsyning er ikke frigivet')
    canvas.drawRightString(192*mm, 12*mm, f'Side {document.page}')
    canvas.restoreState()


class ManualDocument(SimpleDocTemplate):
    def beforeDocument(self):
        self.heading_count = 0

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Heading1':
            title = flowable.getPlainText()
            if title == 'Indhold':
                return
            self.heading_count += 1
            bookmark = 'chapter_'+str(self.heading_count)
            self.canv.bookmarkPage(bookmark)
            self.canv.addOutlineEntry(title, bookmark, 0, False)
            self.notify('TOCEntry', (0, title, self.page, bookmark))


if __name__ == '__main__':
    destination = ROOT / 'exports' / 'manual_da.pdf'
    text_destination = ROOT / 'exports' / 'manual_da_text.pdf'
    destination.parent.mkdir(exist_ok=True)
    document = ManualDocument(str(text_destination), pagesize=A4,
                                 rightMargin=18*mm, leftMargin=18*mm,
                                 topMargin=18*mm, bottomMargin=21*mm,
                                 title='100 V / 40 A – konstruktionsudkast og målekort',
                                 author='SWM-PORWER-SUP')
    content = [Paragraph('100 V / 40 A laboratorieforsyning', styles['Title']),
               Paragraph('Dansk udviklingsmanual – uafsluttet konstruktionsudkast',
                         styles['Heading2']),
               Paragraph('Projektstatus: '+datetime.datetime.now(ZoneInfo('Europe/Copenhagen')).strftime('%d.%m.%Y'),
                         styles['BodyDA']),
               Paragraph('Indgang: 230 V AC / 32 A. Målet er en galvanisk isoleret '
                         'og flydende udgang med justerbar spænding og strømgrænse.',
                         styles['BodyDA']),
               Paragraph('<b>Denne revision indeholder måle-/testkort, '
                         'chassisdiagram for to isolerede netmoduler og et '
                         'fuldt routet LTC3779-enkeltfaseudkast omkring 100 V / 10 A '
                         'samt diagram og routet styrekort for eksperimentel analog CV/CC. '
                         'Den samlede 0–100 V / 40 A-regulering, beskyttelser og '
                         'systemintegration er ikke færdige. CAD-routingen er kontrolleret; ingen hardwarevalidering '
                         'eller frigivelse til fremstilling er udført.</b>',
                         styles['BodyDA'])]
    contents = TableOfContents()
    contents.levelStyles = [ParagraphStyle('ContentsDA', fontName='DejaVu',
                                           fontSize=9, leading=15, spaceBefore=5)]
    content.extend([PageBreak(), Paragraph('Indhold', styles['Heading1']), contents])
    sources = ['krav.md', 'frontend-selection.md', 'power-phase.md', 'manual.md',
               'architecture-research.md', 'multiphase-research.md',
               'low-current-output.md',
               'protection-and-test-plan.md']
    if (ROOT / 'docs/control.md').exists():
        sources.insert(3, 'control.md')
    for appendix in ['control-layout.md', 'power-layout.md', 'power-analysis.md',
                     'phase-balancing.md', 'low-current-loop.md',
                     'bus-protection.md', 'bus-disconnect-design.md',
                     'component-qualification.md', 'ac-protection-research.md',
                     'decisions.md', 'final-status.md']:
        if (ROOT / 'docs' / appendix).exists():
            sources.append(appendix)
    if (ROOT / 'docs/validation.md').exists():
        sources.append('validation.md')
    for source in sources:
        content.append(PageBreak())
        content.extend(parse_markdown(ROOT / 'docs' / source))
    inventory = ROOT / 'bom/current-draft.csv'
    if inventory.exists():
        content.extend([PageBreak(), Paragraph('Samlet komponentoversigt', styles['Heading1']),
                        Paragraph('Referencer starter forfra på hvert kort. Tabellen viser '
                                  'de aktuelle diagramdele og eksterne krav, inklusive '
                                  'ufærdige valg. Den komplette CSV indeholder også footprints, '
                                  'kilder og individuelle frigivelsesmarkeringer. Generiske '
                                  'værdier er ikke producentgodkendte varenumre. '
                                  'SHUNT_EXT på målekortet og SHUNT_EXTERNAL ved styrekortet '
                                  'henviser til samme fysiske 1 mΩ udgangsshunt; de er ikke '
                                  'to separate indkøbsdele.', styles['BodyDA'])])
        rows = [[Paragraph(inline(x), styles['CellDA']) for x in
                 ['Kort / reference', 'Værdi / antal', 'Funktion og status']]]
        with inventory.open(encoding='utf-8-sig', newline='') as source:
            for row in csv.DictReader(source):
                rows.append([Paragraph(inline(row['Kort']+' / '+row['Reference']), styles['CellDA']),
                             Paragraph(inline(row['Værdi']+'; antal '+row['Antal']), styles['CellDA']),
                             Paragraph(inline(row['Funktion']+' Status: '+row['Status']), styles['CellDA'])])
        table = Table(rows, colWidths=[31*mm, 51*mm, 92*mm], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                                   ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                                   ('GRID', (0,0), (-1,-1), .25, colors.HexColor('#cbd5e1')),
                                   ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
        content.append(table)
    study_inventory = ROOT / 'bom/phase-balancing-study.csv'
    if study_inventory.exists():
        content.extend([PageBreak(), Paragraph('Supplerende komponentliste: fasestrømstudie', styles['Heading1']),
                        Paragraph('Denne liste vedrører kun det nye énkanals studieskema. '
                                  'Det er ikke integreret i de routede kort og indgår ikke i '
                                  'de 206 poster i hovedlisten. Systemantal og kanalantal '
                                  'skal læses sammen med CSV-filens forklaring; ingen '
                                  'indkøbs- eller hardwarefrigivelse er udført.', styles['BodyDA'])])
        study_rows = [[Paragraph(inline(x), styles['CellDA']) for x in
                       ['Reference', 'Værdi / antal', 'Funktion og status']]]
        with study_inventory.open(encoding='utf-8-sig', newline='') as source:
            for row in csv.DictReader(source):
                study_rows.append([Paragraph(inline(row['Reference']), styles['CellDA']),
                                   Paragraph(inline(row['Value']+'; antal '+row['Quantity']), styles['CellDA']),
                                   Paragraph(inline(row['Description']+' Status: '+row['Release_status']), styles['CellDA'])])
        study_table = Table(study_rows, colWidths=[25*mm, 53*mm, 96*mm], repeatRows=1, hAlign='LEFT')
        study_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                                         ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                                         ('GRID', (0,0), (-1,-1), .25, colors.HexColor('#cbd5e1')),
                                         ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
        content.append(study_table)
    provenance = ROOT / 'references/sources.json'
    if provenance.exists():
        content.extend([PageBreak(), Paragraph('Originale datablade og referencekredsløb', styles['Heading1']),
                        Paragraph('PDF-originalerne ligger i references/ i ZIP-pakken. '
                                  'Tabellen angiver deres officielle kilde og et kort hash-id; '
                                  'references/sources.json indeholder den fulde SHA-256 og filstørrelse. '
                                  'At et datablad findes er ikke en kvalifikation af hele konstruktionen. '
                                  'Uafklarede komponenter er fortsat markeret i BOM og kontrolstatus.', styles['BodyDA'])])
        rows = [[Paragraph(inline(x), styles['CellDA']) for x in
                 ['Lokal original', 'Officiel kilde / SHA-256-id']]]
        for source in json.loads(provenance.read_text()):
            rows.append([Paragraph(inline(source['file']), styles['CellDA']),
                         Paragraph(inline(source['official_url'])+'<br/>'+inline(source['sha256'][:16]), styles['CellDA'])])
        source_table = Table(rows, colWidths=[58*mm, 116*mm], repeatRows=1, hAlign='LEFT')
        source_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'),
                                          ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e2e8f0')),
                                          ('GRID', (0,0), (-1,-1), .25, colors.HexColor('#cbd5e1')),
                                          ('TOPPADDING', (0,0), (-1,-1), 5),
                                          ('BOTTOMPADDING', (0,0), (-1,-1), 5)]))
        content.append(source_table)
    schematics = [(name, ROOT/'exports'/directory/(stem+'.pdf')) for name, directory, stem in
                  [('Målekort', 'measurement', 'measurement'), ('Effektfase', 'power', 'power_phase'),
                   ('Netdelens chassisdiagram', 'frontend', 'frontend'), ('Styrekort', 'control', 'control')]]
    schematics = [(name, path) for name, path in schematics if path.exists()]
    phase_study = ROOT / 'exports/control/studies/phase_sensor_study.pdf'
    if phase_study.exists():
        schematics.append(('Fasestrømstudie – ikke integreret, ingen PCB', phase_study))
    content.extend([PageBreak(), Paragraph('Native KiCad-diagrammer', styles['Heading1']),
                    Paragraph('De følgende appendikssider er de aktuelle KiCad PDF-eksporter '
                              'i originalformat. Deres kontrolstatus står tidligere i manualen. '
                              'Læs diagrammernes netnavne sammen med stik- og testpunkttabellerne.',
                              styles['BodyDA'])])
    for name, path in schematics:
        content.append(Paragraph(inline(name+': '+str(path.relative_to(ROOT))), styles['BodyDA']))
    document.multiBuild(content, onFirstPage=footer, onLaterPages=footer)
    # Ghostscript preserves vector schematics and handles KiCad's recursive
    # annotation dictionaries without pdfunite's repeated dictionary warnings.
    info_path = Path('/workspace/scratch/kicad-psu-runtime/manual_metadata.ps')
    info_path.parent.mkdir(parents=True, exist_ok=True)
    title_hex = ('\ufeff100 V / 40 A – dansk konstruktionsudkast').encode('utf-16-be').hex()
    info_path.write_text('[ /Title <'+title_hex+'> /Author (SWM-PORWER-SUP) /DOCINFO pdfmark\n')
    result = subprocess.run(['gs', '-q', '-dBATCH', '-dNOPAUSE', '-dSAFER',
                             '-dAutoRotatePages=/None', '-sDEVICE=pdfwrite',
                             '-dCompatibilityLevel=1.7', '-sOutputFile='+str(destination),
                             str(text_destination), *[str(path) for _, path in schematics],
                             str(info_path)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('PDF merge failed: '+result.stderr[-1500:])
    if result.stderr.strip():
        print('PDF merge diagnostic: '+result.stderr[-1000:])
    print(destination)
