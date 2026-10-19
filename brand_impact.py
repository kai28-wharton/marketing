"""Workbook-linked Brand diagnosis, separating score reconstruction from causality.

The candidate position-to-Brand identity is checked against all supplied retailer
rows in both rounds. It does not establish an input-to-position response curve.
The frozen v2 attribution is displayed as a model audit, not the actual causes.
"""
import math
from prediction import configuration, point
from round_review import COMPANY

TERMS=(('low_depth','LOWER COST DEPTH'),('high_depth','HIGHER COST DEPTH'),
       ('private_low','LOWER COST PRIVATE BRAND'),('private_high','HIGHER COST PRIVATE BRAND'))


def reconstruct(positions):
    return .5*sum(positions[attr] for _,attr in TERMS)


def parameter_model_audit(data,legacy_data):
    """Exact Shapley over changed Brand-relevant parameters of the frozen model."""
    from app import BASE, DEFAULT_ASSUMPTIONS
    plan=data['team']['decisions'];strength=DEFAULT_ASSUMPTIONS['score_response']
    current=data['rounds']['0']['scores'];config=configuration(legacy_data,BASE)
    relevant={'vendor','analytics','experience','coverage','private_quality','national_quality',
              'low_breadth','high_breadth','low_private','high_private'}
    active=[f['key'] for f in data['factors'] if f['key'] in relevant and plan[f['key']]!=BASE[f['key']]]
    cache={}
    for mask in range(1<<len(active)):
        p=dict(BASE)
        p.update({key:plan[key] for j,key in enumerate(active) if mask&(1<<j)})
        cache[mask]=point(p,BASE,current,config,strength)['BRAND']
    allocations={key:0. for key in plan};n=len(active)
    for j,key in enumerate(active):
        for mask in range(1<<n):
            if mask&(1<<j):continue
            size=mask.bit_count()
            allocations[key]+=(cache[mask|(1<<j)]-cache[mask])/(n*math.comb(n-1,size))
    full=point(plan,BASE,current,config,strength)['BRAND']
    rows=[]
    for f in data['factors']:
        key=f['key'];single=dict(BASE,**{key:plan[key]});undo=dict(plan,**{key:BASE[key]})
        rows.append(dict(key=key,label=f['label'],cell=data['team']['cells'][key],reference=BASE[key],
                         submitted=plan[key],change=plan[key]-BASE[key],unit=f['unit'],
                         one_at_a_time=point(single,BASE,current,config,strength)['BRAND']-current['BRAND'],
                         leave_one_out=full-point(undo,BASE,current,config,strength)['BRAND'],
                         shapley=allocations[key],brand_channel_in_v2=key in relevant))
    return dict(rows=rows,predicted_brand=full,predicted_change=full-current['BRAND'],
                allocated_change=sum(allocations.values()),active_parameters=len(active),subsets_evaluated=len(cache),
                boundary='Exact allocation of the frozen v2 mathematical response, not observed causal contributions. Depth has no Brand term in v2; its zero is a model omission, not evidence of no real effect. Old reference inputs are unverified screenshot assumptions.')


