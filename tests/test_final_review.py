import csv
import hashlib
import json
import math
import unittest
from statistics import mean

from app import ROOT
from current_review import build_dataset
from market_value_analysis import _value_rows, _value_fit, _value_predict
from marketing_report import build_current_report
from round_review import dataset
from wacc_analysis import fit_wacc, predict_wacc


class FinalReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=dataset()

    def test_final_results_and_no_new_approved_budget(self):
        d=self.data
        self.assertEqual(d['current_round'],8)
        self.assertTrue(d['simulation_complete'])
        self.assertEqual(d['final_review']['scored_rounds'],list(range(1,9)))
        self.assertEqual(d['final_review']['snapshot_count'],9)
        self.assertIsNone(d['strategy']['funding']['approved_budget'])
        last=d['history_analysis']['history'][-1]
        self.assertEqual(last['market_value'],1_038_044_778)
        self.assertEqual(last['net_income'],75_834_309)
        self.assertEqual(last['wacc'],10)
        self.assertAlmostEqual(last['unit_share'],.123)
        self.assertIn('scorecard-round8.csv',last['unit_share_source'])

    def test_final_objectives_are_source_values_and_not_old_conclusions(self):
        r=self.data['final_review']
        by={o['quadrant']:o for o in r['objectives']}
        self.assertEqual(by['BRAND']['rank'],1)
        self.assertEqual(by['EXPERIENCE']['rank'],1)
        self.assertAlmostEqual(by['FRICTIONLESS']['gap'],-.7)
        self.assertEqual(by['FRICTIONLESS']['fair_value'],4.6)
        self.assertTrue(by['LOW PRICE']['target_met'])
        self.assertEqual(r['objectives_met'],3)
        self.assertEqual(r['experience_leader_rounds'],[8])
        self.assertEqual(r['frictionless_below_floor_rounds'],list(range(1,9)))
        for check in self.data['history_analysis']['reconstruction']:
            self.assertEqual(check['observations'],63)

    def test_report_history_matches_raw_r0_to_r8_exports(self):
        def rows(relative):
            with (ROOT/'materials/round8'/relative).open(encoding='utf-8-sig',newline='') as source:
                return list(csv.DictReader(source))
        def number(value):
            value=value.replace('$','').replace(',','').replace('%','')
            return -float(value[1:-1]) if value.startswith('(') else float(value)
        score={r['Name']:r for r in rows('finance/scorecard-round8.csv')}
        income={r['Name']:r for r in rows('finance/incomeStatement-round8.csv')}
        balance={r['Name']:r for r in rows('finance/balanceSheet-round8.csv')}
        kahn={r['Quadrant']:r for r in rows('marketing/kahn-round8.csv')}
        revenue={int(r['ROUND']):r for r in rows('marketing/marketRevenue-round8.csv')}
        clv={int(r['ROUND']):r for r in rows('marketing/marketCLV-round8.csv')}
        strategy=self.data['final_review']['segmentation_strategy']
        for point in self.data['history_analysis']['history']:
            n=point['round'];column=f'Round-{n}'
            for key,label in (('market_value','Market Value'),('clv','Customer Lifetime Value'),
                              ('wacc','Weighted Average Cost of Capital (WACC)')):
                self.assertEqual(point[key],number(score[label][column]))
            self.assertAlmostEqual(point['gross_margin'],number(score['Gross Margin'][column])/100,delta=.0005)
            self.assertAlmostEqual(point['gross_margin'],number(income['Gross Profit'][column])/point['revenue'])
            self.assertEqual(point['net_income'],number(income['Net Income'][column]))
            self.assertEqual(point['revenue'],number(income['Net Revenue'][column]))
            self.assertEqual(point['debt'],sum(number(balance[k][column]) for k in ('Short Term Loans','Long Term Debt')))
            for q,observed in point['quadrants'].items():
                raw=kahn[f'Round {n} {q}'];own=number(raw["GETCHELL'S"])
                self.assertEqual(observed['score'],own)
                self.assertEqual(observed['fair_value'],number(raw['FAIR VALUE']))
                self.assertEqual(observed['rank'],1+sum(number(v)>own for k,v in raw.items() if k not in ('Quadrant','FAIR VALUE',"GETCHELL'S")))
            total_revenue=sum(number(revenue[n][f'SEGMENT {i}']) for i in range(1,7))
            total_clv=sum(number(clv[n][f'SEGMENT {i}']) for i in range(1,7))
            self.assertAlmostEqual(total_revenue,point['revenue'],delta=2)
            self.assertAlmostEqual(total_clv,point['clv'],delta=2)
            for group in strategy['rows']+strategy['groups']:
                actual=next(p for p in group['history'] if p['round']==n)
                expected_revenue=sum(number(revenue[n][sid]) for sid in group['ids'])
                expected_clv=sum(number(clv[n][sid]) for sid in group['ids'])
                self.assertEqual(actual['revenue'],expected_revenue)
                self.assertEqual(actual['clv'],expected_clv)
                self.assertAlmostEqual(actual['mix'],expected_revenue/total_revenue)
                self.assertAlmostEqual(actual['clv_mix'],expected_clv/total_clv)

    def test_segment_scorecard_reconciles_and_uses_consistent_denominators(self):
        r=self.data['final_review'];rows=r['rows'];f=r['finance'];core=r['core']
        self.assertEqual(len(rows),6)
        self.assertAlmostEqual(sum(s['revenue'] for s in rows),f['revenue'],delta=2)
        self.assertAlmostEqual(sum(s['mix'] for s in rows),1)
        self.assertAlmostEqual(sum(s['contribution_to_revenue_growth'] for s in rows),1)
        targets=[s for s in rows if s['id'] in ('SEGMENT 3','SEGMENT 6')]
        self.assertEqual(core['revenue'],sum(s['revenue'] for s in targets))
        self.assertEqual(core['revenue'],225_330_895)
        self.assertAlmostEqual(core['mix'],core['revenue']/f['revenue'],places=7)
        self.assertGreater(core['mix_change_pp'],0)
        self.assertGreater(core['clv_mix_change_pp'],0)
        self.assertEqual(next(s for s in rows if s['id']=='SEGMENT 6')['role'],'Secondary target')
        self.assertNotIn('S5 convenience',r['conclusion'])
        self.assertEqual(max(rows,key=lambda s:s['revenue'])['id'],'SEGMENT 1')
        self.assertTrue(all(s['revenue_growth']>0 for s in targets))

    def test_replay_objective_audit_uses_scored_rounds_and_source_goals(self):
        r=self.data['final_review']
        by={x['quadrant']:x for x in r['objective_delivery']}
        self.assertEqual({q:x['count'] for q,x in by.items()},
                         {'EXPERIENCE':1,'BRAND':6,'FRICTIONLESS':0,'LOW PRICE':8})
        self.assertEqual(r['all_objectives_met_rounds'],[])
        history=self.data['history_analysis']['history']
        for q,x in by.items():
            self.assertEqual(x['total'],8)
            self.assertEqual(x['rounds_met'],[row['round'] for row in history[1:] if row['quadrants'][q]['target_met']])
            self.assertEqual(x['final'],history[-1]['quadrants'][q])
            self.assertNotIn(0,x['rounds_met'])
        for row in history[1:]:
            for q in ('LOW PRICE','FRICTIONLESS'):
                value=row['quadrants'][q]
                self.assertEqual(value['target_met'],value['score']>=value['fair_value'])

    def test_segmentation_priority_audit_reconciles(self):
        r=self.data['final_review']['segmentation_strategy']
        self.assertEqual(r['priority_order'],['SEGMENT 3','SEGMENT 6',['SEGMENT 2','SEGMENT 4','SEGMENT 5']])
        self.assertEqual([x['ids'][0] for x in r['rows']],
                         ['SEGMENT 3','SEGMENT 6','SEGMENT 2','SEGMENT 4','SEGMENT 5','SEGMENT 1'])
        self.assertAlmostEqual(sum(x['growth_share'] for x in r['groups']),1)
        self.assertAlmostEqual(sum(x['clv_growth_share'] for x in r['groups']),1)
        self.assertAlmostEqual(sum(x['constant_mix_difference'] for x in r['rows']),0,delta=2)
        core=r['groups'][0]
        self.assertEqual(core['revenue'],225_330_895)
        self.assertAlmostEqual(core['constant_mix_difference'],6_634_165.82,places=1)
        by={x['ids'][0]:x for x in r['rows']}
        self.assertLess(by['SEGMENT 3']['mix_change_pp'],0)
        self.assertAlmostEqual(core['mix_change_pp'],by['SEGMENT 3']['mix_change_pp']+by['SEGMENT 6']['mix_change_pp'])
        for point in core['history']:
            for key in ('revenue','clv','mix','clv_mix'):
                self.assertAlmostEqual(point[key],sum(next(p for p in by[sid]['history'] if p['round']==point['round'])[key]
                                                     for sid in ('SEGMENT 3','SEGMENT 6')))
        self.assertLess(by['SEGMENT 2']['phases'][1]['growth'],0)
        self.assertGreater(by['SEGMENT 4']['mix_change_pp'],0)
        self.assertGreater(by['SEGMENT 6']['mix_change_pp'],0)
        for group in r['rows']+r['groups']:
            self.assertEqual([x['round'] for x in group['history']],list(range(9)))
            for phase in group['phases']:
                self.assertAlmostEqual((1+phase['per_round_growth'])**(phase['end']-phase['start'])-1,
                                       phase['growth'])
        self.assertIn('not a counterfactual',r['benchmark_basis'])

    def test_value_model_is_refitted_to_all_nine_snapshots(self):
        v=self.data['history_analysis']['market_value_analysis']['value']
        rows=_value_rows(self.data['history_analysis']['history'])
        fit=_value_fit(rows,v['features'],v['penalty'])
        self.assertEqual(v['observations'],9)
        self.assertEqual([p['round'] for p in v['predictions']],list(range(9)))
        self.assertNotIn('market_debt_weight',v['features'])
        for row,p in zip(rows,v['predictions']):
            self.assertAlmostEqual(p['fitted'],_value_predict(fit,row))
            self.assertAlmostEqual(p['error_pct'],p['fitted']/p['actual']-1)
        self.assertAlmostEqual(v['fitted_mape'],mean(abs(p['error_pct']) for p in v['predictions']))
        self.assertLess(v['fitted_mape'],.03)
        self.assertIn('1.5896',v['equation'])
        self.assertNotIn('Seven company',v['boundary'])

    def test_wacc_model_has_fresh_fit_and_secondary_validation(self):
        a=self.data['wacc_analysis'];m=a['model'];rows=a['history']
        self.assertEqual((a['periods'],a['decision_transitions']),(9,8))
        self.assertEqual(m['observations'],9)
        self.assertEqual(m['penalty'],.01)
        fit=fit_wacc(rows,m['penalty'],m['features'])
        for i,p in enumerate(m['predictions']):
            self.assertAlmostEqual(p['fitted'],predict_wacc(fit,rows[i]))
            trial=fit_wacc(rows[:i]+rows[i+1:],m['penalty'],m['features'])
            self.assertAlmostEqual(p['leave_one_out'],predict_wacc(trial,rows[i]))
        self.assertAlmostEqual(m['fitted_mae_pp'],mean(abs(p['fitted']-p['actual']) for p in m['predictions']))
        self.assertLess(m['fitted_mae_pp'],.07)
        self.assertNotIn('search',m)
        self.assertIn('10.9222',m['equation'])

    def test_score_models_use_fitted_components_and_all_eight_decisions(self):
        k=self.data['history_analysis']['market_value_analysis']['kahn']
        self.assertEqual(k['observations'],8)
        self.assertEqual(k['input_count'],15)
        self.assertEqual(len(k['models']),4)
        by={m['quadrant']:m for m in k['models']}
        for m in k['models']:
            self.assertEqual([p['round'] for p in m['predictions']],list(range(1,9)))
            self.assertAlmostEqual(m['mae'],mean(abs(p['error']) for p in m['predictions']))
            self.assertTrue(all(math.isfinite(p['fitted']) for p in m['predictions']))
            self.assertLess(m['mae'],m['persistence_mae'])
        # The enhanced game: Low Price is fitted relative to the six-peer average;
        # Frictionless and Experience inherit bounded service carryover.
        self.assertIn('six-peer average',by['LOW PRICE']['equation'])
        self.assertIn('peer-relative',by['LOW PRICE']['level_equation'])
        self.assertLess(by['LOW PRICE']['mae'],.05)
        self.assertGreater(by['LOW PRICE']['r_squared'],.6)
        self.assertGreater(by['LOW PRICE']['hide_one_mae'],by['LOW PRICE']['mae'])
        self.assertTrue(all('peer' in p and 'relative' in p for p in by['LOW PRICE']['predictions']))
        for p in by['LOW PRICE']['predictions']:
            self.assertAlmostEqual(p['fitted'],p['peer']+p['fitted_relative'])
        for h in self.data['history_analysis']['history']:
            self.assertIn('LOW PRICE',h['peer_scores'])
        self.assertLess(by['FRICTIONLESS']['mae'],.06)
        self.assertGreater(by['FRICTIONLESS']['r_squared'],.95)
        self.assertLess(by['EXPERIENCE']['mae'],.05)
        self.assertGreater(by['EXPERIENCE']['r_squared'],.99)
        service=next(p for p in k['position_equations'] if p['target']=='CUSTOMER SERVICE')
        self.assertIn('prior Customer Service position',service['equation'])
        self.assertTrue(any('relative Online × relative Analytics' in p['equation'] for p in k['position_equations']))
        self.assertTrue(any('relative Shopping Experience × relative Analytics' in p['equation'] for p in k['position_equations']))

    def test_final_reports_embed_final_data_and_no_editable_plan(self):
        for page in ('marketing','segmentation','marketvalue','wacc','combined'):
            html=build_current_report(self.data,page)
            payload=json.loads(html.split('<script type="application/json" id="review-data">')[1].split('</script>')[0])
            self.assertEqual(payload['current_round'],8)
            self.assertEqual(payload['report_page'],page)
            self.assertTrue(payload['simulation_complete'])
            self.assertIn('final_review',payload)
            self.assertIn('Final market-value model',html)
            self.assertNotIn('decisions',payload['team'])
            self.assertNotIn('draft',payload['strategy'])
            self.assertNotIn('ROUND 9 PLANNING',html.split('<script')[0])
            if page=='combined':
                self.assertIn('Final R1–R8 Marketing & Finance Report',html.split('<script')[0])
                self.assertIn('<section class="report-section report-brief"',html)
                self.assertIn('<nav class="report-nav"',html)
                for section in ('overview','stp','segmentation','marketvalue','wacc'):
                    self.assertIn(f"section('{section}',",html)
                self.assertNotIn("section('second-chance',",html)
                self.assertNotIn('href="#second-chance"',html)
                self.assertIn('Expand detailed evidence',html)
                self.assertIn('report-detail:not([open])',html)

    def test_analysis_does_not_edit_submitted_workbooks(self):
        paths=[p for p in (ROOT/'decision_making').rglob('*.xlsx') if not p.name.startswith('~$')]
        before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        build_dataset(ROOT,8)
        self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
