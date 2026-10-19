import copy
import math
import unittest
import app
from forecast import project, DEFAULT_PLANNING


class ForecastTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=app.load_data()
        cls.plan=dict(app.BASE, online=2_500_000, service=15_300_000, experience=10_200_000)

    def project(self, plan=None, **planning):
        return project({'decisions':self.plan if plan is None else plan, 'planning':planning},
                       self.data, app.BASE, app.evaluate)

    def test_default_year1_matches_existing_engine(self):
        report=self.project()['working']
        expected=app.evaluate(self.plan)
        first=report['periods'][1]
        self.assertAlmostEqual(first['revenue'], expected['revenue'])
        self.assertAlmostEqual(first['net_income'], expected['net_income'])
        self.assertEqual(first['scores'], expected['scores'])
        self.assertEqual(first['explicit_spend'],68_000_000)
        self.assertEqual(first['remaining'],1_814_000)

    def test_no_double_counting_of_score_uplift_or_expenses(self):
        report=self.project()['working']
        first,second=report['periods'][1:]
        for key in ['scores','revenue','net_income','operating_expenses','explicit_spend']:
            self.assertEqual(first[key],second[key],key)
        self.assertAlmostEqual(report['cumulative_projected_net_income'],first['net_income']+second['net_income'])
        baseline=app.evaluate(app.BASE)
        self.assertAlmostEqual(first['operating_expenses'],111_160_439+1_000_000)
        unchanged=self.project(app.BASE)['working']['periods']
        self.assertAlmostEqual(unchanged[2]['net_income'],baseline['net_income'])

    def test_delayed_realization_and_recurring_full_cost(self):
        report=self.project(year1_realization=.5,year2_catchup=.5)['working']
        actual,first,second=report['periods']
        target=app.evaluate(self.plan)
        self.assertEqual(first['realization'],.5)
        self.assertEqual(second['realization'],.75)
        for q in actual['scores']:
            self.assertAlmostEqual(first['scores'][q],actual['scores'][q]+.5*(target['scores'][q]-actual['scores'][q]))
            self.assertAlmostEqual(second['scores'][q],actual['scores'][q]+.75*(target['scores'][q]-actual['scores'][q]))
        self.assertEqual(first['operating_expenses'],second['operating_expenses'])
        self.assertGreater(second['net_income'],first['net_income'])

    def test_exogenous_growth_and_unit_cost_inflation(self):
        flat=self.project()['working']['periods']
        changed=self.project(market_growth=.03,cogs_inflation=.04)['working']['periods']
        for year in (1,2):
            self.assertAlmostEqual(changed[year]['revenue'],flat[year]['revenue']*1.03**year,places=5)
            self.assertAlmostEqual(changed[year]['cogs'],flat[year]['cogs']*1.03**year*1.04**year,places=5)
            self.assertEqual(changed[year]['scores'],flat[year]['scores'])
        self.assertEqual(changed[1]['operating_expenses'],changed[2]['operating_expenses'])

    def test_alternatives_and_unpriced_brand_costs(self):
        output=self.project()
        self.assertEqual([p['key'] for p in output['comparisons']],['reference','controlled','brand'])
        brand=output['comparisons'][2]
        self.assertIn('National Brand Quality',brand['unpriced_changes'])
        self.assertEqual(brand['periods'][2]['explicit_spend'],68_000_000)
        self.assertGreater(brand['periods'][2]['scores']['BRAND'],output['comparisons'][1]['periods'][2]['scores']['BRAND'])

    def test_accounting_reconciliation_and_stress_bounds(self):
        for settings in [{},{'year1_realization':0,'year2_catchup':0},
                         {'market_growth':-.2,'cogs_inflation':.3,'year1_realization':.2,'year2_catchup':1}]:
            report=self.project(**settings)['working']
            for row in report['periods']:
                self.assertAlmostEqual(row['gross_profit'],row['revenue']-row['cogs'])
                self.assertAlmostEqual(row['ebit'],row['gross_profit']-row['operating_expenses'])
                self.assertAlmostEqual(row['net_income'],row['ebit']-row['interest']-row['taxes'])
                if row['year']:
                    for q,(lo,hi) in row['score_ranges'].items():
                        self.assertTrue(0<=lo<=row['scores'][q]<=hi<=10)
                    self.assertLessEqual(row['profit_range'][0],row['net_income'])
                    self.assertGreaterEqual(row['profit_range'][1],row['net_income'])
            self.assertNotIn('cash',report['periods'][2])

    def test_overspend_and_validation(self):
        report=self.project(dict(self.plan,online=10_000_000))['working']
        self.assertFalse(report['feasible'])
        self.assertLess(report['periods'][2]['remaining'],0)
        for settings in [{'market_growth':.3},{'cogs_inflation':math.nan},
                         {'year1_realization':True},{'year2_catchup':1.01},{'unknown':1}]:
            with self.assertRaises(ValueError):
                self.project(**settings)
        with self.assertRaises(ValueError):
            self.project({})

    def test_no_mutation_and_shared_assumptions(self):
        before=copy.deepcopy(self.plan)
        output=project({'decisions':self.plan,'assumptions':{'score_response':0}},self.data,app.BASE,app.evaluate)
        self.assertEqual(self.plan,before)
        self.assertEqual(DEFAULT_PLANNING['market_growth'],0)
        for scenario in [output['working'],*output['comparisons']]:
            self.assertEqual(scenario['assumptions']['score_response'],0)
            self.assertEqual(scenario['periods'][2]['scores'],scenario['periods'][0]['scores'])


if __name__=='__main__':
    unittest.main()
