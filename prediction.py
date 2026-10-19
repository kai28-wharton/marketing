"""Versioned, bounded Kahn sensitivity model. Coefficients are explicit priors,
not learned simulator rules. Historical scores inform stress widths, not causality.
"""
import itertools
import math

VERSION = 'kahn-2.0'
QUADRANTS = ('BRAND', 'EXPERIENCE', 'FRICTIONLESS', 'LOW PRICE')
DRIVERS = ('online', 'service', 'experience', 'vendor', 'analytics', 'coverage')
LABELS = {'online': 'Online investment', 'service': 'Customer service',
          'experience': 'Shopping experience', 'vendor': 'Vendor management',
          'analytics': 'Customer analytics', 'coverage': 'Retail coverage',
          'products': 'Product, assortment & pricing'}
WEIGHTS = {
    'BRAND': {'vendor': .8, 'analytics': .45, 'store_quality': .25,
              'vendor_analytics': .2, 'quality': .32, 'breadth': .3, 'private': -.15},
    'EXPERIENCE': {'store_quality': 3., 'service': 1.6, 'analytics': .65,
                   'online': .3, 'service_experience': .7, 'analytics_experience': .4, 'breadth': .12},
    'FRICTIONLESS': {'online': 3., 'service': .65, 'analytics': .7, 'vendor': .6,
                     'reach': 1.1, 'online_analytics': .8, 'depth': .2},
    'LOW PRICE': {'vendor': .55, 'analytics': .15, 'markup': -.07, 'private': .18},
}


def clamp(v, lo=0., hi=1.):
    return min(hi, max(lo, v))


def configuration(data, reference):
    industry = {f['key']: f['industry'] for f in data['factors']}
    metrics = {r['name']: r['value'] for r in data['scorecard']}
    return {
        'half_saturation': {k: max(1., industry[k]['average']) for k in DRIVERS},
        'online_share': clamp(metrics['Online Sales'] / 100),
        'operating_scores': {'vendor': clamp(metrics['Vendor Management Score'] / 100),
                             'analytics': clamp(metrics['Customer Analytics Score'] / 100)},
        'reference': dict(reference),
    }


def capabilities(plan, config, half_scale=1., channel_shift=0.):
    base = config['reference']
    half = {k: v * half_scale for k, v in config['half_saturation'].items()}
    share = clamp(config['online_share'] + channel_shift, .05, .95)

    def sat(x, h):
        return x / (x + h) if x > 0 else 0.

    # Service supports both channels; more physical reach increases its workload.
    load = share + (1-share) * plan['coverage'] / base['coverage']
    service = sat(plan['service'] / max(.05, load), half['service'])
    # Experience spend is diluted across stores. No stores means no in-store experience.
    per_store_half = half['experience'] / max(1., config['half_saturation']['coverage'])
    store_quality = sat(plan['experience'] / plan['coverage'], per_store_half) if plan['coverage'] > 0 else 0.
    out = {'online': sat(plan['online'], half['online']), 'service': service,
           'store_quality': store_quality, 'reach': sat(plan['coverage'], half['coverage'])}
    for k in ('vendor', 'analytics'):
        raw, anchor = sat(plan[k], half[k]), sat(base[k], half[k])
        # At a 100% observed operating score, positive gains retain only 15% of
        # assumed response. Cuts retain full downside; 100% isn't proof of zero ROI.
        gain_room = 1 - .85 * config['operating_scores'][k]
        out[k] = anchor + (raw-anchor) * (gain_room if raw > anchor else 1.)
    out['service_experience'] = service * store_quality
    out['analytics_experience'] = out['analytics'] * store_quality
    out['online_analytics'] = out['online'] * out['analytics']
    out['vendor_analytics'] = out['vendor'] * out['analytics']
    return out, share


def point(plan, reference, current, config, strength, half_scale=1., channel_shift=0.):
    levels, share = capabilities(plan, config, half_scale, channel_shift)
    anchors, _ = capabilities(reference, config, half_scale, channel_shift)
    features = {k: 2*(v-anchors[k]) for k, v in levels.items()}
    for k in ('store_quality', 'service_experience', 'analytics_experience', 'reach'):
        features[k] *= 1-share
    features['online'] *= share
    features['quality'] = ((plan['private_quality']-reference['private_quality']) +
                           (plan['national_quality']-reference['national_quality'])) / 2
    features['breadth'] = (plan['low_breadth'] + plan['high_breadth'] - reference['low_breadth'] - reference['high_breadth']) / 100
    features['depth'] = (plan['low_depth'] + plan['high_depth'] - reference['low_depth'] - reference['high_depth']) / 100
    features['private'] = (plan['low_private'] + plan['high_private'] - reference['low_private'] - reference['high_private']) / 100
    features['markup'] = .76*(plan['low_markup']-reference['low_markup']) + .24*(plan['high_markup']-reference['high_markup'])
    # Logistic response preserves baseline exactly and respects the assumed 0–10
    # bounds without an abrupt score-clipping plateau. Unit slope at the anchor.
    scores = {}
    for q in QUADRANTS:
        raw = strength * sum(features[k]*w for k, w in WEIGHTS[q].items())
        anchor = clamp(current[q], .001, 9.999)
        slope = max(.05, anchor*(1-anchor/10))
        log_odds = math.log(anchor/(10-anchor)) + raw/slope
        scores[q] = 10/(1+math.exp(-clamp(log_odds, -60, 60))) if raw else current[q]
    return scores


