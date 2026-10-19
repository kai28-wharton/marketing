"""Exact finite-grid scenario search, independently verifiable, never a global optimum.

The historical v2 heuristic is intentionally untouched. This engine evaluates
the same current model as the studio, includes cash/capital/inventory channels,
and refuses candidates whose affected economic pathways are unspecified.
"""
import itertools
import math
from review_model import evaluate
from round_review import QUADRANTS

MAX_GRID=20_000

def finite(value,label,lo=0,hi=1e12):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError(f'{label} must be finite and between {lo:g} and {hi:g}.')
    return float(value)


def optimize(payload,data):
    from app import SPEND
    if not isinstance(payload,dict):raise ValueError('Expected an optimization object.')
    if set(payload)-{'decisions','assumptions','economics','budget','max_cash_use','step','objective','score_floors','ranges'}:
        raise ValueError('Unknown optimization field; locks are expressed by omitted factors or equal range bounds.')
    base=evaluate(payload.get('decisions'),data,payload.get('assumptions'),payload.get('economics'))
    budget=finite(payload.get('budget'),'Explicit scenario budget')
    cash_limit=finite(payload.get('max_cash_use'),'Maximum incremental cash use')
    step=finite(payload.get('step'),'Grid step',1,1e8)
    objective=payload.get('objective','profit')
    if objective not in ('profit','positioning','market_value'):raise ValueError('Unknown optimization objective.')
    if objective=='market_value':
        return dict(status='blocked',result=None,checked=0,missing_assumptions=base['unresolved_valuation'],
                    message='Simulator market value uses max(DCF, CLV/private-brand, liquidation), not fixed P/E. Forecast, horizon, credit/WACC and valuation-floor formulas are missing; no valuation optimum can be claimed.')
    floors=dict(base['scores'])
    requested=payload.get('score_floors',{})
    if not isinstance(requested,dict) or set(requested)-set(QUADRANTS):raise ValueError('Unknown Kahn score floor.')
    floors.update({q:finite(v,q+' floor',0,10) for q,v in requested.items()})
    ranges=payload.get('ranges')
    if not isinstance(ranges,dict) or not ranges or set(ranges)-set(SPEND):
        raise ValueError('Supply explicit ranges for one or more of the five spending inputs; all other factors remain locked.')
    grids=[];keys=sorted(ranges);size=1
    for key in keys:
        bounds=ranges[key]
        if not isinstance(bounds,list) or len(bounds)!=2:raise ValueError('Each range must have [minimum, maximum].')
        f=next(f for f in data['factors'] if f['key']==key)
        lo=finite(bounds[0],key+' minimum',f['min'],f['max']);hi=finite(bounds[1],key+' maximum',lo,f['max'])
        steps=(hi-lo)/step
        if abs(steps-round(steps))>1e-8:raise ValueError('Range widths must be exact multiples of the grid step.')
        count=round(steps)+1;size*=count
        if size>MAX_GRID:raise ValueError(f'Grid exceeds {MAX_GRID:,} candidates; narrow the ranges or increase the step.')
        grids.append([lo+j*step for j in range(count)])
    def constraints(r):
        return (not r['unresolved_economics'] and not r['unresolved_model_channels'] and
                r['explicit_spend']<=budget+1e-6 and
                -r['incremental_cash_delta']<=cash_limit+1e-6 and
                all(r['scores'][q]>=floors[q]-1e-9 for q in QUADRANTS) and
                (objective!='market_value' or r['market_value'] is not None))
    def utility(r):
        if objective=='profit':return r['net_income']
        if objective=='market_value':return r['market_value']
        return sum(r['scores'][q]*w for q,w in [('BRAND',.4),('EXPERIENCE',.4),('FRICTIONLESS',.15),('LOW PRICE',.05)])
    best=None;best_value=-math.inf;feasible=0;unresolved=set();missing_channels=set();rejected_missing=0
    # Include unchanged start as a separate incumbent only when it lies in all
    # specified ranges. It need not be a node of their discretization.
    in_ranges=all(ranges[k][0]<=base['decisions'][k]<=ranges[k][1] for k in keys)
    incumbent_feasible=in_ranges and constraints(base)
    if incumbent_feasible:best=base;best_value=utility(base)
    for values in itertools.product(*grids):
        trial=dict(base['decisions'],**dict(zip(keys,values)))
        r=evaluate(trial,data,base['assumptions'],base['economics'])
        if r['unresolved_economics'] or r['unresolved_model_channels']:
            unresolved.update(r['unresolved_economics']);rejected_missing+=1
            missing_channels.update(r['unresolved_model_channels'])
            continue
        if not constraints(r):continue
        feasible+=1;value=utility(r)
        if value>best_value+1e-8:best,best_value=r,value
    # Incomplete nodes prevent any assertion of a best result over the requested
    # domain; do not quietly present the best of only the modeled subset.
    if rejected_missing:
        return dict(status='blocked',result=None,missing_assumptions=sorted(unresolved),
                    unresolved_model_channels=sorted(missing_channels),
                    checked=size,rejected_missing=rejected_missing,
                    message=('Brand depth response requires controlled input-to-position evidence or simulator rules; an old zero Brand coefficient is not a verified no-effect finding. ' if 'brand_depth_response' in missing_channels else '')+
                            'Specify affected economic assumptions and resolve unmodeled channels before comparing this grid. Unknown is not zero.')
    if best is None:
        return dict(status='infeasible',result=None,checked=size,feasible=feasible,
                    message='No candidate satisfies the stated budget, cash-use and Kahn floors.')
    # Recalculate the selected plan and independently check every safety condition.
    verified=evaluate(best['decisions'],data,base['assumptions'],base['economics'])
    if not constraints(verified) or abs(utility(verified)-best_value)>1e-6:
        raise ValueError('Optimizer verification failed; no candidate returned.')
    return dict(status='verified_grid',result=verified,objective=objective,objective_value=best_value,
                checked=size,feasible=feasible,step=step,budget=budget,max_cash_use=cash_limit,score_floors=floors,
                incumbent_feasible=incumbent_feasible,
                locked=[k for k in base['decisions'] if k not in keys or ranges[k][0]==ranges[k][1]],ranges=ranges,
                method='Exhaustive finite-grid search plus in-range starting incumbent; deterministic and independently re-evaluated.',
                guarantee='Best only over the explicitly enumerated grid and eligible start under this one-period scenario. Not a game-value, continuous/global or multiperiod optimum. Does not enforce the documented two-quadrant strategy or resolve the conflicting fair-value thresholds.',
                validation=dict(calculation_checked=True,predictive_accuracy_established=False),
                assumptions=verified['assumptions'],economics=verified['economics'])
