"""Current-round workspace with explicit submission/export/planning chronology.

Older named snapshots remain reproducible through dataset(1). The active view
uses the latest export and its user-linked workbook, never relabels old advice
as a new submission, and never assumes the next decision budget is confirmed.
"""
import hashlib

from round_review import COMPANY, QUADRANTS, ATTRIBUTES, statements, ratios, kahn_rows


def import_submission(root, decision_round, outcome_export_round=None):
    import app
    from assortment import import_team_plan
    path=root/'decision_making'/f'round_{decision_round}'/f'decision_making_team11_round{decision_round}.xlsx'
    factors=[dict(zip(['key','label','baseline','min','max','unit','group'],f)) for f in app.FACTORS]
    team=import_team_plan(factors,app.validate,path)
    if not team['available']:raise ValueError(f'Submitted workbook missing: {path}')
    team.update(source=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                decision_round=decision_round,outcome_export_round=outcome_export_round,
                note=(f'User-confirmed decision {decision_round} associated with materials/round{outcome_export_round} outcomes. Original export labels are preserved.' if outcome_export_round is not None else
                      f'Historical submitted workbook renamed as decision {decision_round}. Its filename/header are preserved; no additional outcome mapping is inferred.'))
    return team


def marketing_snapshot(root, rounds, current, previous):
    from app import read_csv, number
    folder=root/f'materials/round{current}/marketing'
    def table(name):return read_csv(folder/f'{name}-round{current}.csv')
    raw=[dict(file=str(p.relative_to(root)),columns=list(rows[0]) if rows else [],rows=rows)
         for p in sorted(folder.glob('*.csv')) for rows in [read_csv(p)]]
    rev={int(r['ROUND']):r for r in table('marketRevenue')}
    size={int(r['ROUND']):r for r in table('marketSize')}
    clvpath=folder/f'marketCLV-round{current}.csv'
    clv={int(r['ROUND']):r for r in read_csv(clvpath)} if clvpath.exists() else {}
    prefs=table('preference');segments=[]
    total=sum(number(v) for k,v in rev[current].items() if k!='ROUND')
    for k in range(1,7):
        sid=f'SEGMENT {k}';p={r['Preference']:number(r[sid]) for r in prefs if int(r['Round'])==current}
        old={r['Preference']:number(r[sid]) for r in prefs if int(r['Round'])==previous}
        now=number(rev[current][sid]);before=number(rev[previous][sid]);denom=sum(p.values())
        segments.append(dict(id=sid,revenue=now,prior_revenue=before,change=now-before,growth=now/before-1,
                             revenue_share=now/total,size=number(size[current][sid]),
                             size_growth=number(size[current][sid])/number(size[previous][sid])-1,
                             clv=number(clv[current][sid]) if current in clv else None,
                             prior_clv=number(clv[previous][sid]) if previous in clv else None,
                             preferences=p,prior_preferences=old,normalized_preferences={a:v/denom for a,v in p.items()},
                             top_preferences=sorted(p,key=p.get,reverse=True)[:3],
                             history=[dict(round=r,revenue=number(rev[r][sid]),size=number(size[r][sid]),
                                           clv=number(clv[r][sid]) if r in clv else None) for r in sorted(rev)]))
    access={r['COMPANY']:r for r in table('revenueByAccessPoint')};offering=table('revenueByOffering')
    totals={n:sum(number(r[f'Round-{n} {tier}']) for r in offering for tier in ('LOWER COST','HIGHER COST')) for n in (previous,current)}
    companies=[]
    for r in offering:
        company=r['COMPANY'];now=sum(number(r[f'Round-{current} {t}']) for t in ('LOWER COST','HIGHER COST'))
        before=sum(number(r[f'Round-{previous} {t}']) for t in ('LOWER COST','HIGHER COST'))
        companies.append(dict(name=company,revenue=now,prior_revenue=before,growth=now/before-1,
                              share=now/totals[current],prior_share=before/totals[previous],
                              low=number(r[f'Round-{current} LOWER COST']),high=number(r[f'Round-{current} HIGHER COST']),
                              online=number(access[company][f'Round-{current} ONLINE']),store=number(access[company][f'Round-{current} STORE'])))
    pos=table('productPosition');positions=[]
    for r in pos:
        if int(r['Round'])!=current:continue
        prior=next(p for p in pos if int(p['Round'])==previous and p['Category']==r['Category'])
        values={k:number(v) for k,v in r.items() if k not in ('Category','Round')}
        positions.append(dict(attribute=r['Category'],current=values[COMPANY],prior=number(prior[COMPANY]),values=values,
                              rank=1+sum(v>values[COMPANY] for v in values.values())))
    return dict(available=True,segments=segments,companies=companies,positions=positions,attributes=ATTRIBUTES,raw_tables=raw,
                reported_revenue_total=totals[current],segment_clv_available=current in clv,
                segment_revenue_difference=total-rounds[current]['income']['Net Revenue'],
                segment_clv_difference=sum(s['clv'] for s in segments)-rounds[current]['scorecard']['Customer Lifetime Value'] if current in clv else None,
                notes=[f'Observed exports: materials/round{current}; comparison: round {previous}.',
                       'Revenue is company segment revenue; market-size consumers are not verified company buyers.',
                       f'Segment CLV is reported in marketCLV-round{current}.csv; historical rows in this new file may backfill previously unavailable data.',
                       'No segment contribution, offering/channel affinity or causal response is inferred.',
                       'Fair value uses the CSV FAIR VALUE series, not a 75% or exact 67% formula.'])


