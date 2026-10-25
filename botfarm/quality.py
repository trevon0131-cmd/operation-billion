"""Lightweight offline artifact quality gates. Never claims a market sale."""
import csv
import io
import json
import struct
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from .workshop import atomic_text

PRODUCT_FILES = {'product.svg', 'product.html', 'product.csv', 'product.md', 'sticker_transparent.png'}


def inspect(path: Path):
    path = Path(path)
    faults = []
    found = sorted(p for p in path.iterdir() if p.is_file() and p.name in PRODUCT_FILES) if path.is_dir() else []
    if not found:
        faults.append('No original product file generated')
    for file in found:
        if file.stat().st_size < 100:
            faults.append(f'{file.name} is unusually small')
            continue
        try:
            if file.suffix == '.svg':
                root = ET.fromstring(file.read_text(encoding='utf-8'))
                if not root.tag.endswith('svg'): faults.append('Malformed SVG root')
            elif file.suffix == '.png':
                head = file.read_bytes()[:24]
                if head[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('!II', head[16:24]) != (640, 640):
                    faults.append('Unexpected PNG signature or dimensions')
            elif file.suffix == '.html':
                markup = file.read_text(encoding='utf-8').lower()
                if '<!doctype html>' not in markup or '</html>' not in markup: faults.append('Incomplete HTML')
            elif file.suffix == '.csv':
                rows = list(csv.reader(io.StringIO(file.read_text(encoding='utf-8'))))
                if len(rows) < 3: faults.append('CSV template does not have meaningful rows')
        except (ValueError, UnicodeError, OSError, ET.ParseError, struct.error, csv.Error):
            faults.append(f'{file.name} failed format validation')
    for needed in ['metadata.json', 'listing_DRAFT.md']:
        if not (path/needed).is_file(): faults.append(f'Missing {needed}')
    if (path/'metadata.json').is_file():
        try:
            meta=json.loads((path/'metadata.json').read_text(encoding='utf-8'))
            if meta.get('publication_status') != 'DRAFT_ONLY' or meta.get('revenue_usd') is not None:
                faults.append('Unverified publication or income claim in metadata')
        except (ValueError,UnicodeError): faults.append('Malformed metadata')
    return {'passed':not faults, 'issues':faults, 'checked_files':[x.name for x in found]}


def prepare_sell_kit(path: Path, channel: str):
    """Generates files for a *later* legitimate storefront; never posts online."""
    report = inspect(path)
    if not report['passed']:
        raise ValueError('Product QC failure: '+', '.join(report['issues']))
    meta=json.loads((path/'metadata.json').read_text(encoding='utf-8'))
    products=[path/name for name in report['checked_files']]
    target=path/'PRODUCT_PACKAGE.zip'
    # Atomic replacement stops half-written ZIPs being mistaken for finished items.
    pending=path/'PRODUCT_PACKAGE.zip.tmp'
    try:
        with ZipFile(pending,'w',compression=ZIP_DEFLATED) as archive:
            for p in products: archive.write(p,arcname=p.name)
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)
    instructions=(
        '# Sales preparation checklist — NOT LISTED\n\n'
        f'Proposed channel: {channel}. This is an idea, not an established connected store.\n\n'
        '1. Review the actual product files and ensure they are useful, complete, original and accurately described.\n'
        '2. Open your OWN eligible marketplace account; verify identity, payments, taxes and seller eligibility.\n'
        '3. Review platform fees, terms, banned items and rules governing AI-made content.\n'
        '4. Upload PRODUCT_PACKAGE.zip as a digital download only if that platform accepts ZIPs; copy the listing draft after checking it.\n'
        '5. Preview and place a test order using the marketplace’s supported testing method before selling.\n'
        '6. Publish using the platform interface only after you approve; record actual performance thereafter.\n\n'
        'Nothing here registers a business, creates a seller account, posts ads, accepts payment, ships products, or generates buyers.\n'
    )
    atomic_text(path/'SELLING_CHECKLIST.md',instructions)
    atomic_text(path/'QUALITY_REPORT.json',json.dumps(report,indent=2))
    return {'zip':str(target),'quality':report, 'selling_checklist':str(path/'SELLING_CHECKLIST.md')}
