"""Compact full-history models for the completed R1–R8 simulation.

Financial fits include R0 (nine snapshots); score responses exclude the initial
state (eight scored rounds). Fixed penalties and small mechanism-based designs,
not a 15-coefficient claim from eight decisions. Metrics are computed afresh.
"""
import math
from statistics import mean


def metrics(actual, fitted):
    errors = [p-a for a, p in zip(actual, fitted)]
    total = sum((a-mean(actual))**2 for a in actual)
    return dict(mae=mean(abs(e) for e in errors), rmse=math.sqrt(mean(e*e for e in errors)),
                r_squared=1-sum(e*e for e in errors)/total if total else None,
                max_error=max(abs(e) for e in errors))


def final_market_value(history):
    from market_value_analysis import _value_rows, _value_metrics, _raw_model
    rows = _value_rows(history)
    for r in rows:
        r['log_clv'] = math.log(r['clv'])
        r['log_revenue'] = math.log(r['revenue'])
    primary = ['log_ebit', 'wacc', 'book_debt_weight']
    fit = _value_metrics(rows, primary, .01)
    intercept, raw = _raw_model(fit['model'])
    labels = ['ln(EBIT in $)', 'WACC (%)', 'book debt weight']
    equation = f'ln(Market value in $) = {intercept:.4f} ' + ' '.join(
        f"{'+' if b >= 0 else '−'} {abs(b):.4f} × {label}" for b, label in zip(raw, labels))
    comparison = []
    for name, features in [('Final: earnings + WACC + book leverage', primary),
                           ('Earnings + WACC', ['log_ebit', 'wacc']),
                           ('Add strategy shortfall instead of leverage', ['log_ebit', 'wacc', 'strategy_deficit']),
                           ('Add revenue scale instead of leverage', ['log_ebit', 'wacc', 'log_revenue']),
                           ('Add customer equity instead of leverage', ['log_ebit', 'wacc', 'log_clv'])]:
        trial = _value_metrics(rows, features, .01)
        comparison.append(dict(name=name, fitted_mape=trial['fitted_mape'], hide_one_mape=trial['hide_one_mape']))
    actual = [p['actual'] for p in fit['predictions']]
    fitted = [p['fitted'] for p in fit['predictions']]
    return dict(features=primary, penalty=.01, observations=len(rows), equation=equation,
                intercept=intercept, coefficients=[dict(term=f, label=l, coefficient=b) for f, l, b in zip(primary, labels, raw)],
                predictions=fit['predictions'], fitted_mape=fit['fitted_mape'], hide_one_mape=fit['hide_one_mape'],
                r_squared=fit['r_squared'], **{k:v for k,v in metrics(actual,fitted).items() if k!='r_squared'},
                comparison=comparison, method='Log-linear ridge, fixed λ=0.01; three finance predictors and an intercept. Fit on all R0–R8 snapshots. Internal scaling is converted back to raw units for the equation. Market debt weight is excluded because it contains the market-value target.',
                boundary='Full-sample descriptive fit, not a forecast or causal marketing return. R² measures log-value fit. Book debt weight = debt / (debt + book equity). Recovered historical financial columns retain source provenance; earlier-only testing is not the main selection criterion.')


def final_wacc(rows):
    from wacc_analysis import WACC_FEATURES, wacc_errors
    features = WACC_FEATURES
    fit = wacc_errors(rows, features, .01)
    model = fit['model']
    labels = ['market debt weight', 'ln(EBIT / market value)', 'ln(EBIT in $M)']
    equation = f"WACC (%) = {model['intercept']:.4f} " + ' '.join(
        f"{'+' if b >= 0 else '−'} {abs(b):.4f} × {label}" for b, label in zip(model['coefficients'], labels))
    actual = [p['actual'] for p in fit['predictions']]
    fitted = [p['fitted'] for p in fit['predictions']]
    comparison = []
    for name, fs in [('Final: market weight + earnings yield + EBIT', features),
                     ('Market weight + earnings yield', ('market_debt_weight', 'log_earnings_yield')),
                     ('Book leverage + interest cover', ('book_debt_weight', 'log_interest_cover'))]:
        trial = wacc_errors(rows, fs, .01)
        comparison.append(dict(name=name, fitted_mae_pp=trial['fitted_mae_pp'], loo_mae_pp=trial['loo_mae_pp']))
    result = dict(model, **{k:v for k,v in fit.items() if k!='model'})
    result.update(equation=equation, observations=len(rows), selected_penalty=.01,
                  r_squared=metrics(actual, fitted)['r_squared'], rmse_pp=metrics(actual, fitted)['rmse'],
                  max_error_pp=metrics(actual, fitted)['max_error'], comparison=comparison,
                  method='Ridge regression in percentage points, fixed λ=0.01; all R0–R8 snapshots, three financing predictors and an intercept. The full-sample fit is primary; hide-one-round error is a secondary robustness check.',
                  boundary='Market debt weight = debt / (debt + reported equity market value). EBIT and market value are observed jointly with WACC. This is an explanatory association, not the simulator credit formula or a causal decision-to-WACC calculator. No old subset-search statistics are reused.')
    return result


