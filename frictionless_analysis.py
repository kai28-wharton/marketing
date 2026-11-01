"""Mechanism audit, not a simulator replica or a certified investment forecast.

Keep this diagnostic separate from Experience's older position specification.
The six observations cannot identify timing or analytics amplification reliably.
"""
import itertools
from statistics import mean

from market_value_analysis import _predict, _raw_model, _ridge, _standardize


PENALTY = .1
COMPONENTS = ('CUSTOMER SERVICE', 'ONLINE INVEST')
FEATURES = {
    'service_avg': ('Customer Service ÷ exported industry average', '×'),
    'online_pos_t': ('Prior online position', 'index'),
    'online_avg': ('Online Investment ÷ exported industry average', '×'),
    'online_analytics': ('Relative Online Investment × relative Customer Analytics', '×²'),
}
SPECS = {
    'CUSTOMER SERVICE': ['service_avg'],
    'ONLINE INVEST': ['online_pos_t', 'online_avg', 'online_analytics'],
}


def _bounded_fit(rows, target, features=None):
    """Exact active-set ridge: spend slopes >=0; online carryover in [0,1].

    Bounds are mechanism assumptions, NOT evidence that positive effects were
    learned. The intercept is free and every training fold recomputes scaling.
    """
    features = features or SPECS[target]
    carryover = {f for f in features if f.endswith('_pos_t')}
    choices = [(None, 0., 1.) if f in carryover else (None, 0.) for f in features]
    centers, scales = _standardize(rows, features)
    best = None
    for values in itertools.product(*choices):
        fixed = {f: v for f, v in zip(features, values) if v is not None}
        free = [f for f in features if f not in fixed]
        targets = [r['y'][target] - sum(v*r['x'][f] for f, v in fixed.items()) for r in rows]
        trial = _ridge(rows, free, targets, PENALTY)
        intercept, raw = _raw_model(trial)
        slopes = dict(fixed, **dict(zip(free, raw)))
        if any(v < -1e-9 for v in slopes.values()) or any(slopes[f] > 1+1e-9 for f in carryover):
            continue
        slopes = {f: max(0., min(1., v)) if f in carryover else max(0., v)
                  for f, v in slopes.items()}
        loss = sum((intercept + sum(slopes[f]*r['x'][f] for f in features) - r['y'][target])**2
                   for r in rows) + PENALTY*sum((slopes[f]*s)**2 for f, s in zip(features, scales))
        if best is None or loss < best[0]:
            coefficients = [intercept + sum(slopes[f]*c for f, c in zip(features, centers))]
            coefficients += [slopes[f]*s for f, s in zip(features, scales)]
            best = loss, dict(features=features, centers=centers, scales=scales,
                              coefficients=coefficients, penalty=PENALTY)
    return best[1]


def _position(model, row):
    return max(0., min(10., _predict(model, row)))


def _rows(history, lag):
    rows = []
    for t in range(1, len(history)):
        source = history[t-lag]
        x = {}
        for key, label in [('online', 'Online Investment'), ('service', 'Customer Service'),
                           ('analytics', 'Customer Analytics')]:
            average = source['industry'][label]['Average']
            if average is None or average <= 0:
                raise ValueError('Frictionless audit requires positive exported spending benchmarks.')
            x[key+'_avg'] = source['decisions'][key]/average
        x['online_analytics'] = x['online_avg']*x['analytics_avg']
        x['online_pos_t'] = history[t-1]['positions']['ONLINE INVEST']
        rows.append(dict(x=x, y=history[t]['positions'], round=history[t]['round'],
                         input_round=source['round'], prior_round=history[t-1]['round'],
                         actual=history[t]['quadrants']['FRICTIONLESS']['score'],
                         prior_score=history[t-1]['quadrants']['FRICTIONLESS']['score']))
    return rows


def _evaluate(rows):
    models = {target: _bounded_fit(rows, target) for target in COMPONENTS}
    predictions, forward, hidden = [], [], []
    for i, row in enumerate(rows):
        positions = {target: dict(actual=row['y'][target], fitted=_position(models[target], row))
                     for target in COMPONENTS}
        for p in positions.values():
            p['error'] = p['fitted']-p['actual']
        score = sum(p['fitted'] for p in positions.values())
        predictions.append(dict(round=row['round'], input_round=row['input_round'],
                                actual=row['actual'], fitted=score, error=score-row['actual'],
                                positions=positions))
        training = rows[:i]+rows[i+1:]
        estimate = sum(_position(_bounded_fit(training, c), row) for c in COMPONENTS)
        hidden.append(dict(round=row['round'], actual=row['actual'], fitted=estimate,
                           error=estimate-row['actual']))
        if i >= 3:
            estimate = sum(_position(_bounded_fit(rows[:i], c), row) for c in COMPONENTS)
            forward.append(dict(round=row['round'], input_round=row['input_round'],
                                training_rounds=[r['round'] for r in rows[:i]],
                                actual=row['actual'], fitted=estimate, error=estimate-row['actual'],
                                persistence=row['prior_score']))
    return dict(models=models, predictions=predictions, hidden=hidden, forward=forward,
                fitted_mae=mean(abs(p['error']) for p in predictions),
                hide_one_mae=mean(abs(p['error']) for p in hidden),
                forward_mae=mean(abs(p['error']) for p in forward),
                forward_persistence_mae=mean(abs(p['actual']-p['persistence']) for p in forward))


