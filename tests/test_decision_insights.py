import copy
import unittest
from decision_insights import build_insights, CROSSWALKS
from round_review import dataset, QUADRANTS


class DecisionInsightsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=dataset(1);cls.insights=cls.data['insights']

    def test_brand_drop_rank_and_peer_comparison(self):
        b=self.insights['brand']
        self.assertAlmostEqual(b['change'],-2.6)
        self.assertEqual((b['prior_rank'],b['current_rank']),(1,5))
        self.assertAlmostEqual(b['relative_change'],3.7/6.3-1)
        self.assertAlmostEqual(b['peer_mean_change'],.4333333333333333)
        self.assertAlmostEqual(b['gap_change'],b['change']-b['peer_mean_change'])
        self.assertEqual(len(b['peers']),7)
        self.assertNotIn('FAIR VALUE',{r['company'] for r in b['peers']})

    def test_brand_bridge_is_model_error_not_invented_causal_allocation(self):
        b=self.insights['brand']
        self.assertAlmostEqual(b['prior']+b['modeled_change']+b['unexplained_residual'],b['current'])
        self.assertAlmostEqual(b['unexplained_residual'],-2.7636401076)
        self.assertIn('not explained causally',b['conclusion'])
        self.assertEqual(len(b['decisions']),16)
        self.assertTrue(all(h['test'] and h['limit'] for h in b['hypotheses']))
        positions={p['attribute']:p for p in b['positions']}
        self.assertAlmostEqual(positions['HIGHER COST DEPTH']['relative_change'],-.76)

    def test_gross_margin_bridge_reconciles_and_mix_was_helpful(self):
        f=self.insights['finance']
        self.assertAlmostEqual(f['margin_change_pp'],-2.5900089987)
        self.assertLess(f['within_effect_pp'],0)
        self.assertGreater(f['mix_effect_pp'],0)
        self.assertAlmostEqual(f['within_effect_pp']+f['mix_effect_pp']+f['margin_rounding_residual_pp'],f['margin_change_pp'])
        self.assertAlmostEqual(f['margin_rounding_residual_pp'],0,places=6)
        for row in f['offerings']:self.assertLess(row['margin_change_pp'],0)
        for row in f['offerings']:
            self.assertAlmostEqual(row['implied_markup_current'],row['submitted_markup'],places=8)
            self.assertAlmostEqual(row['current_margin'],row['margin_at_submitted_markup'],places=8)
        self.assertAlmostEqual(f['offerings'][0]['implied_markup_prior'],.54,places=8)
        self.assertAlmostEqual(f['offerings'][1]['implied_markup_prior'],.66,places=8)

    def test_cash_bridge_reconciles_without_claiming_verified_cash_flow(self):
        f=self.insights['finance']
        self.assertEqual(f['cash_change'],-4_598_444)
        self.assertEqual(sum(r['value'] for r in f['cash_rows']),f['cash_proxy_change'])
        self.assertEqual(f['cash_bridge_residual'],-1)
        self.assertEqual(f['cash_proxy_change']+f['cash_bridge_residual'],f['cash_change'])
        self.assertIn('not a supplied cash-flow statement',f['cash_boundary'])
        self.assertTrue(any('proxy' in r['basis'] for r in f['cash_rows']))
        self.assertEqual(f['depreciation_reconciliation'],0)
        self.assertEqual(f['equity_vs_income_residual'],0)

    def test_liquidity_current_improved_but_quick_worsened(self):
        f=self.insights['finance']
        self.assertGreater(f['current_ratio'],f['current_ratio_prior'])
        self.assertLess(f['current_ratio'],1)
        self.assertLess(f['quick_ratio'],f['quick_ratio_prior'])
        self.assertEqual(f['working_capital'],-72_994_273)
        self.assertGreater(f['working_capital_change'],0)

    def test_financing_thresholds_and_stresses_have_independent_formulas(self):
        f=self.insights['finance'];i=self.data['rounds']['1']['income']
        self.assertAlmostEqual(f['interest_cover'],42_985_651/30_062_720)
        self.assertAlmostEqual(f['margin_buffer_pp'],100*12_922_931/481_926_248)
        self.assertAlmostEqual(f['break_even_margin']+f['margin_buffer_pp']/100,f['margin_current'],places=7)
        self.assertAlmostEqual(f['sales_decline_to_pretax_breakeven'],12_922_931/161_948_949)
        self.assertEqual(f['additional_ebit_for_2x_cover'],17_139_789)
        s=f['stress'][0]
        self.assertAlmostEqual(s['net_income_change'],-.01*i['Net Revenue']*(1-i['Income Taxes']/i['Income Before Taxes']))
        self.assertAlmostEqual(f['ten_days_inventory_funding'],319_977_298/365*10)

    def test_crosswalks_assign_each_preference_once(self):
        attrs=set(self.data['marketing']['attributes'])
        for mapping in CROSSWALKS.values():
            entries=[a for group in mapping.values() for a in group]
            self.assertEqual(set(entries),attrs)
            self.assertEqual(len(entries),len(attrs))

    def test_segment_indices_and_effects_reconcile_for_both_mappings(self):
        for lens in self.insights['segment_lenses'].values():
            for s in lens['segments']:
                self.assertAlmostEqual(sum(s['weights'].values()),1)
                self.assertAlmostEqual(s['index_change'],sum(s['score_effects'].values())+s['preference_effect'])
                self.assertAlmostEqual(s['current_index'],sum(s['weights'][q]*self.data['rounds']['1']['scores'][q] for q in QUADRANTS))
            self.assertAlmostEqual(lens['portfolio_change'],lens['within_effect']+lens['mix_effect'])
            self.assertIn('not measured segment Kahn',lens['boundary'])

    def test_mapping_changes_exposure_conclusion_not_observed_scores(self):
        a,b=(self.insights['segment_lenses'][k] for k in ('product','convenience'))
        self.assertNotEqual(a['largest_brand_exposure'],b['largest_brand_exposure'])
        self.assertEqual(a['most_brand_sensitive'],'SEGMENT 3')
        self.assertEqual(b['most_brand_sensitive'],'SEGMENT 3')
        self.assertNotEqual(a['portfolio_change'],b['portfolio_change'])

    def test_analysis_does_not_mutate_decisions_or_model(self):
        before=copy.deepcopy(self.data)
        expected=copy.deepcopy(self.insights)
        expected['brand'].pop('parameter_impact')
        self.assertEqual(build_insights(self.data),expected)
        self.assertEqual(self.data,before)


if __name__=='__main__':unittest.main()
