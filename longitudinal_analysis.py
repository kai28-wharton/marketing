"""Observed-history diagnostics and deliberately small, non-causal valuation models.

No decision prescription or simulation submission is produced here. Source
positions reconstruct reported scores; they do not estimate spending responses.
"""
import math
from statistics import mean

from market_value_analysis import build_analysis as build_market_value_analysis
from round_review import COMPANY, QUADRANTS


def solve(matrix, vector):
    a=[list(row)+[v] for row,v in zip(matrix,vector)]
    for i in range(len(a)):
        pivot=max(range(i,len(a)),key=lambda j:abs(a[j][i]))
        a[i],a[pivot]=a[pivot],a[i]
        if abs(a[i][i])<1e-12:raise ValueError('Singular diagnostic model.')
        d=a[i][i];a[i]=[v/d for v in a[i]]
        for j in range(len(a)):
            if j!=i:
                d=a[j][i];a[j]=[v-d*w for v,w in zip(a[j],a[i])]
    return [row[-1] for row in a]


def ridge_fit(rows, features, penalty=1.0):
    """Training-fold scaling and an unpenalized intercept; no hyperparameter search."""
    centers=[mean(r[k] for r in rows) for k in features]
    scales=[math.sqrt(mean((r[k]-m)**2 for r in rows)) or 1 for k,m in zip(features,centers)]
    x=[[1]+[(r[k]-m)/s for k,m,s in zip(features,centers,scales)] for r in rows]
    y=[math.log(r['market_value']) for r in rows];n=len(features)+1
    a=[[sum(row[i]*row[j] for row in x)+(penalty if i==j and i>0 else 0) for j in range(n)] for i in range(n)]
    beta=solve(a,[sum(row[i]*v for row,v in zip(x,y)) for i in range(n)])
    return dict(features=list(features),centers=centers,scales=scales,coefficients=beta,penalty=penalty)


def ridge_predict(model,row):
    z=[1]+[(row[k]-m)/s for k,m,s in zip(model['features'],model['centers'],model['scales'])]
    return math.exp(sum(b*v for b,v in zip(model['coefficients'],z)))


def valuation_models(history):
    rows=[dict(r,log_ebit=math.log(r['ebit'])) for r in history if r['ebit'] is not None and r['ebit']>0 and r['market_value'] is not None and r['market_value']>0]
    if len(rows)<5:return dict(status='Insufficient complete periods',models=[],observations=len(rows))
    output=[]
    for name,features in [('Finance only',['log_ebit','wacc']),('Finance + Kahn gaps',['log_ebit','wacc','strategy_deficit'])]:
        fit=ridge_fit(rows,features);predictions=[];forward=[]
        for i,row in enumerate(rows):
            training=rows[:i]+rows[i+1:]
            loo=ridge_predict(ridge_fit(training,features),row)
            fitted=ridge_predict(fit,row)
            predictions.append(dict(round=row['round'],actual=row['market_value'],fitted=fitted,leave_one_out=loo))
            if i>=3:
                estimate=ridge_predict(ridge_fit(rows[:i],features),row)
                forward.append(dict(round=row['round'],actual=row['market_value'],estimate=estimate))
        output.append(dict(name=name,**fit,observations=len(rows),predictions=predictions,forward=forward,
                           fitted_mape=mean(abs(p['fitted']/p['actual']-1) for p in predictions),
                           loo_mape=mean(abs(p['leave_one_out']/p['actual']-1) for p in predictions),
                           forward_mape=mean(abs(p['estimate']/p['actual']-1) for p in forward),
                           latest_fit=predictions[-1]['fitted']))
    return dict(status='Exploratory association only',observations=len(rows),models=output,
                equation='ln(MV) = intercept + coefficients × training-standardized features; ridge penalty λ=1, unpenalized intercept.',
                feature_definition='log_ebit = ln(gross profit − operating expenses); wacc = reported percent points; strategy_deficit = Experience leader gap + Brand top-two gap + Low Price/Frictionless CSV shortfalls.',
                boundary='Seven company-period observations at most in the current package. Trends, persistence and bundled decisions confound coefficients. Leave-one-out uses other periods including future periods; expanding-window errors use earlier periods only. Neither is a frozen pre-outcome backtest. No causal score premium, simulator formula, forecast interval or optimized decision is identified. Predictions use observed same-period financial/Kahn inputs, not a forecast of next-period inputs.')


