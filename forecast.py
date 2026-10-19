"""Two-period what-if projections. No repeated compounding of decision effects."""
import math

DEFAULT_PLANNING = {'market_growth': 0., 'cogs_inflation': 0.,
                    'year1_realization': 1., 'year2_catchup': .5}
PERIODS = ['Round 0 actual', 'Year 1 / Round 1', 'Year 2 / Round 2']


def validate_planning(planning):
    if planning is None:
        return dict(DEFAULT_PLANNING)
    if not isinstance(planning, dict) or set(planning) - set(DEFAULT_PLANNING):
        raise ValueError('Unknown Year-2 planning assumption.')
    clean = dict(DEFAULT_PLANNING, **planning)
    for key, lo, hi in [('market_growth', -.2, .2), ('cogs_inflation', -.1, .3),
                         ('year1_realization', 0, 1), ('year2_catchup', 0, 1)]:
        value = clean[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
            raise ValueError(f'{key} must be a finite number between {lo} and {hi}.')
    return clean


def forecast_plan(plan, assumptions, planning, data, reference, evaluate):
    target = evaluate(plan, assumptions, data)
    p, a = target['decisions'], target['assumptions']
    income = {r['name']:r['value'] for r in data['income']}
    scores = {r['quadrant']:r['value'] for r in data['kahn'] if r['round']==0 and r['company']=="GETCHELL'S"}
    actual = dict(period=PERIODS[0], year=0, revenue=income['Net Revenue'], cogs=income['Cost of Goods Sold'],
                  gross_profit=income['Gross Profit'], gross_margin=income['Gross Profit']/income['Net Revenue'],
                  operating_expenses=income['Operating Expenses'], ebit=income['Gross Profit']-income['Operating Expenses'],
                  interest=income['Interest Expense'], taxes=income['Income Taxes'], net_income=income['Net Income'],
                  return_on_sales=income['Net Income']/income['Net Revenue'], scores=scores,
                  explicit_spend=None, remaining=None, feasible=None)
    rows = [actual]
    realized = planning['year1_realization']
    spend_delta = target['spent']-sum(reference[k] for k in ('online','service','experience','vendor','analytics'))
    for year in (1, 2):
        if year == 2:
            realized += (1-realized)*planning['year2_catchup']
        score = {q:scores[q]+realized*(target['scores'][q]-scores[q]) for q in scores}
        gain = sum((score[q]-scores[q])*w for q,w in [('BRAND',.35),('EXPERIENCE',.35),('FRICTIONLESS',.2),('LOW PRICE',.1)])
        demand = a['demand_response']*gain
        revenue = cogs = 0.
        for prefix, label in [('low','Lower Cost'), ('high','Higher Cost')]:
            price = (1+p[prefix+'_markup']/100)/(1+reference[prefix+'_markup']/100)
            units = max(.1, 1+demand-a['price_elasticity']*(price-1))
            units *= (1+planning['market_growth'])**year
            revenue += income[label+' Revenue']*price*units
            cogs += income[label+' COGS']*units*(1+planning['cogs_inflation'])**year
        gross = revenue-cogs
        expenses = income['Operating Expenses']+spend_delta
        ebit = gross-expenses
        profit = ebit-income['Interest Expense']
        stress = revenue*a['uncertainty']
        ranges = {}
        for q in scores:
            lo, hi = target['kahn']['intervals'][q]
            floor = target['kahn']['historical_evidence'][q]['stress_floor']
            ranges[q] = [max(0, scores[q]+realized*(lo-scores[q])-floor*(1-realized)),
                         min(10, scores[q]+realized*(hi-scores[q])+floor*(1-realized))]
        rows.append(dict(period=PERIODS[year], year=year, realization=realized, revenue=revenue, cogs=cogs,
                         gross_profit=gross, gross_margin=gross/revenue, operating_expenses=expenses, ebit=ebit,
                         interest=income['Interest Expense'], taxes=0, net_income=profit, return_on_sales=profit/revenue,
                         scores=score, score_ranges=ranges, explicit_spend=target['spent'], remaining=target['remaining'],
                         feasible=target['feasible'], revenue_range=[revenue-stress,revenue+stress],
                         profit_range=[profit-stress,profit+stress]))
    return dict(decisions=p, assumptions=a, planning=planning, model_version=target['model_version'],
                periods=rows, warnings=target['warnings'], unpriced_changes=target['unpriced_changes'],
                feasible=target['feasible'], cumulative_projected_net_income=sum(r['net_income'] for r in rows[1:]))


def project(payload, data, reference, evaluate):
    planning = validate_planning(payload.get('planning'))
    # evaluate() validates the full decision and model-assumption payload.
    custom = forecast_plan(payload.get('decisions'), payload.get('assumptions'), planning, data, reference, evaluate)
    controlled = dict(reference, online=2_500_000, service=15_300_000, experience=10_200_000)
    presets = [
        ('reference', 'Screenshot reference', reference),
        ('controlled', 'Controlled service + convenience test', controlled),
        ('brand', 'Conditional brand-quality test — unpriced', dict(controlled, national_quality=6)),
    ]
    comparisons = []
    for key, name, plan in presets:
        result = forecast_plan(plan, custom['assumptions'], planning, data, reference, evaluate)
        comparisons.append(dict(key=key, name=name, **result))
    return dict(working=custom, comparisons=comparisons, periods=PERIODS,
                planning_defaults=DEFAULT_PLANNING,
                convention='Year 1 = next simulated round (Round 1); Year 2 = following round (Round 2). These are planning periods, not verified calendar-year durations.',
                methodology=[
                    'Same decision plan and nominal explicit investment budget in both projected periods; spending recurs annually.',
                    'Each Kahn score converges toward one fixed v2 target. Year-1 realization is a fraction of the total change; Year 2 captures the chosen fraction of the remainder. Identical investments do not repeatedly add the same score gain.',
                    'Market-growth and COGS-inflation assumptions compound from Round 0 for one/two periods; defaults are zero.',
                    'Segment price and demand are recomputed relative to Round 0 each period, not repeatedly multiplied by the same decision uplift.',
                    'Operating expense = Round-0 operating expense + full annual change in five-field spending, even if benefits are delayed. Historical operating costs and interest otherwise stay fixed; taxes assumed zero.',
                    'Revenue/profit stress ranges are user-defined stresses, not confidence intervals. Kahn bands are structural scenario envelopes.',
                    'No projected cash balance, financing, balance sheet or market share is fabricated. Store, quality and assortment implementation costs remain unknown and excluded.',
                    'Budget checks cover only five known spending fields in each period; unpriced changes can make apparent headroom misleading.',
                ])
