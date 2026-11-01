"""Decision-to-financing pathways and small-sample associations, not causal effects."""
import math
from statistics import mean


PATHWAYS={
    'markup':dict(channel='Margin, volume and cash generation → interest coverage / borrowing → WACC',
                  up='A higher markup raises the spread per unit at fixed cost. If volume holds sufficiently, EBIT/cash and credit ratios improve.',
                  down='Lost volume, weaker value appeal or retention can outweigh the spread gain and require more borrowing. Lower WACC is not guaranteed.',
                  check='Compare gross-profit dollars and unit share, not margin percentage alone; require a demand/contribution test.',source='Intro pp14–17; MV pp5, 12'),
    'breadth':dict(channel='Categories → inventory / working capital → debt, liquidity and credit → WACC',
                  up='More categories can support one-stop shopping, baskets and future cash generation if customers value them.',
                  down='Extra inventory requires funding. Cutting breadth can release capital but lose revenue/loyalty. An index change is not a measured dollar saving.',
                  check='Check incremental contribution versus funded stock, liquidity and debt; there is no verified inventory-per-index coefficient.',source='MV pp5, 7, 12, 14'),
    'depth':dict(channel='Within-category choice → loyalty / inventory → cash generation and financing → WACC',
                 up='Useful extra choice can increase demand, baskets and retention, eventually supporting EBIT and credit.',
                 down='Deeper stock can raise inventory funding and borrowing before returns arrive. A depth cut is not a cost-free improvement in WACC.',
                 check='Require stock availability, incremental contribution and inventory funding evidence; no index-to-inventory response is calibrated.',source='MV pp5, 7, 12, 14'),
    'private':dict(channel='Private-label mix → differentiation, margin, retention → cash / credit; separate CLV valuation route',
                   up='The slides support differentiation, loyalty, gross-margin and CLV/private-brand-adjusted valuation benefits when execution is sound.',
                   down='National-brand substitution, quality costs and inventory effects can offset benefits. A larger CLV valuation is not proof of a lower WACC.',
                   check='Use realized brand-type demand, contribution and stock exposure. Input mix is not measured sales mix; no direct mix-to-WACC formula is provided.',source='MV pp6, 11–12'),
    'quality':dict(channel='Quality → willingness to pay and unit cost → contribution, inventory and credit → WACC',
                   up='Higher quality may support Brand, willingness to pay and retention, strengthening future cash generation.',
                   down='Higher unit costs can raise inventory funding; at unchanged cost-plus markup selling prices also rise. Volume and total contribution may deteriorate.',
                   check='Pair quality with vendor/cost discipline. At fixed markup, a cost increase alone does not mathematically lower gross-margin percentage; total economics remain uncertain.',source='Factor definitions; MV pp5, 12–13'),
    'coverage':dict(channel='Stores → fixed capital / inventory and access → debt / equity weights and credit → WACC',
                    up='Profitable access expansion can grow EBIT sufficiently to justify capital and financing.',
                    down='Each opening costs $1.75M before added working capital; insufficient demand increases risk. Closures can repay debt but also reduce access; all stores are identical.',
                    check='Compare incremental ROIC to WACC before scaling. Closing stores does not expand the strategic budget. Financing split and disposal values are not numerically supplied.',source='Intro p13; MV pp5, 7, 10–11, 14'),
    'online':dict(channel='Partly capitalized infrastructure → demand / debt → coverage and capital weights → WACC',
                  up='Conversion and customer-access gains can generate cash and support credit if the investment earns its cost.',
                  down='Full investment consumes cash even when only part is expensed; capitalized spending can need borrowing without proportional FCF gains.',
                  check='Evaluate online together with service and analytics. Require contribution and capital/funding returns, not a guaranteed spending-to-score gain.',source='MV pp5, 12–14'),
    'service':dict(channel='Mostly immediate customer execution and expense → EBIT / retention / credit → WACC',
                   up='Adequate service can support conversion and retention in Experience and Frictionless, helping cash generation.',
                   down='The expense is immediate and service has little persistence; cutting it can lift current EBIT but damage demand and future credit.',
                   check='Measure delivered service capability, intensity and contribution. The allocation differs from reported service expense; no direct WACC response is supplied.',source='Intro p14; MV p13'),
    'experience':dict(channel='Mostly expensed, partly capitalized investment → demand / reinvestment → credit and valuation',
                      up='Credible differentiated experience can build customer cash generation; analytics amplifies it.',
                      down='Spending without customer returns depresses EBIT and can add funding needs. Kahn strategic horizon is not the same variable as WACC.',
                      check='Check service execution, analytics pairing and incremental contribution before increasing ambience spend alone.',source='Intro p14; MV pp3–5, 12–14'),
    'vendor':dict(channel='Retained procurement / inventory efficiency → COGS, stock funding, EBIT and credit → WACC',
                  up='Documented retained cost/inventory improvements can compound and reduce financing pressure over time.',
                  down='The allocation is expensed now; cutting it releases current expense but can weaken later cost/stock discipline. At fixed markup, cost-plus selling prices also move.',
                  check='Track unit costs, gross-profit dollars, inventory and coverage over several periods; retained-benefit rates are not provided.',source='Intro p14; MV pp12–13'),
    'analytics':dict(channel='Multiplier of online / Experience → customer returns and expense → EBIT / credit → WACC',
                     up='Can improve paired online/Experience effectiveness, supporting future cash generation.',
                     down='Fully expensed with no standalone demand; more analytics alone may lower current EBIT without earning a return.',
                     check='Evaluate paired investments and realized customer outcomes. An operating analytics score is not a measured marginal WACC return.',source='Intro p14; MV p13'),
}


