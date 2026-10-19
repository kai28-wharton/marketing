"""Latest-round review server, with a frozen v2 engine retained for historical audits.

The active UI uses round_review.dataset and review_model.evaluate. The legacy
load_data/evaluate/optimize functions below must not be mistaken for current
forecasts; retaining their coefficients makes the historical misses reproducible.
"""
import csv
import json
import math
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from prediction import predict

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'scenarios.sqlite3'
BUDGET = 69_814_000
FACTORS = [
    ('low_markup', 'Lower Cost Products: Price Markup', 54, 0, 150, '%', 'Lower-cost products'),
    ('low_breadth', 'Lower Cost Products: Breadth', 50, 1, 100, 'index', 'Lower-cost products'),
    ('low_depth', 'Lower Cost Products: Depth', 50, 1, 100, 'index', 'Lower-cost products'),
    ('low_private', 'Lower Cost Products: Private Brand', 50, 0, 100, '%', 'Lower-cost products'),
    ('high_markup', 'Higher Cost Products: Price Markup', 66, 0, 150, '%', 'Higher-cost products'),
    ('high_breadth', 'Higher Cost Products: Breadth', 50, 1, 100, 'index', 'Higher-cost products'),
    ('high_depth', 'Higher Cost Products: Depth', 50, 1, 100, 'index', 'Higher-cost products'),
    ('high_private', 'Higher Cost Products: Private Brand', 50, 0, 100, '%', 'Higher-cost products'),
    ('private_quality', 'Private Brand Quality', 5, 1, 10, 'index', 'Quality & reach'),
    ('national_quality', 'National Brand Quality', 5, 1, 10, 'index', 'Quality & reach'),
    ('coverage', 'Retail Coverage', 200, 0, 1000, 'stores', 'Quality & reach'),
    ('online', 'Online Investment', 2_000_000, 0, BUDGET, '$', 'Investment allocation'),
    ('service', 'Customer Service', 15_000_000, 0, BUDGET, '$', 'Investment allocation'),
    ('experience', 'Shopping Experience', 10_000_000, 0, BUDGET, '$', 'Investment allocation'),
    ('vendor', 'Vendor Management', 30_000_000, 0, BUDGET, '$', 'Investment allocation'),
    ('analytics', 'Customer Analytics', 10_000_000, 0, BUDGET, '$', 'Investment allocation'),
]
BASE = {f[0]: f[2] for f in FACTORS}
SPEND = ['online', 'service', 'experience', 'vendor', 'analytics']
# Five explicit investment/expense boxes total $67M.
DEFAULT_ASSUMPTIONS = {'score_response': 0.55, 'demand_response': 0.025,
                       'price_elasticity': 1.2, 'uncertainty': 0.10}


def number(value):
    s = str(value).strip()
    negative = s.startswith('(') and s.endswith(')')
    s = s.strip('()').replace('$', '').replace(',', '').replace('%', '')
    return float(s) * (-1 if negative else 1)


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def load_data():
    """Frozen Round 0 inputs for historical v2 comparison and regressions only."""
    materials = ROOT / 'materials'
    financial_dir = materials / 'round0' / 'finance'
    financial = {}
    for key, name in [('balance', 'balanceSheet'), ('income', 'incomeStatement'), ('scorecard', 'scorecard')]:
        financial[key] = [{'name': r['Name'], 'display': r['Round-0'], 'value': number(r['Round-0'])}
                          for r in read_csv(financial_dir / f'{name}-round0.csv')]
    industry = {r['Decision']: {k.lower(): number(r[k]) for k in ['Average', 'Minimum', 'Maximum']}
                for r in read_csv(ROOT / 'decision_making' / 'round_1' / 'industryDecisions-round0.csv')}
    factors = [dict(zip(['key', 'label', 'baseline', 'min', 'max', 'unit', 'group'], f),
                    industry=industry[f[1]], priced=f[0] in SPEND) for f in FACTORS]
    kahn = []
    for r in read_csv(materials / 'round0' / 'marketing' / 'kahn-round0.csv'):
        _, round_text, quadrant = r['Quadrant'].split(' ', 2)
        for company, value in r.items():
            if company != 'Quadrant':
                kahn.append({'round': int(round_text), 'quadrant': quadrant,
                             'company': company, 'value': number(value)})
    docs = {}
    for name in ['company', 'competitors']:
        path = materials / f'{name}.md'
        docs[name] = path.read_text().strip() if path.exists() else ''
    data = dict(**financial, factors=factors, kahn=kahn, documents=docs,
                baseline=BASE, budget=BUDGET, assumptions=DEFAULT_ASSUMPTIONS,
                sources=['materials/round0/finance/balanceSheet-round0.csv', 'materials/round0/finance/incomeStatement-round0.csv',
                          'decision_making/round_1/industryDecisions-round0.csv', 'materials/round0/finance/scorecard-round0.csv',
                         'materials/round0/marketing/kahn-round0.csv',
                         'materials/company.md', 'materials/competitors.md'])
    from marketing import load_marketing
    try:
        data['marketing'] = load_marketing(ROOT,data)
    except (OSError,ValueError,KeyError) as exc:
        data['marketing'] = {'available':False,'sources':[],'message':'Marketing files could not be interpreted: '+str(exc)}
    data['sources'].extend(data['marketing']['sources'])
    from assortment_evidence import build_readiness
    data['assortment_readiness'] = build_readiness(data)
    return data


