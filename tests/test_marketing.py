import tempfile
import unittest
from pathlib import Path
import app
from marketing import load_marketing,assortment_alignment


class MarketingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=app.load_data();cls.m=cls.data['marketing']

    def test_all_sources_and_segment_columns_are_preserved(self):
        self.assertTrue(self.m['available'])
        self.assertEqual(len(self.m['raw_tables']),9)
        self.assertEqual(len(self.m['sources']),9)
        self.assertEqual(len(self.m['segments']),6)
        segments={s['id']:s for s in self.m['segments']}
        self.assertEqual(segments['SEGMENT 1']['size'],2_866_451)
        self.assertEqual(segments['SEGMENT 6']['size'],2_599_520)
        self.assertEqual(segments['SEGMENT 1']['revenue'],64_993_892)
        self.assertEqual(segments['SEGMENT 6']['clv'],146_313_071)
        self.assertEqual([r['round'] for r in segments['SEGMENT 2']['history']],[-2,-1,0])

    def test_scope_reconciliation_and_rounding_are_explicit(self):
        self.assertEqual(self.m['totals']['segment_revenue'],372_795_207)
        self.assertEqual(self.m['totals']['segment_clv'],818_472_769)
        self.assertEqual(self.m['checks'][0]['difference'],0)
        self.assertEqual(self.m['checks'][1]['difference'],1)
        self.assertAlmostEqual(self.m['totals']['reported_share_sum'],1.002)
        self.assertIn('not whole-market revenue',self.m['checks'][0]['meaning'])
        self.assertTrue(any('penetration' in n and 'without buyer counts' in n for n in self.m['notes']))

    def test_preferences_are_raw_and_normalization_is_separate(self):
        segments={s['id']:s for s in self.m['segments']}
        self.assertAlmostEqual(segments['SEGMENT 2']['preference_sum'],1.64)
        self.assertEqual(segments['SEGMENT 2']['preferences']['BREADTH'],.38)
        self.assertEqual(segments['SEGMENT 6']['preferences']['DEPTH'],.02)
        self.assertEqual(segments['SEGMENT 5']['preferences']['SHOPPING EXPERIENCE'],.43)
        for s in segments.values():
            self.assertAlmostEqual(sum(s['normalized_preferences'].values()),1)
            self.assertEqual(len(s['preferences']),8)

    def test_share_denominators_and_ambiguous_pricing(self):
        own=self.m['own_company']
        self.assertEqual(self.m['reported_company_revenue_total'],2_751_577_551)
        self.assertAlmostEqual(own['derived_low_offering_share'],283_086_216/1_924_684_695)
        self.assertAlmostEqual(own['derived_high_offering_share'],89_708_991/826_892_856)
        self.assertEqual(own['reported_low_all_market_share'],.103)
        self.assertEqual(own['reported_high_all_market_share'],.033)
        self.assertTrue(self.m['pricing_cost_match'])
        self.assertEqual(own['reported_pricing']['low'],116.72)
        self.assertEqual(own['online'],191_374_614)
        self.assertEqual(own['store'],181_420_593)

    def test_product_positions_do_not_replace_kahn_scores(self):
        positions={p['attribute']:p for p in self.m['positions']}
        self.assertEqual(len(positions),12)
        self.assertEqual(positions['LOWER COST DEPTH']['rank_numeric'],1)
        self.assertEqual(positions['HIGHER COST DEPTH']['own'],5)
        self.assertEqual(positions['CUSTOMER SERVICE']['own'],3.4)
        result=app.evaluate(app.BASE,data=self.data)
        self.assertEqual(result['scores']['EXPERIENCE'],5.8)
        self.assertEqual(result['scores']['FRICTIONLESS'],3.4)
        self.assertEqual(result['revenue'],372_795_207)

    def test_preference_alignment_is_only_a_diagnostic(self):
        base=app.BASE;candidate=dict(base,low_breadth=60)
        no_change=assortment_alignment(self.m,base,base)
        self.assertTrue(all(r['alignment_change_pp']==0 for r in no_change['rows']))
        output=assortment_alignment(self.m,base,candidate)
        rows={r['segment']:r for r in output['rows']}
        self.assertGreater(rows['SEGMENT 2']['breadth_change_pp'],rows['SEGMENT 3']['breadth_change_pp'])
        for basis,value in output['weighted_changes_pp'].items():
            self.assertAlmostEqual(value,sum(r['alignment_change_pp']*r[basis+'_share'] for r in output['rows']))
        self.assertIn('not a predicted Kahn',output['warning'])
        self.assertIn('Equal offering exposure',output['method'])
        self.assertFalse(assortment_alignment({'available':False},base,candidate)['available'])

    def test_missing_or_incomplete_marketing_set_is_not_silently_invented(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(load_marketing(directory,self.data)['available'])
            folder=Path(directory)/'materials'/'marketing';folder.mkdir(parents=True)
            (folder/'marketCLV-round0.csv').write_text('ROUND\n0\n')
            self.assertFalse(load_marketing(directory,self.data)['available'])
