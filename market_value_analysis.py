"""Lagged Kahn fits, two-stage position models and a non-circular value fit.

Brand and Low Price use decisions in round t to explain ratings in round t+1.
Experience retains a lagged position fit. Frictionless has a separate audited
conditional specification and timing sensitivity; neither is verified mechanics. Six
transitions are available. Fifteen distinct input series are used because
private and national quality are identical in every observed round. A fixed
ridge penalty is used for every fitted equation so the six transitions are not
used to tune a penalty as well as coefficients.
"""
import math
from statistics import mean

QUADRANTS=('BRAND','EXPERIENCE','LOW PRICE','FRICTIONLESS')
KAHN_PENALTY=0.1
VALUE_PENALTY=0.01

INPUT_KEYS=(
    'low_markup','low_breadth','low_depth','low_private',
    'high_markup','high_breadth','high_depth','high_private',
    'private_quality','coverage','online','service','experience','vendor','analytics',
)

FEATURES={
    'price':dict(label='Price markup',unit='%',inputs=['low_markup','high_markup'],
                 definition='Average of lower-cost and higher-cost price markup (%).'),
    'breadth':dict(label='Assortment breadth',unit='index',inputs=['low_breadth','high_breadth'],
                   definition='Average of lower-cost and higher-cost breadth (index points).'),
    'depth':dict(label='Assortment depth',unit='index',inputs=['low_depth','high_depth'],
                 definition='Average of lower-cost and higher-cost depth (index points).'),
    'private':dict(label='Private-brand mix',unit='%',inputs=['low_private','high_private'],
                   definition='Average private-brand share across both product lines (%).'),
    'quality':dict(label='Quality (private = national)',unit='index',inputs=['private_quality','national_quality'],
                   definition='Private Brand Quality and National Brand Quality; identical in every observed round, so they enter as one shared quality setting.'),
    'reach':dict(label='Retail Coverage',unit='10 stores',inputs=['coverage'],
                 definition='Retail coverage (tens of stores).'),
    'service':dict(label='Customer Service',unit='$M',inputs=['service'],
                   definition='Customer-service spending ($M).'),
    'service_int':dict(label='Service intensity',unit='$10k/store',inputs=['service','coverage'],
                       definition='Customer-service spending per store ($10k per store).'),
    'experience_int':dict(label='Experience intensity',unit='$10k/store',inputs=['experience','coverage'],
                          definition='Shopping-experience spending per store ($10k per store).'),
    'online':dict(label='Online Investment',unit='$M',inputs=['online'],
                  definition='Online investment ($M).'),
    'online_pos':dict(label='Online position',unit='index',inputs=['online'],position=True,
                      definition='Reported ONLINE INVEST position (0–10), not online spending.'),
    'service_pos':dict(label='Customer Service position',unit='index',inputs=['service'],position=True,
                       definition='Reported CUSTOMER SERVICE position (0–10), not service spending.'),
    'vendor':dict(label='Vendor Management',unit='$M',inputs=['vendor'],
                  definition='Vendor-management spending ($M).'),
    'analytics':dict(label='Customer Analytics',unit='$M',inputs=['analytics'],
                     definition='Customer-analytics spending ($M).'),
    'assortment':dict(label='Assortment (breadth + depth)',unit='index',inputs=['low_breadth','high_breadth','low_depth','high_depth'],
                      definition='Average of Lower/Higher Cost Products breadth and depth settings (index points).'),
}

POSITION_SPECS={
    'ONLINE INVEST':dict(key='online',decision='online',decision_label='Online Investment',prior='online_pos_t',
                         features=['online_pos_t','online_avg'],
                         rationale='Online position is fitted to its prior position and online spending relative to the same round’s industry average. The ratio is the competitor benchmark; nominal dollars alone are not treated as capability.'),
    'CUSTOMER SERVICE':dict(key='service',decision='service',decision_label='Customer Service',prior='service_pos_t',
                            features=['service_pos_t','service_avg','analytics_avg'],
                            rationale='Customer-service position is fitted to its prior position, service spending relative to the industry average, and analytics spending relative to the industry average. Analytics is a documented service/experience enabler; its coefficient is positive and stable in hide-one refits.'),
    'SHOPPING EXPERIENCE':dict(key='experience',decision='experience',decision_label='Shopping Experience',prior='exp_pos_t',
                               features=['exp_pos_t','experience_avg'],
                               rationale='Shopping-experience position is fitted to its prior position and shopping-experience spending relative to the industry average. Service is modeled separately and added in the reported score identity.'),
}

