"""Shared disclosure and data-readiness content; no optimizer or cost estimates."""

LIMITATIONS = [
    'This is an uncalibrated sensitivity model, not an optimization model. Increasing all four settings can mechanically improve modeled demand and profit because the added assortment costs and downsides are not priced. Do not interpret 100/100/100/100 as an optimum.',
    'Breadth/depth are 1–100 indices in the supplied screenshot, not verified percentages, SKU counts or budget shares. They do not have to sum to 100. Depth is not automatically inventory units per SKU; the simulator’s precise definitions and legal bounds need verification.',
    'Kahn v2 gives both segments the same per-index breadth and depth coefficients. Equal changes in lower/higher-cost breadth (or depth) currently have identical effects. Segment-specific assortment elasticities are unknown.',
    'Breadth currently affects Brand and Experience; depth affects Frictionless. Low-price positioning does not directly change when these four inputs change and markups are fixed. These are illustrative model links, not simulator rules.',
    'Financial estimates propagate modeled demand through revenue and volume-related COGS in both segments. They exclude assortment implementation, incremental inventory, markdowns, stockouts, cannibalization, choice overload, space limits and working-capital costs.',
    'Known investment spending remains fixed, but this does not mean assortment changes are free or affordable. All profit estimates are before unknown assortment costs. Additional inventory is an asset/cash-funding requirement, not automatically an immediate expense.',
    'There are zero paired historical decision/next-round-outcome observations suitable for causal calibration in the current data. Structural stress ranges are not statistical confidence intervals or validated forecast errors.',
    'Green/red changes indicate positive/negative numbers, not financial desirability. For example, an increase in COGS is green by the requested sign convention but is not itself a financial benefit.',
    'Industry minimum/maximum values are observed benchmarks, not verified simulator constraints. More precise-looking decimal output does not make the underlying assumptions more reliable.',
]


