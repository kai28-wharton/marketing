import copy
import hashlib
import json
import math
import unittest
from statistics import mean

from app import ROOT, read_csv, number
from longitudinal_analysis import build_analysis, ridge_fit, ridge_predict, valuation_models
from marketing_report import build_current_report
from round_review import dataset, COMPANY
from current_review import import_submission


class LongitudinalAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Preserve the historical R6 model/budget contract independently of the
        # current final-results view, which is covered by test_final_review.py.
        cls.data=dataset(6)
        cls.a=cls.data['history_analysis']

    def test_latest_context_and_confirmed_simulator_budget(self):
        d=self.data
        self.assertEqual((d['previous_round'],d['current_round'],d['planning_round']),(5,6,7))
        self.assertTrue(d['availability']['finance_current'])
        self.assertEqual(d['strategy']['funding']['approved_budget'],83_151_028)
        self.assertEqual(d['simulation']['budget']['exact_next_budget'],83_151_028)
        self.assertEqual(d['historical_budget'],81_549_510)
        self.assertNotIn('round3_decision',d)
        self.assertEqual(d['team']['column_label'],'Round 6 decision')

    def test_missing_standalone_history_is_recovered_from_labeled_columns(self):
        self.assertEqual(self.data['rounds']['3']['income']['Net Income'],18_862_121)
        self.assertEqual(self.data['rounds']['3']['finance_source_round'],6)
        self.assertIn('Round-3 columns',self.a['history'][3]['finance_source'])
        self.assertFalse(dataset(3)['availability']['finance_current'])

    def test_every_quadrant_uses_exported_floors_and_actual_ranks(self):
        d=self.data
        self.assertEqual([r['round'] for r in self.a['history']],list(range(7)))
        for r in self.a['history']:
            for q,v in r['quadrants'].items():
                source=[x for x in d['kahn'] if x['round']==r['round'] and x['quadrant']==q]
                floor=next(x['value'] for x in source if x['company']=='FAIR VALUE')
                self.assertEqual(v['fair_value'],floor)
                self.assertAlmostEqual(v['gap'],v['score']-floor)
                self.assertEqual(v['rank'],1+sum(x['value']>v['score'] for x in source if x['company']!='FAIR VALUE'))
                self.assertGreaterEqual(v['target_gap'],0)
        now=self.a['history'][-1]['quadrants']
        self.assertAlmostEqual(now['EXPERIENCE']['target_gap'],2.2)
        self.assertAlmostEqual(now['FRICTIONLESS']['target_gap'],1.8)
        self.assertEqual(now['BRAND']['target_gap'],0)
        self.assertTrue(now['BRAND']['target_met'])
        self.assertNotAlmostEqual(now['EXPERIENCE']['fair_value'],.75*now['EXPERIENCE']['leader'])

    def test_output_reconstruction_uses_all_retailers_not_input_response(self):
        for r in self.a['reconstruction']:
            self.assertEqual(r['observations'],49)
            self.assertLessEqual(r['max_absolute_error'],.100001)
        for r in self.a['history']:
            self.assertAlmostEqual(r['experience_reconstructed'],r['positions']['CUSTOMER SERVICE']+r['positions']['SHOPPING EXPERIENCE'])
            self.assertAlmostEqual(r['frictionless_reconstructed'],r['positions']['CUSTOMER SERVICE']+r['positions']['ONLINE INVEST'])

    def test_segment_series_and_unit_share_denominators_are_source_values(self):
        rows=read_csv(ROOT/'materials/round6/marketing/unitMarketShare-round6.csv')
        for r in self.a['history']:
            total=sum(number(x[f"Round-{r['round']} Share"]) for x in rows if x['Product'].startswith(COMPANY+' '))
            self.assertAlmostEqual(r['unit_share'],total)
        for s in self.a['segments']:
            self.assertEqual(len(s['history']),7)
            start,end=s['history'][0],s['history'][-1]
            self.assertAlmostEqual(s['relative_revenue_index'],(end['revenue']/start['revenue'])/(end['size']/start['size']))
            self.assertAlmostEqual(s['revenue_growth'],end['revenue']/start['revenue']-1)
        self.assertAlmostEqual(self.a['history'][-1]['unit_share'],.119)
        self.assertEqual(max(self.a['segments'],key=lambda s:s['clv'])['id'],'SEGMENT 1')

    def test_ridge_validation_recomputes_training_scaling_and_earlier_only_fits(self):
        history=self.a['history'];rows=[dict(r,log_ebit=math.log(r['ebit'])) for r in history]
        self.assertEqual(self.a['valuation']['observations'],7)
        for m in self.a['valuation']['models']:
            self.assertEqual(len(m['predictions']),7)
            self.assertEqual([p['round'] for p in m['forward']],[3,4,5,6])
            for i,p in enumerate(m['predictions']):
                training=rows[:i]+rows[i+1:]
                independent=ridge_predict(ridge_fit(training,m['features']),rows[i])
                self.assertAlmostEqual(p['leave_one_out'],independent)
            for p in m['forward']:
                i=p['round']
                self.assertAlmostEqual(p['estimate'],ridge_predict(ridge_fit(rows[:i],m['features']),rows[i]))
            self.assertAlmostEqual(m['loo_mape'],mean(abs(p['leave_one_out']/p['actual']-1) for p in m['predictions']))
            self.assertTrue(all(p['fitted']>0 and math.isfinite(p['fitted']) for p in m['predictions']))
        self.assertEqual(valuation_models(history[:3])['models'],[])

    def test_lagged_kahn_fits_and_non_circular_market_value_fit(self):
        analysis=self.a['market_value_analysis'];kahn=analysis['kahn'];value=analysis['value']
        self.assertEqual(len(self.data['factors']),16)
        self.assertEqual(kahn['transitions'],6)
        self.assertEqual(kahn['input_count'],15)
        self.assertEqual(len(kahn['models']),4)
        self.assertEqual({m['quadrant'] for m in kahn['models']},{'BRAND','EXPERIENCE','LOW PRICE','FRICTIONLESS'})
        for model in kahn['models']:
            identity=model['form']=='identity';two_stage=model['form']=='two_stage'
            self.assertEqual([p['round'] for p in model['predictions']],[1,2,3,4,5,6])
            self.assertAlmostEqual(model['fitted_mae'],mean(abs(p['error']) for p in model['predictions']))
            self.assertTrue(all(math.isfinite(p['fitted']) for p in model['predictions']))
            self.assertIn('=',model['equation'])
            self.assertNotIn('standardized_equation',model)
            self.assertEqual(len(model['top_factors']),2 if (identity or two_stage) else 3)
            if identity:
                self.assertIsNone(model['hide_one_mae'])
                self.assertEqual([c['importance_rank'] for c in model['top_factors']],[1,2])
                self.assertTrue(all(c['raw_coefficient']==1.0 for c in model['coefficients']))
                self.assertTrue(all(c['latest_contribution']>=0 for c in model['coefficients']))
            elif two_stage:
                self.assertIsNotNone(model['hide_one_mae'])
                if not model.get('audited'):
                    self.assertLess(model['hide_one_mae'],model['persistence_mae'])
                self.assertEqual([c['importance_rank'] for c in model['top_factors']],[1,2])
                self.assertTrue(all(c['raw_coefficient']==1.0 for c in model['coefficients']))
                self.assertTrue(all(c['latest_contribution']>=0 for c in model['coefficients']))
                if not model.get('audited'):
                    self.assertTrue(all(pm['hide_one_mae']<pm['persistence_mae'] for pm in model['position_models']))
                for pm in model['position_models']:
                    self.assertTrue(all(c['raw_coefficient']>=0 for c in pm['coefficients']))
            else:
                self.assertEqual([c['importance_rank'] for c in model['top_factors']],[1,2,3])
                ranked=sorted(model['coefficients'],key=lambda c:abs(c['latest_contribution']),reverse=True)
                self.assertEqual([c['term'] for c in model['top_factors']],[c['term'] for c in ranked[:3]])
            for c in model['coefficients']:
                self.assertNotIn('standardized',c)
                self.assertTrue(math.isfinite(c['raw_coefficient']))
                self.assertTrue(math.isfinite(c['latest_contribution']))
                self.assertGreaterEqual(c['top3_folds'],0)
                self.assertLessEqual(c['top3_folds'],6)
            for p in model['predictions']:
                source=next(r for r in self.a['history'] if r['round']==p['round'])['quadrants'][model['quadrant']]['score']
                self.assertEqual(p['actual'],source)
                self.assertAlmostEqual(p['error'],p['fitted']-p['actual'])
        experience=next(m for m in kahn['models'] if m['quadrant']=='EXPERIENCE')
        self.assertEqual(experience['form'],'two_stage')
        self.assertEqual(experience['position_components'],['CUSTOMER SERVICE','SHOPPING EXPERIENCE'])
        pooled=kahn['position_pooled']
        self.assertEqual(pooled['transitions'],18)
        pooled_coefficients={c['term']:c['raw_coefficient'] for c in pooled['coefficients']}
        self.assertGreater(pooled_coefficients['pos_t'],0)
        self.assertGreater(pooled_coefficients['rel_spend'],0)
        self.assertGreater(pooled_coefficients['analytics'],0)
        self.assertLess(pooled['hide_one_mae'],pooled['persistence_mae'])
        brand=next(m for m in kahn['models'] if m['quadrant']=='BRAND')
        self.assertEqual(brand['features'],['quality','assortment','private','vendor','analytics'])
        self.assertIn('vendor',next(m for m in kahn['models'] if m['quadrant']=='LOW PRICE')['features'])
        frictionless=next(m for m in kahn['models'] if m['quadrant']=='FRICTIONLESS')
        self.assertEqual(frictionless['form'],'two_stage')
        self.assertEqual(frictionless['position_components'],['CUSTOMER SERVICE','ONLINE INVEST'])
        self.assertEqual(frictionless['top_factors'][0]['label'],'Customer Service position')
        self.assertEqual(frictionless['top_factors'][1]['label'],'Online Investment position')
        self.assertAlmostEqual(frictionless['latest']['fitted'],sum(p['fitted'] for p in frictionless['latest']['positions'].values()))
        service=next(pm for pm in frictionless['position_models'] if pm['target']=='CUSTOMER SERVICE')
        self.assertEqual(service['features'],['service_avg'])
        self.assertNotIn('analytics_avg',service['features'])
        self.assertTrue(frictionless['audited'])
        self.assertEqual(frictionless['preferred'],'persistence')
        self.assertLess(frictionless['forward_persistence_mae'],frictionless['forward_mae'])
        features={f['key']:f for f in kahn['feature_map']}
        self.assertEqual(features['quality']['latest_value'],8)
        self.assertAlmostEqual(features['assortment']['latest_value'],34.75)
        self.assertAlmostEqual(features['private']['latest_value'],60)
        self.assertAlmostEqual(features['vendor']['latest_value'],22)
        self.assertAlmostEqual(features['analytics']['latest_value'],13)
        self.assertEqual(features['online_pos']['latest_value'],1.3)
        self.assertEqual(features['service_pos']['latest_value'],1.5)
        low=next(m for m in kahn['models'] if m['quadrant']=='LOW PRICE')
        self.assertLess(brand['hide_one_mae'],brand['persistence_mae'])
        self.assertGreater(low['hide_one_mae'],low['persistence_mae'])
        self.assertEqual(low['preferred'],'persistence')
        self.assertEqual(len(value['predictions']),7)
        self.assertEqual(value['observations'],7)
        self.assertNotIn('market_debt_weight',value['features'])
        self.assertIn('log_ebit',value['features'])
        self.assertIn('ln(EBIT)',value['equation'])
        self.assertLess(value['fitted_mape'],.03)
        self.assertLess(value['hide_one_mape'],.10)
        self.assertLess(value['forward_mape'],value['baseline_mape'])
        for p in value['predictions']:
            self.assertGreater(p['fitted'],0)
            self.assertTrue(math.isfinite(p['fitted']))

    def test_frictionless_constraints_and_no_analytics_only_service_effect(self):
        from frictionless_analysis import _rows, _bounded_fit, _position
        rows=_rows(self.a['history'],0)
        for i in range(len(rows)):
            training=rows[:i]+rows[i+1:]
            online=_bounded_fit(training,'ONLINE INVEST')
            service=_bounded_fit(training,'CUSTOMER SERVICE')
            from market_value_analysis import _raw_model
            slopes=dict(zip(online['features'],_raw_model(online)[1]))
            self.assertTrue(all(v>=0 for v in slopes.values()))
            self.assertLessEqual(slopes['online_pos_t'],1)
            low=copy.deepcopy(rows[i]);high=copy.deepcopy(low)
            high['x']['online_analytics']*=2
            self.assertGreaterEqual(_position(online,high),_position(online,low))
            self.assertEqual(_position(service,low),_position(service,high))
            more_online=copy.deepcopy(low)
            more_online['x']['online_avg']*=2
            more_online['x']['online_analytics']*=2
            self.assertGreaterEqual(_position(online,more_online),_position(online,low))
            more_service=copy.deepcopy(low)
            more_service['x']['service_avg']*=2
            self.assertGreaterEqual(_position(service,more_service),_position(service,low))
            low['x'].update(online_avg=0,online_analytics=0)
            high['x'].update(online_avg=0,online_analytics=0,analytics_avg=100)
            self.assertEqual(_position(online,low),_position(online,high))
            for model in (online,service):
                self.assertGreaterEqual(_position(model,rows[i]),0)
                self.assertLessEqual(_position(model,rows[i]),10)

    def test_frictionless_forward_checks_exclude_later_outcomes(self):
        from frictionless_analysis import _rows, _evaluate
        history=copy.deepcopy(self.a['history'])
        original=_evaluate(_rows(history,0))
        first=original['forward'][0]
        self.assertEqual(first['round'],4)
        self.assertEqual(first['input_round'],4)
        self.assertEqual(first['training_rounds'],[1,2,3])
        history[5]['positions']['CUSTOMER SERVICE']=9
        history[6]['positions']['ONLINE INVEST']=9
        changed=_evaluate(_rows(history,0))
        self.assertEqual(original['forward'][0],changed['forward'][0])
        self.assertEqual([p['round'] for p in original['forward']],[4,5,6])
        self.assertAlmostEqual(original['forward_mae'],mean(abs(p['error']) for p in original['forward']))
        for p in original['forward']:
            self.assertTrue(all(r<p['round'] for r in p['training_rounds']))
        audited=next(m for m in self.a['market_value_analysis']['kahn']['models'] if m['quadrant']=='FRICTIONLESS')
        self.assertEqual(len(audited['audit']['comparison']),4)
        self.assertTrue(all(abs(r['expense_fraction']-.4)<1e-12 for r in audited['audit']['timing']))

    def test_analysis_does_not_mutate_data_or_source_workbooks(self):
        paths=list((ROOT/'decision_making').rglob('*.xlsx'))
        before_hash={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        d=copy.deepcopy(self.data);before=copy.deepcopy(d)
        submissions={r:import_submission(ROOT,r,r) for r in range(7)}
        build_analysis(d,submissions,ROOT)
        self.assertEqual(d,before)
        self.assertEqual(before_hash,{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_offline_analysis_has_models_and_no_editable_draft(self):
        for page in ('marketing','segmentation','marketvalue'):
            html=build_current_report(self.data,page)
            payload=json.loads(html.split('<script type="application/json" id="review-data">')[1].split('</script>')[0])
            self.assertEqual(payload['report_page'],page)
            self.assertIn('history_analysis',payload)
            self.assertEqual(payload['strategy']['funding']['approved_budget'],83_151_028)
            self.assertNotIn('decisions',payload['team'])
            self.assertNotIn('draft',payload['strategy'])
            self.assertIn('function marketValueAnalysis()',html)
            self.assertIn('Customer segmentation analysis</a>',html)
