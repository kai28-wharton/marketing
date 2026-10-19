"""PDF-consistent local score priors; not fitted simulator response functions.

Numerical weights are retained v2 priors only where compatible with the slides.
No direct analytics term, vendor→Brand term, or stores→preference term survives.
Missing assortment, mix and access responses remain explicitly unquantified.
"""
import math
from prediction import configuration, clamp

WEIGHTS={
    'BRAND':{'quality':.32},
    'EXPERIENCE':{'experience':3.,'service':1.6,'analytics_experience':.4},
    'FRICTIONLESS':{'online':3.,'service':.65,'online_analytics':.8},
    'LOW PRICE':{'vendor':.55,'markup':-.07},
}
FACTOR_FEATURES={
    'low_markup':['markup'],'high_markup':['markup'],
    'low_breadth':[],'high_breadth':[],'low_depth':[],'high_depth':[],
    'low_private':[],'high_private':[],
    'private_quality':['quality'],'national_quality':['quality'],
    'coverage':[],'online':['online','online_analytics'],'service':['service'],
    'experience':['experience','analytics_experience'],'vendor':['vendor'],
    'analytics':['online_analytics','analytics_experience'],
}


def scores(plan,reference,current,data,strength):
    config=configuration(data,reference);share=config['online_share'];half=config['half_saturation']
    def levels(p):
        sat=lambda k:p[k]/(p[k]+half[k]) if p[k]>0 else 0.
        a=sat('analytics');e=sat('experience');o=sat('online')
        return dict(experience=2*e*(1-share),service=2*sat('service'),online=2*o*share,
                    vendor=2*sat('vendor'),analytics_experience=2*a*e*(1-share),online_analytics=2*a*o*share,
                    quality=(p['private_quality']+p['national_quality'])/2,
                    markup=.76*p['low_markup']+.24*p['high_markup'])
    start=levels(reference);end=levels(plan);result={}
    for q,weights in WEIGHTS.items():
        raw=strength*sum((end[k]-start[k])*v for k,v in weights.items())
        anchor=clamp(current[q],.001,9.999);slope=max(.05,anchor*(1-anchor/10))
        log_odds=math.log(anchor/(10-anchor))+raw/slope
        result[q]=10/(1+math.exp(-clamp(log_odds,-60,60))) if raw else current[q]
    return result