def shapley(plan, reference, current, config, strength):
    # Exact grouped Shapley: all 128 subsets of 6 drivers + the product group.
    # Allocates interactions fairly and sums to the actual bounded score delta.
    groups = list(DRIVERS) + ['products']
    changed = [k for k in reference if k not in DRIVERS]
    cache = {}
    for mask in range(1 << len(groups)):
        p = dict(reference)
        for i, group in enumerate(groups):
            if mask & (1 << i):
                for key in (changed if group == 'products' else [group]):
                    p[key] = plan[key]
        cache[mask] = point(p, reference, current, config, strength)
    output = []
    n = len(groups)
    for i, group in enumerate(groups):
        values = {q: 0. for q in QUADRANTS}
        for mask in range(1 << n):
            if mask & (1 << i):
                continue
            size = bin(mask).count('1')
            weight = 1 / (n * math.comb(n-1, size))
            for q in QUADRANTS:
                values[q] += weight * (cache[mask | (1 << i)][q] - cache[mask][q])
        output.append({'key': group, 'label': LABELS[group], 'contributions': values})
    return output


def predict(plan, reference, data, strength, detailed=True):
    current = {r['quadrant']: r['value'] for r in data['kahn']
               if r['company'] == "GETCHELL'S" and r['round'] == 0}
    config = configuration(data, reference)
    scores = point(plan, reference, current, config, strength)
    output = {'version': VERSION, 'scores': scores,
              'status': 'Uncalibrated structural sensitivity model; no measured predictive accuracy.'}
    if not detailed:
        return output
    # Structural stress envelope, NOT a probability or statistical confidence band.
    stresses = [point(plan, reference, current, config, strength*s, h, c)
                for s, h, c in itertools.product((.6, 1.4), (.75, 1.25), (-.1, .1))]
    intervals, ranks, history = {}, {}, {}
    for q in QUADRANTS:
        observed = sorted((r for r in data['kahn'] if r['company'] == "GETCHELL'S" and r['quadrant'] == q), key=lambda r:r['round'])
        steps = [b['value']-a['value'] for a, b in zip(observed, observed[1:])]
        floor = max(.08, max(map(abs, steps), default=0.))
        history[q] = {'observations': len(observed), 'changes': steps, 'stress_floor': floor}
        lo = max(0, min([scores[q]]+[s[q] for s in stresses])-floor)
        hi = min(10, max([scores[q]]+[s[q] for s in stresses])+floor)
        intervals[q] = [lo, hi]
        peers = [r for r in data['kahn'] if r['quadrant'] == q and r['round'] == 0 and r['company'] != "GETCHELL'S"]
        rank = lambda value: 1 + sum(r['value'] > value+1e-9 for r in peers)
        ranks[q] = {'point': rank(scores[q]), 'best': rank(hi), 'worst': rank(lo),
                    'basis': 'Other retailers frozen at observed Round-0 scores; not a competitor forecast.'}
    sensitivities = []
    for key in DRIVERS:
        factor = next(f for f in data['factors'] if f['key'] == key)
        step = 25 if key == 'coverage' else 1_000_000
        row = {'key': key, 'label': LABELS[key], 'step': step, 'priced': key != 'coverage'}
        for direction, sign in [('increase', 1), ('decrease', -1)]:
            value = plan[key] + sign*step
            if not factor['min'] <= value <= factor['max']:
                row[direction] = None
                continue
            p = dict(plan, **{key:value})
            trial = point(p, reference, current, config, strength)
            row[direction] = {'score_changes': {q:trial[q]-scores[q] for q in QUADRANTS},
                              'explicit_spending_change': sign*step if key != 'coverage' else None}
        sensitivities.append(row)
    extrapolations = [{'key':f['key'], 'label':f['label'], 'value':plan[f['key']],
                       'observed_min':f['industry']['minimum'], 'observed_max':f['industry']['maximum']}
                      for f in data['factors'] if f['key'] in DRIVERS and not f['industry']['minimum'] <= plan[f['key']] <= f['industry']['maximum']]
    output.update(intervals=intervals, ranks=ranks, historical_evidence=history,
                  attribution=shapley(plan, reference, current, config, strength),
                  sensitivities=sensitivities, extrapolations=extrapolations,
                  evidence={'financial_rounds': 1, 'kahn_rounds': 3, 'paired_decision_outcome_rounds': 0,
                            'causal_calibration': False, 'out_of_sample_validation': False},
                  configuration=config, weights=WEIGHTS,
                  interval_method='Structural stress envelope over response strength ×0.6/1.4, half-saturation ×0.75/1.25, online sales share ±10 percentage points, widened by max absolute historical score step (minimum 0.08). Not a confidence interval.',
                  notes=['Industry averages set assumed half-saturation scales; this is not fitted response evidence.',
                         'Online sales mix weights channel exposure; it is a proxy, not measured causal channel attribution.',
                         'Vendor and analytics upside is damped using their observed operating scores; downside remains active.',
                         'Coverage improves modeled reach but dilutes service and in-store experience spending; store costs remain unknown.',
                         'Attribution uses exact grouped Shapley values; describes this model, not real-world causation.'])
    return output
