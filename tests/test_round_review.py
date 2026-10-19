import copy
import json
import math
import unittest
from html.parser import HTMLParser
from round_review import dataset, QUADRANTS
from review_model import evaluate, factor_probes, VERSION
from marketing_report import build_current_report


class RoundReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=dataset(1)
        cls.plan=cls.data['team']['decisions']

    def test_current_workbook_is_the_submitted_reference(self):
        self.assertEqual(self.plan['low_breadth'],78)
        self.assertEqual(self.plan['low_depth'],25)
        self.assertEqual(self.plan['high_depth'],10)
        self.assertEqual(self.plan['online'],6_500_000)
        self.assertEqual(self.plan['experience'],13_000_000)
        self.assertEqual(sum(self.plan[k] for k in ('online','service','experience','vendor','analytics')),69_814_000)
        self.assertEqual(len(self.data['team']['sha256']),64)
        self.assertEqual(self.data['team']['cells']['low_breadth'],'Sheet1!B3')

    def test_current_and_prior_statement_values(self):
        now=self.data['rounds']['1'];prior=self.data['rounds']['0']
        self.assertEqual(now['income']['Net Revenue'],481_926_248)
        self.assertEqual(now['income']['Net Income'],8_399_905)
        self.assertEqual(prior['income']['Net Income'],-6_289_333)
        self.assertEqual(now['scorecard']['Market Value'],248_965_528)
        self.assertEqual(now['scores']['BRAND'],3.7)
        self.assertAlmostEqual(now['ratios']['interest_cover'],42_985_651/30_062_720)
        self.assertLess(now['ratios']['quick_ratio'],.25)

    def test_round1_reference_is_exactly_anchored(self):
        before=copy.deepcopy(self.data)
        out=evaluate(self.plan,self.data)
        now=self.data['rounds']['1']
        self.assertEqual(out['version'],VERSION)
        self.assertEqual(out['scores'],now['scores'])
        self.assertEqual(out['revenue'],now['income']['Net Revenue'])
        self.assertEqual(out['net_income'],now['income']['Net Income'])
        self.assertAlmostEqual(out['market_value'],now['scorecard']['Market Value'])
        self.assertEqual(out['revenue_delta'],0)
        self.assertEqual(out['profit_delta'],0)
        self.assertEqual(self.data,before)

    def test_old_prediction_misses_are_preserved(self):
        rows={r['metric']:r for r in self.data['audit']['rows']}
        self.assertAlmostEqual(rows['revenue']['predicted'],376_615_888.839,places=2)
        self.assertAlmostEqual(rows['net_income']['predicted'],-17_698_965.463,places=2)
        self.assertGreater(rows['BRAND']['predicted'],6.4)
        self.assertEqual(rows['BRAND']['observed'],3.7)
        self.assertGreater(rows['BRAND']['error'],2.7)
        for row in rows.values():self.assertAlmostEqual(row['error'],row['predicted']-row['observed'])
        for r in self.data['audit']['alternatives']:
            self.assertIsNone(r['observed_result'])
            for key in ('low_breadth','high_depth','private_quality'):
                self.assertEqual(r['decisions'][key],self.plan[key])

    def test_marketing_scopes_missing_clv_and_fair_value(self):
        m=self.data['marketing']
        self.assertEqual(len(m['segments']),6)
        self.assertEqual(len(m['companies']),7)
        self.assertEqual(len(m['raw_tables']),12)
        self.assertEqual(m['segment_revenue_difference'],-1)
        self.assertFalse(m['segment_clv_available'])
        self.assertTrue(all(s['clv'] is None for s in m['segments']))
        self.assertNotIn('FAIR VALUE',[c['name'] for c in m['companies']])
        self.assertIn('FAIR VALUE',[r['company'] for r in self.data['kahn']])
        self.assertFalse(m['fair_value_available'])
        self.assertEqual(max(m['segments'],key=lambda s:s['revenue'])['id'],'SEGMENT 2')
        self.assertEqual(max(m['segments'],key=lambda s:s['growth'])['id'],'SEGMENT 4')

    def test_definition_ambiguity_not_invented_away(self):
        self.assertTrue(self.data['definitions_available'])
        self.assertIn('Price Markup:',self.data['definitions'])
        self.assertTrue(any('Private Brand' in s for s in self.data['definition_issues']))
        self.assertEqual(self.data['model']['paired_transitions'],1)
        self.assertFalse(self.data['model']['causal_calibration'])

    def test_observed_accounting_is_not_identity_for_investment(self):
        mapping={r['key']:r['ratio'] for r in self.data['accounting']}
        self.assertAlmostEqual(mapping['online'],.4)
        self.assertAlmostEqual(mapping['experience'],.8)
        self.assertGreater(mapping['service'],1)
        self.assertEqual(mapping['vendor'],1)
        self.assertEqual(mapping['analytics'],1)

    def test_all_sixteen_factors_have_both_direction_probes(self):
        probes=factor_probes(self.data)
        self.assertEqual(len(probes),16)
        self.assertEqual({p['key'] for p in probes},set(self.plan))
        for row in probes:
            self.assertIn('provisional',row['definition_status'])
            self.assertTrue(row['affected_quadrants'] or row['increase']['unresolved_model_channels'])
            for direction in ('increase','decrease'):
                self.assertIsNotNone(row[direction])
                self.assertEqual(set(row[direction]['score_changes']),set(QUADRANTS))
                self.assertTrue(all(math.isfinite(v) for v in row[direction]['score_changes'].values()))

    def test_unknown_costs_and_nonpositive_earnings_value(self):
        changed=evaluate(dict(self.plan,high_depth=20),self.data)
        self.assertTrue(changed['unpriced_changes'])
        negative=evaluate(dict(self.plan,online=69_814_000,service=69_814_000),self.data)
        self.assertLess(negative['net_income'],0)
        self.assertIsNone(negative['market_value'])
        self.assertEqual(negative['tax'],0)
        self.assertLess(negative['historical_headroom'],0)

    def test_validation(self):
        for plan in ({},dict(self.plan,online=True),dict(self.plan,online=math.nan),dict(self.plan,high_depth=-1)):
            with self.assertRaises(ValueError):evaluate(plan,self.data)

    def test_probes_respect_explicit_response_assumptions(self):
        for row in factor_probes(self.data,assumptions={'score_response':0}):
            for direction in ('increase','decrease'):
                self.assertTrue(all(v==0 for v in row[direction]['score_changes'].values()))

    def test_snapshot_contains_current_marketing_only_data(self):
        class Parser(HTMLParser):
            def __init__(self):super().__init__();self.inside=False;self.text='';self.resources=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if tag=='script':self.inside=a.get('id')=='review-data'
                if 'src' in a:self.resources.append(a['src'])
                if 'href' in a:self.resources.append(a['href'])
            def handle_endtag(self,tag):
                if tag=='script':self.inside=False
            def handle_data(self,text):
                if self.inside:self.text+=text
        html=build_current_report(self.data);p=Parser();p.feed(html);snap=json.loads(p.text)
        self.assertEqual(snap['rounds']['1']['income']['Net Revenue'],481_926_248)
        self.assertNotIn('decisions',snap['team'])
        self.assertNotIn('probes',snap)
        self.assertEqual(set(snap['strategy']),{'policy','segments','boundary'})
        self.assertEqual(snap['strategy']['policy']['primary_segment'],'SEGMENT 6')
        self.assertEqual(snap['strategy']['policy']['primary'],'EXPERIENCE')
        self.assertNotIn('draft',snap['strategy'])
        self.assertNotIn('recommendations',snap['strategy'])
        self.assertEqual(len(snap['strategy']['segments']),6)
        self.assertFalse(p.resources)
        self.assertIn("connect-src 'none'",html)

    def test_cache_returns_isolated_copies(self):
        d=dataset(1);d['team']['decisions']['online']=0
        self.assertEqual(dataset(1)['team']['decisions']['online'],6_500_000)


if __name__=='__main__':unittest.main()