def validate(values, assumptions=None):
    if not isinstance(values, dict) or set(values) != set(BASE):
        raise ValueError('Supply all 16 decision fields, with no unknown fields.')
    clean = {}
    for key, label, _, low, high, _, _ in FACTORS:
        v = values[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f'{label} must be a finite number between {low} and {high}.')
        clean[key] = float(v)
    a = dict(DEFAULT_ASSUMPTIONS)
    if assumptions is not None:
        if not isinstance(assumptions, dict) or set(assumptions) - set(a):
            raise ValueError('Unknown assumption field.')
        a.update(assumptions)
    for key, low, high in [('score_response', 0, 2), ('demand_response', 0, .1),
                           ('price_elasticity', 0, 3), ('uncertainty', .01, .5)]:
        v = a[key]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not low <= v <= high:
            raise ValueError(f'Invalid assumption: {key}.')
    return clean, a


def evaluate(values, assumptions=None, data=None, detailed=True):
    """Frozen v2 sensitivity, not the current Round-1-anchored model."""
    p, a = validate(values, assumptions)
    data = data or load_data()
    income = {r['name']: r['value'] for r in data['income']}
    current = {r['quadrant']: r['value'] for r in data['kahn']
               if r['company'] == "GETCHELL'S" and r['round'] == 0}
    kahn = predict(p, BASE, data, a['score_response'], detailed=detailed)
    scores = kahn['scores']
    score_gain = sum((scores[k] - current[k]) * w for k, w in
                     [('BRAND', .35), ('EXPERIENCE', .35), ('FRICTIONLESS', .2), ('LOW PRICE', .1)])
    demand_lift = a['demand_response'] * score_gain
    revenues, cogs, volume = [], [], []
    segments = {}
    for prefix, label in [('low', 'Lower Cost'), ('high', 'Higher Cost')]:
        price_ratio = (1 + p[prefix + '_markup'] / 100) / (1 + BASE[prefix + '_markup'] / 100)
        units = max(.1, 1 + demand_lift - a['price_elasticity'] * (price_ratio - 1))
        volume.append(units)
        revenues.append(income[label + ' Revenue'] * price_ratio * units)
        cogs.append(income[label + ' COGS'] * units)
        segments[prefix] = {'revenue':revenues[-1], 'cogs':cogs[-1],
                            'gross_profit':revenues[-1]-cogs[-1]}
    revenue = sum(revenues)
    gross_profit = revenue - sum(cogs)
    spent = sum(p[k] for k in SPEND)
    spending_delta = spent - sum(BASE[k] for k in SPEND)
    # Anchor to Round 0 and apply changes relative to screenshot plan. No claim
    # that screenshot investment equals the accounting period's expense.
    profit_delta = gross_profit - income['Gross Profit'] - spending_delta
    profit = income['Net Income'] + profit_delta
    unpriced = [f[1] for f in FACTORS if f[0] not in SPEND and p[f[0]] != BASE[f[0]]]
    warnings = ['Illustrative sensitivity model, not a calibrated simulator forecast.',
                'Round-0 financials are the anchor; unchanged decisions reproduce Round 0, not a validated next-round result.',
                'Only five explicit spending fields are budgeted. Quality, assortment and store costs are unknown.',
                'Round-0 online expense ($0.8M) differs from screenshot investment ($2M); investment is not assumed to equal accounting expense.']
    if spent > BUDGET:
        warnings.append('OVER BUDGET: this plan cannot be finalized.')
    if unpriced:
        warnings.append('Unpriced decision changes: ' + ', '.join(unpriced) + '. Financial estimates exclude their implementation costs.')
    if scores['BRAND'] < current['BRAND'] or scores['EXPERIENCE'] < current['EXPERIENCE']:
        warnings.append('This scenario weakens at least one of the Brand / Experience pillars in the illustrative model.')
    if p['vendor'] > BASE['vendor'] or p['analytics'] > BASE['analytics']:
        warnings.append('Vendor/analytics operating scores are already 100%; additional spending has deliberately limited assumed upside, not measured incremental ROI.')
    if p['coverage'] != BASE['coverage']:
        warnings.append('Coverage changes affect modeled reach and per-store spending intensity; store opening/closure and inventory costs are excluded.')
    if detailed and kahn['extrapolations']:
        warnings.append('Outside observed industry range: ' + ', '.join(r['label'] for r in kahn['extrapolations']) + '. Effects are extrapolated, not validated.')
    uncertainty = revenue * a['uncertainty']
    return dict(decisions=p, assumptions=a, spent=spent, remaining=BUDGET-spent,
                feasible=spent <= BUDGET, unpriced_changes=unpriced, scores=scores,
                model_version=kahn['version'], kahn=kahn,
                revenue=revenue, revenue_delta=revenue-income['Net Revenue'],
                cogs=sum(cogs), gross_profit=gross_profit, segments=segments,
                net_income=profit, profit_delta=profit_delta, gross_margin=gross_profit/revenue,
                volume_change=(sum(volume)/2-1),
                revenue_range=[revenue-uncertainty, revenue+uncertainty],
                profit_range=[profit-uncertainty, profit+uncertainty],
                warnings=warnings)


