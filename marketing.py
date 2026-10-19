"""Marketing source ingestion, reconciliation and descriptive segment diagnostics.
No causal response coefficients or assortment costs are fitted from these tables.
"""
import csv
import math
from pathlib import Path

FILES = ('marketCLV','marketRevenue','marketSize','preference','pricing','productPosition',
         'revenueByAccessPoint','revenueByOffering','revenueMarketShare')
SEGMENTS = tuple('SEGMENT '+str(i) for i in range(1,7))
ATTRIBUTES = ('LOW PRICE','BREADTH','DEPTH','BRAND','ONLINE','RETAIL','CUSTOMER SERVICE','SHOPPING EXPERIENCE')
COMPANY = "GETCHELL'S"


def numeric(value):
    value=float(value)
    if not math.isfinite(value) or value<0:
        raise ValueError('Marketing numeric values must be finite and nonnegative.')
    return value


def load_marketing(root,data):
    directory=Path(root)/'materials'/'round0'/'marketing'
    if not directory.exists():
        return {'available':False,'message':'No materials/marketing directory found.','sources':[]}
    raw={}
    for name in FILES:
        path=directory/(name+'-round0.csv')
        if not path.is_file():
            return {'available':False,'message':'Marketing source set is incomplete: missing '+path.name,'sources':[]}
        with path.open(encoding='utf-8-sig',newline='') as stream:
            reader=csv.DictReader(stream)
            raw[name]={'file':str(path.relative_to(root)),'columns':reader.fieldnames,'rows':list(reader)}
    history={}
    for name in ('marketRevenue','marketSize','marketCLV'):
        rounds={}
        for row in raw[name]['rows']:
            round_id=int(row['ROUND'])
            if round_id in rounds:raise ValueError('Duplicate marketing round in '+name)
            rounds[round_id]={s:numeric(row[s]) for s in SEGMENTS}
        if 0 not in rounds:raise ValueError('Round 0 missing from '+name)
        history[name]=rounds
    preferences={s:{} for s in SEGMENTS}
    for row in raw['preference']['rows']:
        if int(row['Round'])!=0:continue
        attr=row['Preference']
        if attr not in ATTRIBUTES:raise ValueError('Unknown preference attribute: '+attr)
        for s in SEGMENTS:
            if attr in preferences[s]:raise ValueError('Duplicate preference attribute')
            preferences[s][attr]=numeric(row[s])
    if any(set(p)!=set(ATTRIBUTES) or sum(p.values())<=0 for p in preferences.values()):
        raise ValueError('Each segment needs the eight nonempty preference attributes.')
    totals={name:{r:sum(values.values()) for r,values in rounds.items()} for name,rounds in history.items()}
    segments=[]
    for s in SEGMENTS:
        p=preferences[s];total=sum(p.values())
        row={'id':s,'preferences':p,'preference_sum':total,
             'normalized_preferences':{k:v/total for k,v in p.items()},
             'top_preferences':sorted(p,key=lambda k:-p[k])[:3], 'history':[]}
        for r in sorted(set(history['marketSize'])&set(history['marketRevenue'])&set(history['marketCLV'])):
            row['history'].append({'round':r,'size':history['marketSize'][r][s],
                                   'revenue':history['marketRevenue'][r][s],'clv':history['marketCLV'][r][s]})
        for key,name in [('size','marketSize'),('revenue','marketRevenue'),('clv','marketCLV')]:
            value=history[name][0][s];prior=history[name].get(-1,{}).get(s)
            row[key]=value;row[key+'_share']=value/totals[name][0] if totals[name][0] else 0
            row[key+'_growth']=value/prior-1 if prior else None
        segments.append(row)
    offerings={r['COMPANY']:{'low':numeric(r['Round-0 LOWER COST']),'high':numeric(r['Round-0 HIGHER COST'])}
               for r in raw['revenueByOffering']['rows']}
    access={r['COMPANY']:{'online':numeric(r['Round-0 ONLINE']),'store':numeric(r['Round-0 STORE'])}
            for r in raw['revenueByAccessPoint']['rows']}
    pricing={r['COMPANY']:{'low':numeric(r['Round-0 LOWER COST']),'high':numeric(r['Round-0 HIGHER COST'])}
             for r in raw['pricing']['rows']}
    positions=[]
    for r in raw['productPosition']['rows']:
        if int(r['Round'])!=0:continue
        values={k:numeric(v) for k,v in r.items() if k not in ('Category','Round')}
        if COMPANY not in values:raise ValueError('Getchell’s product-position values missing.')
        own=values[COMPANY];leader=max(values,key=values.get)
        positions.append({'attribute':r['Category'],'values':values,'own':own,
                          'rank_numeric':1+sum(v>own for v in values.values()),'companies':len(values),
                          'leader':leader,'leader_value':values[leader]})
    reported_shares={r['Product']:numeric(r['Round-0 Share']) for r in raw['revenueMarketShare']['rows']}
    offering_totals={k:sum(v[k] for v in offerings.values()) for k in ('low','high')}
    industry=sum(offering_totals.values())
    companies=[]
    for name,offer in offerings.items():
        total=sum(offer.values());channel=access.get(name)
        companies.append({'name':name,'low_revenue':offer['low'],'high_revenue':offer['high'],
                          'revenue':total,'high_mix':offer['high']/total if total else 0,
                          'derived_overall_share':total/industry if industry else 0,
                          'derived_low_offering_share':offer['low']/offering_totals['low'] if offering_totals['low'] else 0,
                          'derived_high_offering_share':offer['high']/offering_totals['high'] if offering_totals['high'] else 0,
                          'online':channel['online'] if channel else None,'store':channel['store'] if channel else None,
                          'online_mix':channel['online']/sum(channel.values()) if channel and sum(channel.values()) else None,
                          'reported_pricing':pricing.get(name),
                          'reported_low_all_market_share':reported_shares.get(name+' LOWER COST'),
                          'reported_high_all_market_share':reported_shares.get(name+' HIGHER COST')})
    own_company=next(c for c in companies if c['name']==COMPANY)
    income={r['name']:r['value'] for r in data['income']}
    scorecard={r['name']:r['value'] for r in data['scorecard']}
    revenue_gap=totals['marketRevenue'][0]-income['Net Revenue']
    clv_gap=totals['marketCLV'][0]-scorecard['Customer Lifetime Value']
    shares_total=sum(reported_shares.values())
    checks=[
        {'label':'Segment revenue vs Getchell’s financial revenue','difference':revenue_gap,
         'status':'Reconciled' if abs(revenue_gap)<=1 else 'Mismatch',
         'meaning':'Exact reconciliation strongly indicates company revenue by customer segment—not whole-market revenue. Scope is inferred from reconciliation, not explicitly declared by the filename.'},
        {'label':'Segment CLV vs company CLV scorecard','difference':clv_gap,
         'status':'Rounding-level difference' if abs(clv_gap)<=1 else 'Mismatch',
         'meaning':'Treat the segment CLV figures as allocation of the reported company CLV; a $1 discrepancy is retained, not silently corrected.'},
        {'label':'Rounded all-market offering shares','difference':shares_total-1,
         'status':'Rounded inputs',
         'meaning':'Reported component shares sum to '+format(shares_total,'.3%')+'. Preserve them; derive separate ratios from reported revenues and disclose the denominator.'},
    ]
    channel_diffs=[{'company':name,'difference':sum(access[name].values())-sum(offer.values())}
                   for name,offer in offerings.items() if name in access and sum(access[name].values())!=sum(offer.values())]
    cost_match=all(abs(pricing[COMPANY][key]-scorecard['Cost of '+label+' Cost Products'])<.001 for key,label in [('low','Lower'),('high','Higher')])
    notes=[
        'Market-size units and segment definitions are not specified. These are reported size figures, not verified unique customer counts. No customer penetration rate can be computed without buyer counts and matched denominator definitions.',
        'Preference entries do not sum to one within a segment. Display raw values as relative preference measures, not population percentages. Any normalized weights are an explicitly assumed within-segment scaling.',
        'No segment-by-offering purchase or inventory cross-tab is supplied. Brand/experience-oriented segments are not automatically higher-cost buyers; price-sensitive segments are not automatically lower-cost buyers.',
        'Product-position numbers are a different table/scale from the Kahn matrix. Numerical ranks compare reported values only; the simulator’s exact score interpretation, ceiling and marginal response remain unverified.',
        'Pricing values match the scorecard product-cost metrics for Getchell’s.' if cost_match else 'Pricing values differ from scorecard product-cost metrics.',
        'Do not treat the pricing table as verified selling prices or recalibrate markups/elasticities until its units and cost-versus-price basis are confirmed.',
        'Reported offering shares are contributions to the common all-market denominator, not penetration or market share within each offering. Derived within-offering shares use only the seven reported companies.',
        'The new files provide descriptive customer evidence, not causal decision-to-sales formulas, incremental assortment costs, or a calibrated optimization model.',
    ]
    return {'available':True,'sources':[raw[n]['file'] for n in FILES],'raw_tables':list(raw.values()),
            'segments':segments,'attributes':list(ATTRIBUTES),'companies':companies,'own_company':own_company,
            'positions':positions,'offering_totals':offering_totals,'reported_company_revenue_total':industry,
            'history_totals':{name:[{'round':r,'value':v} for r,v in sorted(rounds.items())] for name,rounds in totals.items()},
            'totals':{'size':totals['marketSize'][0],'segment_revenue':totals['marketRevenue'][0],
                      'segment_clv':totals['marketCLV'][0],'reported_share_sum':shares_total},
            'checks':checks,'channel_reconciliation_differences':channel_diffs,'pricing_cost_match':cost_match,'notes':notes,
            'scope':{'revenue':'Getchell’s segment revenue (scope inferred by exact financial reconciliation)',
                     'clv':'Company segment CLV allocation (inferred by scorecard reconciliation within $1)',
                     'size':'Reported segment size; units/market universe not confirmed'},
            'paired_causal_observations':0}


