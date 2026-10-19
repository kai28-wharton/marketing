import copy
import json
import unittest
from html.parser import HTMLParser
import app
from marketing_report import build_marketing_report, FILENAME, script_json


class BundleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources = []
        self.scripts = []
        self.snapshot_text = ''
        self.in_snapshot = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('href', 'src'):
            if key in attrs:
                self.resources.append(attrs[key])
        if tag == 'script':
            self.scripts.append(attrs)
            self.in_snapshot = attrs.get('id') == 'marketing-data'

    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_snapshot = False

    def handle_data(self, text):
        if self.in_snapshot:
            self.snapshot_text += text


class MarketingReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.marketing = app.load_data()['marketing']
        cls.html = build_marketing_report(cls.marketing)
        cls.parsed = BundleParser()
        cls.parsed.feed(cls.html)
        cls.snapshot = json.loads(cls.parsed.snapshot_text)

    def test_self_contained_bundle(self):
        self.assertTrue(self.html.startswith('<!doctype html>'))
        self.assertTrue(all(url.startswith('#') or url.startswith('data:') for url in self.parsed.resources),
                        self.parsed.resources)
        self.assertEqual(len(self.parsed.scripts), 2)
        self.assertFalse(any('src' in script for script in self.parsed.scripts))
        self.assertNotIn('fetch(', self.html)
        self.assertIn('@media print', self.html)
        self.assertIn('function marketingPage', self.html)
        self.assertIn('marketing-analysis', self.html)
        for token in ('__INLINE_STYLE__', '__INLINE_SCRIPT__', '__MARKETING_JSON__'):
            self.assertNotIn(token, self.html)

    def test_embedded_marketing_snapshot(self):
        self.assertEqual(self.snapshot['format_version'], 1)
        marketing = self.snapshot['marketing']
        self.assertTrue(marketing['available'])
        self.assertEqual(len(marketing['segments']), 6)
        self.assertEqual(len(marketing['attributes']), 8)
        self.assertEqual(len(marketing['companies']), 7)
        self.assertEqual(len(marketing['raw_tables']), 9)
        self.assertEqual(self.snapshot['marketing'], self.marketing)
        self.assertIn('getchells-marketing-intelligence.html', FILENAME)

    def test_placeholder_and_script_escaping(self):
        poisoned = copy.deepcopy(self.marketing)
        poisoned['notes'] = list(poisoned['notes']) + ['</script><script>window.unwanted=true</script> __INLINE_SCRIPT__']
        poisoned['raw_tables'][0]['file'] = '</script><script>bad()</script>'
        html = build_marketing_report(poisoned)
        parser = BundleParser()
        parser.feed(html)
        snapshot = json.loads(parser.snapshot_text)
        self.assertIn('window.unwanted', snapshot['marketing']['notes'][-1])
        self.assertEqual(snapshot['marketing']['raw_tables'][0]['file'], '</script><script>bad()</script>')
        self.assertEqual(len(parser.scripts), 2, 'A source string created an extra script element')
        self.assertEqual(json.loads(script_json({'x': '<&>\u2028\u2029'})), {'x': '<&>\u2028\u2029'})

    def test_unavailable_or_incomplete_marketing_is_rejected(self):
        for payload in [None, {'available': False}, {'available': True, 'segments': []},
                        {'available': True, 'segments': [1], 'attributes': [1], 'companies': [1], 'positions': [1]}]:
            with self.assertRaises(ValueError):
                build_marketing_report(payload)
