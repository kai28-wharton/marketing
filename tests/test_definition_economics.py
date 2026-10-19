import copy
import itertools
import math
import unittest
from decision_economics import SCHEMA
from round_review import dataset, QUADRANTS
from review_model import evaluate, factor_probes
from review_optimizer import optimize


class DefinitionEconomicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=dataset(1);cls.plan=cls.data['team']['decisions']
        # Test scenarios only, not learned coefficients or recommended settings.
        cls.e=dict(quality_cost_per_point=.05,vendor_cost_sensitivity=.1,vendor_inventory_sensitivity=.2,
                   breadth_inventory_sensitivity=.8,depth_inventory_sensitivity=.4,
                    inventory_holding_rate=0,inventory_financing_rate=.08,new_capital_depreciation_rate=.1,
                    new_store_capex=1_750_000,closed_store_book_value=500_000,store_recovery_fraction=.7)

    def test_all_scenario_baselines_reproduce_actuals_and_zero_cash_change(self):
        for e in (None,self.e,dict(self.e,online_expense_fraction=.7,experience_expense_fraction=.3)):
            r=evaluate(self.plan,self.data,economics=e)
            self.assertEqual(r['net_income'],8_399_905)
            self.assertEqual(r['revenue'],481_926_248)
            self.assertEqual(r['incremental_cash_delta'],0)
            self.assertEqual(r['capitalized_spending_change'],0)
            self.assertFalse(r['unresolved_economics'])

    def test_quality_increases_unit_cost_and_selling_price_at_unchanged_markup(self):
        p=dict(self.plan,private_quality=7,national_quality=7)
        r=evaluate(p,self.data,{'score_response':0,'price_elasticity':0},self.e)
        factor=math.exp(.05)
        for tier,label in [('low','Lower Cost'),('high','Higher Cost')]:
            o=r['offerings'][tier]
            self.assertAlmostEqual(o['unit_cost_ratio'],factor)
            self.assertAlmostEqual(o['price_ratio'],factor)
            self.assertAlmostEqual(o['cogs'],self.data['rounds']['1']['income'][label+' COGS']*factor)
        self.assertNotIn('quality_cost_per_point',r['unresolved_economics'])

    def test_markup_is_on_cost_and_does_not_change_unit_cost(self):
        r=evaluate(dict(self.plan,low_markup=55),self.data,{'score_response':0,'price_elasticity':0},self.e)
        self.assertAlmostEqual(r['offerings']['low']['price_ratio'],1.55/1.5)
        self.assertEqual(r['offerings']['low']['unit_cost_ratio'],1)
        self.assertEqual(r['offerings']['low']['unit_ratio'],1)

    def test_breadth_stock_is_not_immediately_charged_as_cogs(self):
        r=evaluate(dict(self.plan,low_breadth=83),self.data,{'score_response':0},self.e)
        i=self.data['rounds']['1']['income'];b=self.data['rounds']['1']['balance']
        expected=b['Inventory']*i['Lower Cost COGS']/i['Cost of Goods Sold']*(math.exp(.8*.05)-1)
        self.assertAlmostEqual(r['inventory_change'],expected,places=6)
        self.assertEqual(r['cogs'],i['Cost of Goods Sold'])
        self.assertEqual(r['holding_expense_change'],0)
        self.assertAlmostEqual(r['financing_expense_change'],expected*.08)
        self.assertAlmostEqual(r['profit_delta'],-expected*.08*(1-r['tax_rate']),places=6)
        self.assertAlmostEqual(r['incremental_cash_delta'],r['profit_delta']-expected,places=6)

    def test_online_and_experience_capitalization_not_double_expensed(self):
        for key,fraction in [('online',.4),('experience',.8)]:
            r=evaluate(dict(self.plan,**{key:self.plan[key]+1_000_000}),self.data,{'score_response':0},self.e)
            capital=(1-fraction)*1_000_000
            dep=capital*.1
            self.assertAlmostEqual(r['capitalized_spending_change'],capital)
            self.assertAlmostEqual(r['depreciation_change'],dep)
            self.assertAlmostEqual(r['operating_expenses']-self.data['rounds']['1']['income']['Operating Expenses'],1_000_000*fraction+dep)
            expected=-(1_000_000*fraction+dep)*(1-r['tax_rate'])+dep-capital
            self.assertAlmostEqual(r['incremental_cash_delta'],expected,places=6)

    def test_analytics_is_fully_expensed(self):
        r=evaluate(dict(self.plan,analytics=self.plan['analytics']+1_000_000),self.data,{'score_response':0},self.e)
        self.assertEqual(r['capitalized_spending_change'],0)
        self.assertAlmostEqual(r['operating_expenses']-self.data['rounds']['1']['income']['Operating Expenses'],1_000_000)

    def test_vendor_affects_product_cost_and_inventory_separately_from_kahn(self):
        r=evaluate(dict(self.plan,vendor=self.plan['vendor']+1_000_000),self.data,{'score_response':0,'price_elasticity':0},self.e)
        self.assertEqual(r['scores'],self.data['rounds']['1']['scores'])
        self.assertLess(r['offerings']['low']['unit_cost_ratio'],1)
        self.assertLess(r['offerings']['low']['price_ratio'],1)
        self.assertLess(r['inventory_change'],0)
        self.assertLess(r['cogs'],self.data['rounds']['1']['income']['Cost of Goods Sold'])

    def test_store_opening_and_closing_cash_and_writeoff(self):
        r=evaluate(dict(self.plan,coverage=201),self.data,{'score_response':0},self.e)
        self.assertEqual(r['store_opening_capex'],1_750_000)
        self.assertEqual(r['capitalized_spending_change'],1_750_000)
        self.assertEqual(r['depreciation_change'],175_000)
        r=evaluate(dict(self.plan,coverage=199),self.data,{'score_response':0},self.e)
        self.assertEqual(r['disposal_proceeds'],350_000)
        self.assertEqual(r['closure_writeoff'],150_000)
        self.assertAlmostEqual(r['incremental_cash_delta'],r['profit_delta']+150_000+350_000)
        with self.assertRaises(ValueError):evaluate(dict(self.plan,coverage=200.5),self.data)

    def test_unknown_is_not_silently_zero_and_private_mix_response_is_unknown(self):
        r=evaluate(dict(self.plan,private_quality=7),self.data)
        self.assertIn('quality_cost_per_point',r['unresolved_economics'])
        r=evaluate(dict(self.plan,high_private=80),self.data,economics=self.e)
        self.assertIn('high_private_mix_response',r['unresolved_economics'])
        self.assertTrue(all('empty' not in p['definition_status'] for p in factor_probes(self.data)))

    def test_input_validation_no_nan_bool_unknown_or_invalid_fraction(self):
        for e in ({'x':1},{'quality_cost_per_point':math.nan},{'inventory_holding_rate':True},
                  {'online_expense_fraction':1.1},{'online_expense_fraction':None},{'vendor_cost_sensitivity':-1}):
            with self.assertRaises(ValueError):evaluate(self.plan,self.data,economics=e)

    def payload(self,**changes):
        p=dict(decisions=self.plan,economics=self.e,budget=71_000_000,max_cash_use=2_000_000,
               ranges={'online':[6_000_000,7_000_000],'experience':[12_500_000,13_500_000]},step=500_000,
               score_floors={q:0 for q in QUADRANTS})
        p.update(changes);return p

    def test_optimizer_matches_independent_brute_force_and_constraints(self):
        p=self.payload();before=copy.deepcopy(p)
        out=optimize(p,self.data)
        values=[]
        for online,experience in itertools.product((6_000_000,6_500_000,7_000_000),(12_500_000,13_000_000,13_500_000)):
            r=evaluate(dict(self.plan,online=online,experience=experience),self.data,economics=self.e)
            if r['explicit_spend']<=p['budget'] and -r['incremental_cash_delta']<=p['max_cash_use']:
                values.append(r['net_income'])
        self.assertEqual(out['status'],'verified_grid')
        self.assertEqual(out['checked'],9)
        self.assertAlmostEqual(out['objective_value'],max(values))
        self.assertEqual(out['feasible'],len(values))
        self.assertEqual(p,before)
        self.assertEqual(optimize(p,self.data),out)
        for k in self.plan:
            if k not in p['ranges']:self.assertEqual(out['result']['decisions'][k],self.plan[k])
        self.assertFalse(out['validation']['predictive_accuracy_established'])

    def test_optimizer_refuses_unspecified_pathways_across_whole_domain(self):
        out=optimize(self.payload(economics={}),self.data)
        self.assertEqual(out['status'],'blocked')
        self.assertIsNone(out['result'])
        self.assertIn('new_capital_depreciation_rate',out['missing_assumptions'])
        out=optimize(self.payload(ranges={'vendor':[26_500_000,27_500_000]},economics={}),self.data)
        self.assertIn('vendor_cost_sensitivity',out['missing_assumptions'])
        p=dict(self.plan,low_private=50)
        out=optimize(self.payload(decisions=p),self.data)
        self.assertIn('low_private_mix_response',out['missing_assumptions'])

    def test_budget_cash_and_score_constraints_are_enforced(self):
        self.assertEqual(optimize(self.payload(budget=0),self.data)['status'],'infeasible')
        out=optimize(self.payload(max_cash_use=0,score_floors={q:10 for q in QUADRANTS}),self.data)
        self.assertEqual(out['status'],'infeasible')
        out=optimize(self.payload(max_cash_use=0),self.data)
        self.assertLessEqual(-out['result']['incremental_cash_delta'],1e-6)
        out=optimize(self.payload(score_floors={}),self.data)
        self.assertTrue(all(out['result']['scores'][q]>=self.data['rounds']['1']['scores'][q]-1e-9 for q in QUADRANTS))

    def test_optimizer_validates_bounds_grid_size_budget_cash_and_objective(self):
        for changes in ({'budget':None},{'max_cash_use':None},{'step':0},{'objective':'magic'},
                        {'ranges':{'coverage':[200,225]}},{'ranges':{'online':[7e6,6e6]}},
                        {'ranges':{'online':[0,69_814_000]},'step':1},
                        {'ranges':{'online':[6_000_000,6_750_000]},'step':500_000},
                        {'ranges':{'online':[True,1]}},{'score_floors':{'x':1}}):
            with self.assertRaises(ValueError):optimize(self.payload(**changes),self.data)

    def test_market_value_objective_is_not_a_profit_or_pe_proxy(self):
        b=optimize(self.payload(objective='market_value'),self.data)
        self.assertEqual(b['status'],'blocked')
        self.assertIsNone(b['result'])
        self.assertIn('dcf_forecast_and_terminal_rules',b['missing_assumptions'])


if __name__=='__main__':unittest.main()
