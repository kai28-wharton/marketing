import copy
import csv
from pathlib import Path
import unittest
from round_review import dataset
from brand_impact import reconstruct
from review_model import evaluate, factor_probes
from review_optimizer import optimize


class BrandImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=dataset(1);cls.x=cls.data['insights']['brand']['parameter_impact']

    def test_actual_workbook_linkage_and_cells(self):
        rows={r['key']:r for r in self.x['linked_depth_decisions']}
        self.assertEqual(rows['low_depth']['input'],25)
        self.assertEqual(rows['low_depth']['cell'],'Sheet1!B4')
        self.assertEqual(rows['high_depth']['input'],10)
        self.assertEqual(rows['high_depth']['cell'],'Sheet1!B8')
        self.assertTrue(all(r['inside_industry_range'] for r in rows.values()))
        self.assertEqual(self.x['sha256'],self.data['team']['sha256'])
        self.assertIn('unverified screenshot',self.x['input_boundary'])

    def test_four_terms_reproduce_all_reported_retailer_rows_with_rounding(self):
        self.assertEqual(self.x['validation_rows'],14)
        self.assertEqual(self.x['within_005'],14)
        self.assertLessEqual(self.x['max_absolute_error'],.05+1e-9)
        self.assertEqual(len({r['company'] for r in self.x['validation']}),7)
        self.assertNotIn('FAIR VALUE',{r['company'] for r in self.x['validation']})
        self.assertIn('same 14',self.x['discovery_status'])
        for r in self.x['validation']:self.assertAlmostEqual(r['actual']-r['reconstructed'],r['residual'])

    def test_change_decomposition_is_exact_with_residual_retained(self):
        rows={r['key']:r for r in self.x['contributions']}
        self.assertAlmostEqual(rows['low_depth']['brand_change'],-1)
        self.assertAlmostEqual(rows['high_depth']['brand_change'],-1.9)
        self.assertAlmostEqual(rows['private_low']['brand_change'],.15)
        self.assertAlmostEqual(rows['private_high']['brand_change'],.15)
        self.assertAlmostEqual(self.x['gross_adverse'],2.9)
        self.assertAlmostEqual(self.x['positive_offset'],.3)
        self.assertAlmostEqual(self.x['reconstructed_change'],-2.6)
        self.assertAlmostEqual(self.x['residual_change'],0)
        self.assertAlmostEqual(self.x['reconstructed_change']+self.x['residual_change'],self.x['observed_change'])
        self.assertAlmostEqual(rows['high_depth']['gross_adverse_share'],1.9/2.9)

    def test_brand_why_how_source_references_and_observation_count(self):
        root=Path(__file__).resolve().parents[1]
        lines=(root/'materials/round1/marketing/productPosition-round1.csv').read_text().splitlines()
        for key,prior_line,current_line in [('high_depth',23,11),('low_depth',22,10)]:
            term=next(r for r in self.x['contributions'] if r['key']==key)
            for line,rnd,field in [(prior_line,0,'prior_position'),(current_line,1,'current_position')]:
                row=next(csv.reader([lines[line-1]]))
                self.assertEqual(row[0],term['attribute'])
                self.assertEqual(int(row[1]),rnd)
                self.assertEqual(float(row[2]),term[field])
        observations={(r['company'],r['round']) for r in self.x['validation']}
        companies={company for company,rnd in observations}
        self.assertEqual(observations,{(company,rnd) for company in companies for rnd in (0,1)})
        script=(root/'web/review.js').read_text()
        for text in ['WHY / HOW · Sources, assumptions & arithmetic',
                     'is hardcoded in our analysis',
                     'independent tests or held-out validation',
                     'not a percentage of proven causal loss']:
            self.assertIn(text,script)

    def test_positions_not_decision_indices_are_used(self):
        observed={r['attribute']:r['current_position'] for r in self.x['contributions']}
        self.assertAlmostEqual(reconstruct(observed),3.75)
        self.assertNotEqual(reconstruct(observed),.5*(25+10+44+70))

    def test_score_position_substitutions_not_simulator_counterfactuals(self):
        rows=self.x['substitutions']
        self.assertAlmostEqual(rows[0]['brand'],4.7)
        self.assertAlmostEqual(rows[1]['brand'],5.6)
        self.assertAlmostEqual(rows[2]['brand'],6.6)
        self.assertAlmostEqual(rows[3]['brand'],3.4)
        self.assertTrue(all('Not an input-level' in r['basis'] for r in rows))

    def test_legacy_individual_attribution_sums_and_exposes_depth_omission(self):
        a=self.x['legacy_parameter_audit'];rows={r['key']:r for r in a['rows']}
        self.assertEqual(len(rows),16)
        self.assertAlmostEqual(sum(r['shapley'] for r in rows.values()),a['predicted_change'],places=10)
        self.assertAlmostEqual(a['allocated_change'],a['predicted_change'],places=10)
        self.assertAlmostEqual(a['predicted_brand'],6.463640107619982)
        for key in ('high_depth','low_depth'):
            self.assertFalse(rows[key]['brand_channel_in_v2'])
            self.assertEqual(rows[key]['one_at_a_time'],0)
            self.assertEqual(rows[key]['shapley'],0)
        self.assertLess(rows['vendor']['shapley'],0)
        self.assertGreater(rows['private_quality']['shapley'],0)

    def test_missing_future_depth_response_is_flagged_and_blocks_optimization(self):
        plan=dict(self.data['team']['decisions'],high_depth=15)
        r=evaluate(plan,self.data)
        self.assertIn('brand_depth_response',r['unresolved_model_channels'])
        payload=dict(decisions=plan,ranges={'analytics':[8_314_000,8_314_000]},step=500_000,budget=70_000_000,max_cash_use=1_000_000,
                     economics=dict(depth_inventory_sensitivity=0,inventory_holding_rate=0,inventory_financing_rate=0))
        out=optimize(payload,self.data)
        self.assertEqual(out['status'],'blocked')
        self.assertIsNone(out['result'])
        self.assertIn('brand_depth_response',out['unresolved_model_channels'])
        baseline=evaluate(self.data['team']['decisions'],self.data)
        self.assertFalse(baseline['unresolved_model_channels'])

    def test_probes_flag_unknown_brand_response_without_rewriting_workbook(self):
        before=copy.deepcopy(self.data)
        rows={r['key']:r for r in factor_probes(self.data)}
        for key in ('low_depth','high_depth'):
            for direction in ('increase','decrease'):
                self.assertIn('brand_depth_response',rows[key][direction]['unresolved_model_channels'])
        self.assertEqual(self.data,before)

    def test_brand_diagnostic_distinguishes_partial_component_from_full_prediction(self):
        for key in ('low_depth','high_depth','low_breadth','high_breadth','low_private','high_private'):
            plan=dict(self.data['team']['decisions'])
            plan[key]+=5
            result=evaluate(plan,self.data)
            d=result['score_diagnostics']['BRAND']
            self.assertEqual(d['status'],'partial')
            self.assertIsNone(d['full_prediction'])
            self.assertEqual(d['modeled_component_score'],result['scores']['BRAND'])
            self.assertEqual(d['reference'],3.7)
            self.assertEqual([r['key'] for r in d['changed_inputs']],[key])
            self.assertTrue(d['missing_channels'])
        baseline=evaluate(self.data['team']['decisions'],self.data)['score_diagnostics']['BRAND']
        self.assertEqual(baseline['status'],'conditional')
        self.assertEqual(baseline['full_prediction'],3.7)
        self.assertFalse(baseline['missing_channels'])

    def test_quality_response_is_retained_but_does_not_fill_missing_depth_response(self):
        result=evaluate(dict(self.data['team']['decisions'],high_depth=15,private_quality=7),self.data)
        d=result['score_diagnostics']['BRAND']
        self.assertGreater(d['modeled_component_score'],3.7)
        self.assertIsNone(d['full_prediction'])
        self.assertEqual(d['missing_channels'],['brand_depth_response'])


if __name__=='__main__':unittest.main()
