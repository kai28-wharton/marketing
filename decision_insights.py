"""Reconciled observed bridges and explicitly assumed segment/Kahn diagnostics.

No decision-response coefficients are fitted and no segment-specific Kahn scores
or causal Brand-loss attribution are invented.
"""
from round_review import COMPANY, QUADRANTS

CROSSWALKS = {
    'product': {'BRAND':['BRAND','BREADTH','DEPTH'],
                'EXPERIENCE':['CUSTOMER SERVICE','SHOPPING EXPERIENCE'],
                'FRICTIONLESS':['ONLINE','RETAIL'],'LOW PRICE':['LOW PRICE']},
    'convenience': {'BRAND':['BRAND'],
                    'EXPERIENCE':['CUSTOMER SERVICE','SHOPPING EXPERIENCE'],
                    'FRICTIONLESS':['ONLINE','RETAIL','BREADTH','DEPTH'],'LOW PRICE':['LOW PRICE']},
}


def brand_analysis(data):
    a,b=data['rounds']['0'],data['rounds']['1']
    peers=[]
    for company in sorted({r['company'] for r in data['kahn']}):
        if company=='FAIR VALUE':continue
        values={r['round']:r['value'] for r in data['kahn'] if r['company']==company and r['quadrant']=='BRAND'}
        peers.append(dict(company=company,prior=values[0],current=values[1],change=values[1]-values[0]))
    other=[r for r in peers if r['company']!=COMPANY]
    p0=sum(r['prior'] for r in other)/len(other);p1=sum(r['current'] for r in other)/len(other)
    prior=a['scores']['BRAND'];current=b['scores']['BRAND']
    predicted=next(r['predicted'] for r in data['audit']['rows'] if r['metric']=='BRAND')
    return dict(prior=prior,current=current,change=current-prior,relative_change=current/prior-1,
                prior_rank=1+sum(r['prior']>prior for r in other),current_rank=1+sum(r['current']>current for r in other),
                peer_mean_prior=p0,peer_mean_current=p1,peer_mean_change=p1-p0,
                gap_prior=prior-p0,gap_current=current-p1,gap_change=(current-p1)-(prior-p0),
                peers=peers,predicted=predicted,modeled_change=predicted-prior,
                unexplained_residual=current-predicted,
                bridge=[dict(label='Round 0 Brand',value=prior),dict(label='Frozen v2 modeled change',value=predicted-prior),
                        dict(label='Model residual (not a cause)',value=current-predicted),dict(label='Round 1 Brand',value=current)],
                positions=[dict(r,change=r['current']-r['prior'],relative_change=r['current']/r['prior']-1 if r['prior'] else None)
                           for r in data['marketing']['positions']],
                decisions=[dict(key=f['key'],label=f['label'],reference=f['prior_reference'],submitted=f['baseline'],
                                change=f['baseline']-f['prior_reference'],unit=f['unit']) for f in data['factors']],
                conclusion='The 2.6-point fall is observed, not explained causally by the supplied files. Peer comparisons isolate relative deterioration, and position/input shifts identify tests—not proven causes.',
                hypotheses=[
                    dict(title='Product-range proposition changed',
                         evidence='Higher-cost depth position fell 5.0 → 1.2; lower-cost depth 3.7 → 1.7, while lower-cost breadth rose 2.4 → 3.9. Higher-cost submitted depth is 10.',
                         limit=f"The latest workbook has lower-cost depth {data['team']['decisions']['low_depth']:g} at {data['team']['cells']['low_depth']}. The old input reference is not a verified prior submission; the input-to-position transformation is still unidentified.",
                         test='Hold spending, price, quality and private-brand inputs fixed; test higher-cost depth alone and record Brand, category purchases, margin and inventory.'),
                    dict(title='Quality and private-brand proposition may interact',
                         evidence='Submitted private/national quality is 6/6; Private Brand inputs are 44/70. Brand still fell despite higher quality versus the old assumed 5/5 reference.',
                          limit='MV p12 now identifies Private Brand as mix. The 44/70 settings are not observed sales shares; no numeric separate mix/quality response or valuation coefficient is supplied.',
                          test='Test mix and quality separately under the documented CLV/brand and cost mechanisms, with vendor discipline and cash safeguards.'),
                    dict(title='Execution and competitive position need investigation',
                         evidence='Service position slipped 3.4 → 3.2; shopping experience rose 2.4 → 2.8. Experience Kahn improved 5.8 → 6.0 while Brand declined.',
                         limit='This contradicts a blanket claim that all customer experience weakened. Competitor changes and the simulator transformation remain confounded.',
                         test='Inspect brand-specific customer/category outcomes and simulator score definitions; do not respond with undifferentiated experience spending.'),
                ])