def assortment_alignment(marketing,baseline,candidate):
    if not marketing or not marketing.get('available'):return {'available':False}
    # Cost-tier affinity is absent: equal exposure across the two offerings is a
    # declared diagnostic assumption, NOT a fitted demand or financial model.
    breadth=((candidate['low_breadth']-baseline['low_breadth'])+(candidate['high_breadth']-baseline['high_breadth']))/200
    depth=((candidate['low_depth']-baseline['low_depth'])+(candidate['high_depth']-baseline['high_depth']))/200
    rows=[]
    for s in marketing['segments']:
        p=s['normalized_preferences'];b=p['BREADTH']*breadth;d=p['DEPTH']*depth
        rows.append({'segment':s['id'],'breadth_preference':s['preferences']['BREADTH'],
                     'depth_preference':s['preferences']['DEPTH'],'breadth_change_pp':100*b,'depth_change_pp':100*d,
                     'alignment_change_pp':100*(b+d),
                     'size_share':s['size_share'],'revenue_share':s['revenue_share'],'clv_share':s['clv_share']})
    return {'available':True,'rows':rows,
            'weighted_changes_pp':{basis:sum(r['alignment_change_pp']*r[basis+'_share'] for r in rows) for basis in ('size','revenue','clv')},
            'method':'Normalize each segment’s eight raw preferences by their sum. Alignment change = breadth weight × average two-offering breadth-index change / 100 + depth weight × average depth-index change / 100; report ×100 as index points. Equal offering exposure is assumed because purchase affinity is missing.',
            'warning':'Descriptive preference-alignment proxy only—not a predicted Kahn score, sales lift, market share, penetration or profit. Does not change the existing Kahn/financial forecasts. No segment-by-cost-tier affinity or marginal cost is inferred.'}