POSITION_FEATURES={
    'online_pos_t':dict(label='Prior online position',unit='index'),
    'online_avg':dict(label='Online spend ÷ industry average',unit='×'),
    'service_pos_t':dict(label='Prior service position',unit='index'),
    'service_avg':dict(label='Service spend ÷ industry average',unit='×'),
    'analytics_avg':dict(label='Analytics spend ÷ industry average',unit='×'),
    'exp_pos_t':dict(label='Prior shopping-experience position',unit='index'),
    'experience_avg':dict(label='Experience spend ÷ industry average',unit='×'),
}

KAHN_SPECS={
    'BRAND':dict(features=['quality','assortment','private','vendor','analytics'],form='level',
                 rationale='Brand is fitted to the shared quality setting, the assortment breadth/depth average, private-brand mix, Vendor Management and Customer Analytics. Vendor and analytics enter separately so the equation uses the actual workbook decisions rather than a combined spending score.'),
    'LOW PRICE':dict(features=['price','private','vendor','analytics'],form='level',
                     rationale='Low Price is fitted to price markup, private-brand mix, vendor management and customer analytics separately. The fit is shown even though the rating is nearly flat and persistence is more accurate.'),
}


def solve(matrix,vector):
    a=[list(row)+[v] for row,v in zip(matrix,vector)]
    for i in range(len(a)):
        pivot=max(range(i,len(a)),key=lambda j:abs(a[j][i]))
        a[i],a[pivot]=a[pivot],a[i]
        if abs(a[i][i])<1e-12:
            raise ValueError('Singular diagnostic model.')
        d=a[i][i]
        a[i]=[v/d for v in a[i]]
        for j in range(len(a)):
            if j!=i:
                d=a[j][i]
                a[j]=[v-d*w for v,w in zip(a[j],a[i])]
    return [row[-1] for row in a]


def _standardize(rows,features,key='x'):
    source=(lambda r:r[key]) if key is not None else (lambda r:r)
    centers=[mean(source(r)[f] for r in rows) for f in features]
    scales=[math.sqrt(mean((source(r)[f]-m)**2 for r in rows)) or 1 for f,m in zip(features,centers)]
    return centers,scales


def _ridge(rows,features,targets,penalty,key='x'):
    centers,scales=_standardize(rows,features,key)
    source=(lambda r:r[key]) if key is not None else (lambda r:r)
    x=[[1]+[(source(r)[f]-m)/s for f,m,s in zip(features,centers,scales)] for r in rows]
    p=len(features)+1
    a=[[sum(row[i]*row[j] for row in x)+(penalty if i==j and i>0 else 0) for j in range(p)] for i in range(p)]
    beta=solve(a,[sum(row[i]*v for row,v in zip(x,targets)) for i in range(p)])
    return dict(features=list(features),centers=centers,scales=scales,coefficients=beta,penalty=penalty)


def _predict(model,row,key='x'):
    source=row[key] if key is not None else row
    z=[1]+[(source[f]-m)/s for f,m,s in zip(model['features'],model['centers'],model['scales'])]
    return sum(b*v for b,v in zip(model['coefficients'],z))


