"""Observed final strategy scorecard; no segment profit or causal ROI inferred."""


def segmentation_strategy_review(analysis):
    """Reconcile the stated priority order with outcomes; not spending attribution."""
    segments = {s['id']: s for s in analysis['segments']}
    history = analysis['history']
    totals = {r['round']: sum(next(x for x in s['history'] if x['round']==r['round'])['revenue']
                              for s in segments.values()) for r in history}
    clv_total = {r['round']: sum(next(x for x in s['history'] if x['round']==r['round'])['clv']
                                 for s in segments.values()) for r in history}
    def outcome(ids, label):
        selected = [segments[i] for i in ids]
        series = []
        for r in history:
            n = r['round']
            observations = [next(x for x in s['history'] if x['round']==n) for s in selected]
            revenue = sum(x['revenue'] for x in observations)
            clv = sum(x['clv'] for x in observations)
            series.append(dict(round=n, revenue=revenue, clv=clv,
                               mix=revenue/totals[n], clv_mix=clv/clv_total[n]))
        first, last = series[0], series[-1]
        phases = []
        for start, end in ((0,2),(2,6),(6,8)):
            a = next(x for x in series if x['round']==start)
            b = next(x for x in series if x['round']==end)
            phases.append(dict(start=start, end=end, growth=b['revenue']/a['revenue']-1,
                               per_round_growth=(b['revenue']/a['revenue'])**(1/(end-start))-1,
                               mix_change_pp=100*(b['mix']-a['mix'])))
        return dict(label=label, ids=ids, history=series, phases=phases,
                    revenue=last['revenue'], initial_revenue=first['revenue'],
                    revenue_growth=last['revenue']/first['revenue']-1,
                    incremental_revenue=last['revenue']-first['revenue'],
                    growth_share=(last['revenue']-first['revenue'])/(totals[8]-totals[0]),
                    mix=last['mix'], initial_mix=first['mix'], mix_change_pp=100*(last['mix']-first['mix']),
                    clv=last['clv'], clv_growth=last['clv']/first['clv']-1,
                    clv_mix=last['clv_mix'], initial_clv_mix=first['clv_mix'],
                    clv_growth_share=(last['clv']-first['clv'])/(clv_total[8]-clv_total[0]),
                    constant_mix_benchmark=first['mix']*totals[8],
                    constant_mix_difference=last['revenue']-first['mix']*totals[8])
    priority = [('SEGMENT 3','1 · S3 · primary'),('SEGMENT 6','2 · S6 · secondary'),
                ('SEGMENT 2','3 · S2 · supporting'),('SEGMENT 4','3 · S4 · supporting'),
                ('SEGMENT 5','3 · S5 · supporting'),('SEGMENT 1','S1 · outside stated priorities')]
    rows = [outcome([sid],label) for sid,label in priority]
    groups = [outcome(['SEGMENT 3','SEGMENT 6'],'S3 + S6 · targets'),
              outcome(['SEGMENT 2','SEGMENT 4','SEGMENT 5'],'S2 + S4 + S5 · supporting'),
              outcome(['SEGMENT 1'],'S1 · outside priorities')]
    return dict(priority_order=['SEGMENT 3','SEGMENT 6',['SEGMENT 2','SEGMENT 4','SEGMENT 5']],
                rows=rows, groups=groups,
                company_growth=totals[8]/totals[0]-1,
                phases=[dict(start=start,end=end,per_round_growth=(totals[end]/totals[start])**(1/(end-start))-1)
                        for start,end in ((0,2),(2,6),(6,8))],
                phase_basis='R0–R2, R2–R6 and R6–R8 are descriptive execution windows, not treatment periods. Per-round compound growth normalizes their unequal lengths.',
                benchmark_basis='R0 revenue mix × actual R8 company revenue is a composition benchmark, not a counterfactual forecast, lost sales or recoverable revenue.')