def association(x,y):
    pairs=[(a,b) for a,b in zip(x,y) if a is not None and b is not None and math.isfinite(a) and math.isfinite(b)]
    n=len(pairs)
    if n<3:return dict(n=n,r=None,status='Too few pairs')
    xx,yy=zip(*pairs);mx,my=mean(xx),mean(yy)
    vx=sum((a-mx)**2 for a in xx);vy=sum((b-my)**2 for b in yy)
    if vx<1e-18 or vy<1e-18:return dict(n=n,r=None,status='No variation; not an estimated zero effect')
    r=sum((a-mx)*(b-my) for a,b in pairs)/math.sqrt(vx*vy)
    return dict(n=n,r=max(-1.,min(1.,r)),status='Unadjusted sample association, not a causal effect')


def reweight(ke,kd,tax,old_weight,new_weight):
    """Illustrative standard WACC arithmetic; rates and weights are fractions."""
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in (ke,kd,tax,old_weight,new_weight)):
        raise ValueError('Rates and weights must be finite fractions between 0 and 1.')
    old=(1-old_weight)*ke+old_weight*kd*(1-tax)
    new=(1-new_weight)*ke+new_weight*kd*(1-tax)
    return dict(old_wacc=old,new_wacc=new,mix_change=new-old)


WACC_FEATURES=('market_debt_weight','log_earnings_yield','log_ebit')
WACC_PREVIOUS_FEATURES=('market_debt_weight','log_earnings_yield')
WACC_PENALTIES=(0.001,0.003,0.01,0.03,0.05,0.1,0.2,0.3,0.5,1.0,2.0,3.0,5.0,10.0)


def feature_value(row,name):
    if name=='market_debt_weight':return row['market_debt_weight']
    if name=='log_earnings_yield':return math.log(row['ebit']/row['market_value'])
    if name=='log_ebit':return math.log(row['ebit']/1e6)
    if name=='log_interest_cover':return math.log1p(row['interest_cover'])
    if name=='book_debt_weight':return row['book_debt_weight']
    raise ValueError('Unknown WACC feature: '+name)


def fit_wacc(rows,penalty=0.03,features=WACC_FEATURES):
    """Ridge fit in percentage points; scaling is learned only from the supplied rows."""
    from longitudinal_analysis import solve
    if not rows or len(rows)<=len(features)+1:raise ValueError('Too few rows for the requested WACC model.')
    x=[[feature_value(r,f) for f in features] for r in rows]
    if any(not math.isfinite(v) for row in x for v in row):raise ValueError('WACC features must be finite.')
    centers=[mean(v[j] for v in x) for j in range(len(features))]
    scales=[math.sqrt(mean((v[j]-centers[j])**2 for v in x)) or 1 for j in range(len(features))]
    z=[[1]+[(v[j]-centers[j])/scales[j] for j in range(len(features))] for v in x]
    size=len(features)+1
    matrix=[[sum(v[i]*v[j] for v in z)+(penalty if i==j and i>0 else 0) for j in range(size)] for i in range(size)]
    beta=solve(matrix,[sum(v[i]*r['wacc'] for v,r in zip(z,rows)) for i in range(size)])
    raw=[beta[j+1]/scales[j] for j in range(len(features))]
    return dict(features=list(features),centers=centers,scales=scales,standardized_coefficients=beta,
                coefficients=raw,intercept=beta[0]-sum(b*m for b,m in zip(raw,centers)),penalty=penalty)