def build_brand_impact(data,legacy_data):
    raw=next(t for t in data['marketing']['raw_tables'] if t['file'].endswith('productPosition-round1.csv'))
    by_round={r:{row['Category']:row for row in raw['rows'] if int(row['Round'])==r} for r in (0,1)}
    companies=list(data['marketing']['positions'][0]['values'])
    validation=[]
    for rnd in (0,1):
        for company in companies:
            positions={attr:float(by_round[rnd][attr][company]) for _,attr in TERMS}
            predicted=reconstruct(positions)
            actual=next(r['value'] for r in data['kahn'] if r['round']==rnd and r['quadrant']=='BRAND' and r['company']==company)
            validation.append(dict(round=rnd,company=company,reconstructed=predicted,actual=actual,residual=actual-predicted))
    own={r:{attr:float(by_round[r][attr][COMPANY]) for _,attr in TERMS} for r in (0,1)}
    scores={r:data['rounds'][str(r)]['scores']['BRAND'] for r in (0,1)}
    residual={r:scores[r]-reconstruct(own[r]) for r in (0,1)}
    contributions=[]
    for key,attr in TERMS:
        before=own[0][attr];after=own[1][attr]
        contributions.append(dict(key=key,attribute=attr,prior_position=before,current_position=after,
                                  position_change=after-before,weight=.5,brand_change=.5*(after-before),
                                  input=data['team']['decisions'].get(key),cell=data['team']['cells'].get(key),
                                  reference=next((f['prior_reference'] for f in data['factors'] if f['key']==key),None)))
    adverse=-sum(min(0,r['brand_change']) for r in contributions)
    for row in contributions:
        row['gross_adverse_share']=(-row['brand_change']/adverse) if row['brand_change']<0 and adverse else None
    substitutions=[]
    for label,keys in [('Restore lower-cost depth position only',['low_depth']),
                       ('Restore higher-cost depth position only',['high_depth']),
                       ('Restore both depth positions',['low_depth','high_depth']),
                       ('Remove both private-position improvements',['private_low','private_high'])]:
        change=-sum(r['brand_change'] for r in contributions if r['key'] in keys)
        substitutions.append(dict(label=label,brand=scores[1]+change,change=change,
                                  basis='Substitute observed positions while holding all other terms and the R1 residual fixed. Not an input-level simulator counterfactual.'))
    max_error=max(abs(r['residual']) for r in validation)
    linked=[]
    factor_map={f['key']:f for f in data['factors']}
    for key in ('high_depth','low_depth'):
        row=next(r for r in contributions if r['key']==key);f=factor_map[key]
        linked.append(dict(**row,label=f['label'],input_change=row['input']-row['reference'],
                           industry_min=f['industry']['minimum'],industry_max=f['industry']['maximum'],
                           inside_industry_range=f['industry']['minimum']<=row['input']<=f['industry']['maximum']))
    return dict(source=data['team']['source'],sha256=data['team']['sha256'],column=data['team']['column_label'],
                formula='Brand ≈ 0.5 × (LOWER COST DEPTH + HIGHER COST DEPTH + LOWER COST PRIVATE BRAND + HIGHER COST PRIVATE BRAND), using reported positions—not decision indices.',
                contributions=contributions,linked_depth_decisions=linked,
                gross_adverse=adverse,positive_offset=sum(max(0,r['brand_change']) for r in contributions),
                reconstructed_change=sum(r['brand_change'] for r in contributions),observed_change=scores[1]-scores[0],
                prior_reconstructed=reconstruct(own[0]),current_reconstructed=reconstruct(own[1]),
                prior_residual=residual[0],current_residual=residual[1],residual_change=residual[1]-residual[0],
                validation=validation,validation_rows=len(validation),max_absolute_error=max_error,
                within_005=sum(abs(r['residual'])<=.05+1e-9 for r in validation),
                discovery_status='Exploratory identity discovered and checked on the same 14 reported rows; not independent held-out validation or an official simulator formula. FAIR VALUE has no product-position row and is not included.',
                substitutions=substitutions,legacy_parameter_audit=parameter_model_audit(data,legacy_data),
                conclusion='Depth contraction is the strongest score-linked explanation supported by the observed data; higher-cost depth is the largest adverse reconstructed component. Private-brand-position gains offset part of the loss. Input-to-position causality and future restoration sizes are not established.',
                input_boundary='The current workbook is user-linked to R1 but editable. Cell provenance and hash identify this snapshot, not an immutable simulator execution log. The previous input reference is an unverified screenshot; the prior and current product positions and Brand scores are observed.',
                test_plan=[dict(key='high_depth',cell=data['team']['cells']['high_depth'],current=data['team']['decisions']['high_depth'],test=min(factor_map['high_depth']['max'],data['team']['decisions']['high_depth']+5),
                                rationale='First test: largest adverse score-linked term; increase only higher-cost depth by five input points.'),
                           dict(key='low_depth',cell=data['team']['cells']['low_depth'],current=data['team']['decisions']['low_depth'],test=min(factor_map['low_depth']['max'],data['team']['decisions']['low_depth']+5),
                                rationale='Second separate test: increase only lower-cost depth by five input points; do not combine with the first test.')])