def frictionless_analysis(history, legacy, legacy_rows):
    """Show a source-aligned conditional diagnostic; prefer persistence if it wins.

    Expense alignment is evidence for same-round spending, not proof of score
    timing. Both alignments are reported; neither is a frozen backtest.
    """
    from market_value_analysis import _fit_position_model

    rows = _rows(history, 0)
    same = _evaluate(rows)
    lagged = _evaluate(_rows(history, 1))
    legacy_forward = []
    for i in range(3, len(legacy_rows)):
        row = legacy_rows[i]
        score = sum(_predict(_fit_position_model(legacy_rows[:i], c), {'x': row['x']}) for c in COMPONENTS)
        legacy_forward.append(abs(score-history[i+1]['quadrants']['FRICTIONLESS']['score']))
    summaries = []
    for target in COMPONENTS:
        model = same['models'][target]
        intercept, raw = _raw_model(model)
        coefficients = [dict(term=f, label=FEATURES[f][0], unit=FEATURES[f][1],
                             raw_coefficient=b, latest_contribution=b*rows[-1]['x'][f],
                             direction='constrained nonnegative', importance_rank=i+1)
                        for i, (f, b) in enumerate(zip(model['features'], raw))]
        label = 'Customer Service' if target == 'CUSTOMER SERVICE' else 'Online Investment'
        equation = f'{label} position(r) = clip[0,10]({intercept:.4f} ' + ' '.join(
            f"{'+' if b >= 0 else '−'} {abs(b):.4f} × {FEATURES[f][0]}"
            for f, b in zip(model['features'], raw)) + ')'
        predictions = [dict(round=p['round'], **p['positions'][target]) for p in same['predictions']]
        held = [abs(_position(_bounded_fit(rows[:i]+rows[i+1:], target), r)-r['y'][target])
                for i, r in enumerate(rows)]
        summaries.append(dict(target=target, decision_key='service' if target == 'CUSTOMER SERVICE' else 'online',
                              decision_label=label, features=model['features'], coefficients=coefficients,
                              intercept=intercept, equation=equation, predictions=predictions,
                              fitted_mae=mean(abs(p['error']) for p in predictions), hide_one_mae=mean(held),
                              persistence_mae=mean(abs(history[i]['positions'][target]-r['y'][target])
                                                   for i, r in enumerate(rows)),
                              latest=dict(round=rows[-1]['round'], input_round=rows[-1]['input_round'],
                                   features={f: rows[-1]['x'][f] for f in model['features']},
                                   actual=predictions[-1]['actual'], fitted=predictions[-1]['fitted']),
                              rationale='Mechanism constraints are imposed, not empirically proven. No standalone analytics term; no service carryover.'))
    result = dict(legacy)
    result.update(audited=True, form_label='Mechanism-constrained diagnostic',
                  position_models=summaries, predictions=same['predictions'], latest=same['predictions'][-1],
                  fitted_mae=same['fitted_mae'], hide_one_mae=same['hide_one_mae'],
                  forward_mae=same['forward_mae'], forward_persistence_mae=same['forward_persistence_mae'],
                  forward=same['forward'], preferred='persistence' if same['forward_persistence_mae'] <= same['forward_mae'] else 'diagnostic',
                  documented_note='Analytics multiplies online investment in this diagnostic; it is not an additive service effect. Constraints encode assumptions, not empirical confirmation. Persistence wins the current earlier-only check.',
                  rationale='Audited conditional diagnostic: current-round service spending has no fitted carryover; analytics amplifies online investment through an interaction, not a standalone service term. Prior online position is retained. Same-round spending is observed, not forecast. Score timing remains uncertain, so the one-round-lag alternative is also shown.')
    actual_mean = mean(p['actual'] for p in same['predictions'])
    result['r_squared'] = 1-sum(p['error']**2 for p in same['predictions'])/sum((p['actual']-actual_mean)**2 for p in same['predictions'])
    result['audit'] = dict(
        source='MarketValue_Slides.pdf p13; PivotOrPerish_Intro wemba.pdf p14',
        corrections=['Analytics belongs in an online-investment interaction, not a standalone service-position term.',
                     'Service has little documented persistence; its prior position is excluded rather than fitted at 0.728.',
                     'Same-round expenses match submitted investment; this supports auditing timing but does not prove when positions respond.',
                     'Nonnegative slopes and online carryover between 0 and 1 are explicit mechanism assumptions, not discovered positive effects.',
                     'The previous leave-one-out score used later periods and followed specification search; it was not forward validation.'],
        comparison=[dict(name='Previous lagged additive model (superseded)', fitted_mae=legacy['fitted_mae'],
                         hide_one_mae=legacy['hide_one_mae'], forward_mae=mean(legacy_forward)),
                    dict(name='Constrained same-round conditional diagnostic', **{k: same[k] for k in ('fitted_mae', 'hide_one_mae', 'forward_mae')}),
                    dict(name='Constrained one-round-lag sensitivity', **{k: lagged[k] for k in ('fitted_mae', 'hide_one_mae', 'forward_mae')}),
                    dict(name='Prior-score persistence', fitted_mae=None, hide_one_mae=legacy['persistence_mae'],
                         forward_mae=same['forward_persistence_mae'])],
        timing=[dict(round=r['round'], online_decision=r['decisions']['online'],
                     online_expense=r['online_expense'], expense_fraction=r['online_expense']/r['decisions']['online'])
                for r in history],
        boundary='Six scored periods; three earlier-only checks (R4–R6). Same-round tests condition on observed spending and benchmarks, not information forecast before the round. Timing, analytics strength, and rival reactions are not identified. Specifications were reviewed using this dataset, so these are retrospective diagnostics, not a frozen backtest. Do not optimize the Round 7 budget with these coefficients.')
    return result