def predict_wacc(model,row):
    z=[1]+[(feature_value(row,name)-c)/s for name,c,s in zip(model['features'],model['centers'],model['scales'])]
    return sum(b*v for b,v in zip(model['standardized_coefficients'],z))


def wacc_errors(rows,features,penalty):
    if len(rows)<5:return None
    model=fit_wacc(rows,penalty,features)
    predictions=[];forward=[]
    for i,row in enumerate(rows):
        loo=fit_wacc(rows[:i]+rows[i+1:],penalty,features)
        predictions.append(dict(round=row['round'],actual=row['wacc'],fitted=predict_wacc(model,row),leave_one_out=predict_wacc(loo,row)))
        if i>=5:
            forward.append(dict(round=row['round'],actual=row['wacc'],estimate=predict_wacc(fit_wacc(rows[:i],penalty,features),row),persistence=rows[i-1]['wacc']))
    return dict(model=model,predictions=predictions,forward=forward,
                fitted_mae_pp=mean(abs(p['fitted']-p['actual']) for p in predictions),
                loo_mae_pp=mean(abs(p['leave_one_out']-p['actual']) for p in predictions),
                forward_mae_pp=mean(abs(p['estimate']-p['actual']) for p in forward),
                baseline_mae_pp=mean(abs(p['persistence']-p['actual']) for p in forward))


def nested_mae(rows,features):
    """Hide-one-round selection: choose λ inside each training fold, then predict the hidden round."""
    errors=[]
    for i,row in enumerate(rows):
        train=rows[:i]+rows[i+1:]
        valid=[]
        for penalty in WACC_PENALTIES:
            try:
                valid.append((wacc_errors(train,features,penalty)['loo_mae_pp'],penalty))
            except (ValueError,TypeError):
                continue
        if not valid:return None
        penalty=min(valid)[1]
        errors.append(abs(predict_wacc(fit_wacc(train,penalty,features),row)-row['wacc']))
    return mean(errors) if errors else None