def financial_analysis(data):
    a,b=(data['rounds'][str(data.get(k,v))] for k,v in [('previous_round',0),('current_round',1)]);i0,i1=a['income'],b['income'];b0,b1=a['balance'],b['balance']
    totals=[sum(i[l+' Revenue'] for l in ('Lower Cost','Higher Cost')) for i in (i0,i1)]
    offerings=[]
    for label in ('Lower Cost','Higher Cost'):
        w0=i0[label+' Revenue']/totals[0];w1=i1[label+' Revenue']/totals[1]
        m0=1-i0[label+' COGS']/i0[label+' Revenue'];m1=1-i1[label+' COGS']/i1[label+' Revenue']
        key='low_markup' if label=='Lower Cost' else 'high_markup'
        markup=data['team']['decisions'][key]/100
        offerings.append(dict(offering=label,prior_margin=m0,current_margin=m1,margin_change_pp=100*(m1-m0),
                              implied_markup_prior=i0[label+' Revenue']/i0[label+' COGS']-1,
                              implied_markup_current=i1[label+' Revenue']/i1[label+' COGS']-1,
                              submitted_markup=markup,margin_at_submitted_markup=markup/(1+markup),
                              prior_mix=w0,current_mix=w1,within_effect_pp=100*w1*(m1-m0),mix_effect_pp=100*(w1-w0)*m0))
    margin_change=100*(b['ratios']['gross_margin']-a['ratios']['gross_margin'])
    within=sum(r['within_effect_pp'] for r in offerings);mix=sum(r['mix_effect_pp'] for r in offerings)
    dep_change=b1['Accumulated Depreciation']-b0['Accumulated Depreciation']
    cash_rows=[('Net income',i1['Net Income'],'observed earnings, not cash'),
               ('Depreciation add-back',i1['Depreciation'],'noncash expense; conditional bridge add-back'),
               ('Gross P&E increase proxy',-(b1['Property and Equipment']-b0['Property and Equipment']),'balance-sheet capital-movement proxy, not verified cash capex'),
               ('Receivables increase',-(b1['Accounts Receivable']-b0['Accounts Receivable']),'balance-sheet movement'),
               ('Inventory increase',-(b1['Inventory']-b0['Inventory']),'balance-sheet movement'),
               ('Payables increase',b1['Accounts Payable']-b0['Accounts Payable'],'balance-sheet movement'),
               ('Short-term loan change',b1['Short Term Loans']-b0['Short Term Loans'],'balance-sheet movement'),
               ('Long-term debt change',b1['Long Term Debt']-b0['Long Term Debt'],'balance-sheet movement')]
    cash_change=b1['Cash']-b0['Cash'];cash_proxy=sum(r[1] for r in cash_rows)
    revenue=i1['Net Revenue'];gross=i1['Gross Profit'];opex=i1['Operating Expenses'];interest=i1['Interest Expense']
    pretax=i1['Income Before Taxes'];tax_rate=i1['Income Taxes']/pretax
    def stress(label,gp_delta=0,interest_delta=0):
        p=pretax+gp_delta-interest_delta;net=p-max(0,p)*tax_rate
        return dict(label=label,pretax=p,net_income=net,net_income_change=net-i1['Net Income'])
    debt=b1['Short Term Loans']+b1['Long Term Debt']
    days_stock=i1['Cost of Goods Sold']/365*10
    return dict(margin_prior=a['ratios']['gross_margin'],margin_current=b['ratios']['gross_margin'],
                gross_profit_change=i1['Gross Profit']-i0['Gross Profit'],
                margin_change_pp=margin_change,offerings=offerings,within_effect_pp=within,mix_effect_pp=mix,
                margin_rounding_residual_pp=margin_change-within-mix,
                cash_prior=b0['Cash'],cash_current=b1['Cash'],cash_change=cash_change,cash_rows=[dict(label=l,value=v,basis=basis) for l,v,basis in cash_rows],
                cash_proxy_change=cash_proxy,cash_bridge_residual=cash_change-cash_proxy,
                depreciation_reconciliation=i1['Depreciation']-dep_change,
                equity_vs_income_residual=(b1['Shareholder’s Equity']-b0['Shareholder’s Equity'])-i1['Net Income'],
                current_ratio_prior=a['ratios']['current_ratio'],current_ratio=b['ratios']['current_ratio'],
                quick_ratio_prior=a['ratios']['quick_ratio'],quick_ratio=b['ratios']['quick_ratio'],
                working_capital=b['ratios']['working_capital'],working_capital_change=b['ratios']['working_capital']-a['ratios']['working_capital'],
                inventory_current_asset_share=b1['Inventory']/b1['Total Current Assets'],
                ebit=b['ratios']['ebit'],interest=interest,interest_cover=b['ratios']['interest_cover'],
                interest_ebit_share=interest/b['ratios']['ebit'],pretax_buffer=pretax,
                break_even_margin=(opex+interest)/revenue,margin_buffer_pp=100*pretax/revenue,
                sales_decline_to_pretax_breakeven=pretax/gross,
                additional_ebit_for_2x_cover=max(0,2*interest-b['ratios']['ebit']),
                stress=[stress('Gross margin −1 percentage point',gp_delta=-.01*revenue),
                        stress('Revenue −5%, same gross margin',gp_delta=-.05*gross),
                        stress('Borrowing cost +1pp on period-end debt',interest_delta=.01*debt)],
                ten_days_inventory_funding=days_stock,ten_days_inventory_cash_share=days_stock/b1['Cash'],
                cash_boundary='Balance-sheet-consistent bridge, not a supplied cash-flow statement. Gross P&E movement is a proxy; disposals, noncash capex, reclassifications and timing cannot be identified. Residual agreement does not verify cash capex.',
                stress_boundary='Independent one-way arithmetic stresses, not forecasts or combined cases. Opex/interest held fixed except the named shock; tax uses the observed positive-income rate with no loss refund. Inventory stress assumes 365 days and is not the simulator DOI definition.')