def feature_values(decisions):
    """Fifteen distinct inputs plus interpretable composites."""
    low_breadth=decisions['low_breadth'];high_breadth=decisions['high_breadth']
    low_depth=decisions['low_depth'];high_depth=decisions['high_depth']
    breadth=(low_breadth+high_breadth)/2
    depth=(low_depth+high_depth)/2
    return {
        'price':(decisions['low_markup']+decisions['high_markup'])/2,
        'breadth':breadth,
        'depth':depth,
        'private':(decisions['low_private']+decisions['high_private'])/2,
        'quality':decisions['private_quality'],
        'reach':decisions['coverage']/10,
        'service':decisions['service']/1e6,
        'service_int':decisions['service']/decisions['coverage']/1e4 if decisions['coverage'] else 0.,
        'experience_int':decisions['experience']/decisions['coverage']/1e4 if decisions['coverage'] else 0.,
        'online':decisions['online']/1e6,
        'vendor':decisions['vendor']/1e6,
        'analytics':decisions['analytics']/1e6,
        'assortment':(breadth+depth)/2,
    }


def transition_rows(history):
    rows=[]
    for t in range(len(history)-1):
        rows.append(dict(
            transition=t,next_round=history[t+1]['round'],
            x=feature_values(history[t]['decisions']),
            y={q:history[t+1]['quadrants'][q]['score'] for q in QUADRANTS},
            prior={q:history[t]['quadrants'][q]['score'] for q in QUADRANTS},
        ))
    return rows


def _fit_kahn_model(rows,quadrant,spec):
    features=spec['features'];form=spec['form']
    targets=[r['y'][quadrant] if form=='level' else r['y'][quadrant]-r['prior'][quadrant] for r in rows]
    model=_ridge(rows,features,targets,KAHN_PENALTY)
    model.update(quadrant=quadrant,form=form)
    return model


def _predict_kahn(model,row):
    raw=_predict(model,row)
    return raw if model['form']=='level' else row['prior'][model['quadrant']]+raw


def _raw_model(model):
    """Convert the standardized ridge fit back to the displayed input units."""
    raw=[beta/scale for beta,scale in zip(model['coefficients'][1:],model['scales'])]
    intercept=model['coefficients'][0]-sum(b*m for b,m in zip(raw,model['centers']))
    return intercept,raw


def _equation_term(value,feature):
    return (f"{'+' if value>=0 else '−'} {abs(value):.4f} × "
            f"{FEATURES[feature]['label']} ({FEATURES[feature]['unit']})")


def _position_rows(history):
    labels=(('online','Online Investment'),('service','Customer Service'),
            ('experience','Shopping Experience'),('analytics','Customer Analytics'))
    rows=[]
    for t in range(len(history)-1):
        industry=history[t].get('industry',{})
        x={}
        for key,label in labels:
            average=(industry.get(label) or {}).get('Average')
            x[key+'_avg']=history[t]['decisions'][key]/average if average else None
        x.update(online_pos_t=history[t]['positions']['ONLINE INVEST'],
                 service_pos_t=history[t]['positions']['CUSTOMER SERVICE'],
                 exp_pos_t=history[t]['positions']['SHOPPING EXPERIENCE'])
        y=dict(history[t+1]['positions'])
        prior=dict(history[t]['positions'])
        rows.append(dict(transition=t,next_round=t+1,x=x,y=y,prior=prior))
    return rows


def _fit_position_model(rows,target):
    spec=POSITION_SPECS[target];features=spec['features']
    training=[dict(x=r['x'],y=r['y'][target]) for r in rows]
    model=_ridge(training,features,[r['y'] for r in training],KAHN_PENALTY)
    model.update(quadrant=target,form='level')
    return model


def _position_term(value,feature):
    f=POSITION_FEATURES[feature]
    return f"{'+' if value>=0 else '−'} {abs(value):.4f} × {f['label']} ({f['unit']})"


