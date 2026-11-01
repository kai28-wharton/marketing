"""Latest observed workspace plus a reproducible historical export-1 audit.

The default dataset selects the latest available package; dataset(1) preserves
the older analysis. Submitted bundles do not identify sixteen causal effects.
"""
import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path

COMPANY = "GETCHELL'S"
QUADRANTS = ('BRAND', 'EXPERIENCE', 'FRICTIONLESS', 'LOW PRICE')
ATTRIBUTES = ('LOW PRICE','BREADTH','DEPTH','BRAND','ONLINE','RETAIL','CUSTOMER SERVICE','SHOPPING EXPERIENCE')


def statements(root, round_id, export_round=None):
    from app import read_csv, number
    out = {}
    for key, name in [('income','incomeStatement'),('balance','balanceSheet'),('scorecard','scorecard')]:
        source=round_id if export_round is None else export_round
        path = root / 'materials' / f'round{source}' / 'finance' / f'{name}-round{source}.csv'
        out[key] = {r['Name']: number(r[f'Round-{round_id}']) for r in read_csv(path)}
    return out


def kahn_rows(root, round_id=1):
    from app import read_csv, number
    rows = []
    for row in read_csv(root/f'materials/round{round_id}/marketing/kahn-round{round_id}.csv'):
        _, rnd, quadrant = row['Quadrant'].split(' ',2)
        rows.extend(dict(round=int(rnd),quadrant=quadrant,company=c,value=number(v))
                    for c,v in row.items() if c!='Quadrant')
    return rows


def ratios(s):
    i,b=s['income'],s['balance']
    div=lambda a,b:a/b if b else None
    ebit=i['Gross Profit']-i['Operating Expenses']
    return dict(gross_margin=div(i['Gross Profit'],i['Net Revenue']),net_margin=div(i['Net Income'],i['Net Revenue']),
                operating_ratio=div(i['Operating Expenses'],i['Net Revenue']),ebit=ebit,
                interest_cover=div(ebit,i['Interest Expense']),current_ratio=div(b['Total Current Assets'],b['Total Current Liabilities']),
                quick_ratio=div(b['Cash']+b['Accounts Receivable'],b['Total Current Liabilities']),
                working_capital=b['Total Current Assets']-b['Total Current Liabilities'],
                debt_equity=div(b['Short Term Loans']+b['Long Term Debt'],b['Shareholder’s Equity']),
                liabilities_assets=div(b['Total Liabilities'],b['Total Assets']))


