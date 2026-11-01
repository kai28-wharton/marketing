import json
import math
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
import app


class AnalysisTests(unittest.TestCase):
    def test_imports_and_negative_accounting_values(self):
        data = app.load_data()
        self.assertEqual(len(data['factors']), 16)
        self.assertEqual(len(data['kahn']), 96)
        self.assertEqual(app.number('($6,289,333)'), -6_289_333)
        self.assertEqual(app.number('(4.0%)'), -4)
        self.assertEqual(app.number('\ufeff'.strip('\ufeff') + '$1,000'), 1000)
        self.assertEqual({r['quadrant'] for r in data['kahn']}, {'BRAND', 'EXPERIENCE', 'FRICTIONLESS', 'LOW PRICE'})

    def test_reference_anchor_and_budget(self):
        r = app.evaluate(app.BASE)
        self.assertEqual(r['spent'], 67_000_000)
        self.assertEqual(r['remaining'], 2_814_000)
        self.assertAlmostEqual(r['revenue'], 372_795_207)
        self.assertAlmostEqual(r['net_income'], -6_289_333)
        self.assertEqual(r['scores']['BRAND'], 6.3)
        self.assertEqual(r['scores']['EXPERIENCE'], 5.8)
        self.assertTrue(r['feasible'])

    def test_overspend_and_unpriced_changes(self):
        p = dict(app.BASE, online=6_000_000, national_quality=7)
        r = app.evaluate(p)
        self.assertFalse(r['feasible'])
        self.assertEqual(r['remaining'], -1_186_000)
        self.assertIn('National Brand Quality', r['unpriced_changes'])

    def test_investment_response_and_cost(self):
        r = app.evaluate(dict(app.BASE, online=3_000_000))
        base = app.evaluate(app.BASE)
        self.assertGreater(r['scores']['FRICTIONLESS'], base['scores']['FRICTIONLESS'])
        self.assertGreater(r['revenue'], base['revenue'])
        self.assertEqual(r['spent'] - base['spent'], 1_000_000)

    def test_input_validation(self):
        for bad in [None, {}, dict(app.BASE, low_depth=101), dict(app.BASE, online=math.nan),
                    dict(app.BASE, online=True), dict(app.BASE, national_quality=0), dict(app.BASE, bogus=1)]:
            with self.assertRaises(ValueError):
                app.evaluate(bad)
        for assumptions in [{'uncertainty': 0}, {'price_elasticity': -1}, {'foo': 1}, {'score_response': math.inf}]:
            with self.assertRaises(ValueError):
                app.evaluate(app.BASE, assumptions)

    def test_zero_score_response(self):
        r = app.evaluate(dict(app.BASE, experience=12_000_000), {'score_response': 0})
        self.assertEqual(r['scores']['EXPERIENCE'], 5.8)
        self.assertAlmostEqual(r['net_income'], -8_289_333)

    def test_optimizer_constraints_locks_and_repeatability(self):
        for goal in ['balanced', 'profit', 'positioning']:
            payload = {'decisions': app.BASE, 'goal': goal, 'locked': ['vendor']}
            r = app.optimize(payload)['result']
            self.assertTrue(r['feasible'])
            self.assertEqual(r['decisions']['vendor'], app.BASE['vendor'])
            self.assertGreaterEqual(r['scores']['BRAND'], 6.3 - 1e-8)
            self.assertGreaterEqual(r['scores']['EXPERIENCE'], 5.8 - 1e-8)
            for key in app.BASE:
                if key not in app.SPEND:
                    self.assertEqual(r['decisions'][key], app.BASE[key])
            self.assertEqual(r, app.optimize(payload)['result'])

    def test_all_locked_and_invalid_optimization(self):
        r = app.optimize({'decisions': app.BASE, 'locked': app.SPEND})['result']
        self.assertEqual(r['decisions'], app.BASE)
        for payload in [{'decisions': dict(app.BASE, online=10_000_000)},
                        {'decisions': app.BASE, 'goal': 'unknown'},
                        {'decisions': app.BASE, 'locked': ['coverage']}]:
            with self.assertRaises(ValueError):
                app.optimize(payload)


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.old_db = app.DB
        app.DB = Path(cls.temp.name) / 'scenarios.sqlite3'
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        app.DB = cls.old_db
        cls.temp.cleanup()

    def request(self, path, body=None, headers=None):
        request = Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                          headers=headers or {})
        with urlopen(request) as response:
            return response.status, response.read()

    def test_static_and_data(self):
        for path in ['/', '/app.js', '/style.css', '/api/data', '/vivid.css', '/review.css', '/marketing-report', '/customer-segmentation-report', '/final-report']:
            self.assertEqual(self.request(path)[0], 200)
        with self.assertRaises(HTTPError) as err:
            self.request('/materials/company.md')
        self.assertEqual(err.exception.code, 404)
        err.exception.close()

    def test_evaluate_and_persistence(self):
        from round_review import dataset
        historical=dataset(2)
        plan=historical['team']['decisions']
        with patch('round_review.dataset',return_value=historical):
            code, body = self.request('/api/impact', {'decisions':plan})
        result=json.loads(body)
        self.assertEqual(code,200)
        self.assertEqual(result['result']['revenue'],561_280_114)
        self.assertEqual(len(result['probes']),16)
        self.assertEqual(dataset(2)['team']['decisions'],plan)

    def test_round4_api_exposes_partial_data_and_blocks_financial_predictions(self):
        from round_review import dataset
        patcher=patch('round_review.dataset',return_value=dataset(3))
        patcher.start()
        self.addCleanup(patcher.stop)
        code,body=self.request('/api/data')
        data=json.loads(body)
        self.assertEqual((data['current_round'],data['planning_round']),(3,4))
        self.assertFalse(data['availability']['finance_current'])
        self.assertIsNone(data['sensitivity'])
        self.assertEqual(data['probes'],[])
        for endpoint in ('/api/impact','/api/optimize'):
            with self.assertRaises(HTTPError) as err:
                self.request(endpoint,{'decisions':data['team']['decisions']})
            self.assertEqual(err.exception.code,400)
            self.assertIn('financial exports are missing',json.load(err.exception)['error'])
            err.exception.close()

    def test_chat_endpoint(self):
        with self.assertRaises(HTTPError) as err:
            self.request('/api/chat', {'question':'What is our budget?'})
        self.assertEqual(err.exception.code, 404)
        err.exception.close()

    def test_projection_endpoint(self):
        with self.assertRaises(HTTPError) as err:
            self.request('/api/project',{'decisions':app.BASE})
        self.assertEqual(err.exception.code,404)
        err.exception.close()

    def test_html_report_endpoint(self):
        code,body=self.request('/marketing-report')
        self.assertEqual(code,200)
        self.assertTrue(body.startswith(b'<!doctype html>'))
        self.assertIn(b'review-data',body)
        self.assertIn(b'481926248',body)
        code,body=self.request('/final-report')
        self.assertEqual(code,200)
        self.assertIn(b'report-nav',body)
        self.assertEqual(body.count(b'<section class="report-section"'),6)

    def test_assortment_endpoints(self):
        for path in ('/api/assortment/team','/api/scenarios','/assortment.js','/whatif.js','/assortment-offline','/team-report'):
            with self.assertRaises(HTTPError) as err:self.request(path)
            self.assertEqual(err.exception.code,404)
            err.exception.close()

    def test_offline_assortment_endpoint(self):
        for path in ('/api/assortment','/api/assortment/offline','/api/scenarios','/api/report'):
            with self.assertRaises(HTTPError) as err:self.request(path,{'decisions':app.BASE})
            self.assertEqual(err.exception.code,404)
            err.exception.close()

    def test_bad_input_and_cross_origin(self):
        for payload in [{'decisions': {}}, ['bad input']]:
            with self.assertRaises(HTTPError) as err:
                self.request('/api/impact', payload)
            self.assertEqual(err.exception.code, 400)
            err.exception.close()
        with self.assertRaises(HTTPError) as err:
            self.request('/api/impact', {'decisions': app.BASE}, {'Origin':'https://evil.example'})
        self.assertEqual(err.exception.code, 403)
        err.exception.close()

    def test_current_optimizer_uses_definition_aware_model_and_explicit_constraints(self):
        from round_review import dataset
        historical=dataset(2)
        patcher=patch('round_review.dataset',return_value=historical)
        patcher.start()
        self.addCleanup(patcher.stop)
        plan=historical['team']['decisions']
        payload=dict(decisions=plan,ranges={'online':[8_000_000,9_000_000]},step=500_000,
                     budget=74_000_000,max_cash_use=1_000_000)
        code,body=self.request('/api/optimize',payload)
        self.assertEqual(code,200)
        self.assertEqual(json.loads(body)['status'],'blocked')
        payload['economics']=dict(inventory_holding_rate=0,inventory_financing_rate=.08,new_capital_depreciation_rate=.1)
        code,body=self.request('/api/optimize',payload)
        out=json.loads(body)
        self.assertEqual(out['status'],'verified_grid')
        self.assertEqual(out['result']['version'],'review-5.0')
        self.assertEqual(out['checked'],3)
        self.assertLessEqual(out['result']['explicit_spend'],payload['budget'])
        self.assertLessEqual(-out['result']['incremental_cash_delta'],payload['max_cash_use'])
        self.assertFalse(out['validation']['predictive_accuracy_established'])
        with self.assertRaises(HTTPError) as err:self.request('/api/optimize',dict(payload,budget=None))
        self.assertEqual(err.exception.code,400)
        err.exception.close()


if __name__ == '__main__':
    unittest.main()