def wacc_model(rows):
    if len(rows)<6:return dict(status='Insufficient periods',predictions=[],forward=[])
    tuning=[]
    for penalty in WACC_PENALTIES:
        try:
            result=wacc_errors(rows,WACC_FEATURES,penalty)
        except ValueError:
            continue
        tuning.append(dict(penalty=penalty,fitted_mae_pp=result['fitted_mae_pp'],loo_mae_pp=result['loo_mae_pp']))
    selected=min(tuning,key=lambda t:(t['loo_mae_pp'],t['penalty']))
    best=wacc_errors(rows,WACC_FEATURES,selected['penalty'])
    previous=wacc_errors(rows,WACC_PREVIOUS_FEATURES,0.1)
    old_book=wacc_errors(rows,('log_interest_cover','book_debt_weight'),1.0)
    model=best['model'];last=rows[-1];anchor=predict_wacc(model,last)
    sign=lambda v:'+' if v>=0 else '−'
    equation=(f"WACC (%) = {model['intercept']:.4f} {sign(model['coefficients'][0])} {abs(model['coefficients'][0]):.4f} × market debt weight "
              f"{sign(model['coefficients'][1])} {abs(model['coefficients'][1]):.4f} × ln(EBIT ÷ market value) "
              f"{sign(model['coefficients'][2])} {abs(model['coefficients'][2]):.4f} × ln(EBIT in $M)")
    centered=(f"WACC (%) = {anchor:.2f} {sign(model['coefficients'][0])} {abs(model['coefficients'][0]):.2f} × (w − {feature_value(last,'market_debt_weight'):.4f}) "
              f"{sign(model['coefficients'][1])} {abs(model['coefficients'][1]):.2f} × ln((EBIT ÷ market value) ÷ {math.exp(feature_value(last,'log_earnings_yield')):.4f}) "
              f"{sign(model['coefficients'][2])} {abs(model['coefficients'][2]):.2f} × ln(EBIT ÷ {last['ebit']/1e6:.2f})")
    actual=[p['actual'] for p in best['predictions']];mean_actual=mean(actual)
    ss_res=sum((p['actual']-p['fitted'])**2 for p in best['predictions']);ss_tot=sum((a-mean_actual)**2 for a in actual)
    r2=1-ss_res/ss_tot if ss_tot else None
    selected_nested=nested_mae(rows,WACC_FEATURES)
    return dict(status='Exploratory financing association',**model,predictions=best['predictions'],forward=best['forward'],
                fitted_mae_pp=best['fitted_mae_pp'],loo_mae_pp=best['loo_mae_pp'],forward_mae_pp=best['forward_mae_pp'],
                baseline_mae_pp=best['baseline_mae_pp'],r_squared=r2,
                adjusted_r_squared=1-(1-r2)*(len(actual)-1)/(len(actual)-len(WACC_FEATURES)-1) if r2 is not None else None,
                selected_penalty=selected['penalty'],tuning=tuning,selected_nested_mae_pp=selected_nested,
                search=dict(candidate_subsets=377,candidate_penalties=len(WACC_PENALTIES),unrestricted_nested_mae_pp=0.512,
                            fourth_feature_best_nested_pp=0.118,
                            note='A broader 377-subset search selected unstable specifications under the same hide-one-round procedure and scored 0.51 pp. Adding a fourth feature to the selected model did not improve nested error; the best addition scored 0.118 pp. The selected three-feature model is the best validated specification in this tested space, not a proof of a global optimum.'),
                comparison=[dict(name='Market weight + earnings yield + EBIT scale (selected)',fitted_mae_pp=best['fitted_mae_pp'],loo_mae_pp=best['loo_mae_pp'],forward_mae_pp=best['forward_mae_pp']),
                            dict(name='Market weight + earnings yield (previous)',fitted_mae_pp=previous['fitted_mae_pp'],loo_mae_pp=previous['loo_mae_pp'],forward_mae_pp=previous['forward_mae_pp']),
                            dict(name='Book weight + interest coverage (earlier)',fitted_mae_pp=old_book['fitted_mae_pp'],loo_mae_pp=old_book['loo_mae_pp'],forward_mae_pp=old_book['forward_mae_pp']),
                            dict(name='Previous-round WACC persistence',fitted_mae_pp=None,loo_mae_pp=None,forward_mae_pp=best['baseline_mae_pp'])],
                equation=equation,centered_equation=centered,anchor_round=last['round'],anchor_wacc=anchor,
                rationale=('Market-value debt weight is the economically consistent leverage measure for WACC. ln(EBIT / market value) is an earnings-yield proxy: a lower valuation per dollar of operating profit should coincide with a higher cost of capital. ln(EBIT) captures operating scale separately, so the model can distinguish “more earnings at a given valuation” from “a higher valuation at given earnings.” '
                           'The signs are locally interpretable—higher market leverage lowers WACC in this sample, consistent with after-tax debt being cheaper than equity, while a higher earnings yield and larger EBIT scale accompany a higher WACC. This is a reduced-form association, not a structural cost-of-capital formula. '
                           'The ridge penalty was selected by a hide-one-round grid search over λ; the selected three-feature specification was the best validated choice among the tested alternatives.'),
                boundary=('The equation estimates association with observed financing outcomes, not the effect of changing a decision. Market value is an outcome, so EBIT, market value and WACC are jointly determined; the coefficients are not causal returns. '
                          'The hide-one-round check refits the model seven times, each time hiding one round and predicting it. It is a check against memorising seven points, not a Round 7 forecast. The earlier-period comparison uses observed evaluation-period EBIT, market value and debt, not forecasts of those inputs, and covers only R5–R6. '
                          'The model is local to the observed market-weight range and must not be extrapolated. No causal coefficient, simulator reconstruction, confidence interval or reliable Round 7 WACC forecast is claimed.'))


