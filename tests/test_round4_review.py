import hashlib
import unittest

from app import ROOT, read_csv
from round_review import COMPANY, dataset
from review_model import evaluate, factor_probes
from review_optimizer import optimize
from marketing_report import build_current_report


class Round4ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = dataset(3)

    def test_latest_submission_is_round3_not_analyst_recommendation(self):
        d = self.data
        self.assertEqual((d['previous_round'],d['current_round'],d['planning_round']),(2,3,4))
        self.assertIn('round_3/decision_making_team11_round3.xlsx',d['team']['source'])
        self.assertEqual(d['team']['sha256'],hashlib.sha256((ROOT/d['team']['source']).read_bytes()).hexdigest())
        self.assertEqual(d['historical_budget'],74_631_166)
        self.assertAlmostEqual(d['team']['decisions']['low_markup'],56)
        self.assertEqual(d['team']['decisions']['high_private'],60)
        self.assertEqual(d['team']['decisions']['private_quality'],8)
        self.assertEqual(d['team']['decisions']['service'],11_350_000)
        self.assertEqual(d['team']['decisions']['coverage'],236)
        self.assertNotIn('round3_decision',d)
        self.assertEqual(d['strategy']['draft'],d['team']['decisions'])
        self.assertTrue(all(f['industry_round']==3 for f in d['factors']))

    def test_current_marketing_and_competitors_are_sourced_from_round3(self):
        d = self.data
        self.assertEqual(d['rounds']['3']['scores'],{'BRAND':4.9,'EXPERIENCE':5.3,'LOW PRICE':4.6,'FRICTIONLESS':2.7})
        objectives={r['quadrant']:r for r in d['strategy']['objectives']}
        self.assertEqual(objectives['BRAND']['rank'],1)
        self.assertAlmostEqual(objectives['FRICTIONLESS']['fair_gap'],-2.4)
        self.assertAlmostEqual(objectives['EXPERIENCE']['leader_gap'],1.4)
        self.assertIn('2.40',objectives['FRICTIONLESS']['target'])
        self.assertIn('Defend',objectives['BRAND']['target'])
        self.assertTrue(all('/round3/' in t['file'] for t in d['marketing']['raw_tables']))
        self.assertEqual(len(d['marketing']['raw_tables']),15)
        self.assertEqual(d['marketing']['company_revenue'],565_528_830)
        self.assertEqual(d['marketing']['company_clv'],1_192_154_605)
        source=read_csv(ROOT/'materials/round3/marketing/marketCLV-round3.csv')[-1]
        self.assertEqual({s['id']:s['clv'] for s in d['marketing']['segments']},{k:float(v) for k,v in source.items() if k!='ROUND'})

    def test_missing_finance_is_not_filled_with_previous_actuals(self):
        d = self.data
        self.assertEqual(d['availability']['financial_round'],2)
        self.assertFalse(d['availability']['finance_current'])
        self.assertEqual(len(d['availability']['missing_finance']),3)
        for key in ('income','balance','scorecard','ratios'):
            self.assertEqual(d['rounds']['3'][key],{})
        self.assertEqual(d['insights']['finance']['source_round'],2)
        self.assertFalse(d['insights']['finance']['current'])
        self.assertEqual(d['accounting'],[])
        self.assertEqual(d['economic_defaults'],{})
        self.assertTrue(all(v is None for v in d['reconciliations'].values()))
        self.assertFalse(any(r['round']==3 for r in d['simulation']['capital_efficiency']))
        for call in (lambda:evaluate(d['team']['decisions'],d),lambda:factor_probes(d),lambda:optimize({'decisions':d['team']['decisions']},d)):
            with self.assertRaisesRegex(ValueError,'financial exports are missing'):
                call()

    def test_round4_budget_is_not_inferred_from_round3(self):
        f = self.data['strategy']['funding']
        self.assertIsNone(f['approved_budget'])
        self.assertIsNone(f['headroom'])
        self.assertEqual(f['previous_budget_round'],3)
        self.assertEqual(f['previous_confirmed_budget'],74_631_166)
        self.assertAlmostEqual(f['revenue_arm'],79_174_036.2)
        self.assertIn('Round 4',f['budget_source'])

    def test_offline_reports_keep_round_and_finance_provenance(self):
        import json
        for page in ('marketing','segmentation'):
            html=build_current_report(self.data,page)
            payload=json.loads(html.split('<script type="application/json" id="review-data">')[1].split('</script>')[0])
            self.assertEqual(payload['planning_round'],4)
            self.assertFalse(payload['availability']['finance_current'])
            self.assertEqual(payload['segment_decision']['finance']['source_round'],2)
            self.assertNotIn('decisions',payload['team'])
            self.assertIn('ROUND 4 PLANNING',html)
