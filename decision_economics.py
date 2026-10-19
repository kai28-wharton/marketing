"""Definition-supported pathways with explicit, unestimated scenario coefficients.

None means unknown, not a learned zero. A partial diagnostic can use a zero
placeholder, but the optimizer must reject affected candidates with unresolved
pathways. Capitalization splits inferred from R1 expense/input are provisional.
"""
import math

SCHEMA = {
    'quality_cost_per_point': (0, 1, 'Unit-cost log change per average quality point; equal private/national exposure is assumed'),
    'vendor_cost_sensitivity': (0, 5, 'Unit-cost log reduction per vendor capacity change'),
    'vendor_inventory_sensitivity': (0, 5, 'Inventory log reduction per vendor capacity change'),
    'breadth_inventory_sensitivity': (0, 5, 'Inventory log increase per 100 breadth-index points'),
    'depth_inventory_sensitivity': (0, 5, 'Inventory log increase per 100 depth-index points; pathway supported by MV 12, numeric rate unknown'),
    'inventory_holding_rate': (0, 0, 'Zero: MV 14 explicitly excludes inventory holding expense; funding and interest remain separate'),
    'inventory_financing_rate': (0, 1, 'Incremental period financing expense / inventory dollars'),
    'new_capital_depreciation_rate': (0, 1, 'Same-period depreciation / incremental capitalized spending'),
    'new_store_capex': (1_750_000, 1_750_000, 'MV 14: fixed capital cost per additional store (USD); debt/cash split is not supplied'),
    'closed_store_book_value': (0, 100_000_000, 'Book value per closed store (USD)'),
    'store_recovery_fraction': (0, 1, 'Fraction of closed-store book value recovered in cash'),
    'online_expense_fraction': (0, 1, 'Expensed share of online investment; remainder capitalized (provisional latest observed split)'),
    'experience_expense_fraction': (0, 1, 'Expensed share of experience investment; remainder capitalized (provisional latest observed split)'),
}


def scenario(data, values=None):
    if values is not None and (not isinstance(values, dict) or set(values)-set(SCHEMA)):
        raise ValueError('Unknown economic scenario field.')
    out={k:None for k in SCHEMA}
    ratios={r['key']:r['ratio'] for r in data['accounting']}
    out.update(online_expense_fraction=ratios['online'],experience_expense_fraction=ratios['experience'])
    out.update(inventory_holding_rate=0,new_store_capex=1_750_000)
    out.update(values or {})
    for key,value in out.items():
        lo,hi,_=SCHEMA[key]
        if value is None:
            if key in ('inventory_holding_rate','new_store_capex'):raise ValueError(key+' is specified by the supplied simulation slides; it cannot be unknown.')
            if key.endswith('expense_fraction'):raise ValueError(key+' must be specified.')
            continue
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
            raise ValueError(f'{key} must be a finite number between {lo} and {hi}, or unknown (null).')
    return out


