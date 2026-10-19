import math
import random
import unittest
import app
from prediction import DRIVERS, QUADRANTS, VERSION


class PredictionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = app.load_data()
        cls.base = app.evaluate(app.BASE, data=cls.data)

    def evaluate(self, changes=None, detailed=True, **kwargs):
        return app.evaluate(dict(app.BASE, **(changes or {})), data=self.data, detailed=detailed, **kwargs)

    def test_anchor_and_zero_strength(self):
        for q in QUADRANTS:
            self.assertEqual(self.base['scores'][q], next(r['value'] for r in self.data['kahn'] if r['company']=="GETCHELL'S" and r['quadrant']==q and r['round']==0))
        changed = self.evaluate({'online':10e6, 'coverage':500}, assumptions={'score_response':0})
        self.assertEqual(changed['scores'], self.base['scores'])
        self.assertEqual(changed['model_version'], VERSION)

    def test_attribution_reconciles_including_interactions(self):
        result = self.evaluate({'online':5e6, 'analytics':12e6, 'service':18e6, 'experience':14e6,
                                'vendor':25e6, 'coverage':300, 'national_quality':7, 'low_markup':60})
        rows = result['kahn']['attribution']
        self.assertEqual(len(rows), 7)
        for q in QUADRANTS:
            self.assertAlmostEqual(sum(r['contributions'][q] for r in rows), result['scores'][q]-self.base['scores'][q], places=11)
        for row in self.base['kahn']['attribution']:
            self.assertTrue(all(abs(v)<1e-12 for v in row['contributions'].values()))

    def test_monotonic_spending_at_fixed_coverage(self):
        for key in DRIVERS:
            if key == 'coverage':
                continue
            previous = None
            for scale in [0, .5, 1, 1.5, 2]:
                result = self.evaluate({key:min(app.BUDGET, app.BASE[key]*scale)}, detailed=False)
                if previous:
                    for q in QUADRANTS:
                        self.assertGreaterEqual(result['scores'][q]+1e-12, previous[q], (key,q))
                previous = result['scores']

    def test_diminishing_marginal_returns(self):
        for key, q in [('online','FRICTIONLESS'), ('service','EXPERIENCE'), ('experience','EXPERIENCE')]:
            low = self.evaluate({key:app.BASE[key]}, detailed=False)['scores'][q]
            low_plus = self.evaluate({key:app.BASE[key]+1e6}, detailed=False)['scores'][q]
            high = self.evaluate({key:app.BASE[key]+10e6}, detailed=False)['scores'][q]
            high_plus = self.evaluate({key:app.BASE[key]+11e6}, detailed=False)['scores'][q]
            self.assertGreater(low_plus-low, high_plus-high, key)

    def test_saturated_operating_scores_preserve_downside(self):
        for key, q in [('vendor','BRAND'), ('analytics','FRICTIONLESS')]:
            gain = self.evaluate({key:app.BASE[key]+1e6}, detailed=False)['scores'][q]-self.base['scores'][q]
            loss = self.base['scores'][q]-self.evaluate({key:app.BASE[key]-1e6}, detailed=False)['scores'][q]
            self.assertGreater(gain, 0)
            self.assertGreater(loss, gain*3)

    def test_coverage_dilution_and_zero_store_edge(self):
        expanded = self.evaluate({'coverage':300})
        self.assertLess(expanded['scores']['EXPERIENCE'], self.base['scores']['EXPERIENCE'])
        funded = self.evaluate({'coverage':300, 'service':22.5e6, 'experience':15e6})
        self.assertGreater(funded['scores']['EXPERIENCE'], expanded['scores']['EXPERIENCE'])
        self.assertEqual(expanded['spent'], self.base['spent'])
        self.assertIn('Retail Coverage', expanded['unpriced_changes'])
        zero = self.evaluate({'coverage':0})
        self.assertTrue(all(math.isfinite(v) for v in zero['scores'].values()))
        self.assertLess(zero['scores']['EXPERIENCE'], self.base['scores']['EXPERIENCE'])

    def test_online_analytics_complementarity(self):
        base = self.base['scores']['FRICTIONLESS']
        online = self.evaluate({'online':5e6}, detailed=False)['scores']['FRICTIONLESS']
        analytics = self.evaluate({'analytics':15e6}, detailed=False)['scores']['FRICTIONLESS']
        both = self.evaluate({'online':5e6, 'analytics':15e6}, detailed=False)['scores']['FRICTIONLESS']
        self.assertGreater(both-base, (online-base)+(analytics-base))

    def test_stress_envelopes_and_evidence_labels(self):
        model = self.evaluate({'online':10e6, 'coverage':500})['kahn']
        for q in QUADRANTS:
            lo, hi = model['intervals'][q]
            self.assertLessEqual(lo, model['scores'][q])
            self.assertGreaterEqual(hi, model['scores'][q])
            self.assertTrue(0 <= lo <= hi <= 10)
            self.assertLessEqual(model['ranks'][q]['best'], model['ranks'][q]['point'])
            self.assertGreaterEqual(model['ranks'][q]['worst'], model['ranks'][q]['point'])
        self.assertEqual(model['evidence']['paired_decision_outcome_rounds'], 0)
        self.assertFalse(model['evidence']['causal_calibration'])
        self.assertIn('Not a confidence interval', model['interval_method'])

    def test_sensitivities_match_direct_calculation(self):
        for row in self.base['kahn']['sensitivities']:
            for direction, sign in [('increase',1), ('decrease',-1)]:
                expected = self.evaluate({row['key']:app.BASE[row['key']]+sign*row['step']}, detailed=False)
                for q in QUADRANTS:
                    self.assertAlmostEqual(row[direction]['score_changes'][q], expected['scores'][q]-self.base['scores'][q])
        zero = self.evaluate({'online':0})
        self.assertIsNone(next(r for r in zero['kahn']['sensitivities'] if r['key']=='online')['decrease'])

    def test_random_domain_bounds_and_detailed_fast_parity(self):
        rng = random.Random(903)
        for _ in range(30):
            plan = {f[0]:rng.uniform(f[3],f[4]) for f in app.FACTORS}
            fast = app.evaluate(plan,data=self.data,detailed=False)
            full = app.evaluate(plan,data=self.data)
            self.assertEqual(full['scores'], fast['scores'])
            self.assertTrue(all(math.isfinite(v) and 0<=v<=10 for v in full['scores'].values()))
            for q in QUADRANTS:
                self.assertAlmostEqual(sum(r['contributions'][q] for r in full['kahn']['attribution']), full['scores'][q]-self.base['scores'][q], places=10)

    def test_extrapolation_and_optimizer_final_model(self):
        model = self.evaluate({'online':0})['kahn']
        self.assertIn('online', [r['key'] for r in model['extrapolations']])
        optimized = app.optimize({'decisions':app.BASE})['result']
        self.assertIn('attribution', optimized['kahn'])
        self.assertEqual(optimized['model_version'], VERSION)
        self.assertTrue(optimized['feasible'])


if __name__ == '__main__':
    unittest.main()