def segment_analysis(data,lens):
    mapping=CROSSWALKS[lens];a,b=(data['rounds'][str(data.get(k,v))] for k,v in [('previous_round',0),('current_round',1)]);segments=[]
    total0=sum(s['prior_revenue'] for s in data['marketing']['segments'])
    for s in data['marketing']['segments']:
        weights={}
        for rnd,p in [(0,s['prior_preferences']),(1,s['preferences'])]:
            denom=sum(p.values());weights[rnd]={q:sum(p[k] for k in attrs)/denom for q,attrs in mapping.items()}
        index0=sum(weights[0][q]*a['scores'][q] for q in QUADRANTS)
        index1=sum(weights[1][q]*b['scores'][q] for q in QUADRANTS)
        score_effects={q:weights[1][q]*(b['scores'][q]-a['scores'][q]) for q in QUADRANTS}
        preference_effect=sum((weights[1][q]-weights[0][q])*a['scores'][q] for q in QUADRANTS)
        segments.append(dict(id=s['id'],revenue=s['revenue'],growth=s['growth'],
                             prior_revenue_share=s['prior_revenue']/total0,revenue_share=s['revenue_share'],
                             weights=weights[1],prior_index=index0,current_index=index1,index_change=index1-index0,
                             score_effects=score_effects,preference_effect=preference_effect,
                             brand_exposure=s['revenue_share']*weights[1]['BRAND']))
    p0=sum(s['prior_revenue_share']*s['prior_index'] for s in segments)
    p1=sum(s['revenue_share']*s['current_index'] for s in segments)
    return dict(lens=lens,mapping=mapping,segments=segments,prior_portfolio_index=p0,current_portfolio_index=p1,
                portfolio_change=p1-p0,within_effect=sum(s['revenue_share']*s['index_change'] for s in segments),
                mix_effect=sum((s['revenue_share']-s['prior_revenue_share'])*s['prior_index'] for s in segments),
                most_brand_sensitive=max(segments,key=lambda s:s['weights']['BRAND'])['id'],
                largest_brand_exposure=max(segments,key=lambda s:s['brand_exposure'])['id'],
                boundary='Descriptive preference-weighted company-score index, not measured segment Kahn, utility, causal impact, revenue at risk or a forecast. All segments face the same company scores; only assumed weights differ. Changing the crosswalk changes conclusions, not decisions or the backend model.')


def build_insights(data):
    return dict(brand=brand_analysis(data),finance=financial_analysis(data),
                segment_lenses={key:segment_analysis(data,key) for key in CROSSWALKS})