def build_readiness(data):
    tables={key:{r['name']:r['value'] for r in data[key]} for key in ('balance','income','scorecard')}
    known=[]
    for label,table,name,unit,source in [
        ('Inventory','balance','Inventory','$','materials/balanceSheet-round0.csv'),
        ('Cash','balance','Cash','$','materials/balanceSheet-round0.csv'),
        ('Days of inventory','scorecard','Days of Inventory','days','materials/scorecard-round0.csv'),
        ('WACC','scorecard','Weighted Average Cost of Capital (WACC)','%','materials/scorecard-round0.csv'),
    ]:
        known.append({'label':label,'value':tables[table].get(name),'unit':unit,'source':source})
    assets=tables['balance'].get('Total Current Assets')
    liabilities=tables['balance'].get('Total Current Liabilities')
    income=tables['income']
    total=income.get('Net Revenue',0)
    low_revenue=income.get('Lower Cost Revenue',0)
    high_revenue=income.get('Higher Cost Revenue',0)
    marketing=data.get('marketing',{})
    result = {
        'recommendation_evidence':{
            'low_revenue_share':low_revenue/total if total else None,
            'low_gross_margin':(low_revenue-income.get('Lower Cost COGS',0))/low_revenue if low_revenue else None,
            'high_gross_margin':(high_revenue-income.get('Higher Cost COGS',0))/high_revenue if high_revenue else None,
            'source':'materials/incomeStatement-round0.csv',
        },
        'status':'Not ready to establish an optimum — critical marginal-response, cost and constraint data are missing.',
        'limitations':list(LIMITATIONS),'known_data':known,
        'liquidity':{'current_assets':assets,'current_liabilities':liabilities,
                     'current_ratio':assets/liabilities if assets is not None and liabilities else None},
        'inventory_note':'The balance sheet anchors existing inventory; it does not tell us how changing an assortment index changes SKUs, units, purchases or cash requirements. Do not assume inventory is proportional to breadth × depth.',
        'capital_note':'WACC is a possible economic opportunity-cost benchmark, not a verified inventory carrying rate or an extra accounting expense. If used, separate economic-profit analysis from accounting profit and avoid double-counting financing costs already included.',
        'requirements':[
            {'topic':'Starting financial and positioning baseline','status':'Available',
             'have':'Round-0 inventory, cash, COGS, expenses, interest, Kahn scores and reported operating metrics.',
             'need':'Confirm round duration and metric definitions. These anchor a model but do not establish marginal assortment effects.',
             'where':'Existing balance sheet, income statement, scorecard and Kahn CSVs; simulator accounting guide.',
             'why':'Reconcile the starting point and ensure future costs are not counted twice.'},
            {'topic':'Meaning of each index and allowed decisions','status':'Partial',
             'have':'A screenshot with 1–100 breadth/depth settings and cross-sectional industry ranges.',
             'need':'Exact index-to-category/SKU mapping for both segments, legal bounds, and what depth means in this simulation.',
             'where':'Breadth/depth information icons, simulator help, case instructions or instructor materials.',
             'why':'Translate a setting change into an operational change; benchmark ranges are not legal limits.'},
            {'topic':'Assortment → inventory and purchase requirements','status':'Missing',
             'have':'Aggregate starting inventory, not the inventory required by each setting.',
             'need':'SKU counts, inventory by segment, minimum stock/order quantities, lead times, unit costs and purchasing rules at different index levels.',
             'where':'Detailed SKU/inventory/purchasing reports and simulator inventory formulas.',
             'why':'Estimate inventory investment, replenishment, stockouts and working-capital needs.'},
            {'topic':'Incremental assortment and holding costs','status':'Missing',
             'have':'Aggregate COGS/expenses and reported product-cost metrics, but no verified incremental rate per index or SKU.',
             'need':'Incremental buying, handling, merchandising, storage, shrinkage and expected markdown/obsolescence costs; identify what is already included in COGS/opex.',
             'where':'Cost schedules, operating reports, vendor terms and simulation rules.',
             'why':'Prevent a free-assortment assumption and calculate profit after the extra costs without double-counting.'},
            {'topic':'Segment demand and Kahn response','status':'Missing',
             'have':'Three Kahn rounds and current segment revenue/COGS, without paired historical decisions that caused those outcomes.',
             'need':'Actual submitted decisions linked to subsequent scores, segment sales/units, prices and customer preferences; competitor/environment changes; nonlinear or cannibalization effects.',
             'where':'Prior and future round decision exports and outcome reports; customer research; simulator response rules.',
             'why':'Estimate benefits, diminishing returns and possible downsides rather than reward every increase.'},
            {'topic':'Cash, credit and payment timing','status':'Partial',
             'have':'Current cash, receivables, payables, debt, interest expense and WACC.',
             'need':'Supplier/customer payment timing, purchases, credit availability/limits, marginal borrowing rates, minimum cash and forecast financing rules.',
             'where':'Cash-flow/financing reports, loan terms and the simulator finance guide.',
             'why':'A plan can improve modeled profit but still be unaffordable; inventory investment must be funded.'},
            {'topic':'Physical and operational constraints','status':'Missing',
             'have':'Retail coverage and service/vendor spending, not capacity constraints.',
             'need':'Shelf/warehouse capacity, service workload, stockout/service standards and implementation/time-lag restrictions.',
             'where':'Store/warehouse/operations reports and simulator constraints.',
             'why':'Exclude operationally impossible assortments and price the effect on service and convenience.'},
            {'topic':'Agreed marketing–finance objective','status':'Team decision',
             'have':'A general aim to protect Brand/Experience and improve Frictionless.',
             'need':'Explicit Kahn targets/weights, minimum service levels, acceptable profit/loss, cash/debt/inventory caps, horizon and risk tolerance.',
             'where':'Learning-team agreement, informed by the case strategy and verified finance constraints.',
             'why':'“Optimal” is undefined until the team specifies which benefits to pursue and which financial risks to accept.'},
        ],
        'balance_steps':[
            'Agree the objective: maximize profit after verified assortment costs subject to explicit Kahn/service targets, or compare a Pareto frontier of marketing and financial trade-offs. Do not maximize all scores alone.',
            'Model revenue and segment COGS, then add only incremental operating/markdown costs not already counted. Treat inventory investment as an asset and cash-flow requirement; include financing consistently.',
            'Enforce minimum cash, available credit, known investment budget, inventory/space limits and verified simulator bounds. Keep the remaining 12 decisions fixed for this experiment.',
            'Collect paired decisions/outcomes, calibrate response/cost assumptions, and test on held-out rounds against unchanged-plan baselines. Use stress scenarios until reliable evidence exists; do not claim measured accuracy without validation.',
        ],
    }
    if marketing.get('available'):
        result['recommendation_evidence']['marketing']={
            'positions':{p['attribute']:{'own':p['own'],'rank':p['rank_numeric'],'count':p['companies']} for p in marketing['positions']},
            'breadth_priority_segment':max(marketing['segments'],key=lambda s:s['preferences']['BREADTH'])['id'],
            'breadth_priority_value':max(s['preferences']['BREADTH'] for s in marketing['segments']),
        }
        row=next(r for r in result['requirements'] if r['topic']=='Segment demand and Kahn response')
        row.update(status='Partial',
                   have='Six segment preference profiles, three rounds of reported size/revenue/CLV, and current competitor product positions. Segment revenue reconciles to company revenue; it is not industry TAM.',
                   need='Verified segment-size units and buyer counts for penetration; segment-by-offering purchases/inventory; paired submitted decisions and next-round outcomes; causal elasticities, cannibalization and competitor/environment controls.',
                   where='New materials/marketing CSVs supply descriptive evidence. Obtain simulator definitions, segment-by-offering reports and subsequent decision/outcome exports for the remaining gaps.')
        result['limitations'].append('New segment preferences and competitor positions are descriptive, not calibrated assortment response. Segment-by-cost-tier affinity and buyer penetration remain unknown; the segment-alignment panel does not alter the financial or Kahn forecast.')
    return result