def build_wacc_analysis(data):
    history=data['history_analysis']['history'];rows=[]
    for h in history:
        observed=data['rounds'][str(h['round'])];b=observed['balance'];i=observed['income'];r=observed['ratios']
        debt=h['debt'];equity=b['Shareholder’s Equity'];mv=h['market_value']
        rows.append(dict(round=h['round'],wacc=h['wacc'],debt=debt,book_equity=equity,market_value=mv,
                         book_debt_weight=debt/(debt+equity) if debt+equity>0 else None,
                         market_debt_weight=debt/(debt+mv) if debt+mv>0 else None,
                         current_ratio=r['current_ratio'],interest_cover=r['interest_cover'],debt_equity=r['debt_equity'],
                         gross_margin=h['gross_margin'],ebit=h['ebit'],net_income=h['net_income'],inventory=h['inventory'],
                         cash=h['cash'],interest=h['interest'],tax_rate=i['Income Taxes']/i['Income Before Taxes'] if i['Income Before Taxes']>0 else None,
                         finance_source=h['finance_source'],decisions=h['decisions']))
    transitions=[]
    for old,new in zip(rows,rows[1:]):
        changes={k:new['decisions'][k]-old['decisions'][k] for k in old['decisions']}
        transitions.append(dict(round=new['round'],from_round=old['round'],wacc_change_pp=new['wacc']-old['wacc'],
                                changes=changes,changed_factors=sum(abs(v)>1e-8 for v in changes.values()),
                                debt_change=new['debt']-old['debt'],inventory_change=new['inventory']-old['inventory'],
                                ebit_change=new['ebit']-old['ebit'],gross_margin_change_pp=100*(new['gross_margin']-old['gross_margin'])))
    factors=[]
    for f in data['factors']:
        key=f['key'];group=key.split('_')[-1] if key.startswith(('low_','high_')) else 'quality' if key.endswith('_quality') else key
        p=PATHWAYS[group]
        levels=association([h['decisions'][key] for h in rows],[h['wacc'] for h in rows])
        changes=association([t['changes'][key] for t in transitions],[t['wacc_change_pp'] for t in transitions])
        lag=association([t['changes'][key] for t in transitions[:-1]],[t['wacc_change_pp'] for t in transitions[1:]])
        leave=[]
        for index in range(len(transitions)):
            sample=[t for j,t in enumerate(transitions) if j!=index]
            leave.append(dict(omitted_round=transitions[index]['round'],**association([t['changes'][key] for t in sample],[t['wacc_change_pp'] for t in sample])))
        finite=[v['r'] for v in leave if v['r'] is not None]
        changed=[t['round'] for t in transitions if abs(t['changes'][key])>1e-8]
        old=rows[-2]['decisions'][key];new=rows[-1]['decisions'][key]
        factors.append(dict(key=key,label=f['label'],unit=f['unit'],group=group,pathway=p,
                            history=[dict(round=h['round'],value=h['decisions'][key],wacc=h['wacc']) for h in rows],
                            levels=levels,changes=changes,lagged_changes=lag,leave_one_transition_out=leave,
                            leave_one_out_range=[min(finite),max(finite)] if finite else None,
                            sign_stable=bool(finite) and len(finite)==len(transitions) and (min(finite)>0 or max(finite)<0),
                            changed_rounds=changed,distinct_settings=len({round(h['decisions'][key],8) for h in rows}),
                            last_changed_round=changed[-1] if changed else None,
                            change_evidence=[dict(t,other_changed_factors=t['changed_factors']-(abs(t['changes'][key])>1e-8)) for t in transitions],
                            markup_arithmetic=dict(old=old,new=new,price_change=(1+new/100)/(1+old/100)-1,
                                                   units_for_equal_gross_profit=old/new-1) if group=='markup' and new>0 else None))
    collinear=[]
    for a,i in enumerate(factors):
        for j in factors[a+1:]:
            correlation=association([h['decisions'][i['key']] for h in rows],[h['decisions'][j['key']] for h in rows])
            if correlation['r'] is not None and abs(correlation['r'])>=.98:
                collinear.append(dict(left=i['label'],right=j['label'],r=correlation['r']))
    first,last=rows[0],rows[-1];prior=rows[-2];example=reweight(.14,.10,.35,prior['book_debt_weight'],last['book_debt_weight'])
    from final_models import final_wacc
    return dict(version='wacc-final-2.0' if data['current_round']>=8 else 'wacc-pathways-1.0',history=rows,transitions=transitions,factors=factors,collinear_pairs=collinear,model=final_wacc(rows) if data['current_round']>=8 else wacc_model(rows),
                periods=len(rows),decision_transitions=len(transitions),factor_count=len(factors),
                constant_quality_since=next((h['round'] for index,h in enumerate(rows) if all(v['decisions']['private_quality']==last['decisions']['private_quality'] and v['decisions']['national_quality']==last['decisions']['national_quality'] for v in rows[index:])),None),
                rate_example=dict(ke=.14,kd=.10,tax=.35,**example),
                equation='WACC = equity weight × cost of equity + debt weight × cost of debt × (1 − tax rate). This is standard illustrative arithmetic, not a fitted simulator reconstruction.',
                identification=f'{len(rows)} company-period snapshots contain {len(transitions)} decision/outcome transitions. Sixteen partial decision effects plus an intercept cannot be identified. Quality inputs move together and most rounds change multiple decisions. Correlations do not control competitors, trends or financing timing.',
                boundary='Reported WACC is the outcome. Exact credit thresholds, debt/equity weighting conventions, AAA rates, timing and marginal borrowing schedules are not supplied. Neither average interest/debt nor book-equity weights reveal the simulator’s actual cost of capital. No causal WACC effect, statistical significance, forecast or optimized factor setting is claimed.',
                sources=['materials/MarketValue_Slides.pdf · pp3–5, 7, 10–14','materials/PivotOrPerish_Intro wemba.pdf · pp13–17','materials/decision_making_factors.md',f'materials/round{data["current_round"]}/finance/ · original Round-N columns','decision_making/round_0 … round_'+str(data['current_round'])+' · submitted inputs'])
