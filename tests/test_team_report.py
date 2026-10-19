import unittest
from html.parser import HTMLParser
import app
from team_report import build_report


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources=[]
        self.scripts=0

    def handle_starttag(self,tag,attrs):
        if tag=='script':
            self.scripts+=1
        for key,value in attrs:
            if key in ('href','src'):
                self.resources.append(value)


class TeamReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=app.load_data()
        cls.html=build_report(None,cls.data,app.BASE,app.evaluate)

    def test_checked_numbers_and_caveats(self):
        for value in ['$2,500,000','$15,300,000','$10,200,000','$30,000,000',
                      '$10,000,000','$68,000,000','$1,814,000','$4,314,000','6.3006','3.4792','−$7,206,252']:
            self.assertIn(value,self.html)
        self.assertIn('cannot establish a defensible global optimum',self.html)
        self.assertIn('not meaningfully improve Brand',self.html)
        self.assertIn('not an observed service-quality rating',self.html)
        self.assertIn('implementation cost is unknown',self.html)

    def test_offline_self_contained_html(self):
        parser=ResourceParser()
        parser.feed(self.html)
        self.assertTrue(self.html.startswith('<!doctype html>'))
        self.assertIn('@media print',self.html)
        self.assertIn('<style>',self.html)
        self.assertEqual(parser.scripts,0)
        self.assertTrue(all(url.startswith('#') for url in parser.resources))
        self.assertNotIn('http://127.0.0.1',self.html)

    def test_submitted_plan_and_settings_are_included(self):
        plan=dict(app.BASE,online=3_000_000,national_quality=6)
        html=build_report({'decisions':plan,'planning':{'market_growth':.03,'year1_realization':.5}},self.data,app.BASE,app.evaluate)
        self.assertIn('$3,000,000',html)
        self.assertIn('3.0%',html)
        self.assertIn('50.0%',html)
        self.assertIn('Submitted page draft',html)
        self.assertIn('Year 2 / Round 2',html)

    def test_escape_source_names_and_validate_input(self):
        data=dict(self.data,sources=['<img src=x onerror=alert(1)>'])
        html=build_report(None,data,app.BASE,app.evaluate)
        self.assertIn('&lt;img',html)
        self.assertNotIn('<img src=x',html)
        with self.assertRaises(ValueError):
            build_report({'decisions':{}},self.data,app.BASE,app.evaluate)
