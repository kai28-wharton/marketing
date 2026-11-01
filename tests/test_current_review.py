import copy
import hashlib
import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
from app import ROOT
from round_review import dataset
from review_model import evaluate, factor_probes
from marketing_report import build_current_report


class CurrentReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=dataset(2)

    def test_round_context_is_explicit_and_latest(self):
        d=self.data
        self.assertEqual((d['previous_round'],d['current_round'],d['planning_round']),(1,2,3))
        self.assertEqual(d['timeline']['latest_decision_round'],2)
        self.assertEqual(d['timeline']['latest_export_round'],2)
        self.assertIn('round_2/decision_making_team11_round2.xlsx',d['team']['source'])
        self.assertIn('round_1/decision_making_team11_round1.xlsx',d['previous_team']['source'])
        self.assertEqual(d['team']['column_label'],'Round 2 decision')
        for t in (d['team'],d['previous_team']):
            self.assertEqual(t['sha256'],hashlib.sha256((ROOT/t['source']).read_bytes()).hexdigest())

    def test_current_finance_and_kahn_are_from_export_two(self):
        s=self.data['rounds']['2']
        self.assertEqual(s['income']['Net Revenue'],561_280_114)
        self.assertEqual(s['income']['Net Income'],10_768_169)
        self.assertEqual(s['scorecard']['Market Value'],255_271_438)
        self.assertEqual(s['scores'],{'BRAND':4.1,'EXPERIENCE':5.8,'LOW PRICE':4.6,'FRICTIONLESS':3.1})
        floors={r['quadrant']:r for r in self.data['simulation']['fair_value'] if r['round']==2}
        self.assertEqual({q:r['active_floor'] for q,r in floors.items()},{'BRAND':3.3,'EXPERIENCE':4.3,'LOW PRICE':3.6,'FRICTIONLESS':5})
        self.assertAlmostEqual(floors['BRAND']['active_gap'],.8)
        self.assertAlmostEqual(floors['FRICTIONLESS']['active_gap'],-1.9)

    def test_actual_submitted_plan_supersedes_prior_recommendation(self):
        p=self.data['team']['decisions']
        for key,value in {'low_breadth':68,'low_depth':30,'high_markup':54,'private_quality':7,'national_quality':7,
                          'coverage':236,'online':8_000_000,'service':14_000_000,'experience':15_000_000,
                          'vendor':26_422_000,'analytics':8_000_000}.items():self.assertEqual(p[key],value)
        self.assertEqual(self.data['historical_budget'],71_422_000)
        self.assertEqual(sum(r['change']!=0 for r in self.data['decision_changes']),11)

    def test_current_segment_clv_is_reported_not_missing_or_imputed(self):
        m=self.data['marketing']
        self.assertTrue(m['segment_clv_available'])
        six=next(s for s in m['segments'] if s['id']=='SEGMENT 6')
        self.assertEqual(six['clv'],220_337_276)
        self.assertEqual(six['prior_clv'],190_349_983)
        self.assertEqual(six['preferences']['DEPTH'],.04)
        self.assertEqual(max(r['round'] for r in six['history']),2)
        self.assertTrue(all('/round2/' in t['file'] for t in m['raw_tables']))
        self.assertEqual(len(m['raw_tables']),15)

    def test_brand_experience_stp_uses_size_clv_and_raw_preferences(self):
        s=self.data['strategy'];p=s['policy'];by_id={r['id']:r for r in s['segments']}
        self.assertEqual((p['primary'],p['secondary']),( 'EXPERIENCE','BRAND'))
        self.assertEqual((p['primary_segment'],p['secondary_segment']),('SEGMENT 3','SEGMENT 5'))
        self.assertEqual(p['defend_segments'],['SEGMENT 2','SEGMENT 6'])
        self.assertEqual(by_id['SEGMENT 3']['preferences']['BRAND'],.3)
        self.assertEqual(by_id['SEGMENT 3']['preferences']['SHOPPING EXPERIENCE'],.4)
        self.assertEqual(by_id['SEGMENT 5']['preferences']['SHOPPING EXPERIENCE'],.43)
        self.assertAlmostEqual(s['focus_summary']['market_population_share'],3_888_246/14_489_001)
        self.assertAlmostEqual(s['focus_summary']['reported_clv_share'],348_187_499/1_143_054_915)
        self.assertEqual({o['quadrant']:o['rank'] for o in s['objectives']},
                         {'EXPERIENCE':2,'BRAND':4,'LOW PRICE':7,'FRICTIONLESS':5})
        self.assertAlmostEqual(s['objectives'][3]['fair_gap'],-1.9)
        self.assertIn('Primary target: Segment 3',self.data['simulation']['strategy'])
        self.assertIn('fair-value safeguards',self.data['simulation']['strategy'])
        self.assertNotIn('Low Price second',self.data['simulation']['strategy'])

    def test_marketvalue_verdict_grounds_experience_brand_choice(self):
        v=self.data['strategy']['verdict']
        self.assertIn('Experience + Brand',v['decision'])
        self.assertEqual(len(v['criteria']),9)
        self.assertEqual({c['verdict'] for c in v['criteria']},{'Pass','Conditional','Risk'})
        self.assertTrue(any('MV p8' in c['slide'] for c in v['criteria']))
        self.assertTrue(any(c['rule'].startswith('Two differentiators') and c['verdict']=='Pass' for c in v['criteria']))
        self.assertEqual([a['role'] for a in v['alternatives']],['Chosen','Rejected','Not chosen now'])
        self.assertEqual(len(v['playbook']),4)
        self.assertEqual(len(v['competitors']),6)
        seg6=next(c for c in v['competitors'] if c['segment']=='SEGMENT 6')
        self.assertIn('BESTCO',seg6['rivals'])
        self.assertIn('MarketValue_Slides',v['sources'][0])
        self.assertIn('not a validated simulator forecast',v['boundary'])

    def test_segment_focus_group_is_tiered_not_single(self):
        g=self.data['strategy']['focus_group'];by_id={t['id']:t for t in g['tiers']}
        self.assertEqual(list(by_id),['win','defend','reserve','serve'])
        self.assertEqual(by_id['win']['segments'],['SEGMENT 3','SEGMENT 5'])
        self.assertEqual(by_id['defend']['segments'],['SEGMENT 2','SEGMENT 6'])
        self.assertEqual(by_id['reserve']['segments'],['SEGMENT 4'])
        self.assertEqual(by_id['serve']['segments'],['SEGMENT 1'])
        all_segments=[s for t in g['tiers'] for s in t['segments']]
        self.assertEqual(sorted(all_segments),sorted({f'SEGMENT {k}' for k in range(1,7)}))
        self.assertAlmostEqual(by_id['win']['reported_clv'],348_187_499)
        self.assertAlmostEqual(by_id['win']['company_revenue'],182_385_511)
        self.assertIn('not a single segment',g['statement'])

    def test_no_recycled_budget_recommendation_or_fake_backtest(self):
        s=self.data['strategy']
        self.assertEqual(s['funding']['approved_budget'],74_631_166)
        self.assertEqual(s['funding']['headroom'],3_209_166)
        self.assertAlmostEqual(s['funding']['revenue_arm'],78_579_215.96)
        self.assertEqual(s['recommendations'],[])
        self.assertEqual(s['draft'],self.data['team']['decisions'])
        self.assertEqual(self.data['audit']['rows'],[])
        self.assertTrue(all(f['industry_round']==2 for f in self.data['factors']))

    def test_customer_segmentation_decision_preserves_source_measures(self):
        d=self.data['segment_decision'];by_id={s['id']:s for s in d['rows']}
        self.assertEqual(d['candidates'],['SEGMENT 2','SEGMENT 4','SEGMENT 5','SEGMENT 6'])
        self.assertEqual(len(by_id),6)
        for source in self.data['marketing']['segments']:
            row=by_id[source['id']]
            for key in ('preferences','size','clv','revenue','size_growth','growth'):
                self.assertEqual(row[key],source[key])
            self.assertAlmostEqual(row['clv_growth'],source['clv']/source['prior_clv']-1)
        self.assertEqual(sum(s['clv'] for s in d['rows']),d['totals']['clv'])
        self.assertAlmostEqual(sum(s['size_share'] for s in d['rows']),1)
        self.assertAlmostEqual(sum(s['clv_share'] for s in d['rows']),1)
        self.assertGreater(by_id['SEGMENT 6']['size_growth'],by_id['SEGMENT 4']['size_growth'])
        self.assertIn('not the fastest',by_id['SEGMENT 4']['risk'])
        self.assertIn('not mean safe',by_id['SEGMENT 3']['risk'])

    def test_customer_segmentation_lenses_change_the_answer_transparently(self):
        d=self.data['segment_decision'];lenses={l['id']:l for l in d['lenses']}
        self.assertEqual(lenses['SHOPPING EXPERIENCE']['order'],['SEGMENT 5','SEGMENT 6','SEGMENT 4','SEGMENT 2'])
        self.assertEqual(lenses['clv']['order'],['SEGMENT 2','SEGMENT 6','SEGMENT 5','SEGMENT 4'])
        self.assertEqual(lenses['size_growth']['order'],['SEGMENT 6','SEGMENT 4','SEGMENT 2','SEGMENT 5'])
        self.assertEqual(lenses['growth']['order'],['SEGMENT 6','SEGMENT 4','SEGMENT 2','SEGMENT 5'])
        self.assertEqual(len(d['pairwise']),4)
        self.assertEqual(len(d['competitors']),7)
        self.assertEqual({c['name'] for c in d['competitors']},set(s['name'] for s in self.data['marketing']['companies']))
        for c in d['competitors']:
            self.assertEqual(set(c['scores']),{'BRAND','EXPERIENCE','LOW PRICE','FRICTIONLESS'})
        self.assertAlmostEqual(d['finance']['interest_cover'],1.392826366941092)
        self.assertEqual(next(r for r in d['floors'] if r['quadrant']=='FRICTIONLESS')['active_floor'],5)
        self.assertIn('not a forecast',d['boundary'])

    def test_customer_segmentation_builder_does_not_change_policy_or_draft(self):
        from segment_decision import build_segment_decision
        data=copy.deepcopy(self.data);before=copy.deepcopy(data)
        build_segment_decision(data)
        self.assertEqual(data,before)

    def test_segmentation_report_opens_its_own_page_without_editable_inputs(self):
        from html import unescape
        html=build_current_report(self.data,page='segmentation')
        self.assertIn('"report_page": "segmentation"',html)
        self.assertIn('Customer segmentation decision</title>',html)
        self.assertIn('function segmentationHurdle(',html)
        self.assertIn('function serializeSegmentationReport(',html)
        self.assertIn('Download interactive HTML',unescape(html))
        payload=json.loads(html.split('<script type="application/json" id="review-data">')[1].split('</script>')[0])
        self.assertNotIn('decisions',payload['team'])
        self.assertNotIn('draft',payload['strategy'])
        self.assertNotIn('economic_defaults',payload)
        self.assertNotIn('segmentation_debate',self.data)
        with self.assertRaises(ValueError):build_current_report(self.data,page='decisions')

    def test_model_reanchors_to_latest_and_retains_rounding(self):
        before=copy.deepcopy(self.data)
        r=evaluate(self.data['team']['decisions'],self.data)
        s=self.data['rounds']['2']
        self.assertEqual(r['net_income'],s['income']['Net Income'])
        self.assertEqual(r['revenue'],s['income']['Net Revenue'])
        self.assertEqual(r['scores'],s['scores'])
        self.assertEqual(r['version'],'review-5.0')
        self.assertEqual(r['incremental_cash_delta'],0)
        self.assertTrue(all(v is None for v in r['score_stress'].values()))
        changed=evaluate(dict(self.data['team']['decisions'],online=8_500_000),self.data)
        self.assertGreater(changed['scores']['FRICTIONLESS'],3.1)
        self.assertIsNone(changed['market_value'])
        self.assertEqual(len(factor_probes(self.data)),16)
        self.assertEqual(self.data,before)

    def test_offline_snapshot_has_current_context_without_decision_inputs(self):
        class Parser(HTMLParser):
            def __init__(self):super().__init__();self.active=False;self.text=''
            def handle_starttag(self,tag,attrs):
                if tag=='script':self.active=dict(attrs).get('id')=='review-data'
            def handle_endtag(self,tag):
                if tag=='script':self.active=False
            def handle_data(self,text):
                if self.active:self.text+=text
        html=build_current_report(self.data);p=Parser();p.feed(html);d=json.loads(p.text)
        self.assertEqual(d['current_round'],2)
        self.assertEqual(d['planning_round'],3)
        self.assertTrue(d['marketing']['segment_clv_available'])
        self.assertNotIn('decisions',d['team'])
        self.assertNotIn('draft',d['strategy'])
        self.assertIn('verdict',d['strategy'])
        self.assertIn('Experience + Brand',d['strategy']['verdict']['decision'])
        self.assertIn('focus_group',d['strategy'])
        self.assertIn('segment_decision',d)
        self.assertIn('function renderCurrent()',html)
        self.assertIn('EXPORT 2 · ROUND 3 PLANNING',html)


if __name__=='__main__':unittest.main()