def _position_model_summary(rows,target):
    spec=POSITION_SPECS[target];model=_fit_position_model(rows,target)
    predictions=[]
    for row in rows:
        fitted=_predict(model,{'x':row['x']})
        predictions.append(dict(round=row['next_round'],actual=row['y'][target],
                                fitted=fitted,error=fitted-row['y'][target]))
    actual=[p['actual'] for p in predictions];fitted=[p['fitted'] for p in predictions]
    fitted_mae=mean(abs(a-p) for a,p in zip(actual,fitted))
    persistence_mae=mean(abs(r['prior'][target]-r['y'][target]) for r in rows)
    latest=rows[-1] if rows else None
    hide=[];top3_folds={feature:0 for feature in model['features']}
    for i,row in enumerate(rows):
        trial=_fit_position_model(rows[:i]+rows[i+1:],target)
        hide.append(abs(_predict(trial,{'x':row['x']})-row['y'][target]))
        contributions=[]
        for j,feature in enumerate(trial['features']):
            z=(latest['x'][feature]-trial['centers'][j])/trial['scales'][j]
            contributions.append((feature,trial['coefficients'][j+1]*z))
        for feature,_ in sorted(contributions,key=lambda item:abs(item[1]),reverse=True)[:min(3,len(contributions))]:
            top3_folds[feature]+=1
    mean_actual=mean(actual)
    ss_total=sum((a-mean_actual)**2 for a in actual)
    r_squared=1-sum((a-p)**2 for a,p in zip(actual,fitted))/ss_total if ss_total else None
    raw_intercept,raw_coefficients=_raw_model(model)
    terms=[_position_term(b,f) for b,f in zip(raw_coefficients,model['features'])]
    equation=f"{spec['decision_label']} position(t+1) = {raw_intercept:.4f} "+' '.join(terms)
    coefficients=[]
    for feature,beta in zip(model['features'],raw_coefficients):
        f=POSITION_FEATURES[feature]
        contribution=beta*latest['x'][feature]
        coefficients.append(dict(term=feature,label=f['label'],unit=f['unit'],
                                 raw_coefficient=beta,direction='positive' if beta>=0 else 'negative',
                                 latest_contribution=contribution,
                                 top3_folds=top3_folds[feature],top3_share=top3_folds[feature]/len(rows),
                                 importance_rank=0))
    for rank,item in enumerate(sorted(coefficients,key=lambda c:abs(c['latest_contribution']),reverse=True),1):
        item['importance_rank']=rank
    top_factors=sorted(coefficients,key=lambda c:c['importance_rank'])[:3]
    return dict(target=target,key=spec['key'],decision_key=spec['decision'],
                decision_label=spec['decision_label'],prior=spec['prior'],
                features=list(model['features']),form='level',form_label='Position response',
                penalty=KAHN_PENALTY,predictions=predictions,fitted_mae=fitted_mae,
                hide_one_mae=mean(hide),persistence_mae=persistence_mae,r_squared=r_squared,
                coefficients=coefficients,top_factors=top_factors,intercept=raw_intercept,
                equation=equation,rationale=spec['rationale'],preferred='position_model',
                latest=dict(round=latest['next_round'],input_round=latest['transition'],actual=latest['y'][target],
                            fitted=_predict(model,{'x':latest['x']}),
                            error=_predict(model,{'x':latest['x']})-latest['y'][target],
                            features={f:latest['x'][f] for f in model['features']})),model


def _position_models(history):
    rows=_position_rows(history)
    summaries={};fits={}
    for target in POSITION_SPECS:
        summary,model=_position_model_summary(rows,target)
        summaries[target]=summary;fits[target]=model
    return summaries,fits,rows