def build_final_review(data):
    analysis = data['history_analysis']
    history = analysis['history']
    first, last = history[0], history[-1]
    late = next(r for r in history if r['round']==6)
    segments = analysis['segments']
    total_revenue_change = last['revenue']-first['revenue']
    total_clv = sum(s['clv'] for s in segments)
    initial_clv = sum(s['history'][0]['clv'] for s in segments)
    rows = []
    for s in segments:
        baseline = s['history'][0]
        checkpoint = next(r for r in s['history'] if r['round']==3)
        recovery = next(r for r in s['history'] if r['round']==6)
        row = dict(id=s['id'], role='Primary target' if s['id']=='SEGMENT 3' else 'Secondary target' if s['id']=='SEGMENT 6' else 'Defend' if s['id']=='SEGMENT 2' else 'Reserve' if s['id'] in ('SEGMENT 4','SEGMENT 5') else 'Serve',
                   revenue=s['revenue'], initial_revenue=baseline['revenue'], revenue_growth=s['revenue_growth'],
                   checkpoint_growth=s['revenue']/checkpoint['revenue']-1,
                   late_growth=s['revenue']/recovery['revenue']-1,
                   mix=s['revenue_mix'], mix_change_pp=100*s['revenue_mix_change'],
                   clv=s['clv'], clv_growth=s['clv_growth'],
                   clv_mix=s['clv']/total_clv,
                   clv_mix_change_pp=100*(s['clv']/total_clv-baseline['clv']/initial_clv),
                   incremental_revenue=s['revenue']-baseline['revenue'],
                   contribution_to_revenue_growth=(s['revenue']-baseline['revenue'])/total_revenue_change,
                   population_growth=s['population_growth'], preferences=s['preferences'])
        rows.append(row)
    core = [r for r in rows if r['id'] in ('SEGMENT 3','SEGMENT 6')]
    core_summary = dict(revenue=sum(r['revenue'] for r in core), clv=sum(r['clv'] for r in core),
                        mix=sum(r['mix'] for r in core), mix_change_pp=sum(r['mix_change_pp'] for r in core),
                        clv_mix=sum(r['clv_mix'] for r in core), clv_mix_change_pp=sum(r['clv_mix_change_pp'] for r in core),
                        growth_share=sum(r['contribution_to_revenue_growth'] for r in core),
                        late_growth=sum(r['revenue'] for r in core)/sum(next(s for s in segments if s['id']==r['id'])['history'][6]['revenue'] for r in core)-1)
    objectives = [dict(quadrant=q, **v) for q,v in last['quadrants'].items()]
    scored = history[1:]
    objective_delivery = [dict(quadrant=q, rounds_met=[r['round'] for r in scored if r['quadrants'][q]['target_met']],
                               count=sum(r['quadrants'][q]['target_met'] for r in scored),
                               total=len(scored), final=last['quadrants'][q])
                          for q in ('EXPERIENCE','BRAND','FRICTIONLESS','LOW PRICE')]
    # These conclusions describe realized execution and timing, not causal attribution.
    return dict(final_round=last['round'], scored_rounds=[r['round'] for r in scored],
                 snapshot_count=len(history), checkpoint_round=3, rows=rows, core=core_summary,
                 segmentation_strategy=segmentation_strategy_review(analysis),
                 objective_delivery=objective_delivery,
                 all_objectives_met_rounds=[r['round'] for r in scored if all(v['target_met'] for v in r['quadrants'].values())],
                objectives=objectives, objectives_met=sum(v['target_met'] for v in last['quadrants'].values()),
                experience_leader_rounds=[r['round'] for r in scored if r['quadrants']['EXPERIENCE']['rank']==1],
                brand_top_two_rounds=[r['round'] for r in scored if r['quadrants']['BRAND']['rank']<=2],
                frictionless_below_floor_rounds=[r['round'] for r in scored if r['quadrants']['FRICTIONLESS']['gap']<0],
                marketing_wins=[
                     'The final positioning objectives were achieved: Experience and Brand both finish #1. This is an observed score outcome, not proof of a causal targeting effect.',
                     'Service position rose from 1.5 at R6 to 3.0 at R8 while shopping experience rose from 3.3 to 3.6.',
                    'Both target segments grew revenue and aggregate customer equity; S3+S6 growth accelerated over the final two rounds.'],
                marketing_misses=[
                    'Execution arrived late: Experience did not reach #1 until R8. Strong ambience alone had not compensated for weak service.',
                    'The company-wide convenience safeguard was never met: Frictionless remained below the exported fair-value floor in every scored round.',
                    'S3 lost revenue and aggregate-CLV mix while S6 gained both; combined S3+S6 mix gains do not establish target dominance or segment profitability. S1 remained the largest final revenue and customer-equity pool.',
                     'Online capability fell from 1.3 at R6 to 0.9 at R8 while stores expanded. Frictionless improved alongside service recovery but still ended 0.7 below its floor; the service effect is not separately identified.'],
                lessons=[
                    'Protect service execution alongside Brand and shopping experience; a favorable Brand/Experience proposition is not a substitute for delivered capability.',
                    'Pair S6 Experience delivery with Low Price parity; retain Frictionless parity as a company-wide safeguard, not an S6-specific targeting gate.',
                    'Track S3/S6 mix and customer equity separately, not just combined sales; preserve the supporting S2/S4/S5 base and recognize S1 growth.',
                    'Evaluate store and channel investment against customer reach, contribution and funding needs together—not market value or WACC in isolation.'],
                finance=dict(market_value=last['market_value'], value_growth=last['market_value']/first['market_value']-1,
                             revenue=last['revenue'], revenue_growth=last['revenue']/first['revenue']-1,
                             net_income=last['net_income'], initial_net_income=first['net_income'],
                             ebit=last['ebit'], initial_ebit=first['ebit'], debt=last['debt'],
                             debt_change=last['debt']-first['debt'], late_debt_change=last['debt']-late['debt'],
                             interest=last['interest'], wacc=last['wacc'], wacc_change_pp=last['wacc']-first['wacc'],
                             gross_margin=last['gross_margin'], initial_margin=first['gross_margin'],
                             unit_share=last['unit_share'], initial_unit_share=first['unit_share'],
                             revenue_share=last['revenue_share'], stores=last['decisions']['coverage'],
                             late_stores=late['decisions']['coverage']),
                conclusion='A late marketing turnaround and a strong financial recovery under the team-confirmed S3-primary, S6-secondary strategy. Both differentiators finished first; S6 gained revenue mix while S3 lost mix. Frictionless parity and consistent Experience leadership remained unfinished.',
                boundary='Company segment revenue and aggregate CLV are observed. Revenue mix is within Getchell’s, not segment market share. Population is the whole market, not company buyers. No segment profit, acquisition cost, retention, causal marketing ROI or competitor-relative segment penetration is supplied. R3 is an explicit comparison checkpoint, not a proven treatment start date.')