def marketing_data(root, rounds):
    from app import read_csv
    segments=[]
    raw=[]
    for path in sorted((root/'materials/round1/marketing').glob('*.csv')):
        rows=read_csv(path)
        raw.append(dict(file=str(path.relative_to(root)),columns=list(rows[0]) if rows else [],rows=rows))
    def table(name):
        return read_csv(root/'materials/round1/marketing'/f'{name}-round1.csv')
    revenue={int(r['ROUND']):r for r in table('marketRevenue')}
    size={int(r['ROUND']):r for r in table('marketSize')}
    clv_path=root/'materials/round1/marketing/marketCLV-round1.csv'
    clv={int(r['ROUND']):r for r in read_csv(clv_path)} if clv_path.exists() else {}
    prefs=table('preference')
    for k in range(1,7):
        sid=f'SEGMENT {k}'
        p={r['Preference']:float(r[sid]) for r in prefs if int(r['Round'])==1}
        old={r['Preference']:float(r[sid]) for r in prefs if int(r['Round'])==0}
        now=float(revenue[1][sid]);before=float(revenue[0][sid]);total=sum(p.values())
        segments.append(dict(id=sid,revenue=now,prior_revenue=before,change=now-before,growth=now/before-1,
                             revenue_share=now/sum(float(revenue[1][s]) for s in revenue[1] if s!='ROUND'),
                             size=float(size[1][sid]),size_growth=float(size[1][sid])/float(size[0][sid])-1,
                             clv=float(clv[1][sid]) if 1 in clv else None,
                             preferences=p,prior_preferences=old,normalized_preferences={a:v/total for a,v in p.items()},
                             top_preferences=sorted(p,key=p.get,reverse=True)[:3],
                             history=[dict(round=r,revenue=float(revenue[r][sid]),size=float(size[r][sid])) for r in sorted(revenue)]))
    companies=[]
    channels={r['COMPANY']:r for r in table('revenueByAccessPoint')}
    offerings=table('revenueByOffering')
    totals={n:sum(float(r[f'Round-{n} {tier}']) for r in offerings for tier in ('LOWER COST','HIGHER COST')) for n in (0,1)}
    for r in offerings:
        c=r['COMPANY'];x=channels[c];old=sum(float(r[f'Round-0 {t}']) for t in ('LOWER COST','HIGHER COST'))
        now=sum(float(r[f'Round-1 {t}']) for t in ('LOWER COST','HIGHER COST'))
        companies.append(dict(name=c,revenue=now,prior_revenue=old,growth=now/old-1,
                              share=now/totals[1],prior_share=old/totals[0],
                              low=float(r['Round-1 LOWER COST']),high=float(r['Round-1 HIGHER COST']),
                              online=float(x['Round-1 ONLINE']),store=float(x['Round-1 STORE'])))
    positions=[]
    source=table('productPosition')
    for r in source:
        if int(r['Round'])!=1:continue
        prev=next(p for p in source if int(p['Round'])==0 and p['Category']==r['Category'])
        vals={k:float(v) for k,v in r.items() if k not in ('Category','Round')}
        positions.append(dict(attribute=r['Category'],current=vals[COMPANY],prior=float(prev[COMPANY]),values=vals,
                              rank=1+sum(v>vals[COMPANY] for v in vals.values())))
    return dict(segments=segments,companies=companies,positions=positions,attributes=ATTRIBUTES,
                raw_tables=raw,reported_revenue_total=totals[1],segment_clv_available=1 in clv,
                segment_revenue_difference=sum(s['revenue'] for s in segments)-rounds[1]['income']['Net Revenue'],
                fair_value_available=False,
                notes=['Segment revenue reconciles to company revenue within $1; it is not total addressable market.',
                       'Intro p7 labels market size as consumers. Segment market population is not Getchell’s unique buyers; revenue mix is not penetration.',
                       'Preference values are relative weights, not population percentages or estimated elasticities.',
                       'Round 1 segment CLV is unavailable; Round 0 CLV is not carried forward as current.',
                       'FAIR VALUE is a moving quadrant benchmark, not a retailer. Use the CSV FAIR VALUE column as the working floor. Ratios are approximately two-thirds of displayed leaders, not an exact 67% formula; the conflicting 75% slide rule is retained for source audit only.',
                       'Price is defined as cost plus markup. Pricing-file values match cost metrics; do not treat those file values as selling prices.'])