def build_dataset(root,current):
    import app
    from simulation_rules import build_review
    from decision_insights import financial_analysis, segment_analysis, CROSSWALKS
    from decision_economics import SCHEMA, scenario
    from stp_strategy import build_stp
    previous=current-1;planning=current+1
    team=import_submission(root,current,current);prior_team=import_submission(root,previous)
    rounds={r:statements(root,r) for r in range(current+1)};history=kahn_rows(root,current)
    for r,s in rounds.items():
        s['ratios']=ratios(s);s['scores']={row['quadrant']:row['value'] for row in history if row['round']==r and row['company']==COMPANY}
    # Benchmarks retain their actual data vintage even though folders were renamed.
    industry_rows=[]
    for path in sorted((root/'decision_making').glob('round_*/industryDecisions-*.csv')):
        industry_rows.extend(dict(row,source=str(path.relative_to(root))) for row in app.read_csv(path))
    industry_round=max(int(r['Round']) for r in industry_rows);industry={r['Decision']:r for r in industry_rows if int(r['Round'])==industry_round}
    factors=[]
    for f in app.FACTORS:
        row=dict(zip(['key','label','baseline','min','max','unit','group'],f));k=row['key'];context=industry[row['label']]
        row.update(baseline=team['decisions'][k],prior_reference=prior_team['decisions'][k],priced=k in app.SPEND,
                   industry={n.lower():app.number(context[n]) for n in ('Average','Minimum','Maximum')},
                   industry_round=industry_round,industry_source=context['source'])
        factors.append(row)
    latest=rounds[current];prior=rounds[previous]
    accounting=[dict(key=k,decision=team['decisions'][k],expense=latest['income'][line],
                     ratio=latest['income'][line]/team['decisions'][k] if team['decisions'][k] else None,
                     difference=latest['income'][line]-team['decisions'][k]) for k,line in
                [('online','Online Expense'),('service','Customer Service'),('experience','Shopping Experience'),('vendor','Vendor Management'),('analytics','Customer Analytics')]]
    sources=sorted(str(p.relative_to(root)) for p in (root/'materials').rglob('*') if p.suffix in ('.csv','.md','.pdf'))
    sources+=sorted(str(p.relative_to(root)) for p in (root/'decision_making').rglob('*') if p.suffix in ('.xlsx','.csv'))
    definitions=(root/'materials/decision_making_factors.md').read_text()
    data=dict(current_round=current,previous_round=previous,planning_round=planning,
              timeline=dict(latest_decision_round=current,latest_export_round=current,next_decision_round=planning,
                            mapping_source='User confirmed: Round 2 decisions generated materials/round2 outcomes.',
                            naming='Workbook folder labels name submitted decision periods. Export row/column labels remain unchanged.'),
              rounds={str(k):v for k,v in rounds.items()},kahn=history,team=team,previous_team=prior_team,
              submissions={str(previous):prior_team,str(current):team},factors=factors,accounting=accounting,
              historical_budget=sum(team['decisions'][k] for k in app.SPEND),sources=sources,
              definitions=definitions,definitions_available=bool(definitions),definition_issues=[],
              economic_schema={k:dict(min=v[0],max=v[1],description=v[2]) for k,v in SCHEMA.items()},
              audit=dict(version='not-frozen',rows=[],alternatives=[],status='No frozen pre-outcome forecast was supplied for this submission; no backtest accuracy is claimed.'),
              model=dict(version='review-5.0',paired_transitions=2,causal_calibration=False,
                         changes=[f'Anchor conditional scenarios to decision {current} and observed export {current}.',
                                  'Preserve reported CSV fair values, current CLV and original export labels.',
                                  'No prior recommendation is treated as the actual submission or recycled as current advice.'],
                         limitations=['Only two linked submissions; multiple simultaneous changes and competitors prevent causal coefficient identification.',
                                      f'Latest supplied industry aggregate is export round {industry_round}, not round {current}.',
                                      f'Round {planning} allocation budget is not confirmed. The revenue-based arm is not approval to spend.',
                                      'Conditional estimates use uncalibrated priors; unknown effects remain explicitly unquantified.']))
    data['marketing']=marketing_snapshot(root,rounds,current,previous)
    data['simulation']=build_review(data,root)
    data['economic_defaults']=scenario(data)
    data['insights']=dict(finance=financial_analysis(data),segment_lenses={k:segment_analysis(data,k) for k in CROSSWALKS})
    data['strategy']=build_stp(data)
    from segment_decision import build_segment_decision
    data['segment_decision']=build_segment_decision(data)
    data['strategy'].update(draft=dict(team['decisions']),recommendations=[],
                            status=f'Round {planning} segment focus is recommended; a 16-factor allocation has not been generated. Submitted decision {current} remains the reference.',
                            funding=dict(approved_budget=None,reference=data['historical_budget'],spend=data['historical_budget'],change=0,
                                         headroom=None,revenue_arm=round(.14*latest['income']['Net Revenue'],2),
                                         previous_confirmed_budget=71_422_000,previous_budget_round=2,
                                         budget_source='Round 3 ceiling unconfirmed; do not carry forward the Round 2 ceiling.'))
    data['simulation']['strategy']=data['strategy']['policy']['positioning']+' Primary target: Segment 3; secondary Segment 5 with Frictionless parity gate. Low Price and Frictionless are fair-value safeguards. Focus group: win Segments 3+5, defend 2+6, reserve 4, serve 1.'
    data['decision_changes']=[dict(key=f['key'],label=f['label'],unit=f['unit'],prior=prior_team['decisions'][f['key']],
                                   current=team['decisions'][f['key']],change=team['decisions'][f['key']]-prior_team['decisions'][f['key']],cell=team['cells'][f['key']]) for f in factors]
    # Preserve raw historical comparison, but never call it a frozen pre-outcome prediction.
    data['outcome_changes']=[dict(metric=k,prior=prior['scores'][k],current=latest['scores'][k],change=latest['scores'][k]-prior['scores'][k]) for k in QUADRANTS]
    data['reconciliations']=dict(net_income_rounding_residual=latest['income']['Net Income']-(latest['income']['Income Before Taxes']-latest['income']['Income Taxes']),
                                 segment_revenue_residual=data['marketing']['segment_revenue_difference'],
                                 segment_clv_residual=data['marketing']['segment_clv_difference'])
    return data