def calculate(plan,data,a,gain,values=None):
    e=scenario(data,values)
    ref=data['team']['decisions'];now=data['rounds'][str(data.get('current_round',1))];inc=now['income'];bal=now['balance']
    unresolved=[]
    def coefficient(key,active=True):
        if e[key] is None:
            if active:unresolved.append(key)
            return 0.
        return e[key]
    def sat(v,h):return v/(v+h)
    half=next(f['industry']['average'] for f in data['factors'] if f['key']=='vendor')
    vendor_delta=sat(plan['vendor'],half)-sat(ref['vendor'],half)
    vendor_cost=coefficient('vendor_cost_sensitivity',abs(vendor_delta)>1e-12)
    vendor_inventory=coefficient('vendor_inventory_sensitivity',abs(vendor_delta)>1e-12)
    quality_delta=((plan['private_quality']-ref['private_quality'])+(plan['national_quality']-ref['national_quality']))/2
    quality_changed=any(plan[k]!=ref[k] for k in ('private_quality','national_quality'))
    quality_cost=coefficient('quality_cost_per_point',quality_changed)
    # Mix is identified by MV 12, but its economic response/exposures are not.
    for key in ('low_private','high_private'):
        if plan[key]!=ref[key]:unresolved.append(key+'_mix_response')
    offerings={};inventory=0.
    tier_total=inc['Lower Cost COGS']+inc['Higher Cost COGS']
    for tier,label in [('low','Lower Cost'),('high','Higher Cost')]:
        unit_cost_ratio=math.exp(quality_cost*quality_delta-vendor_cost*vendor_delta)
        markup_ratio=(1+plan[tier+'_markup']/100)/(1+ref[tier+'_markup']/100)
        price_ratio=unit_cost_ratio*markup_ratio
        units=max(.1,1+a['demand_response']*gain-a['price_elasticity']*(price_ratio-1))
        revenue=inc[label+' Revenue']*price_ratio*units
        cogs=inc[label+' COGS']*unit_cost_ratio*units
        breadth=(plan[tier+'_breadth']-ref[tier+'_breadth'])/100
        depth=(plan[tier+'_depth']-ref[tier+'_depth'])/100
        inventory_multiplier=math.exp(coefficient('breadth_inventory_sensitivity',breadth!=0)*breadth+
                                      coefficient('depth_inventory_sensitivity',depth!=0)*depth-vendor_inventory*vendor_delta)
        # R1 COGS shares allocate the stock pool, not unobserved private-brand shares.
        stock=bal['Inventory']*inc[label+' COGS']/tier_total*unit_cost_ratio*units*inventory_multiplier
        inventory+=stock
        offerings[tier]=dict(revenue=revenue,cogs=cogs,unit_ratio=units,price_ratio=price_ratio,
                              unit_cost_ratio=unit_cost_ratio,inventory=stock)
    inventory_change=inventory-bal['Inventory']
    if abs(inventory_change)<1e-7:inventory_change=0.;inventory=bal['Inventory']
    holding=max(0,inventory_change)*coefficient('inventory_holding_rate',inventory_change!=0)
    financing=max(0,inventory_change)*coefficient('inventory_financing_rate',inventory_change!=0)
    # Full investment dollars remain in cash use, even when expense is a fraction.
    online_delta=plan['online']-ref['online'];experience_delta=plan['experience']-ref['experience']
    capital=online_delta*(1-e['online_expense_fraction'])+experience_delta*(1-e['experience_expense_fraction'])
    expense=online_delta*e['online_expense_fraction']+experience_delta*e['experience_expense_fraction']
    service_ratio=next(r['ratio'] for r in data['accounting'] if r['key']=='service')
    expense+=(plan['service']-ref['service'])*service_ratio+(plan['vendor']-ref['vendor'])+(plan['analytics']-ref['analytics'])
    stores=plan['coverage']-ref['coverage'];proceeds=writeoff=0.
    store_capex=stores*coefficient('new_store_capex') if stores>0 else 0.
    capital+=store_capex
    if stores<0:
        book=(-stores)*coefficient('closed_store_book_value')
        recovery=coefficient('store_recovery_fraction')
        proceeds=book*recovery;writeoff=book-proceeds
    capital_changed=online_delta!=0 or experience_delta!=0 or stores>0
    depreciation=capital*coefficient('new_capital_depreciation_rate',capital_changed)
    expense+=holding+depreciation+writeoff
    revenue=inc['Net Revenue']+sum(offerings[t]['revenue']-inc[l+' Revenue'] for t,l in [('low','Lower Cost'),('high','Higher Cost')])
    cogs=inc['Cost of Goods Sold']+sum(offerings[t]['cogs']-inc[l+' COGS'] for t,l in [('low','Lower Cost'),('high','Higher Cost')])
    gross=inc['Gross Profit']+(revenue-inc['Net Revenue'])-(cogs-inc['Cost of Goods Sold'])
    pretax=inc['Income Before Taxes']+gross-inc['Gross Profit']-expense-financing
    rate=inc['Income Taxes']/inc['Income Before Taxes']
    tax=max(0,pretax)*rate;net=inc['Net Income']+(pretax-inc['Income Before Taxes'])-(tax-inc['Income Taxes'])
    # Incremental diagnostic relative to the unchanged plan, not ending cash.
    cash_delta=net-inc['Net Income']+depreciation+writeoff-capital-inventory_change+proceeds
    return dict(economics=e,unresolved_economics=sorted(set(unresolved)),offerings=offerings,
                revenue=revenue,cogs=cogs,gross_profit=gross,operating_expenses=inc['Operating Expenses']+expense,
                interest_expense=inc['Interest Expense']+financing,pretax=pretax,tax=tax,tax_rate=rate,net_income=net,
                inventory=inventory,inventory_change=inventory_change,holding_expense_change=holding,
                financing_expense_change=financing,capitalized_spending_change=capital,
                store_opening_capex=store_capex,
                depreciation_change=depreciation,closure_writeoff=writeoff,disposal_proceeds=proceeds,
                incremental_cash_delta=cash_delta,
                cash_boundary='Incremental cash-use diagnostic versus unchanged inputs; not ending cash or a cash-flow forecast. Receivables, payables, debt drawdowns and other cash flows held out.',
                economic_status='Partial diagnostic: unknown coefficients use zero placeholders, not estimated zero effects.' if unresolved else 'Specified conditional scenario; not calibrated simulator rules.')