def _build_dataset(root):
    import app
    from assortment import import_team_plan, TEAM_FILE
    base_data=app.load_data()
    team=import_team_plan(base_data['factors'],app.validate)
    if not team['available']:raise ValueError('Submitted team workbook is required for the Round 1 review.')
    team['source']=str(TEAM_FILE.relative_to(root))
    team['sha256']=hashlib.sha256(TEAM_FILE.read_bytes()).hexdigest()
    rounds={r:statements(root,r) for r in (0,1)}
    history=kahn_rows(root)
    scores={r:{x['quadrant']:x['value'] for x in history if x['round']==r and x['company']==COMPANY} for r in (0,1)}
    factors=copy.deepcopy(base_data['factors'])
    industry={r['Decision']:{k.lower():app.number(r[k]) for k in ('Average','Minimum','Maximum')}
              for r in app.read_csv(root/'decision_making/round_2/industryDecisions-round2.csv') if int(r['Round'])==1}
    definition_path=root/'materials/decision_making_factors.md'
    definitions=definition_path.read_text().strip() if definition_path.exists() else ''
    for f in factors:
        f['prior_reference']=f['baseline'];f['baseline']=team['decisions'][f['key']];f['industry']=industry[f['label']]
    # Freeze old coefficients and inputs; neither refit nor replace its error after seeing the outcome.
    old=app.evaluate(team['decisions'],data=base_data)
    audit=[]
    for key in ('revenue','net_income'):
        observed=rounds[1]['income']['Net Revenue' if key=='revenue' else 'Net Income']
        audit.append(dict(metric=key,predicted=old[key],observed=observed,error=old[key]-observed))
    audit.extend(dict(metric=q,predicted=old['scores'][q],observed=scores[1][q],error=old['scores'][q]-scores[1][q]) for q in QUADRANTS)
    alternatives=[]
    for goal in ('balanced','positioning','profit'):
        opt=app.optimize(dict(decisions=team['decisions'],goal=goal))
        alternatives.append(dict(goal=goal,decisions=opt['result']['decisions'],revenue=opt['result']['revenue'],
                                 net_income=opt['result']['net_income'],scores=opt['result']['scores'],
                                 observed_result=None,method=opt['method']))
    accounting=[]
    mapping={'online':'Online Expense','service':'Customer Service','experience':'Shopping Experience','vendor':'Vendor Management','analytics':'Customer Analytics'}
    for key,line in mapping.items():
        decision=team['decisions'][key];actual=rounds[1]['income'][line]
        accounting.append(dict(key=key,decision=decision,expense=actual,ratio=actual/decision if decision else None,
                               difference=actual-decision))
    sources=[str(p.relative_to(root)) for p in sorted((root/'materials').glob('round*/*/*.csv'))]
    sources += [team['source'],'decision_making/round_2/industryDecisions-round2.csv','materials/decision_making_factors.md']
    from decision_economics import SCHEMA, scenario
    issues=['Private Brand is mix per MarketValue_Slides p12, superseding the duplicated Markdown definition; numeric response/exposures are still unknown.',
            'The national-brand-quality line is unlabeled in Markdown but confirmed by Intro p14.',
            'Slides specify $1.75M/store and no inventory holding expense; numeric response, financing, retention and valuation formulas remain incomplete.'] if definitions else ['Decision definitions are missing.']
    result=dict(current_round=1,previous_round=0,rounds={str(r):dict(**s,ratios=ratios(s),scores=scores[r]) for r,s in rounds.items()},
                kahn=history,team=team,factors=factors,marketing=marketing_data(root,rounds),
                historical_budget=app.BUDGET,definitions=definitions,definitions_available=bool(definitions),
                definition_issues=issues,definitions_sha256=hashlib.sha256(definitions.encode()).hexdigest(),
                economic_schema={k:dict(min=v[0],max=v[1],description=v[2]) for k,v in SCHEMA.items()},
                audit=dict(version='kahn-2.0',rows=audit,alternatives=alternatives,
                           status='Retrospective one-transition error audit; not an out-of-sample validation suite. Alternatives were not simulated and have no observed outcomes.'),
                accounting=accounting,sources=sources,
                 model=dict(version='review-4.0',paired_transitions=1,causal_calibration=False,
                           changes=['Re-anchor at observed Round 1 scores and financials, using the actual submitted workbook as decision reference.',
                                     'Use PDF-consistent direct pathways with uncalibrated numerical priors: analytics only multiplies online/experience; vendor does not directly raise Brand; stores change access, not preference.',
                                    'Apply quality/vendor unit-cost changes to both COGS and cost-plus selling prices under explicit scenario response rates.',
                                     'Separate capitalized investment, depreciation, inventory funding/financing and store capex/disposals. Holding expense is a documented zero; new stores cost $1.75M.',
                                    'Analytics is expensed. R1 online/experience expense fractions and service input ratios remain provisional scenario defaults.',
                                    'Unspecified economic coefficients are exposed as unresolved, never treated as verified zero effects by the new optimizer.',
                                    'Apply observed effective tax rate only to positive modeled pretax income.',
                                     'Retire fixed-P/E market-value projection. Document max(DCF, CLV/private-brand, liquidation); changed-plan value and market-value optimization are unavailable without the missing formulas.',
                                    'Show all sixteen factors with isolated plus/minus probes, prior-weight dependencies, unpriced changes and historical forecast errors.'],
                            limitations=issues+['Input bounds and numerical response rates remain provisional; slides do not supply a fitted simulator formula.',
                                         'A reported-position Brand reconstruction links depth to Brand; its decision-input response is not identified. The old zero Brand depth coefficient is a structural omission, not evidence of no effect.',
                                        'Only one linked submitted plan and result; competitors, demand trends, costs and all decision changes are confounded.',
                                        'The prior reference plan was a screenshot assumption, not a verified Round 0 historical submission.',
                                         'Budget rule is max(14% prior revenue, inflation-adjusted prior budget). Prior actual budget/inflation are unknown; $69.814M is submitted spend, not a verified budget ceiling.',
                                        'Cash diagnostics omit receivables, payables and debt flows. Scenario rates are unestimated; valuation does not establish fair value.']))
    from simulation_rules import build_review
    result['simulation']=build_review(result,root)
    result['economic_defaults']=scenario(result)
    from decision_insights import build_insights
    result['insights']=build_insights(result)
    from strategy_analysis import build_strategy
    result['strategy']=build_strategy(result)
    from brand_impact import build_brand_impact
    result['insights']['brand']['parameter_impact']=build_brand_impact(result,base_data)
    from brand_holistic import build_holistic
    result['insights']['brand']['parameter_impact']['holistic']=build_holistic(result,root)
    result['sources']=sorted(set(result['sources']+[r['file'] for r in result['insights']['brand']['parameter_impact']['holistic']['source_audit']['materials']]+
                                  ['decision_making/round_0/industryDecisions-round0.csv']))
    return result


