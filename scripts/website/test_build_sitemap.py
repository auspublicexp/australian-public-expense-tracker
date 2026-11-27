"""Checks for sitemap mistakes that can hide or misidentify reporting pages."""
import unittest
import xml.etree.ElementTree as ET
from build_sitemap import sitemap_bytes, ORIGIN, NAMESPACE


def report(routes):
    return {'status': 'PASS', 'errors': [], 'warnings': [],
            'pages': {route: {'canonical': ORIGIN + route} for route in routes}}


class SitemapTests(unittest.TestCase):
    def test_preserves_period_queries_and_escapes_xml(self):
        routes = ['/', '/austender/?period=FY2026-27_Q1', '/example.php?period=A&mode=B']
        data = sitemap_bytes(report(routes))
        self.assertIn(b'&amp;', data)
        self.assertEqual({n.text for n in ET.fromstring(data).iter(f'{{{NAMESPACE}}}loc')}, {ORIGIN + r for r in routes})
        self.assertNotIn(b'lastmod', data)

    def test_deduplicates_aliases(self):
        result = report(['/', '/index.php'])
        result['pages']['/index.php']['canonical'] = ORIGIN + '/'
        self.assertEqual(len(ET.fromstring(sitemap_bytes(result))), 1)

    def test_refuses_unchecked_or_external_canonical(self):
        for canonical in [ORIGIN + '/missing.php', 'https://example.com/', ORIGIN + '/#section', '']:
            result = report(['/'])
            result['pages']['/']['canonical'] = canonical
            with self.subTest(canonical=canonical), self.assertRaises(ValueError):
                sitemap_bytes(result)

    def test_refuses_failed_or_warning_report(self):
        for key, value in [('status', 'FAIL'), ('errors', ['missing asset']), ('warnings', ['missing heading'])]:
            result = report(['/'])
            result[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                sitemap_bytes(result)

    def test_refuses_empty_report(self):
        with self.assertRaises(ValueError):
            sitemap_bytes(report([]))


if __name__ == '__main__':
    unittest.main()
