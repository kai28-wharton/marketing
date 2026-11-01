"""Round-1-anchored conditional sensitivity, not a fitted simulation replica."""
from guided_prediction import scores, WEIGHTS, FACTOR_FEATURES
from round_review import QUADRANTS
from decision_economics import calculate

VERSION='review-4.0'
MEANINGS={
    'low_markup':'Defined as markup on lower-cost product cost. Both cost changes and markup changes alter the selling-price ratio.',
    'high_markup':'Markup over higher-cost product cost. Affects assumed price and volume, not company market value directly.',
    'low_breadth':'Number of categories; enables one-stop shopping but requires more inventory. The numeric stock response remains a scenario assumption.',
    'high_breadth':'Higher-cost categories; retained assortment ties up working capital and financing. No inventory holding expense in this simulation (MV 12, 14).',
    'low_depth':'Choice within lower-cost product lines; not verified stock units or SKU count.',
    'high_depth':'Choice within higher-cost product lines; depth reductions coincided with lower reported depth positions, not an isolated causal test.',
    'low_private':'Private-brand mix (MV 12), resolving the duplicated Markdown definition. Not measured sales share. Loyalty, margin and valuation response rates remain unavailable.',
    'high_private':'Higher-cost private-brand mix (MV 12). Direct differentiation and CLV/brand valuation mechanisms are documented; no numeric mix-response function is supplied.',
    'private_quality':'Higher median private-brand quality raises unit cost. Scenario cost response uses assumed equal private/national quality exposure, not fitted shares.',
    'national_quality':'National-brand quality raises unit cost. The source line is unlabeled; its national-brand wording is retained with that caveat.',
    'coverage':'Stores change access, not customer preferences. New-store cost $1.75M (MV 14); financing split, access demand, working-capital and closure rules remain unquantified.',
    'online':'Website infrastructure investment is partly capitalized and partly expensed. The latest observed expense/input ratio is a provisional split, not a verified marginal rule.',
    'service':'Service allocation; accounting service expense exceeds the submitted decision. A larger allocation is not a measured satisfaction gain.',
    'experience':'Store infrastructure, convenience and ambience; partly capitalized. The latest observed expense/input split is provisional; capital still consumes cash.',
    'vendor':'MV 13: fully expensed, highly retained COGS improvement over time; Intro 14: Low Price. No direct Brand response is asserted. Persistence rates are unknown.',
    'analytics':'MV 13: pure multiplier of online and experience, not standalone demand. Expensed; no separately capitalized asset. An operating score of 100% is not a marginal-return coefficient.',
}


def _adapter(data):
    current=data.get('current_round',1);latest=data['rounds'][str(current)]
    return dict(factors=data['factors'],scorecard=[dict(name=k,value=v) for k,v in latest['scorecard'].items()],
                kahn=[dict(row,round=row['round']-current) for row in data['kahn']])


