from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET
import json, re, shutil
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent
XLSX = max(ROOT.glob('*.xlsx'), key=lambda path: path.stat().st_mtime)
OUT = ROOT

NS = {
    'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
    'rel': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'xdr': 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
}

COLS = {
    'A': 'id',
    'D': 'fecha',
    'F': 'hito',
    'H': 'texto',
    'J': 'tematica',
    'L': 'porcentaje',
    'N': 'palabras'
}

SHEET_CONFIG = [
    {
        'name': 'Registro pandemia',
        'slug': 'pandemia',
        'sheet_xml': 'xl/worksheets/sheet1.xml',
        'drawing_xml': 'xl/drawings/drawing1.xml',
        'start_row': 4,
    },
    {
        'name': 'Registro estallido social',
        'slug': 'estallido',
        'sheet_xml': 'xl/worksheets/sheet2.xml',
        'drawing_xml': 'xl/drawings/drawing2.xml',
        'start_row': 4,
    },
]

def col_letters(cell_ref):
    return ''.join(re.findall(r'[A-Z]+', cell_ref))

def row_number(cell_ref):
    return int(''.join(re.findall(r'\d+', cell_ref)))

def excel_date(serial):
    try:
        value = float(serial)
    except (TypeError, ValueError):
        return serial or ''
    # Excel 1900 date system. Good enough for these dates.
    dt = datetime(1899, 12, 30) + timedelta(days=value)
    return dt.strftime('%Y-%m-%d')

def safe_slug(value):
    value = (value or '').lower().strip()
    value = value.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u').replace('ñ','n')
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return value or 'item'

def read_shared_strings(z):
    try:
        xml = z.read('xl/sharedStrings.xml')
    except KeyError:
        return []
    root = ET.fromstring(xml)
    strings = []
    for si in root.findall('main:si', NS):
        parts = []
        for t in si.findall('.//main:t', NS):
            parts.append(t.text or '')
        strings.append(''.join(parts))
    return strings

def cell_value(cell, shared):
    t = cell.attrib.get('t')
    v = cell.find('main:v', NS)
    if v is None:
        return ''
    raw = v.text or ''
    if t == 's':
        return shared[int(raw)] if raw.isdigit() and int(raw) < len(shared) else raw
    return raw

def read_sheet_rows(z, sheet_xml, shared):
    root = ET.fromstring(z.read(sheet_xml))
    rows = {}
    for row in root.findall('.//main:row', NS):
        r = int(row.attrib['r'])
        rows[r] = {}
        for c in row.findall('main:c', NS):
            ref = c.attrib.get('r', '')
            col = col_letters(ref)
            rows[r][col] = cell_value(c, shared)
    return rows

def drawing_image_map(z, drawing_xml):
    rels_path = f"xl/drawings/_rels/{Path(drawing_xml).name}.rels"
    rels_root = ET.fromstring(z.read(rels_path))
    rels = {}
    for rel in rels_root:
        rid = rel.attrib['Id']
        target = rel.attrib['Target']
        rels[rid] = str((Path(drawing_xml).parent / target).resolve()).replace('/xl/drawings/../', '/xl/')
        # Normalize manually because Path.resolve() points to local root
        rels[rid] = 'xl/media/' + Path(target).name

    root = ET.fromstring(z.read(drawing_xml))
    image_by_row = {}
    for anchor in list(root):
        frm = anchor.find('xdr:from', NS)
        pic = anchor.find('xdr:pic', NS)
        if frm is None or pic is None:
            continue
        row = int(frm.find('xdr:row', NS).text) + 1
        blip = pic.find('.//a:blip', NS)
        if blip is None:
            continue
        rid = blip.attrib.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
        if rid in rels:
            image_by_row[row] = rels[rid]
    return image_by_row

def build():
    (OUT / 'assets' / 'images').mkdir(parents=True, exist_ok=True)
    (OUT / 'data').mkdir(parents=True, exist_ok=True)

    items = []
    with ZipFile(XLSX) as z:
        shared = read_shared_strings(z)
        for config in SHEET_CONFIG:
            rows = read_sheet_rows(z, config['sheet_xml'], shared)
            images = drawing_image_map(z, config['drawing_xml'])
            for r in sorted(rows.keys()):
                if r < config['start_row']:
                    continue
                row = rows.get(r, {})
                texto = row.get('H', '').strip()
                palabras = row.get('N', '').strip()
                image_src = images.get(r)
                if not texto and not palabras and not image_src:
                    continue

                image_path = ''
                if image_src:
                    ext = Path(image_src).suffix or '.jpg'
                    filename = f"{config['slug']}-{r:03d}{ext}"
                    dst_file = OUT / 'assets' / 'images' / filename
                    dst_file.write_bytes(z.read(image_src))
                    image_path = f"assets/images/{filename}"

                raw_fecha = row.get('D', '')
                fecha = excel_date(raw_fecha) if raw_fecha else ''
                tematica = row.get('J', '').strip()
                item_id = f"{config['slug']}-{r:03d}"

                items.append({
                    'id': item_id,
                    'hito': row.get('F', '').strip() or config['slug'],
                    'origen': config['name'],
                    'fecha': fecha,
                    'texto': texto,
                    'tematica': tematica,
                    'porcentaje': row.get('L', '').strip(),
                    'palabras': palabras,
                    'image': image_path,
                    'sheetRow': r,
                    'tokens': palabras.split(),
                    'categorySlug': safe_slug(tematica),
                })

    payload = {
        'title': 'Réplica temporal',
        'source': XLSX.name,
        'generatedAt': datetime.now().isoformat(timespec='seconds'),
        'total': len(items),
        'items': items,
    }
    (OUT / 'data' / 'data.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    # Also keep a copy of the Excel in root as archival source.
    archive_copy = OUT / XLSX.name
    if XLSX.resolve() != archive_copy.resolve():
        shutil.copy2(XLSX, archive_copy)

    return payload

if __name__ == '__main__':
    data = build()
    print(f"Generated {data['total']} records in {OUT}")