def build_analysis(data, submissions, root):
    from app import read_csv, number
    current=data['current_round'];folder=root/f'materials/round{current}/marketing'
    positions=read_csv(folder/f'productPosition-round{current}.csv')
    prefs=read_csv(folder/f'preference-round{current}.csv')
    industry={}
    industry_path=root/'decision_making'/f'round_{current}'/f'industryDecisions-round{current}.csv'
    if industry_path.is_file():
        for row in read_csv(industry_path):
            industry.setdefault(int(row['Round']),{})[row['Decision']]={k:number(row[k]) for k in ('Average','Minimum','Maximum')}
    segment_tables={name:{int(row['ROUND']):row for row in read_csv(folder/f'{name}-round{current}.csv')} for name in ('marketSize','marketRevenue','marketCLV')}
    shares={name:read_csv(folder/f'{name}-round{current}.csv') if (folder/f'{name}-round{current}.csv').is_file() else []
            for name in ('unitMarketShare','revenueMarketShare')}
    history=[]
    for r in range(current+1):
        observed=data['rounds'][str(r)];inc=observed['income'];bal=observed['balance'];sc=observed['scorecard'];plan=submissions[r]['decisions']
        pos={p['Category']:number(p[COMPANY]) for p in positions if int(p['Round'])==r}
        quadrants={};peer_scores={}
        for q in QUADRANTS:
            rows=[v for v in data['kahn'] if v['round']==r and v['quadrant']==q]
            retailers=[v for v in rows if v['company']!='FAIR VALUE'];own=next(v['value'] for v in retailers if v['company']==COMPANY)
            floor=next(v['value'] for v in rows if v['company']=='FAIR VALUE')
            peers=sorted((v['value'] for v in retailers if v['company']!=COMPANY),reverse=True)
            peer_scores[q]=mean(peers)
            leader=max(v['value'] for v in retailers);threshold=peers[1] if q=='BRAND' else peers[0]
            quadrants[q]=dict(score=own,fair_value=floor,gap=own-floor,leader=leader,rank=1+sum(v['value']>own for v in retailers),
                              target_threshold=threshold if q in ('BRAND','EXPERIENCE') else floor,
                              target_gap=max(0,threshold-own) if q in ('BRAND','EXPERIENCE') else max(0,floor-own),
                              target_met=(own>=threshold) if q in ('BRAND','EXPERIENCE') else own>=floor)
        deficit=sum(q['target_gap'] for q in quadrants.values())
        debt=bal.get('Short Term Loans',0)+bal.get('Long Term Debt',0) if bal else None
        ebit=inc['Gross Profit']-inc['Operating Expenses'] if inc else None
        capital=debt+bal['Shareholder’s Equity']-bal['Cash'] if bal else None
        sums=lambda name:sum(number(v[f'Round-{r} Share']) for v in shares[name] if v['Product'].startswith(COMPANY+' '))
        history.append(dict(round=r,quadrants=quadrants,positions=pos,industry=industry.get(r,{}),
                            peer_scores=peer_scores,
                            decisions=dict(plan),decision_source=submissions[r]['source'],
                            finance_source=f'materials/round{observed["finance_source_round"]}/finance · Round-{r} columns' if inc else None,
                            revenue=inc.get('Net Revenue'),net_income=inc.get('Net Income'),ebit=ebit,
                            gross_margin=observed['ratios'].get('gross_margin'),interest=inc.get('Interest Expense'),
                            market_value=sc.get('Market Value'),clv=sc.get('Customer Lifetime Value'),wacc=sc.get('Weighted Average Cost of Capital (WACC)'),
                            cash=bal.get('Cash'),inventory=bal.get('Inventory'),debt=debt,book_equity=bal.get('Shareholder’s Equity'),working_capital=observed['ratios'].get('working_capital'),
                            interest_cover=observed['ratios'].get('interest_cover'),roic_proxy=ebit/capital if capital else None,
                             strategy_deficit=deficit,
                             unit_share=sums('unitMarketShare') if shares['unitMarketShare'] else sc['Market Share by Units Sold']/100,
                             unit_share_source=f'materials/round{current}/marketing/unitMarketShare-round{current}.csv' if shares['unitMarketShare'] else f'materials/round{observed["finance_source_round"]}/finance/scorecard-round{observed["finance_source_round"]}.csv · Round-{r} · Market Share by Units Sold',
                             revenue_share=sums('revenueMarketShare') if shares['revenueMarketShare'] else sc['Market Share by Revenue']/100,
                            service_per_store=plan['service']/plan['coverage'] if plan['coverage'] else None,
                            experience_per_store=plan['experience']/plan['coverage'] if plan['coverage'] else None,
                            service_revenue_ratio=plan['service']/inc['Net Revenue'] if inc else None,
                            service_expense=inc.get('Customer Service'),online_expense=inc.get('Online Expense'),
                            analytics_score=sc.get('Customer Analytics Score'),vendor_score=sc.get('Vendor Management Score'),
                            experience_reconstructed=pos['CUSTOMER SERVICE']+pos['SHOPPING EXPERIENCE'],
                            frictionless_reconstructed=pos['CUSTOMER SERVICE']+pos['ONLINE INVEST']))
    first=history[0];last=history[-1];prior=history[-2]
    segment_rows=[]
    total0=sum(number(v) for k,v in segment_tables['marketRevenue'][0].items() if k!='ROUND')
    total1=sum(number(v) for k,v in segment_tables['marketRevenue'][current].items() if k!='ROUND')
    for s in data['marketing']['segments']:
        series=[]
        for r in range(current+1):
            revenue=number(segment_tables['marketRevenue'][r][s['id']]);size=number(segment_tables['marketSize'][r][s['id']]);clv=number(segment_tables['marketCLV'][r][s['id']])
            preference={p['Preference']:number(p[s['id']]) for p in prefs if int(p['Round'])==r}
            series.append(dict(round=r,revenue=revenue,size=size,clv=clv,preferences=preference))
        a,b=series[0],series[-1]
        segment_rows.append(dict(id=s['id'],history=series,preferences=b['preferences'],
                                 revenue=b['revenue'],clv=b['clv'],size=b['size'],
                                 revenue_growth=b['revenue']/a['revenue']-1,clv_growth=b['clv']/a['clv']-1,population_growth=b['size']/a['size']-1,
                                 strategy_period_growth=b['revenue']/series[min(3,current)]['revenue']-1,
                                 revenue_change=b['revenue']-a['revenue'],last_revenue_change=b['revenue']-series[-2]['revenue'],
                                 revenue_mix=b['revenue']/total1,revenue_mix_change=b['revenue']/total1-a['revenue']/total0,
                                 relative_revenue_index=(b['revenue']/a['revenue'])/(b['size']/a['size']),
                                 need_changes={k:b['preferences'][k]-a['preferences'][k] for k in b['preferences']}))
    # Check output reconstruction across every retailer, not just our own seven rows.
    reconstruction=[]
    for q,components in [('EXPERIENCE',('SHOPPING EXPERIENCE','CUSTOMER SERVICE')),('FRICTIONLESS',('ONLINE INVEST','CUSTOMER SERVICE'))]:
        residuals=[]
        for row in data['kahn']:
            if row['round']<0 or row['round']>current or row['quadrant']!=q or row['company']=='FAIR VALUE':continue
            p={v['Category']:number(v[row['company']]) for v in positions if int(v['Round'])==row['round']}
            residuals.append(row['value']-sum(p[k] for k in components))
        reconstruction.append(dict(quadrant=q,components=list(components),observations=len(residuals),
                                   mean_absolute_error=mean(abs(v) for v in residuals),max_absolute_error=max(abs(v) for v in residuals)))
    finance_bridge=[]
    if first['net_income'] is not None and last['net_income'] is not None:
        i0=data['rounds']['0']['income'];i1=data['rounds'][str(current)]['income']
        for label,value in [('Gross profit change',i1['Gross Profit']-i0['Gross Profit']),('Operating expense change',-(i1['Operating Expenses']-i0['Operating Expenses'])),('Interest expense change',-(i1['Interest Expense']-i0['Interest Expense'])),('Income tax change',-(i1['Income Taxes']-i0['Income Taxes']))]:finance_bridge.append(dict(label=label,value=value))
    facts=[
        dict(title='Experience: service offset the ambience gain',evidence=f"R0→R{current}: shopping-experience position {first['positions']['SHOPPING EXPERIENCE']:.1f}→{last['positions']['SHOPPING EXPERIENCE']:.1f}, service {first['positions']['CUSTOMER SERVICE']:.1f}→{last['positions']['CUSTOMER SERVICE']:.1f}; Experience {first['quadrants']['EXPERIENCE']['score']:.1f}→{last['quadrants']['EXPERIENCE']['score']:.1f}.",interpretation='Reported output components explain the observed direction. They do not identify why the service position fell or how much spending restores it.'),
        dict(title='Frictionless: online improvement was not enough',evidence=f"Online position {first['positions']['ONLINE INVEST']:.1f}→{last['positions']['ONLINE INVEST']:.1f}, while service fell. Current Frictionless {last['quadrants']['FRICTIONLESS']['score']:.1f} versus CSV floor {last['quadrants']['FRICTIONLESS']['fair_value']:.1f}.",interpretation='The common weak component is service. More online/analytics dollars alone have not established parity; interaction, competition and evolving needs remain unestimated.'),
        dict(title='Nominal spending is not delivered capability',evidence=f"Service input ${first['decisions']['service']:,.0f}→${last['decisions']['service']:,.0f}; stores {first['decisions']['coverage']:.0f}→{last['decisions']['coverage']:.0f}. Analytics input ${last['decisions']['analytics']:,.0f} is not standalone demand.",interpretation='Check service intensity per store and per revenue, actual service expense and industry benchmarks. The slides describe little service persistence; historical spending is not a permanent service asset.'),
        dict(title='Financial recovery is not proof of strategy success',evidence=f"Market value ${first['market_value']:,.0f}→${last['market_value']:,.0f}; debt ${first['debt']:,.0f}→${last['debt']:,.0f}; unit share {first['unit_share']:.1%}→{last['unit_share']:.1%}.",interpretation='Margin and financing improvements can raise valuation while volume share and customer convenience weaken. Do not conclude the team failed financially, or that the current strategy is sustainably successful, from one metric.')]
    return dict(version='longitudinal-1.0',history=history,segments=segment_rows,reconstruction=reconstruction,diagnosis=facts,
                valuation=valuation_models(history),market_value_analysis=build_market_value_analysis(history),finance_bridge=finance_bridge,
                goals=dict(EXPERIENCE='Rank #1 (ties satisfy rank, sole leadership requires exceeding peers)',BRAND='Rank #1 or #2',**{'LOW PRICE':'Meet exported fair value','FRICTIONLESS':'Meet exported fair value'}),
                boundary='Observed company-level trends, not randomized investment returns. Segment contribution, acquisition cost, retention and segment × offering/channel purchases are unavailable; no causal segment ROI is computed.',
                sources=[f'materials/round{current}/marketing/ · cumulative marketing histories',f'materials/round{current}/finance/ · original Round-N columns; scorecard supplies unit share when the unit-share CSV is absent','decision_making/round_0 … round_'+str(current)+' · actual submitted inputs','materials/MarketValue_Slides.pdf · pp2–14','materials/PivotOrPerish_Intro wemba.pdf · pp7–17'])
