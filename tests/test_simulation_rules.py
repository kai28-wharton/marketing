import copy
import unittest
from app import ROOT
from round_review import dataset, fingerprint
from review_model import evaluate
from review_optimizer import optimize
from simulation_rules import build_review, report_markdown
from marketing_report import build_current_report


class SimulationRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=dataset(1);cls.plan=cls.data['team']['decisions'];cls.rules=cls.data['simulation']

    def test_pdf_sources_have_hashes_page_counts_and_fingerprint(self):
        self.assertEqual([r['pages'] for r in self.rules['documents']],[26,14])
        paths={r[0] for r in fingerprint(ROOT)}
        for r in self.rules['documents']:
            self.assertEqual(len(r['sha256']),64)
            self.assertIn(str(ROOT/r['file']),paths)
            self.assertIn(r['file'],self.data['sources'])
        self.assertEqual(len(self.rules['factor_rules']),16)

    def test_fair_value_conflict_is_retained_not_overwritten(self):
        rows={r['quadrant']:r for r in self.rules['fair_value'] if r['round']==1}
        self.assertAlmostEqual(rows['BRAND']['documented_floor'],3.9)
        self.assertEqual(rows['BRAND']['exported_floor'],3.5)
        self.assertFalse(rows['BRAND']['meets_documented'])
        self.assertTrue(rows['BRAND']['meets_exported'])
        self.assertAlmostEqual(rows['FRICTIONLESS']['documented_gap'],-2.4)
        self.assertAlmostEqual(rows['FRICTIONLESS']['exported_gap'],-1.8)
        self.assertTrue(all(r['mismatch'] for r in rows.values()))
        self.assertTrue(all(r['leader']!='FAIR VALUE' for r in rows.values()))

    def test_csv_fair_value_drives_active_gaps_not_slide_or_fixed_ratio(self):
        rows={r['quadrant']:r for r in self.rules['fair_value'] if r['round']==1}
        for q,floor,gap in [('BRAND',3.5,.2),('EXPERIENCE',4.3,1.7),('FRICTIONLESS',5.1,-1.8),('LOW PRICE',3.6,1.1)]:
            self.assertEqual(rows[q]['active_floor'],floor)
            self.assertAlmostEqual(rows[q]['active_gap'],gap)
            self.assertEqual(rows[q]['meets_active'],gap>=0)
            self.assertIn('FAIR VALUE column',rows[q]['active_source'])
        self.assertAlmostEqual(rows['LOW PRICE']['exported_leader_ratio'],3.6/5.5)
        self.assertNotAlmostEqual(rows['LOW PRICE']['active_floor'],.67*5.5)
        self.assertTrue(rows['BRAND']['meets_active'])
        self.assertFalse(rows['BRAND']['meets_documented'])
        for row in self.rules['fair_value']:
            self.assertEqual(row['active_floor'],row['exported_floor'])
            self.assertAlmostEqual(row['active_gap'],row['own']-row['exported_floor'])

    def test_budget_arm_not_assumed_exact_next_budget(self):
        b=self.rules['budget']
        self.assertAlmostEqual(b['revenue_arm'],67_469_674.72)
        self.assertIsNone(b['exact_next_budget'])
        self.assertIsNone(b['previous_budget'])
        self.assertIsNone(b['inflation_allowance'])
        self.assertEqual(b['submitted_spend'],69_814_000)

    def test_roic_proxy_is_transparent_not_simulator_store_roic(self):
        old,new=self.rules['capital_efficiency']
        self.assertAlmostEqual(new['pretax_roic_proxy'],42_985_651/360_006_401)
        self.assertLess(old['spread'],0)
        self.assertGreater(new['spread'],0)
        self.assertGreater(new['wacc'],old['wacc'])
        self.assertIn('not the simulator',self.rules['caveats'][2])

    def test_known_zero_holding_and_store_cost_are_not_missing(self):
        r=evaluate(self.plan,self.data)
        self.assertEqual(r['economics']['inventory_holding_rate'],0)
        self.assertEqual(r['economics']['new_store_capex'],1_750_000)
        for rates in ({'inventory_holding_rate':.1},{'new_store_capex':1_000_000},{'inventory_holding_rate':None}):
            with self.assertRaises(ValueError):evaluate(self.plan,self.data,economics=rates)

    def test_analytics_has_no_standalone_demand_without_partners(self):
        d=copy.deepcopy(self.data)
        d['team']['decisions'].update(online=0,experience=0)
        plan=dict(d['team']['decisions'],analytics=self.plan['analytics']+1_000_000)
        r=evaluate(plan,d)
        self.assertEqual(r['scores'],d['rounds']['1']['scores'])
        self.assertEqual(r['revenue_delta'],0)
        paired=evaluate(dict(self.plan,analytics=self.plan['analytics']+1_000_000),self.data)
        self.assertGreater(paired['score_changes']['EXPERIENCE'],0)
        self.assertGreater(paired['score_changes']['FRICTIONLESS'],0)
        self.assertEqual(paired['score_changes']['BRAND'],0)
        self.assertEqual(paired['score_changes']['LOW PRICE'],0)

    def test_vendor_no_longer_directly_changes_brand_or_frictionless(self):
        r=evaluate(dict(self.plan,vendor=self.plan['vendor']+1_000_000),self.data)
        self.assertEqual(r['score_changes']['BRAND'],0)
        self.assertEqual(r['score_changes']['FRICTIONLESS'],0)
        self.assertGreater(r['score_changes']['LOW PRICE'],0)

    def test_stores_do_not_change_preference_scores_and_missing_access_is_flagged(self):
        r=evaluate(dict(self.plan,coverage=201),self.data)
        self.assertEqual(r['score_changes'],{q:0 for q in r['scores']})
        self.assertEqual(r['store_opening_capex'],1_750_000)
        self.assertIn('store_access_financing_response',r['unresolved_model_channels'])

    def test_mix_meaning_resolved_but_numeric_channel_is_not_invented(self):
        r=evaluate(dict(self.plan,high_private=75),self.data)
        self.assertIn('high_private_mix_response',r['unresolved_economics'])
        self.assertIn('private_mix_loyalty_valuation_response',r['unresolved_model_channels'])
        self.assertNotIn('high_private_definition',r['unresolved_economics'])

    def test_changed_plan_value_not_synthesized_from_pe_and_optimization_blocked(self):
        ref=evaluate(self.plan,self.data)
        self.assertEqual(ref['market_value'],248_965_528)
        self.assertEqual(ref['valuation_status'],'observed_reference_only')
        r=evaluate(dict(self.plan,online=7_500_000),self.data)
        self.assertIsNone(r['market_value'])
        self.assertIsNone(r['market_value_delta'])
        self.assertIn('clv_brand_floor',r['unresolved_valuation'])
        out=optimize(dict(decisions=self.plan,objective='market_value',budget=70_000_000,max_cash_use=1_000_000,step=500_000,ranges={'online':[6_500_000,7_000_000]}),self.data)
        self.assertEqual(out['status'],'blocked')
        self.assertIsNone(out['result'])

    def test_report_cites_conflicts_and_avoids_demo_access_data(self):
        text=report_markdown(self.data)
        for needle in ('Intro p15','75%','CLV/private-brand','horizon','one Round 1 undo','67,469,674.72'):
            self.assertIn(needle,text)
        html=build_current_report(self.data)
        self.assertNotIn('@pop.edu',html)
        self.assertNotIn('Password:',html)
        self.assertIn("connect-src 'none'",html)

    def test_rule_audit_is_deterministic_and_nonmutating(self):
        before=copy.deepcopy(self.data)
        self.assertEqual(build_review(self.data,ROOT),self.rules)
        self.assertEqual(before,self.data)


if __name__=='__main__':unittest.main()
