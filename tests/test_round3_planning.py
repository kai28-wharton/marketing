import copy
import unittest

from app import validate
from round_review import dataset
from round3_planning import ROUND3_BUDGET, SPENDING, build_round3_planning


class Round3DecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = dataset(2)

    def test_all_16_values_and_budget_reconcile(self):
        p = self.data['round3_decision']
        self.assertEqual(len(p['recommendations']), 16)
        self.assertEqual(set(p['decisions']), set(self.data['team']['decisions']))
        validate(p['decisions'])
        self.assertEqual(p['budget'], 74_631_166)
        self.assertEqual(p['spend'], sum(p['decisions'][k] for k in SPENDING))
        self.assertEqual(p['spend'], 74_000_000)
        self.assertEqual(p['reserve'], 631_166)
        self.assertEqual(p['spend'] + p['reserve'], ROUND3_BUDGET)
        for r in p['recommendations']:
            self.assertEqual(r['change'], r['proposed'] - r['current'])
            self.assertTrue(all(r[k] for k in ('why', 'arithmetic', 'gate', 'citation')))

    def test_financial_gates_and_alternatives_are_not_certified_forecasts(self):
        p = self.data['round3_decision']
        self.assertEqual(p['decisions']['coverage'], 236)
        self.assertEqual(p['fallback']['high_depth'], 10)
        self.assertEqual(p['decisions']['high_depth'], 15)
        self.assertEqual(p['finance']['capital_delta'], 2_000_000)
        self.assertTrue(all(not g['goal_verified'] for g in p['goals']))
        self.assertIsNone(next(g for g in p['goals'] if g['quadrant'] == 'BRAND')['diagnostic'])
        self.assertTrue(p['unresolved'])
        for a in p['alternatives']:
            self.assertEqual(a['spend'], sum(a[k] for k in SPENDING))
            self.assertEqual(a['spend'] + a['reserve'], ROUND3_BUDGET)
            self.assertGreaterEqual(a['reserve'], 0)
        for s in p['stores']:
            if s['change'] < 0:
                self.assertIsNone(s['closure_proceeds'])
            if s['change'] > 0:
                self.assertLess(s['conservative_headroom'], 0)

    def test_builder_does_not_mutate_evidence_or_submitted_plan(self):
        d = copy.deepcopy(self.data)
        before = copy.deepcopy(d)
        build_round3_planning(d)
        self.assertEqual(d, before)
        d['planning_round'] = 4
        with self.assertRaises(ValueError):
            build_round3_planning(d)

    def test_product_holds_have_two_sided_challenges_not_optimality_claims(self):
        p = self.data['round3_decision']
        self.assertEqual(p['hold_summary']['held'], 9)
        self.assertEqual(len(p['product_challenges']), 10)
        for row in p['product_challenges']:
            values = [c['value'] for c in row['candidates']]
            self.assertLess(min(values), row['baseline'])
            self.assertGreater(max(values), row['baseline'])
            self.assertEqual(sum(c['selected'] for c in row['candidates']), 1)
            self.assertTrue(row['criterion'])
            for c in row['candidates']:
                trial = dict(p['decisions'], **{row['key']: c['value']})
                validate(trial)
        low = next(r for r in p['product_challenges'] if r['key'] == 'low_markup')
        cut = next(c for c in low['candidates'] if c['value'] == 48)
        self.assertAlmostEqual(cut['unit_change_break_even'], 50 / 48 - 1)

    def test_openings_are_compared_after_reallocation_and_closures_have_no_fake_savings(self):
        p = self.data['round3_decision']
        self.assertEqual({s['change'] for s in p['store_packages']}, {-10, -5, 0, 1, 5})
        for s in p['store_packages']:
            validate(s['decisions'])
            self.assertEqual(s['spend'], sum(s['decisions'][k] for k in SPENDING))
            self.assertEqual(s['capital_inclusive_total'], s['spend'] + s['opening_capex'])
            self.assertEqual(s['capital_inclusive_total'] + s['reserve'], ROUND3_BUDGET)
            self.assertGreaterEqual(s['reserve'], 0)
            self.assertIsNone(s['net_cash_feasible'])
            self.assertAlmostEqual(s['service_per_store'], s['decisions']['service'] / s['stores'])
            if s['change'] < 0:
                self.assertIsNone(s['closure_proceeds'])
                self.assertIsNone(s['closure_exit_cost'])
                self.assertEqual(s['spend'], p['spend'])
            if s['change'] > 0:
                self.assertEqual(s['opening_capex'], s['change'] * 1_750_000)
                self.assertLess(s['spend'], p['spend'])
