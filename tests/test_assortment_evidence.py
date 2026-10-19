import unittest
import app
from assortment_evidence import build_readiness,LIMITATIONS


class AssortmentEvidenceTests(unittest.TestCase):
    def test_existing_financial_anchors_are_sourced_not_cost_estimates(self):
        readiness=build_readiness(app.load_data())
        facts={row['label']:row for row in readiness['known_data']}
        self.assertEqual(facts['Inventory']['value'],58_651_343)
        self.assertEqual(facts['Cash']['value'],28_845_507)
        self.assertEqual(facts['Days of inventory']['value'],90)
        self.assertEqual(facts['WACC']['value'],7.8)
        self.assertTrue(all(row['source'].startswith('materials/') for row in facts.values()))
        self.assertIn('not a verified inventory carrying rate',readiness['capital_note'])
        self.assertIn('not tell us how',readiness['inventory_note'])

    def test_readiness_distinguishes_existing_data_from_critical_gaps(self):
        readiness=build_readiness(app.load_data())
        rows=readiness['requirements']
        self.assertEqual(len(rows),8)
        self.assertEqual(sum(r['status']=='Missing' for r in rows),3)
        self.assertTrue(any(r['topic']=='Segment demand and Kahn response' and r['status']=='Partial' for r in rows))
        self.assertTrue(any(r['status']=='Available' for r in rows))
        self.assertTrue(any(r['status']=='Team decision' for r in rows))
        self.assertTrue(all(r['need'] and r['where'] and r['why'] for r in rows))
        self.assertIn('Not ready',readiness['status'])
        self.assertTrue(any('maximize profit' in step for step in readiness['balance_steps']))
        self.assertTrue(any('cash' in step and 'inventory' in step for step in readiness['balance_steps']))

    def test_recommendation_evidence_is_derived_from_round0_financials(self):
        evidence=build_readiness(app.load_data())['recommendation_evidence']
        self.assertAlmostEqual(evidence['low_revenue_share'],283_086_216/372_795_207)
        self.assertAlmostEqual(evidence['low_gross_margin'],(283_086_216-183_822_218)/283_086_216)
        self.assertAlmostEqual(evidence['high_gross_margin'],(89_708_991-54_041_561)/89_708_991)
        self.assertEqual(evidence['source'],'materials/incomeStatement-round0.csv')

    def test_limitations_include_monotonic_model_and_accounting_cautions(self):
        text=' '.join(LIMITATIONS)
        for phrase in ('mechanically improve','same per-index','not automatically an immediate expense',
                       'zero paired','not statistical confidence intervals','increase in COGS is green'):
            self.assertIn(phrase,text)
        self.assertEqual(app.load_data()['assortment_readiness']['limitations'][:len(LIMITATIONS)],LIMITATIONS)