def evaluate(plan, data, assumptions=None, economics=None):
    if not data.get('availability',{}).get('prediction_available',True):
        raise ValueError(f"Round {data['current_round']} financial exports are missing. Predictions and optimization require the current income statement, balance sheet and scorecard.")
    from app import validate, SPEND
    plan,a=validate(plan,assumptions)
    if not plan['coverage'].is_integer():
        raise ValueError('Retail coverage must be a whole number of physical stores.')
    reference=data['team']['decisions'];now=data['rounds'][str(data.get('current_round',1))];inc=now['income']
    projection=scores(plan,reference,now['scores'],_adapter(data),a['score_response'])
    gain=sum((projection[q]-now['scores'][q])*w for q,w in [('BRAND',.35),('EXPERIENCE',.35),('FRICTIONLESS',.2),('LOW PRICE',.1)])
    effects=calculate(plan,data,a,gain,economics)
    net=effects['net_income'];revenue=effects['revenue']
    multiple=now['scorecard']['Market Value']/inc['Net Income'] if inc['Net Income']>0 else None
    unchanged=plan==reference
    implied=now['scorecard']['Market Value'] if unchanged else None
    market_delta=implied-now['scorecard']['Market Value'] if implied is not None else None
    spent=sum(plan[k] for k in SPEND)
    unpriced=[f['label'] for f in data['factors'] if not f['priced'] and plan[f['key']]!=reference[f['key']]]
    missing_channels=['brand_depth_response'] if any(plan[key]!=reference[key] for key in ('low_depth','high_depth')) else []
    if any(plan[key]!=reference[key] for key in ('low_breadth','high_breadth')):missing_channels.append('assortment_loyalty_response')
    if plan['coverage']!=reference['coverage']:missing_channels.append('store_access_financing_response')
    if any(plan[key]!=reference[key] for key in ('low_private','high_private')):missing_channels.append('private_mix_loyalty_valuation_response')
    brand_channels=[k for k in missing_channels if k in ('brand_depth_response','assortment_loyalty_response','private_mix_loyalty_valuation_response')]
    brand_inputs=[dict(key=f['key'],label=f['label'],reference=reference[f['key']],current=plan[f['key']])
                  for f in data['factors'] if f['key'] in ('low_depth','high_depth','low_breadth','high_breadth','low_private','high_private')
                  and plan[f['key']]!=reference[f['key']]]
    brand_diagnostic=dict(status='partial' if brand_channels else 'conditional',reference=now['scores']['BRAND'],
                          modeled_component_score=projection['BRAND'],
                          full_prediction=None if brand_channels else projection['BRAND'],
                          missing_channels=brand_channels,changed_inputs=brand_inputs,
                          boundary=f"The numeric component includes the export-{data.get('current_round',1)} anchor and modeled quality response only. Changed depth, breadth and private-mix responses are not estimated; the full Brand forecast is unknown when these channels are missing. This component is not a lower bound.")
    score_stress={r['metric']:abs(r['error']) for r in data['audit']['rows'] if r['metric'] in QUADRANTS}
    return dict(**effects,version=data['model']['version'] if data.get('current_round',1)>=2 else VERSION,decisions=plan,assumptions=a,scores=projection,
                 score_changes={q:projection[q]-now['scores'][q] for q in QUADRANTS},
                  score_stress={q:[max(0,projection[q]-score_stress[q]),min(10,projection[q]+score_stress[q])] if q in score_stress else None for q in QUADRANTS},
                revenue_delta=revenue-inc['Net Revenue'],profit_delta=net-inc['Net Income'],
                explicit_spend=spent,historical_headroom=data['historical_budget']-spent,
                 market_value=implied,market_value_delta=market_delta,earnings_multiple=multiple,
                 valuation_status='observed_reference_only' if unchanged else 'unquantified_simulator_valuation',
                 unresolved_valuation=['dcf_forecast_and_terminal_rules','strategy_horizon_mapping','credit_wacc_schedule','clv_brand_floor','liquidation_floor'],
                unpriced_changes=unpriced,
                 unresolved_model_channels=missing_channels,
                 score_diagnostics={'BRAND':brand_diagnostic},
                  valuation_boundary=f"MV 2–6: max of DCF, CLV/private-brand and liquidation values. No fixed-P/E forecast. Unchanged reference displays reported export-{data.get('current_round',1)} value, not a revaluation under economic edits. Changed-plan value is unavailable because forecast/floor rules are missing.",
                  stress_boundary='Score envelope is ± absolute frozen-model error, where available, clipped at 0–10. Null means no frozen pre-outcome forecast error is available; not a confidence interval.',
                warnings=data['model']['limitations']+(['Unresolved economic pathways: '+', '.join(effects['unresolved_economics'])+'. Profit and value are partial; optimizer cannot treat unknown effects as zero.'] if effects['unresolved_economics'] else [])+
                          (['Unmodeled channels: '+', '.join(missing_channels)+'. Numeric score/profit diagnostics omit these effects; optimization is blocked.'] if missing_channels else []))


def factor_probes(data,plan=None,assumptions=None,economics=None):
    plan=plan or data['team']['decisions']
    start=evaluate(plan,data,assumptions,economics)
    out=[]
    for f in data['factors']:
        key=f['key'];step=1_000_000 if f['unit']=='$' else 25 if key=='coverage' else 5 if f['unit']=='%' or 'breadth' in key or 'depth' in key else 1
        row=dict(key=key,label=f['label'],unit=f['unit'],step=step,meaning=MEANINGS[key],
                 definition_status='Definition supplied; numeric response is provisional.' if data['definitions_available'] else 'Provisional: definition source missing.',
                 affected_quadrants=[q for q in QUADRANTS if any(feature in WEIGHTS[q] for feature in FACTOR_FEATURES[key])],
                 historical_reference=f['prior_reference'],submitted=data['team']['decisions'][key])
        for direction,sign in [('increase',1),('decrease',-1)]:
            value=plan[key]+sign*step
            if value<f['min'] or value>f['max']:
                row[direction]=None;continue
            trial=evaluate(dict(plan,**{key:value}),data,assumptions,economics)
            row[direction]=dict(value=value,score_changes={q:trial['scores'][q]-start['scores'][q] for q in QUADRANTS},
                                 profit_delta=trial['net_income']-start['net_income'],
                                 market_value_delta=trial['market_value']-start['market_value'] if trial['market_value'] is not None and start['market_value'] is not None else None,
                                  inventory_change=trial['inventory']-start['inventory'],
                                  incremental_cash_delta=trial['incremental_cash_delta']-start['incremental_cash_delta'],
                                  unresolved_economics=trial['unresolved_economics'],unpriced=not f['priced'])
            row[direction]['unresolved_model_channels']=trial['unresolved_model_channels']
        out.append(row)
    return out