def final_score_models(history):
    from market_value_analysis import INPUT_KEYS, feature_values, _ridge, _raw_model, _predict
    from frictionless_analysis import _rows, _bounded_fit, _position
    rows = _rows(history, 0)
    for r, h, prior in zip(rows, history[1:], history[:-1]):
        r['x'].update(feature_values(h['decisions']))
        r['x'].update(service_pos_t=prior['positions']['CUSTOMER SERVICE'],
                      experience_avg=h['decisions']['experience']/h['industry']['Shopping Experience']['Average'],
                      experience_pos_t=prior['positions']['SHOPPING EXPERIENCE'])
        r['x']['experience_analytics'] = r['x']['experience_avg']*r['x']['analytics_avg']
    specs = {'CUSTOMER SERVICE': ['service_pos_t', 'service_avg'],
             'ONLINE INVEST': ['online_pos_t', 'online_avg', 'online_analytics'],
             'SHOPPING EXPERIENCE': ['experience_pos_t', 'experience_avg', 'experience_analytics']}
    labels = {'prior_rel': 'prior Low Price minus prior peer average',
              'low_rel': 'lower-cost markup ÷ industry average',
              'high_rel': 'higher-cost markup ÷ industry average',
              'service_pos_t': 'prior Customer Service position',
              'service_avg': 'relative Customer Service',
              'online_pos_t': 'prior Online position',
              'online_avg': 'relative Online Investment',
              'online_analytics': '(relative Online × relative Analytics)',
              'experience_pos_t': 'prior Shopping Experience position',
              'experience_avg': 'relative Shopping Experience',
              'experience_analytics': '(relative Shopping Experience × relative Analytics)',
              'quality': 'shared private/national quality', 'private': 'average private-brand mix (%)',
              'assortment': 'average breadth/depth', 'price': 'average markup (%)',
              'vendor': 'Vendor Management ($M)'}
    position_models = {}; position_equations = []
    for target, fs in specs.items():
        model = _bounded_fit(rows, target, fs)
        position_models[target] = model
        intercept, raw = _raw_model(model)
        eq = f'{target.title()} = clip[0,10]({intercept:.3f} ' + ' '.join(
            f"{'+' if b >= 0 else '−'} {abs(b):.3f} × {labels[f]}" for f,b in zip(fs,raw)) + ')'
        position_equations.append(dict(target=target, equation=eq, features=fs, intercept=intercept,
                                       coefficients=[dict(term=f,label=labels[f],coefficient=b)
                                                     for f,b in zip(fs,raw)]))
    models = []

    def add(q, actual, fitted, equation, inputs, extra=None):
        entry = dict(quadrant=q, equation=equation, inputs=inputs, observations=len(rows),
                     predictions=[dict(round=r['round'], actual=a, fitted=p, error=p-a)
                                  for r,a,p in zip(rows,actual,fitted)], **metrics(actual,fitted))
        if extra:
            entry.update(extra)
        models.append(entry)

    # Brand: shared quality, assortment and private-brand mix.
    actual = [h['quadrants']['BRAND']['score'] for h in history[1:]]
    fit = _ridge(rows, ['quality', 'assortment', 'private'], actual, .1)
    fitted = [_predict(fit, r) for r in rows]
    intercept, raw = _raw_model(fit)
    add('BRAND', actual, fitted,
        f'Brand = {intercept:.3f} ' + ' '.join(
            f"{'+' if b >= 0 else '−'} {abs(b):.3f} × {label}" for b,label in
            zip(raw, ['shared private/national quality', 'average breadth/depth', 'average private-brand mix (%)'])),
        'Quality, assortment and private-brand mix',
        dict(persistence_mae=mean(abs(a-p) for a,p in zip(actual,[h['quadrants']['BRAND']['score'] for h in history[:-1]]))))

    # Experience: fitted service + shopping-experience positions.
    actual = [h['quadrants']['EXPERIENCE']['score'] for h in history[1:]]
    fitted = [sum(_position(position_models[c], r) for c in ('CUSTOMER SERVICE','SHOPPING EXPERIENCE')) for r in rows]
    add('EXPERIENCE', actual, fitted,
        'Experience ≈ Customer Service position + Shopping Experience position',
        'Service (prior + relative spend), Shopping Experience (prior + relative spend × analytics)',
        dict(persistence_mae=mean(abs(a-p) for a,p in zip(actual,[h['quadrants']['EXPERIENCE']['score'] for h in history[:-1]]))))

    # Low Price: ratings are relative, so model deviation from the six-peer mean.
    lp_rows = []
    for h, prior in zip(history[1:], history[:-1]):
        ind = h['industry']; peer = h.get('peer_scores', {}).get('LOW PRICE')
        if peer is None:
            peer = h['quadrants']['LOW PRICE']['score']
        prior_peer = prior.get('peer_scores', {}).get('LOW PRICE', peer)
        lp_rows.append(dict(round=h['round'], peer=peer,
                            actual=h['quadrants']['LOW PRICE']['score'],
                            relative=h['quadrants']['LOW PRICE']['score']-peer,
                            x=dict(prior_rel=prior['quadrants']['LOW PRICE']['score']-prior_peer,
                                   low_rel=h['decisions']['low_markup']/ind['Lower Cost Products: Price Markup']['Average'],
                                   high_rel=h['decisions']['high_markup']/ind['Higher Cost Products: Price Markup']['Average'])))
    lp_features = ['prior_rel', 'low_rel', 'high_rel']
    lp_fit = _ridge(lp_rows, lp_features, [r['relative'] for r in lp_rows], .1)
    lp_intercept, lp_raw = _raw_model(lp_fit)
    lp_fitted = [r['peer']+_predict(lp_fit, r) for r in lp_rows]
    lp_relative_fitted = [_predict(lp_fit, r) for r in lp_rows]
    lp_loo = []
    for i in range(len(lp_rows)):
        trial_rows = lp_rows[:i]+lp_rows[i+1:]
        trial = _ridge(trial_rows, lp_features, [r['relative'] for r in trial_rows], .1)
        lp_loo.append(lp_rows[i]['peer']+_predict(trial, lp_rows[i]))
    lp_actual = [r['actual'] for r in lp_rows]
    lp_deviation = f'{lp_intercept:.3f} ' + ' '.join(
        f"{'+' if b >= 0 else '−'} {abs(b):.3f} × {labels[f]}" for f,b in zip(lp_features,lp_raw))
    add('LOW PRICE', lp_actual, lp_fitted, f'Low Price − six-peer average = {lp_deviation}',
        'Peer-relative rating; prior Low Price gap; lower/higher-cost markup ÷ same-round industry averages',
        dict(level_equation='Low Price = six-peer average + (peer-relative deviation)',
             relative_equation=lp_deviation,
             predictions=[dict(round=r['round'], actual=a, fitted=p, error=p-a,
                               peer=r['peer'], relative=r['relative'], fitted_relative=rp)
                          for r,a,p,rp in zip(lp_rows,lp_actual,lp_fitted,lp_relative_fitted)],
             persistence_mae=mean(abs(a-p) for a,p in zip(lp_actual,[h['quadrants']['LOW PRICE']['score'] for h in history[:-1]])),
             hide_one_mae=mean(abs(a-p) for a,p in zip(lp_actual,lp_loo)),
             relative_mae=mean(abs(r['relative']-p) for r,p in zip(lp_rows,lp_relative_fitted))))

    # Frictionless: fitted service + online positions. Service carryover is bounded.
    actual = [h['quadrants']['FRICTIONLESS']['score'] for h in history[1:]]
    fitted = [sum(_position(position_models[c], r) for c in ('CUSTOMER SERVICE','ONLINE INVEST')) for r in rows]
    add('FRICTIONLESS', actual, fitted,
        'Frictionless ≈ Customer Service position + Online Invest position',
        'Service (prior + relative spend), Online (prior + relative spend × analytics)',
        dict(persistence_mae=mean(abs(a-p) for a,p in zip(actual,[h['quadrants']['FRICTIONLESS']['score'] for h in history[:-1]]))))

    # All fifteen actual decision series are screened, not declared identifiable.
    screen_rows = [dict(x={k:h['decisions'][k] for k in INPUT_KEYS}) for h in history[1:]]
    score = [h['quadrants']['FRICTIONLESS']['score'] for h in history[1:]]
    all_fit = _ridge(screen_rows, list(INPUT_KEYS), score, .1)
    all_predictions = [_predict(all_fit,r) for r in screen_rows]
    return dict(models=models, position_equations=position_equations, observations=len(rows), input_count=15,
                all_input_screen_mae=metrics(score,all_predictions)['mae'],
                method='Full R1–R8 same-round descriptive fits; fixed ridge λ=0.1. Capability models use bounded carryover [0,1] and nonnegative investment slopes. Experience/Frictionless sum fitted positions, not observed positions. Low Price is modeled relative to the six-peer average because the rating scale is perceptual and near-flat. Spending is relative to the same-round exported average; analytics interacts with online/experience, never service alone.',
                boundary='Eight scored rounds cannot identify fifteen independent decision effects. The all-input screen is an overparameterized fit, not the final mechanism. Brand and Low Price coefficients are associations; Low Price has a 0.2-point observed range, so R² is unstable even when absolute error is small. Bounded service carryover is a persistence assumption in this full-sample fit; the earlier-only audit excluded it and preferred persistence. Same-round alignment and bounded capability equations are modeling assumptions, not verified simulator formulas.')