def optimize(payload):
    p, a = validate(payload.get('decisions'), payload.get('assumptions'))
    goal = payload.get('goal', 'balanced')
    if goal not in ('balanced', 'positioning', 'profit'):
        raise ValueError('Unknown optimization objective.')
    locked = payload.get('locked', [])
    if not isinstance(locked, list) or any(k not in SPEND for k in locked):
        raise ValueError('Only investment fields may be locked.')
    if sum(p[k] for k in SPEND) > BUDGET:
        raise ValueError('Start with a within-budget plan before optimizing.')
    data = load_data()
    start = evaluate(p, a, data, detailed=False)
    free = [k for k in SPEND if k not in locked]
    floors = {'online': 2_000_000, 'service': 10_000_000, 'experience': 8_000_000,
              'vendor': 20_000_000, 'analytics': 5_000_000}
    # Preserve a user's lower starting spend instead of silently making it a mandatory floor.
    floors = {k: min(v, p[k]) for k, v in floors.items()}
    weights = {'balanced': (.65, .35), 'positioning': (.95, .05), 'profit': (.15, .85)}[goal]

    def utility(result):
        s = result['scores']
        if s['BRAND'] + 1e-8 < start['scores']['BRAND'] or s['EXPERIENCE'] + 1e-8 < start['scores']['EXPERIENCE']:
            return -math.inf
        positioning = .4*s['BRAND'] + .4*s['EXPERIENCE'] + .15*s['FRICTIONLESS'] + .05*s['LOW PRICE']
        return weights[0]*positioning + weights[1]*result['net_income']/10_000_000

    best, best_result = dict(p), start
    best_value = utility(start)
    rng = random.Random(42)
    # Reproducible local allocation search: no external model or API requests.
    for step in [2_000_000, 1_000_000, 500_000, 100_000]:
        for _ in range(180):
            trial = dict(best)
            if not free:
                break
            source, target = rng.choice(free + ['reserve']), rng.choice(free + ['reserve'])
            if source == target:
                continue
            amount = min(step, BUDGET-sum(trial[k] for k in SPEND)) if source == 'reserve' else min(step, trial[source]-floors[source])
            if amount <= 0:
                continue
            if source != 'reserve':
                trial[source] -= amount
            if target != 'reserve':
                trial[target] += amount
            result = evaluate(trial, a, data, detailed=False)
            value = utility(result)
            if result['feasible'] and value > best_value + 1e-10:
                best, best_result, best_value = trial, result, value
    return dict(result=evaluate(best, a, data), objective=goal,
                method='Reproducible heuristic allocation search; not a guaranteed global optimum.',
                constraints=['Budget ≤ $69,814,000', 'Only the five explicit spending fields can change',
                             'Preserve starting modeled Brand and Experience scores',
                             'Planning spend floors: online $2M; service $10M; experience $8M; vendor $20M; analytics $5M (or starting amount if lower)',
                             'Locked investments unchanged; all non-investment decisions unchanged'])