def _pooled_position_check(rows):
    panel=[]
    for target,spec in POSITION_SPECS.items():
        for row in rows:
            x=dict(pos_t=row['x'][spec['prior']],rel_spend=row['x'][spec['key']+'_avg'],
                   analytics=row['x']['analytics_avg'])
            for key in ('online','service','experience'):
                x['fe_'+key]=1.0 if spec['key']==key else 0.0
            panel.append(dict(x=x,y=row['y'][target],transition=row['transition']))
    features=['pos_t','rel_spend','analytics','fe_online','fe_experience']
    model=_ridge(panel,features,[r['y'] for r in panel],KAHN_PENALTY)
    predictions=[_predict(model,row) for row in panel]
    fitted_mae=mean(abs(row['y']-p) for row,p in zip(panel,predictions))
    persistence_mae=mean(abs(row['x']['pos_t']-row['y']) for row in panel)
    hide=[]
    for transition in range(len(rows)):
        training=[row for row in panel if row['transition']!=transition]
        trial=_ridge(training,features,[row['y'] for row in training],KAHN_PENALTY)
        for row in [row for row in panel if row['transition']==transition]:
            hide.append(abs(_predict(trial,row)-row['y']))
    intercept,raw=_raw_model(model)
    return dict(transitions=len(panel),features=features,intercept=intercept,
                coefficients=[dict(term=f,raw_coefficient=b) for f,b in zip(features,raw)],
                fitted_mae=fitted_mae,hide_one_mae=mean(hide),persistence_mae=persistence_mae,
                note='Pooled cross-check across the three position equations with position fixed effects. It is a robustness check, not the source of the quadrant equations.')


def _two_stage_model(history,quadrant,components,summaries,fits,rows):
    actual=[];fitted=[];predictions=[]
    for i,row in enumerate(rows):
        predicted={component:_predict(fits[component],{'x':row['x']}) for component in components}
        score=sum(predicted.values())
        target=history[i+1]['quadrants'][quadrant]['score']
        actual.append(target);fitted.append(score)
        predictions.append(dict(round=row['next_round'],input_round=row['transition'],actual=target,fitted=score,error=score-target,
                                positions={component:dict(actual=row['y'][component],fitted=predicted[component],
                                                          error=predicted[component]-row['y'][component])
                                           for component in components}))
    fitted_mae=mean(abs(a-p) for a,p in zip(actual,fitted))
    persistence_mae=mean(abs(history[i]['quadrants'][quadrant]['score']-history[i+1]['quadrants'][quadrant]['score'])
                         for i in range(len(rows)))
    hide=[]
    for i,row in enumerate(rows):
        predicted={}
        for component in components:
            trial=_fit_position_model(rows[:i]+rows[i+1:],component)
            predicted[component]=_predict(trial,{'x':row['x']})
        hide.append(abs(sum(predicted.values())-history[i+1]['quadrants'][quadrant]['score']))
    mean_actual=mean(actual);ss_total=sum((a-mean_actual)**2 for a in actual)
    r_squared=1-sum((a-p)**2 for a,p in zip(actual,fitted))/ss_total if ss_total else None
    latest=predictions[-1]
    coefficients=[]
    for rank,component in enumerate(sorted(components,key=lambda c:latest['positions'][c]['actual'],reverse=True),1):
        coefficients.append(dict(term=POSITION_SPECS[component]['key']+'_pos',
                                 label=POSITION_SPECS[component]['decision_label']+' position',
                                 unit='index',raw_coefficient=1.0,direction='positive',
                                 latest_contribution=latest['positions'][component]['actual'],
                                 top3_folds=len(rows),top3_share=1.0,importance_rank=rank))
    equation=' + '.join(f"1.0000 × {POSITION_SPECS[c]['decision_label']} position" for c in components)
    equation=f"{quadrant.title()} = {equation}"
    label={'EXPERIENCE':'service and shopping-experience positions',
           'FRICTIONLESS':'online and service positions'}[quadrant]
    rationale=(f"Two-stage model: each reported position is fitted to its own prior position and spending relative to the "
               f"same round’s industry average; the {quadrant.lower()} score is then the sum of the {label}. "
               f"This links investment money to reported capability without regressing the score directly on nominal spending.")
    return dict(quadrant=quadrant,features=[],form='two_stage',form_label='Two-stage position model',
                penalty=KAHN_PENALTY,predictions=predictions,fitted_mae=fitted_mae,
                hide_one_mae=mean(hide),persistence_mae=persistence_mae,r_squared=r_squared,
                coefficients=coefficients,top_factors=sorted(coefficients,key=lambda c:c['importance_rank']),
                intercept=0.0,equation=equation,position_components=list(components),
                position_models=[summaries[c] for c in components],rationale=rationale,
                preferred='two_stage',latest=latest,
                documented_note='The score identity is reported, not fitted. The position equations are exploratory responses to relative spending; they are not simulator formulas or causal effects. The source describes analytics as a multiplier; with six transitions the fitted form is additive in relative spending, and a separate shopping-experience interaction was not stable.')


