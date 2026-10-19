import copy
import hashlib
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import app
import assortment


class AssortmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=app.load_data()
        cls.team=assortment.import_team_plan(cls.data['factors'],app.validate)
        cls.plan=cls.team['decisions']

    def analyze(self,**changes):
        values={key:self.plan[key] for key in assortment.KEYS}
        values.update(changes)
        return assortment.analyze({'baseline':self.plan,'changes':values},self.data,app.validate,app.evaluate)

    def test_workbook_import_values_units_and_provenance(self):
        self.assertTrue(self.team['available'])
        self.assertEqual(len(self.plan),16)
        expected={'low_breadth':78,'low_depth':25,'high_breadth':50,'high_depth':10,
                  'low_markup':50,'high_markup':52,'low_private':44,'high_private':70,
                  'coverage':200,'online':6_500_000,'service':15_000_000,'experience':13_000_000,
                  'vendor':27_000_000,'analytics':8_314_000,'private_quality':6,'national_quality':6}
        for key,value in expected.items():
            self.assertAlmostEqual(self.plan[key],value)
        self.assertEqual(self.team['cells']['low_breadth'],'Sheet1!B3')
        self.assertEqual(self.team['column_label'],'Round 1 decision')
        self.assertEqual(app.evaluate(self.plan)['remaining'],0)

    def test_no_change_has_zero_deltas(self):
        report=self.analyze()
        self.assertTrue(all(abs(v)<1e-9 for v in report['financial_changes'].values()))
        self.assertTrue(all(v==0 for v in report['score_changes'].values()))
        self.assertEqual(len(report['locked_keys']),12)
        self.assertEqual(report['baseline']['decisions'],report['candidate']['decisions'])

    def test_only_four_inputs_change_without_mutation(self):
        before=copy.deepcopy(self.plan)
        workbook_hash=hashlib.sha256(assortment.TEAM_FILE.read_bytes()).hexdigest()
        report=self.analyze(low_breadth=75,low_depth=45,high_breadth=45,high_depth=35)
        for key in report['locked_keys']:
            self.assertEqual(report['candidate']['decisions'][key],self.plan[key])
        self.assertEqual(self.plan,before)
        self.assertEqual(hashlib.sha256(assortment.TEAM_FILE.read_bytes()).hexdigest(),workbook_hash)
        self.assertEqual(report['financial_changes']['explicit_spend'],0)
        self.assertEqual(report['financial_changes']['remaining'],0)

    def test_input_contract_rejects_other_decisions(self):
        changes={key:self.plan[key] for key in assortment.KEYS}
        bad=[{},dict(changes,online=20e6),dict(changes,low_depth=101),dict(changes,high_breadth=0),
             dict(changes,low_breadth=math.nan),dict(changes,low_depth=True)]
        for values in bad:
            with self.assertRaises(ValueError):
                assortment.analyze({'baseline':self.plan,'changes':values},self.data,app.validate,app.evaluate)

    def test_attribution_and_segment_reconciliation(self):
        report=self.analyze(low_breadth=80,high_breadth=60,low_depth=55,high_depth=25)
        for q,change in report['score_changes'].items():
            self.assertAlmostEqual(sum(row['scores'][q] for row in report['attribution']),change,places=10)
        for metric,change in report['financial_changes'].items():
            self.assertAlmostEqual(sum(row['financial'][metric] for row in report['attribution']),change,places=6)
        for group in ('baseline','candidate'):
            for metric in ('revenue','cogs','gross_profit'):
                self.assertAlmostEqual(sum(s[metric] for s in report['segments'][group].values()),report[group+'_financial'][metric],places=6)

    def test_transparent_model_links_and_symmetry(self):
        breadth=self.analyze(low_breadth=self.plan['low_breadth']+5)
        depth=self.analyze(low_depth=self.plan['low_depth']+5)
        self.assertGreater(breadth['score_changes']['BRAND'],0)
        self.assertGreater(breadth['score_changes']['EXPERIENCE'],0)
        self.assertEqual(breadth['score_changes']['LOW PRICE'],0)
        self.assertGreater(depth['score_changes']['FRICTIONLESS'],0)
        self.assertEqual(depth['score_changes']['BRAND'],0)
        self.assertEqual(breadth['candidate']['scores'],self.analyze(high_breadth=self.plan['high_breadth']+5)['candidate']['scores'])
        self.assertEqual(depth['candidate']['scores'],self.analyze(high_depth=self.plan['high_depth']+5)['candidate']['scores'])
        self.assertTrue(any('same per-index' in text for text in breadth['limitations']))
        self.assertTrue(any('exclude assortment' in text for text in breadth['limitations']))

    def test_bounds_sensitivities_extrapolation_and_fingerprint(self):
        report=self.analyze(low_breadth=100,low_depth=1)
        self.assertIn('Lower Cost Products: Breadth',report['outside_industry_range'])
        self.assertIsNone(report['sensitivities'][0]['increase'])
        self.assertIsNone(report['sensitivities'][1]['decrease'])
        self.assertEqual(report['baseline_fingerprint'],self.analyze()['baseline_fingerprint'])
        self.assertEqual(report['incremental_cost_allowance'],max(0,report['financial_changes']['net_income']))

    def test_missing_and_corrupt_workbook(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'missing.xlsx'
            with patch.object(assortment,'TEAM_FILE',path):
                self.assertFalse(assortment.import_team_plan(self.data['factors'],app.validate)['available'])
            path.write_text('not a workbook')
            with patch.object(assortment,'TEAM_FILE',path):
                with self.assertRaisesRegex(ValueError,'unreadable'):
                    assortment.import_team_plan(self.data['factors'],app.validate)
