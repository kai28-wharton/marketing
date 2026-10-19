import copy
import unittest
import app
from assistant import answer


class AssistantTests(unittest.TestCase):
    def setUp(self):
        self.data = app.load_data()

    def ask(self, question, **kwargs):
        return answer(dict(question=question, decisions=app.BASE, **kwargs), self.data, app.evaluate)

    def text(self, response):
        return '\n'.join(s['text'] for s in response['sections'])

    def test_finance_grounded_and_cited(self):
        response = self.ask('Why are we making a loss?')
        self.assertEqual(response['context'], 'finance')
        self.assertIn('−$6,289,333', self.text(response))
        self.assertIn('$30,060,322', self.text(response))
        self.assertIn('materials/incomeStatement-round0.csv', response['sections'][0]['sources'])

    def test_budget_uses_current_plan_not_just_reference(self):
        p = dict(app.BASE, online=3_000_000)
        response = answer({'question': 'How much budget is remaining?', 'decisions': p}, self.data, app.evaluate)
        self.assertIn('$1,814,000', self.text(response))
        self.assertIn('$68,000,000', self.text(response))
        self.assertEqual(response['context'], 'budget')

    def test_kahn_and_named_competitor(self):
        response = self.ask('Compare Getchell’s with Cadabra')
        text = self.text(response)
        self.assertIn('Brand: 6.3, rank #1', text)
        self.assertIn('CADABRA: Experience 3.1, Frictionless 7.8', text)
        self.assertIn('customer experience / reduce pain', text)

    def test_one_factor_whatif_does_not_mutate(self):
        before = copy.deepcopy(app.BASE)
        response = self.ask('What if online investment were $5M?')
        self.assertEqual(response['context'], 'projection')
        self.assertEqual(response['sections'][0]['kind'], 'Illustrative estimate')
        self.assertIn('OVER BUDGET', self.text(response))
        self.assertIn('$70,000,000', self.text(response))
        self.assertIn('working plan unchanged', self.text(response))
        self.assertEqual(app.BASE, before)

    def test_refuse_ambiguous_and_invalid_tests(self):
        for question in ['What if online and customer service were $5M?', 'Increase online investment by $1M']:
            self.assertIn('one explicit target', self.ask(question)['sections'][0]['title'])
        response = self.ask('What if private brand quality were 15?')
        self.assertIn('outside the planning bounds', response['sections'][0]['title'])

    def test_unsupported_and_empty_background(self):
        response = self.ask('What is the weather in Tokyo?')
        self.assertEqual(response['context'], 'unsupported')
        self.assertIn('rule-based', self.text(response))
        response = self.ask('Which sources and background are available?')
        import app
        context=app.load_data()['documents']['company']
        self.assertIn('company.md: '+(context[:80] if context else 'empty'), self.text(response))

    def test_guide_followup_and_assumptions(self):
        response = self.ask('Walk me through the entire app')
        self.assertEqual(response['context'], 'guide')
        self.assertIn('Decision studio', self.text(response))
        self.assertEqual(self.ask('Tell me more', context='budget')['context'], 'budget')
        response = self.ask('Explain price elasticity assumptions', assumptions={'price_elasticity': 2})
        self.assertIn('Price elasticity: 2', self.text(response))

    def test_exact_scorecard_metric_and_definition(self):
        response = self.ask('What does asset turnover mean?')
        self.assertIn('Asset Turnover: 0.4', self.text(response))
        self.assertIn('period/average-asset convention is unknown', self.text(response))

    def test_validation(self):
        for question in ['', ' ' * 10, 42, 'x' * 2001]:
            with self.assertRaises(ValueError):
                self.ask(question)
        with self.assertRaises(ValueError):
            self.ask('Why?', context='invalid')

    def test_year2_guide_does_not_invent_draft_access(self):
        response=self.ask('Explain the Year 2 projection')
        self.assertEqual(response['context'],'year2')
        self.assertEqual(response['sections'][0]['page'],'whatif')
        self.assertIn('I do not see the separate what-if draft',self.text(response))
        self.assertIn('75%',self.text(response))

    def test_marketing_answer_uses_source_profiles_without_inventing_penetration(self):
        response=self.ask('Which customer preferences matter to segment 2?')
        self.assertEqual(response['context'],'marketing')
        self.assertIn('BREADTH 0.38',self.text(response))
        self.assertIn('not whole-market revenue',self.text(response))
        self.assertIn('penetration cannot be computed',self.text(response))
        self.assertEqual(response['sections'][0]['page'],'marketing')


if __name__ == '__main__':
    unittest.main()