def _kahn_model_summary(rows,quadrant,spec):
    model=_fit_kahn_model(rows,quadrant,spec)
    predictions=[]
    for row in rows:
        fitted=_predict_kahn(model,row)
        actual=row['y'][quadrant]
        predictions.append(dict(round=row['next_round'],actual=actual,fitted=fitted,error=fitted-actual))
    actual=[p['actual'] for p in predictions]
    fitted=[p['fitted'] for p in predictions]
    fitted_mae=mean(abs(a-p) for a,p in zip(actual,fitted))
    persistence_mae=mean(abs(r['prior'][quadrant]-r['y'][quadrant]) for r in rows)
    latest=rows[-1] if rows else None
    hide=[]
    top3_folds={feature:0 for feature in model['features']}
    for i,row in enumerate(rows):
        training=rows[:i]+rows[i+1:]
        trial=_fit_kahn_model(training,quadrant,spec)
        hide.append(abs(_predict_kahn(trial,row)-row['y'][quadrant]))
        contributions=[]
        for j,feature in enumerate(trial['features']):
            z=(latest['x'][feature]-trial['centers'][j])/trial['scales'][j]
            contributions.append((feature,trial['coefficients'][j+1]*z))
        for feature,_ in sorted(contributions,key=lambda item:abs(item[1]),reverse=True)[:min(3,len(contributions))]:
            top3_folds[feature]+=1
    mean_actual=mean(actual)
    ss_total=sum((a-mean_actual)**2 for a in actual)
    r_squared=1-sum((a-p)**2 for a,p in zip(actual,fitted))/ss_total if ss_total else None
    raw_intercept,raw_coefficients=_raw_model(model)
    coefficients=[]
    for i,(feature,beta,raw) in enumerate(zip(model['features'],model['coefficients'][1:],raw_coefficients)):
        latest_z=((latest['x'][feature]-model['centers'][i])/model['scales'][i]
                  if latest else 0.)
        coefficients.append(dict(
            term=feature,label=FEATURES[feature]['label'],unit=FEATURES[feature]['unit'],
            definition=FEATURES[feature]['definition'],raw_coefficient=raw,
            direction='positive' if beta>=0 else 'negative',
            latest_z=latest_z,latest_contribution=beta*latest_z,
            top3_folds=top3_folds[feature],top3_share=top3_folds[feature]/len(rows),
        ))
    ranked=sorted(coefficients,key=lambda c:abs(c['latest_contribution']),reverse=True)
    for rank,coefficient in enumerate(ranked,1):
        coefficient['importance_rank']=rank
    top_factors=ranked[:3]
    terms=[_equation_term(raw,feature)
           for feature,raw in zip(model['features'],raw_coefficients)]
    raw_rhs=f"{raw_intercept:.4f} "+" ".join(terms)
    equation=(f"rating(t+1) = rating(t) + ({raw_rhs})" if spec['form']=='delta'
              else f"rating = {raw_rhs}")
    preferred='persistence' if persistence_mae < mean(hide) else 'input model'
    return dict(quadrant=quadrant,features=list(model['features']),form=spec['form'],
                form_label='Change model' if spec['form']=='delta' else 'Level model',
                penalty=KAHN_PENALTY,predictions=predictions,fitted_mae=fitted_mae,
                hide_one_mae=mean(hide),persistence_mae=persistence_mae,r_squared=r_squared,
                coefficients=coefficients,top_factors=top_factors,
                intercept=raw_intercept,equation=equation,
                rationale=spec['rationale'],preferred=preferred,
                latest=predictions[-1] if predictions else None)


