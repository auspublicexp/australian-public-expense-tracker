"""Build the APET sitemap only after rendering and checking the local website."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

from check_release import check, php_command

ORIGIN = 'https://auspublicexp.org'
NAMESPACE = 'http://www.sitemaps.org/schemas/sitemap/0.9'


def sitemap_bytes(report):
    """Use checked canonical pages; never invent dates or query permutations."""
    if report.get('status') != 'PASS' or report.get('errors') or report.get('warnings'):
        raise ValueError('Resolve release-check errors and warnings before building the sitemap.')
    pages = report.get('pages', {})
    visited = {ORIGIN + route for route in pages}
    urls = set()
    for route, page in pages.items():
        canonical = page.get('canonical', '')
        parts = urlsplit(canonical)
        if (parts.scheme != 'https' or parts.netloc != 'auspublicexp.org'
                or parts.fragment or canonical not in visited):
            raise ValueError(f'{route}: canonical URL was not checked as a local page: {canonical!r}')
        urls.add(canonical)
    if not urls or len(urls) > 50000:
        raise ValueError('Expected 1–50,000 canonical pages.')
    ET.register_namespace('', NAMESPACE)
    root = ET.Element(f'{{{NAMESPACE}}}urlset')
    for url in sorted(urls):
        entry = ET.SubElement(root, f'{{{NAMESPACE}}}url')
        ET.SubElement(entry, f'{{{NAMESPACE}}}loc').text = url
    ET.indent(root, space='  ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--web-root', type=Path, default=Path(__file__).resolve().parents[2] / 'website/public_html')
    parser.add_argument('--php', type=Path, default=shutil.which('php'))
    parser.add_argument('--output', type=Path, help='Defaults to WEB_ROOT/sitemap.xml.')
    parser.add_argument('--report', type=Path, required=True, help='Save the accompanying release-check JSON here.')
    args = parser.parse_args()
    if not args.php:
        parser.error('Specify a PHP executable with --php.')
    root = args.web_root.resolve()
    output = args.output or root / 'sitemap.xml'
    report = check(root, php_command(args.php.resolve()))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    try:
        payload = sitemap_bytes(report)
    except ValueError as exc:
        print(f'Sitemap unchanged: {exc}')
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.tmp')
    temporary.write_bytes(payload)
    temporary.replace(output)
    print(f'Wrote {len(ET.fromstring(payload))} verified canonical URLs to {output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
