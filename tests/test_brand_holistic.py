import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from app import ROOT
from brand_holistic import build_holistic, source_audit, write_report
from round_review import dataset, fingerprint

TEMP=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')


class HolisticBrandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=dataset(1);cls.h=cls.data['insights']['brand']['parameter_impact']['holistic']

    def test_all_materials_reviewed_and_narratives_fingerprinted(self):
        files={str(p.relative_to(ROOT)) for p in (ROOT/'materials').rglob('*') if p.suffix in ('.csv','.md','.pdf')}
        audit=self.h['source_audit']
        self.assertEqual({s['file'] for s in audit['materials']},files)
        self.assertEqual(audit['material_files'],len(files))
        self.assertTrue(files<=set(self.data['sources']))
        stamps={p for p,_,_ in fingerprint(ROOT)}
        self.assertIn(str(ROOT/'materials/company.md'),stamps)
        self.assertIn(str(ROOT/'materials/competitors.md'),stamps)
        for s in audit['materials']:
            self.assertEqual(s['sha256'],hashlib.sha256((ROOT/s['file']).read_bytes()).hexdigest())

    def test_overlap_and_auxiliary_checks_do_not_multiply_samples(self):
        audit=self.h['source_audit']
        self.assertEqual(audit['overlap_cells'],390)  # Includes 14 newly supplied unit-share rows.
        self.assertEqual(audit['auxiliary_cells'],96)
        self.assertFalse(audit['conflicts'])
        self.assertEqual(self.data['insights']['brand']['parameter_impact']['validation_rows'],14)
        self.assertIn('not independent',audit['boundary'])

    def test_conflicting_history_is_reported_not_silently_overwritten(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as tmp:
            root=Path(tmp)
            for s in self.h['source_audit']['materials']:
                p=root/s['file'];p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes((ROOT/s['file']).read_bytes())
            path=root/'materials/round0/marketing/productPosition-round0.csv'
            path.write_text(path.read_text().replace('"3.7","2.1"','"3.8","2.1"'))
            result=source_audit(root)
            self.assertEqual(len(result['conflicts']),1)
            self.assertEqual(result['conflicts'][0]['column'],"GETCHELL'S")

    def test_each_of_sixteen_factors_has_complete_trace_and_counterevidence(self):
        rows=self.h['factors'];plan=self.data['team']['decisions']
        self.assertEqual({r['key'] for r in rows},set(plan))
        self.assertEqual(len(rows),16)
        self.assertEqual(len({r['cell'] for r in rows}),16)
        for r in rows:
            self.assertEqual(r['submitted'],plan[r['key']])
            self.assertEqual(r['cell'],self.data['team']['cells'][r['key']])
            for k in ('mechanism','observed','economics','boundary','evidence_level','sources'):
                self.assertTrue(r[k],(r['key'],k))
            self.assertIsNone(r['prior_input'])
        rows={r['key']:r for r in rows}
        self.assertEqual(rows['low_depth']['industry_round0']['average'],32)
        self.assertEqual(rows['high_depth']['industry_round0']['average'],24)
        self.assertIn('Documented mix',rows['high_private']['evidence_level'])
        self.assertIn('not measured sales share',rows['high_private']['economics'])

    def test_effective_markup_and_conditional_price_proxy_not_pricing_file_prices(self):
        low,high=self.h['offerings']
        for r in (low,high):
            self.assertAlmostEqual(r['current_effective_markup'],r['submitted_markup'],places=8)
            self.assertAlmostEqual(r['prior_price_proxy'],r['prior_cost']*(1+r['prior_effective_markup']))
            self.assertAlmostEqual(r['current_price_proxy'],r['current_cost']*(1+r['current_effective_markup']))
            self.assertNotEqual(r['current_price_proxy'],r['current_cost'])
        self.assertAlmostEqual(low['prior_effective_markup'],.54,places=8)
        self.assertAlmostEqual(high['prior_effective_markup'],.66,places=8)
        self.assertAlmostEqual(low['price_proxy_growth'],.0661545435)
        self.assertAlmostEqual(high['price_proxy_growth'],-.0312662551)
        self.assertIn('not observed transaction price',self.h['boundaries'][4])

    def test_peer_group_excludes_fair_value_and_preserves_share_denominators(self):
        self.assertEqual(self.h['actual_peer_count'],6)
        self.assertTrue(self.h['actual_peers_all_improved'])
        self.assertAlmostEqual(self.h['actual_peer_mean_change'],.4333333333)
        self.assertEqual(len(self.h['competitors']),7)
        self.assertNotIn('FAIR VALUE',{r['company'] for r in self.h['competitors']})
        self.assertAlmostEqual(sum(r['revenue_share'] for r in self.h['competitors']),1)
        self.assertEqual([r['current'] for r in self.h['reported_offering_shares']],[.108,.048])
        self.assertTrue(all(r['low_cost_growth']>0 and r['high_cost_growth']>0 for r in self.h['cost_comparison']))

    def test_commercial_counterevidence_and_liquidity_are_both_visible(self):
        f=self.h['financial']
        self.assertAlmostEqual(f['revenue_growth'],481_926_248/372_795_207-1)
        self.assertAlmostEqual(f['clv_growth'],1_023_100_726/818_472_768-1)
        self.assertEqual(f['cash_change'],-4_598_444)
        self.assertEqual(f['inventory_change'],12_221_849)
        self.assertEqual((f['inventory_days_prior'],f['inventory_days_current']),(90,81))
        self.assertGreater(f['margin_mix_effect_pp'],0)
        self.assertLess(f['margin_rate_effect_pp'],0)
        self.assertAlmostEqual(f['ten_day_stock_funding'],319_977_298/365*10)
        rows={r['key']:r for r in self.h['factors']}
        self.assertIn('100% → 100%',rows['vendor']['observed'])
        self.assertIn('100% → 100%',rows['analytics']['observed'])
        self.assertIn('Expenses rose',rows['service']['economics'])

    def test_segments_and_channels_show_growth_not_invented_lost_sales(self):
        segments=self.h['segments']
        self.assertTrue(all(r['growth']>0 for r in segments))
        self.assertTrue(all(r['current_clv'] is None for r in segments))
        self.assertTrue(all(r['historical_round0_clv']>0 for r in segments))
        s3=next(r for r in segments if r['id']=='SEGMENT 3')
        self.assertEqual(max(segments,key=lambda r:r['brand_weight'])['id'],'SEGMENT 3')
        self.assertAlmostEqual(s3['brand_weight'],.3/1.35)
        self.assertLess(s3['revenue_share'],s3['prior_revenue_share'])
        self.assertTrue(all(r['growth']>0 for r in self.h['channels']))
        self.assertIn('segment × offering × channel',self.h['boundaries'][2])

    def test_rebuild_is_deterministic_and_does_not_mutate_the_model(self):
        before=copy.deepcopy(self.data)
        self.assertEqual(build_holistic(self.data,ROOT),self.h)
        self.assertEqual(self.data,before)

    def test_written_report_covers_all_factors_sources_and_limits(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as tmp:
            path=Path(tmp)/'report.md';write_report(self.data,path);text=path.read_text()
        for r in self.h['factors']:
            self.assertIn('### '+r['label']+' — '+r['cell'],text)
        for r in self.h['source_audit']['materials']:self.assertIn(r['file'],text)
        for phrase in ('not a causal allocation',str(self.h['source_audit']['material_files'])+' supplied','segment × offering × channel','100% → 100%',
                       '$191.64','$375.39','conflicts: 0','not a measured dollar loss','SIMULATION_REVIEW.md'):
            self.assertIn(phrase,text)


if __name__=='__main__':unittest.main()