def fingerprint(root):
    files=[p for p in (root/'materials').rglob('*') if p.suffix in ('.csv','.md','.pdf')]+list((root/'decision_making').glob('**/*'))
    return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) for p in sorted(files) if p.is_file())


@lru_cache(maxsize=2)
def _cached(root, stamp, round_id):
    if round_id==1:return _build_dataset(Path(root))
    from current_review import build_dataset
    return build_dataset(Path(root),round_id)


def dataset(round_id=None):
    from app import ROOT
    if round_id is None:
        round_id=max(int(p.name[5:]) for p in (ROOT/'materials').glob('round*') if p.is_dir() and p.name[5:].isdigit())
    return copy.deepcopy(_cached(str(ROOT),fingerprint(ROOT),round_id))


def write_analysis(data, path):
    r0,r1=data['rounds']['0'],data['rounds']['1']
    lines=['# Round 1: observed results and frozen model audit','',
           'Submitted workbook: `'+data['team']['source']+'` (Column B). User confirms this plan produced Round 1.',
           'SHA-256: `'+data['team']['sha256']+'`','',
           '## Observed trade-off','',
           f"Revenue ${r0['income']['Net Revenue']:,.0f} → ${r1['income']['Net Revenue']:,.0f}; net income ${r0['income']['Net Income']:,.0f} → ${r1['income']['Net Income']:,.0f}.",
           f"Market value ${r0['scorecard']['Market Value']:,.0f} → ${r1['scorecard']['Market Value']:,.0f}; Brand 6.3 → 3.7; Experience 5.8 → 6.0; Frictionless 3.4 → 3.3; Low Price 4.9 → 4.7.",
           'Growth and profitability improved, but Brand deteriorated; higher equity market value does not establish improved strategic positioning.',
           'Cash fell and inventory increased despite profit. Gross margin compressed; interest still absorbs most operating profit.','',
           '## Frozen v2 predictions for submitted plan','', '|Metric|v2 modeled|Round 1 observed|Modeled minus observed|','|---|---:|---:|---:|']
    lines += [f"|{r['metric']}|{r['predicted']:,.4f}|{r['observed']:,.4f}|{r['error']:+,.4f}|" for r in data['audit']['rows']]
    lines += ['',data['audit']['status'],'','## Model changes','']+['- '+s for s in data['model']['changes']]
    lines += ['','## Evidence limits','']+['- '+s for s in data['model']['limitations']+data['marketing']['notes']]
    lines += ['','## Accounting checks','', '|Input|Submitted|Reported expense|Expense/input (provisional)|','|---|---:|---:|---:|']
    lines += [f"|{r['key']}|{r['decision']:,.0f}|{r['expense']:,.0f}|{r['ratio']:.4f}|" for r in data['accounting']]
    lines += ['','Neither Brand collapse nor market-value growth is assigned causally to a single decision. Optimizer alternatives have no observed simulation result.']
    Path(path).write_text('\n'.join(lines)+'\n',encoding='utf-8')
