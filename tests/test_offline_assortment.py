import json
import unittest
from html.parser import HTMLParser
import app
from offline_assortment import build_offline_lab,script_json


class BundleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources=[]
        self.scripts=[]
        self.snapshot_text=''
        self.in_snapshot=False

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        for key in ('href','src'):
            if key in attrs:self.resources.append(attrs[key])
        if tag=='script':
            self.scripts.append(attrs)
            self.in_snapshot=attrs.get('id')=='lab-data'

    def handle_endtag(self,tag):
        if tag=='script':self.in_snapshot=False

    def handle_data(self,text):
        if self.in_snapshot:self.snapshot_text+=text


class OfflineAssortmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=app.load_data()
        cls.html=build_offline_lab(None,cls.data,app.validate,app.evaluate)
        cls.parsed=BundleParser();cls.parsed.feed(cls.html)
        cls.snapshot=json.loads(cls.parsed.snapshot_text)

    def test_self_contained_bundle(self):
        self.assertTrue(self.html.startswith('<!doctype html>'))
        self.assertTrue(all(url.startswith('#') for url in self.parsed.resources))
        self.assertEqual(len(self.parsed.scripts),2)
        self.assertFalse(any('src' in script for script in self.parsed.scripts))
        self.assertIn('function analyze(changes)',self.html)
        self.assertNotIn('fetch(',self.html)
        self.assertNotIn('__SNAPSHOT_JSON__',self.html)
        self.assertNotIn('__INLINE_SCRIPT__',self.html)
        self.assertIn('@media print',self.html)

    def test_embedded_team_plan_and_verification(self):
        self.assertEqual(self.snapshot['baseline']['online'],6_500_000)
        self.assertEqual(self.snapshot['baseline']['low_breadth'],78)
        self.assertEqual(self.snapshot['initial_values']['high_depth'],10)
        expected=app.evaluate(self.snapshot['baseline'])
        self.assertEqual(self.snapshot['verification']['baseline_scores'],expected['scores'])
        self.assertEqual(self.snapshot['verification']['baseline_net_income'],expected['net_income'])
        self.assertIn('decision_making_team11_round1.xlsx',self.snapshot['source'])
        self.assertIn('readiness',self.snapshot)
        self.assertEqual(len(self.snapshot['readiness']['requirements']),8)

    def test_custom_snapshot_and_input_validation(self):
        p=dict(app.BASE,online=3_000_000)
        payload={'baseline':p,'changes':{'low_breadth':70,'low_depth':35,'high_breadth':45,'high_depth':55},'assumptions':{'score_response':.8}}
        parser=BundleParser();parser.feed(build_offline_lab(payload,self.data,app.validate,app.evaluate))
        snapshot=json.loads(parser.snapshot_text)
        self.assertEqual(snapshot['baseline']['online'],3_000_000)
        self.assertEqual(snapshot['initial_values']['low_breadth'],70)
        self.assertEqual(snapshot['assumptions']['score_response'],.8)
        with self.assertRaises(ValueError):
            build_offline_lab({'baseline':p,'changes':{'online':5e6}},self.data,app.validate,app.evaluate)

    def test_snapshot_cannot_break_out_of_json_script(self):
        source='</script><script>window.unwanted=true</script> __INLINE_SCRIPT__'
        payload={'baseline':app.BASE,'changes':{k:50 for k in ('low_breadth','low_depth','high_breadth','high_depth')},'source':source}
        html=build_offline_lab(payload,self.data,app.validate,app.evaluate)
        parser=BundleParser();parser.feed(html)
        self.assertEqual(len(parser.scripts),2)
        self.assertEqual(json.loads(parser.snapshot_text)['source'],source)
        self.assertNotIn(source,html)
        self.assertEqual(json.loads(script_json({'source':'<&>\u2028\u2029'})),{'source':'<&>\u2028\u2029'})