@contextmanager
def connection():
    DB.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    try:
        with con:
            con.execute('CREATE TABLE IF NOT EXISTS scenarios (id INTEGER PRIMARY KEY, name TEXT NOT NULL, created TEXT NOT NULL, payload TEXT NOT NULL)')
            yield con
    finally:
        con.close()


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, data):
        raw = json.dumps(data, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlparse(self.path).path
        try:
            if path == '/api/data':
                from round_review import dataset
                from review_model import evaluate as current_evaluate, factor_probes
                data = dataset()
                data['sensitivity'] = current_evaluate(data['team']['decisions'], data)
                data['probes'] = factor_probes(data)
                return self.respond(200, data)
            if path == '/marketing-report':
                from marketing_report import build_current_report
                content = build_current_report().encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Disposition', 'attachment; filename="getchells-marketing-intelligence.html"')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                return self.wfile.write(content)
            files = {'/': ('index.html', 'text/html'), '/app.js': ('review.js', 'text/javascript'),
                     '/review.css': ('review.css', 'text/css'),
                     '/vivid.css': ('vivid.css', 'text/css'),
                     '/style.css': ('style.css', 'text/css'), '/chat.css': ('chat.css', 'text/css')}
            if path not in files:
                return self.respond(404, {'error': 'Not found'})
            name, mime = files[path]
            content = (ROOT / 'web' / name).read_bytes()
            if name=='review.js':
                content = b'window.__deferReviewInit=true;\n'+content+b'\n'+(ROOT/'web/current.js').read_bytes()+b'\ninit();'
            self.send_response(200)
            self.send_header('Content-Type', mime + '; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(content)
        except (OSError, ValueError, KeyError) as exc:
            self.respond(500, {'error': str(exc)})

    def do_POST(self):
        # Reject cross-origin browser writes to the local service.
        origin = self.headers.get('Origin')
        if origin and origin != 'http://' + self.headers.get('Host', ''):
            return self.respond(403, {'error': 'Cross-origin writes are not allowed.'})
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 100_000:
                raise ValueError('Request body must be between 1 and 100,000 bytes.')
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError('Expected a JSON object.')
            path = urlparse(self.path).path
            if path == '/api/impact':
                from round_review import dataset
                from review_model import evaluate as current_evaluate, factor_probes
                data = dataset()
                result = current_evaluate(body.get('decisions'), data, body.get('assumptions'),body.get('economics'))
                return self.respond(200, dict(result=result, probes=factor_probes(data,result['decisions'],result['assumptions'],result['economics'])))
            if path == '/api/optimize':
                from round_review import dataset
                from review_optimizer import optimize as current_optimize
                return self.respond(200,current_optimize(body,dataset()))
            return self.respond(404, {'error': 'Not found'})
        except (ValueError, TypeError, KeyError) as exc:
            self.respond(400, {'error': str(exc)})
        except (OSError, sqlite3.Error) as exc:
            self.respond(500, {'error': str(exc)})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '8000'))
    print(f"Getchell's Decision Lab → http://127.0.0.1:{port}", flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