def kahn_analysis(history):
    from frictionless_analysis import frictionless_analysis
    rows=transition_rows(history)
    if len(rows)<5:
        return dict(status='Insufficient decision-to-rating transitions',models=[],transitions=len(rows),input_count=len(INPUT_KEYS))
    summaries,fits,position_rows=_position_models(history)
    models=[_kahn_model_summary(rows,'BRAND',KAHN_SPECS['BRAND']),
            _two_stage_model(history,'EXPERIENCE',['CUSTOMER SERVICE','SHOPPING EXPERIENCE'],summaries,fits,position_rows),
            _kahn_model_summary(rows,'LOW PRICE',KAHN_SPECS['LOW PRICE']),
             _two_stage_model(history,'FRICTIONLESS',['CUSTOMER SERVICE','ONLINE INVEST'],summaries,fits,position_rows)]
    models[-1]=frictionless_analysis(history,models[-1],position_rows)
    latest_features=feature_values(history[-1]['decisions']) if history else {}
    latest_positions=history[-1].get('positions',{}) if history else {}
    latest_features.update({'online_pos':latest_positions.get('ONLINE INVEST'),
                            'service_pos':latest_positions.get('CUSTOMER SERVICE')})
    return dict(status='Two direct lagged fits plus two-stage position models for Experience and Frictionless.',
                transitions=len(rows),input_count=len(INPUT_KEYS),penalty=KAHN_PENALTY,
                input_keys=list(INPUT_KEYS),
                feature_map=[dict(key=k,**v,latest_value=latest_features.get(k)) for k,v in FEATURES.items()],
                position_models=summaries,position_pooled=_pooled_position_check(position_rows),models=models,
                boundary=('Brand and Low Price retain lagged input fits. Experience retains the older additive service/analytics position association, not verified mechanics. Frictionless is audited separately: no service carryover, no standalone analytics effect, an online × analytics interaction, bounded position diagnostics, both timing alignments, and earlier-only conditional validation. Persistence is preferred when it wins those checks. Six periods cannot identify fifteen separate input effects, score timing, analytics strength or rival reactions. All spending fits remain exploratory, not causal responses, simulator formulas or budget optimization rules. Private and national quality collapse to one observed series.'))


def _value_rows(history):
    rows=[]
    for r in history:
        book_equity=r.get('book_equity')
        if not book_equity or not r.get('ebit') or r['ebit']<=0 or not r.get('market_value'):
            continue
        row=dict(r)
        row['log_ebit']=math.log(r['ebit'])
        row['book_debt_weight']=r['debt']/(r['debt']+book_equity) if r['debt'] is not None else None
        row['service_per_store']=r.get('service_per_store')
        rows.append(row)
    return rows


def _value_fit(rows,features,penalty=VALUE_PENALTY):
    targets=[math.log(r['market_value']) for r in rows]
    model=_ridge(rows,features,targets,penalty,key=None)
    return model


def _value_predict(model,row):
    return math.exp(_predict(model,row,key=None))


def _value_metrics(rows,features,penalty=VALUE_PENALTY):
    model=_value_fit(rows,features,penalty)
    predictions=[]
    for r in rows:
        fitted=_value_predict(model,r)
        predictions.append(dict(round=r['round'],actual=r['market_value'],fitted=fitted,
                                error_pct=fitted/r['market_value']-1))
    fitted_mape=mean(abs(p['error_pct']) for p in predictions)
    hide=[]
    for i,r in enumerate(rows):
        trial=_value_fit(rows[:i]+rows[i+1:],features,penalty)
        hide.append(abs(_value_predict(trial,r)/r['market_value']-1))
    forward=[]
    for i,r in enumerate(rows):
        if i<len(rows)-2:
            continue
        trial=_value_fit(rows[:i],features,penalty)
        forward.append(abs(_value_predict(trial,r)/r['market_value']-1))
    baseline=[]
    for i,r in enumerate(rows):
        if i<len(rows)-2:
            continue
        baseline.append(abs(rows[i-1]['market_value']/r['market_value']-1))
    y=[math.log(r['market_value']) for r in rows]
    fitted_log=[math.log(p['fitted']) for p in predictions]
    mean_y=mean(y)
    ss_total=sum((v-mean_y)**2 for v in y)
    r_squared=1-sum((a-p)**2 for a,p in zip(y,fitted_log))/ss_total if ss_total else None
    return dict(model=model,predictions=predictions,fitted_mape=fitted_mape,
                hide_one_mape=mean(hide),forward_mape=mean(forward),baseline_mape=mean(baseline),
                r_squared=r_squared)


