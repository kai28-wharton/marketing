import json
import math
import unittest
from round_review import dataset
from wacc_analysis import association, fit_wacc, predict_wacc, reweight
from marketing_report import build_current_report


class WaccAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.a=dataset(6)['wacc_analysis']

    def test_factor_coverage_and_sample_sizes(self):
        a=self.a
        self.assertEqual((a['periods'],a['decision_transitions'],len(a['factors'])),(7,6,16))
        for f in a['factors']:
            self.assertEqual((f['levels']['n'],f['changes']['n'],f['lagged_changes']['n']),(7,6,5))
            self.assertTrue(f['pathway']['source'])
            self.assertEqual(len(f['leave_one_transition_out']),6)
        self.assertEqual(a['constant_quality_since'],3)

    def test_constant_data_is_unknown_not_zero_effect(self):
        self.assertIsNone(association([1,1,1],[2,3,4])['r'])
        self.assertAlmostEqual(association([1,2,3],[3,2,1])['r'],-1)

    def test_credit_ratios_and_proxy_weights(self):
        for r in self.a['history']:
            self.assertAlmostEqual(r['book_debt_weight'],r['debt']/(r['debt']+r['book_equity']))
            self.assertAlmostEqual(r['debt_equity'],r['debt']/r['book_equity'])
        self.assertEqual(self.a['history'][-1]['wacc'],10.3)

    def test_model_validation_refits_on_training_rows_only(self):
        a=self.a;m=a['model'];rows=a['history']
        self.assertEqual(m['features'],['market_debt_weight','log_earnings_yield','log_ebit'])
        self.assertEqual(m['selected_penalty'],0.03)
        self.assertIn(m['selected_penalty'],[t['penalty'] for t in m['tuning']])
        for i,p in enumerate(m['predictions']):
            self.assertAlmostEqual(p['leave_one_out'],predict_wacc(fit_wacc(rows[:i]+rows[i+1:],m['selected_penalty']),rows[i]))
            self.assertTrue(math.isfinite(p['fitted']))
        for p in m['forward']:
            i=p['round']
            self.assertAlmostEqual(p['estimate'],predict_wacc(fit_wacc(rows[:i],m['selected_penalty']),rows[i]))
        self.assertLess(m['fitted_mae_pp'],0.1)
        self.assertLess(m['loo_mae_pp'],0.2)
        self.assertLess(m['selected_nested_mae_pp'],0.2)
        self.assertLess(m['forward_mae_pp'],m['baseline_mae_pp'])
        self.assertGreater(m['comparison'][1]['loo_mae_pp'],m['loo_mae_pp'])
        self.assertEqual(m['search']['candidate_subsets'],377)
        self.assertLess(m['selected_nested_mae_pp'],m['search']['unrestricted_nested_mae_pp'])
        self.assertLess(m['selected_nested_mae_pp'],m['search']['fourth_feature_best_nested_pp'])
        self.assertIn('11.0213',m['equation'])

    def test_reweight_arithmetic(self):
        r=reweight(.14,.10,.35,.5,.3)
        self.assertAlmostEqual(r['mix_change'],.015)
        with self.assertRaises(ValueError):reweight(float('nan'),.1,.35,.5,.3)

    def test_offline_report_opens_wacc_without_editable_draft(self):
        html=build_current_report(page='wacc')
        d=json.loads(html.split('<script type="application/json" id="review-data">')[1].split('</script>')[0])
        self.assertEqual(d['report_page'],'wacc')
        self.assertIn('wacc_analysis',d)
        self.assertNotIn('decisions',d['team'])
        self.assertNotIn('draft',d['strategy'])
        self.assertIn('WACC impact analysis</title>',html)
