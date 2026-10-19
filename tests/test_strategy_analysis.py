import copy
import unittest

from round_review import dataset
from strategy_analysis import build_strategy, SPENDING


class StrategyAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=dataset(1);cls.strategy=cls.data['strategy']

    def test_team_policy_and_round_horizon_are_explicit(self):
        s=self.strategy;p=s['policy']
        self.assertEqual((s['decision_round'],s['outcome_round']),(1,2))
        self.assertEqual((p['primary'],p['secondary']),('EXPERIENCE','LOW PRICE'))
        self.assertEqual(p['experience_min'],6)
        self.assertEqual(p['low_price_min'],4.7)
        self.assertAlmostEqual(p['brand_reference_floor'],3.5)
        self.assertEqual(p['experience_peer_reference'],6.4)
        self.assertFalse(p['frictionless_parity_required_round2'])
        self.assertEqual(len(s['objectives']),4)
        self.assertIn('does not mean #1',p['meaning'])
        self.assertEqual(p['primary_segment'],'SEGMENT 6')
        self.assertIn('Team-selected',self.data['simulation']['strategy'])

    def test_all_segments_have_reported_evidence_and_nonexclusive_roles(self):
        rows={s['id']:s for s in self.strategy['segments']}
        self.assertEqual(len(rows),6)
        self.assertEqual(rows['SEGMENT 6']['market_consumers'],2_724_297)
        self.assertEqual(rows['SEGMENT 6']['revenue'],87_653_065)
        self.assertEqual(rows['SEGMENT 6']['raw_preferences']['DEPTH'],.03)
        self.assertAlmostEqual(rows['SEGMENT 6']['preference_sum'],1.33)
        self.assertIn('Protect',rows['SEGMENT 5']['role'])
        self.assertIn('Defend',rows['SEGMENT 2']['role'])
        self.assertTrue(all(s['clv'] is None for s in rows.values()))
        self.assertAlmostEqual(sum(s['revenue_share'] for s in rows.values()),1)

    def test_each_of_sixteen_inputs_has_action_provenance_and_gate(self):
        rows=self.strategy['recommendations']
        self.assertEqual(len(rows),16)
        self.assertEqual({r['key'] for r in rows},set(self.data['team']['decisions']))
        for r in rows:
            self.assertEqual(r['current'],self.data['team']['decisions'][r['key']])
            self.assertEqual(r['cell'],self.data['team']['cells'][r['key']])
            self.assertEqual(r['proposed']-r['current'],r['change'])
            self.assertTrue(all(r[k] for k in ('action','why','check','citation','pathway')))
        self.assertEqual(self.strategy['draft']['coverage'],200)
        self.assertEqual(self.strategy['draft']['low_markup'],50)
        self.assertEqual(self.strategy['draft']['high_markup'],52)

    def test_confirmed_budget_reconciles_without_claiming_cash_approval(self):
        f=self.strategy['funding'];draft=self.strategy['draft']
        self.assertEqual(f['spend'],sum(draft[k] for k in SPENDING))
        self.assertEqual(f['spend'],71_422_000)
        self.assertEqual(f['change'],1_608_000)
        self.assertEqual(draft['experience'],14_000_000)
        self.assertEqual(draft['vendor'],27_608_000)
        self.assertEqual(draft['service'],15_000_000)
        self.assertEqual(draft['analytics'],8_314_000)
        self.assertEqual(draft['online'],6_500_000)
        self.assertEqual(draft['low_depth'],25)
        self.assertEqual(draft['high_depth'],10)
        self.assertAlmostEqual(f['revenue_arm'],67_469_674.72)
        self.assertAlmostEqual(f['above_revenue_arm'],3_952_325.28)
        self.assertEqual(f['approved_budget'],71_422_000)
        self.assertEqual(f['headroom'],0)
        self.assertIsNone(f['incremental_cash'])
        self.assertIn('not submission-ready',self.strategy['status'])
        self.assertTrue(any('budget compliance is not cash approval' in g for g in self.strategy['gates']))

    def test_price_test_arithmetic_is_not_an_elasticity_forecast(self):
        self.assertAlmostEqual((1+.48)/(1+.50)-1,-.0133333333333333)
        self.assertAlmostEqual(.50/.48-1,.0416666666666667)
        row=next(r for r in self.strategy['recommendations'] if r['key']=='low_markup')
        self.assertIn('fixed unit cost',row['why'])
        self.assertIn('4.17%',row['why'])

    def test_csv_parity_draft_does_not_force_unnecessary_depth_repair(self):
        from review_model import evaluate
        result=evaluate(self.strategy['draft'],self.data)
        self.assertEqual(result['explicit_spend'],71_422_000)
        self.assertNotIn('brand_depth_response',result['unresolved_model_channels'])
        self.assertEqual(result['score_diagnostics']['BRAND']['full_prediction'],3.7)
        self.assertIn('Hold',next(r['action'] for r in self.strategy['recommendations'] if r['key']=='low_depth'))
        self.assertIn('gap +0.20',self.strategy['objectives'][0]['reference'])
        self.assertIsNone(result['market_value'])

    def test_recommendations_do_not_modify_any_plan_or_model(self):
        before=copy.deepcopy(self.data)
        self.assertEqual(build_strategy(self.data),self.strategy)
        self.assertEqual(self.data,before)


if __name__=='__main__':unittest.main()