def market_value_analysis(history):
    rows=_value_rows(history)
    if len(rows)<6:
        return dict(status='Insufficient complete periods',predictions=[],comparison=[])
    primary=['log_ebit','wacc','book_debt_weight']
    result=_value_metrics(rows,primary)
    model=result['model']
    coefficients=[]
    labels={'log_ebit':'ln(EBIT)','wacc':'Reported WACC (%)','book_debt_weight':'Book debt weight'}
    raw=[beta/scale for beta,scale in zip(model['coefficients'][1:],model['scales'])]
    intercept=model['coefficients'][0]-sum(b*m for b,m in zip(raw,model['centers']))
    for key,beta in zip(model['features'],raw):
        coefficients.append(dict(term=key,label=labels.get(key,key),coefficient=beta))
    equation=(f"ln(Market value) = {intercept:.4f} "
              f"{'+' if coefficients[0]['coefficient']>=0 else '−'} {abs(coefficients[0]['coefficient']):.4f} × ln(EBIT) "
              f"{'+' if coefficients[1]['coefficient']>=0 else '−'} {abs(coefficients[1]['coefficient']):.4f} × WACC "
              f"{'+' if coefficients[2]['coefficient']>=0 else '−'} {abs(coefficients[2]['coefficient']):.4f} × book debt weight")
    comparison=[]
    for name,features in [
        ('Selected finance model',primary),
        ('Finance only: EBIT + WACC',['log_ebit','wacc']),
        ('Finance + strategy deficit',['log_ebit','wacc','strategy_deficit']),
        ('Finance + unit share',['log_ebit','wacc','unit_share']),
        ('Finance + service intensity',['log_ebit','wacc','service_per_store']),
    ]:
        metrics=_value_metrics(rows,features)
        comparison.append(dict(name=name,features=features,fitted_mape=metrics['fitted_mape'],
                               hide_one_mape=metrics['hide_one_mape'],forward_mape=metrics['forward_mape'],
                               r_squared=metrics['r_squared']))
    return dict(status='Exploratory valuation association; not a forecast or causal decision model.',
                features=primary,penalty=VALUE_PENALTY,observations=len(rows),
                predictions=result['predictions'],fitted_mape=result['fitted_mape'],
                hide_one_mape=result['hide_one_mape'],forward_mape=result['forward_mape'],
                baseline_mape=result['baseline_mape'],r_squared=result['r_squared'],
                coefficients=coefficients,intercept=intercept,equation=equation,comparison=comparison,
                search=dict(note=('The comparison is restricted to non-circular features. Market-value denominators such as market debt weight were excluded because they mechanically contain the target. A wider search found service intensity better in raw leave-one-out and earlier-period error, but it is a decision proxy; the finance specification is retained because it is interpretable and uses only earnings, the reported discount rate and book leverage.'),
                            best_alternative='Finance + service intensity'),
                boundary=('Seven company-period observations. Book debt weight, WACC and market value are jointly determined; the coefficients are associations, not causal returns. Hide-one-period validation refits the same specification without one period. The R5–R6 earlier-period test uses observed same-period EBIT, WACC and book leverage, not forecasts. No forecast interval, simulator valuation formula or optimized decision is identified.'))


def build_analysis(history):
    if history[-1]['round']>=8:
        from final_models import final_market_value, final_score_models
        return dict(kahn=final_score_models(history),value=final_market_value(history))
    return dict(kahn=kahn_analysis(history),value=market_value_analysis(history))
