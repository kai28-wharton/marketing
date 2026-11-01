"""Manually reviewed, page-cited simulation rules from the two supplied PDFs.

Only curated rules are exported, never raw slides or demo access information.
Qualitative mechanisms are not numeric response coefficients.
"""
import hashlib
from pathlib import Path
from round_review import COMPANY, QUADRANTS

INTRO='materials/PivotOrPerish_Intro wemba.pdf'
VALUE='materials/MarketValue_Slides.pdf'
FACTOR_RULES={
    'low_markup': ('LOW PRICE','Immediate margin/demand trade-off; no persistence.','MV 12; Intro 14'),
    'high_markup': ('LOW PRICE','Immediate margin/demand trade-off; no persistence.','MV 12; Intro 14'),
    'low_breadth': ('Assortment / loyalty','Retained; supports appeal/basket size and ties up working capital, with financing costs.','MV 12'),
    'high_breadth': ('Assortment / loyalty','Retained; monitor capital efficiency rather than maximizing categories.','MV 12'),
    'low_depth': ('Assortment / loyalty','Retained within-category choice; stock funding and interest matter.','MV 12'),
    'high_depth': ('Assortment / loyalty','Retained within-category choice; the observed Brand identity is still not an official formula.','MV 12'),
    'low_private': ('BRAND / valuation','Private-brand MIX supports differentiation, loyalty, margins and the CLV/brand valuation route; coefficients/exposure rules absent.','MV 6, 12'),
    'high_private': ('BRAND / valuation','Mix meaning is now supported; 70% is a decision setting, not measured sales share.','MV 6, 12'),
    'private_quality': ('BRAND','Higher quality supports willingness to pay, raises COGS and needs vendor/cost discipline.','Intro 14; MV 12'),
    'national_quality': ('BRAND','High-quality national brands support Brand; unit-cost and willingness-to-pay rates remain unknown.','Intro 14; MV 12'),
    'coverage': ('Access / capital / debt','Stores change access, not preferences/retention. Identical stores; $1.75M per new store; financing split and marginal access response unspecified.','Intro 13; MV 10–11, 14'),
    'online': ('FRICTIONLESS','Partly capitalized; amplified by analytics; debt-funded growth needs proportional cash-flow gains.','Intro 14; MV 12–13'),
    'service': ('FRICTIONLESS / EXPERIENCE','Immediate, fully expensed, little persistence; tactical satisfaction, not a standalone durable advantage.','Intro 14; MV 13'),
    'experience': ('EXPERIENCE','Medium-term persistence, mostly expensed, amplified by analytics; diminishing returns.','Intro 14; MV 13'),
    'vendor': ('LOW PRICE / structural costs','Fully expensed but highly retained: compounds COGS improvements over time; can reduce financing risk.','Intro 14; MV 13'),
    'analytics': ('Multiplier, not standalone demand','Amplifies online and experience; expensed, no separate capital asset or independent demand term.','Intro 14; MV 13'),
}


def build_review(data,root):
    root=Path(root)
    docs=[dict(file=f,pages=n,sha256=hashlib.sha256((root/f).read_bytes()).hexdigest()) for f,n in [(INTRO,26),(VALUE,14)]]
    fairness=[]
    current=data.get('current_round',1);previous=data.get('previous_round',0)
    for rnd in (previous,current):
        for q in QUADRANTS:
            rows=[r for r in data['kahn'] if r['round']==rnd and r['quadrant']==q]
            actual=[r for r in rows if r['company']!='FAIR VALUE']
            leader=max(actual,key=lambda r:r['value']);own=next(r['value'] for r in actual if r['company']==COMPANY)
            exported=next(r['value'] for r in rows if r['company']=='FAIR VALUE');floor=.75*leader['value']
            fairness.append(dict(round=rnd,quadrant=q,own=own,leader=leader['company'],leader_value=leader['value'],
                                 leader_ratio=own/leader['value'],rank=1+sum(r['value']>own for r in actual),
                                 documented_floor=floor,exported_floor=exported,export_minus_documented=exported-floor,
                                 active_floor=exported,active_gap=own-exported,meets_active=own>=exported-1e-9,
                                 active_source=f'materials/round{current}/marketing/kahn-round{current}.csv FAIR VALUE column',exported_leader_ratio=exported/leader['value'],
                                 documented_gap=own-floor,exported_gap=own-exported,
                                 meets_documented=own>=floor-1e-9,meets_exported=own>=exported-1e-9,
                                 mismatch=abs(exported-floor)>.1))
    ratios=[]
    for rnd in (str(previous),str(current)):
        s=data['rounds'][rnd];b=s['balance'];i=s['income']
        if not i or not b:continue
        invested=b['Short Term Loans']+b['Long Term Debt']+b['Shareholder’s Equity']-b['Cash']
        roic=s['ratios']['ebit']/invested;wacc=s['scorecard']['Weighted Average Cost of Capital (WACC)']/100
        ratios.append(dict(round=int(rnd),ebit=s['ratios']['ebit'],invested_capital_proxy=invested,
                           pretax_roic_proxy=roic,wacc=wacc,spread=roic-wacc,
                           current_ratio=s['ratios']['current_ratio'],interest_cover=s['ratios']['interest_cover'],
                           debt_equity=s['ratios']['debt_equity']))
    latest_floors=[r for r in fairness if r['round']==current]
    by_quadrant={r['quadrant']:r for r in latest_floors}
    priority='Using current CSV fair value: '+ '; '.join(f"{r['quadrant']} {r['own']:g} vs floor {r['active_floor']:g} (gap {r['active_gap']:+.2f})" for r in latest_floors)+'. New team intent: lead Experience, become very competitive in Brand, and hold Low Price and Frictionless at CSV fair value. Meeting a fair-value floor is not leadership; refresh benchmarks from future resolved exports.'
    return dict(version='csv-fair-value-2',documents=docs,fair_value=fairness,capital_efficiency=ratios,
                fair_value_basis=f'Use the reported FAIR VALUE for each quadrant and round from kahn-round{current}.csv. Approximately two-thirds of the displayed leader is descriptive, not a replacement formula. The slide 75% rule is source-audit context only.',
                goal='Increase simulated equity market value through targeted customer value, two credible differentiating quadrants and fair value in the other two—not Brand, profit or a weighted score alone.',
                definition_updates=['FAIR VALUE is a moving benchmark, not an eighth retailer. Use the CSV FAIR VALUE values as the working floors; Intro p15’s conflicting 75% rule is source-audit context only.',
                                    'MV p12 resolves Private Brand as mix, superseding the duplicated Markdown quality definition; realized brand-type sales exposures and numeric effects remain unavailable.',
                                    'MV p14 specifies no inventory holding costs and $1.75M per store. Inventory funding/interest and reinvestment still matter.',
                                    'Intro p14 provides direct quadrant pathways. MV p13 says analytics has no standalone demand term; vendor benefits persist and compound.'],
                valuation=dict(method='max(DCF equity value, CLV/private-brand-adjusted value, liquidation value)',
                               status='Mechanism documented; exact simulator forecast, floors and adjustments unavailable. Constant P/E is not the valuation rule.',
                               formula='FCF_t = operating cash generation less reinvestment; PV = Σ FCF_t/(1+WACC)^t + terminal PV; apply the simulator equity bridge, then compare the three methods.',
                               missing=['Revenue/margin/SG&A/reinvestment forecast rules','Strategy-to-T mapping (6–12 years stated)',
                                        'Terminal cash flow, growth and equity-bridge conventions','CLV/private-brand valuation coefficients',
                                        'Liquidation recovery rates','AAA rate, credit-ratio breakpoints, debt-rate schedule and financing weights',
                                        'Store debt/cash financing split and automatic borrowing mechanics'],
                               horizon_conflict='MV pp3/14 say stronger/stable strategy earns shorter forecast T, while p8 describes a one-dimensional weak strategy as low T. Do not equate longer T with greater durability or invent a monotonic mapping.',
                               sources=['MV 2–6, 8, 14']),
                budget=dict(revenue_arm=.14*(data.get('marketing',{}).get('company_revenue') or data['rounds'][str(current)]['income']['Net Revenue']),
                             exact_next_budget=None,previous_budget={2:71_422_000,3:74_631_166}.get(current),inflation_allowance=None,
                            submitted_spend=sum(data['team']['decisions'][k] for k in ('online','service','experience','vendor','analytics')),
                            rule='max(14% of previous revenue, previous budget with inflation allowance)',
                             boundary='The revenue arm is computable. The next-period ceiling remains unconfirmed; the inflation allowance is missing. Submitted spend alone is not proof of budget approval. Demo slide screenshots are not this team’s budget.',source='Intro 16'),
                factor_rules=[dict(key=k,pathway=v[0],rule=v[1],citation=v[2]) for k,v in FACTOR_RULES.items()],
                segments=[dict(id='SEGMENT '+str(k),positioning=p,competitors=c) for k,p,c in [
                    (1,'Frictionless / Low Price; online',['CADABRA']),
                    (2,'Low Price / Frictionless; in-store',['AIM','PRICEMART']),
                    (3,'Brand / Experience',['ZEPHARA']),
                    (4,'Mixed needs; in-store',['AIM','ZEPHARA','KTBENNEY']),
                    (5,'Frictionless / Experience',['ZEPHARA']),
                    (6,'Low Price / Experience; in-store',['BESTCO'])]],
                revised_brand='Depth remains the leading observed score-linked symptom, but the PDFs prioritize high-quality brand/mix, retained assortment, targeted customers and two-quadrant coherence. Depth alone is not an adequate repair strategy or a verified causal formula.',
                strategy='Team-selected strategy: lead Experience (rank #1 among actual retailers), become very competitive in Brand, and maintain Low Price and Frictionless at reported CSV fair value. Segment 3 is the primary target; Segment 5 is a conditional secondary focus gated on Frictionless parity; Segment 4 is a selective reserve; defend existing Segments 2 and 6. This is team policy, not an inferred optimum.',
                strategy_options=[
                    dict(pair='Brand + Experience',segments='3; selective 4',case='Builds on historical Brand leadership and current strong Experience. Requires Brand recovery and Frictionless parity; not just more quality spending.'),
                    dict(pair='Low Price + Experience',segments='6; selective 4',case=f"Current scores are {by_quadrant['LOW PRICE']['leader_ratio']:.0%}/{by_quadrant['EXPERIENCE']['leader_ratio']:.0%} of their leaders. Needs vendor-led efficiency and differentiated value without destructive markup cuts; monitor CSV parity safeguards."),
                    dict(pair='Frictionless + Experience',segments='5',case=f"Matches the slide profile, but Frictionless is {by_quadrant['FRICTIONLESS']['leader_ratio']:.0%} of the current leader. Requires online/analytics capability; Brand parity cannot be abandoned.")],
                priority=priority,
                caveats=['CSV FAIR VALUE is the active benchmark. Ratios to displayed leaders vary by export and quadrant; do not recalculate every floor as exactly 67% or two-thirds. The conflicting 75%-of-leader slide rule is retained only as an audit note.',
                         'Slides describe mechanisms and qualitative persistence, not calibrated elasticities, retention rates or next-round coefficients. The local model is still not a replica.',
                         'ROIC uses EBIT / (debt + book equity − cash) at period end, a pre-tax proxy—not the simulator’s verified capital definition or store-level profitability. Comparing it to WACC is a teaching diagnostic, not conclusive economic profit.',
                         'MV p11 cautions against idle accumulating cash; this team’s cash fell and liquidity is weak. Fund positive-return investments rather than either hoarding or spending indiscriminately.',
                         'The one Round 1 undo in Intro p24 is a limited learning opportunity, not evidence of unlimited resettable experiments. Design tests before using it; no live submission is authorized.'])


def report_markdown(data):
    x=data['simulation'];lines=['# PDF-grounded simulation review','',x['goal'],'',
        'Sources: Intro = `materials/PivotOrPerish_Intro wemba.pdf`; MV = `materials/MarketValue_Slides.pdf`. Page numbers are PDF pages. Demo data/access information is not exported.','',
        '## Corrections to the earlier analysis','']+['- '+s for s in x['definition_updates']]
    lines+=['','## Brand hypothesis and strategy','',x['revised_brand'],x['strategy'],x['priority'],'',
            '|Candidate two-quadrant strategy|Slide-aligned segments|What must be tested|','|---|---|---|']
    lines += [f"|{r['pair']}|{r['segments']}|{r['case']}|" for r in x['strategy_options']]
    lines+=['','The winning valuation route is unobserved. Market value rose despite WACC rising 7.8% → 7.9%; the observed increase cannot be attributed to a lower discount rate. Earnings/CLV improvements may offset strategy deterioration, but the contribution of each route is not supplied.','',
            '## Fair value: CSV benchmarks govern the analysis','',x['fair_value_basis'],'',
            '|Round|Quadrant|Getchell’s|Leader|CSV fair value|Active gap|CSV floor / leader|',
            '|---|---|---:|---|---:|---:|---:|']
    for r in x['fair_value']:
        lines.append(f"|{r['round']}|{r['quadrant']}|{r['own']:.2f}|{r['leader']} {r['leader_value']:.2f}|{r['active_floor']:.2f}|{r['active_gap']:+.2f}|{100*r['exported_leader_ratio']:.2f}%|")
    lines+=['','## All sixteen pathways','', '|Input|Documented pathway / mechanism|Source|','|---|---|---|']
    for r in x['factor_rules']:lines.append(f"|{r['key']}|{r['pathway']}: {r['rule']}|{r['citation']}|")
    v=x['valuation'];lines+=['','## Valuation model correction and forecast horizon','',v['method'],v['formula'],v['status'],v['horizon_conflict'],'',
                            'Missing inputs required for numerical reproduction:']+['- '+s for s in v['missing']]
    lines+=['','The active model no longer presents fixed-P/E sensitivity as simulated market value. Changed-plan valuation and the market-value optimizer are blocked rather than inventing DCF/floor parameters. The frozen v2 engine remains an error audit only.','',
            '## ROIC, WACC and funding','', '|Round|Pre-tax ROIC proxy|Reported WACC|Spread (pp)|','|---|---:|---:|---:|']
    for r in x['capital_efficiency']:lines.append(f"|{r['round']}|{100*r['pretax_roic_proxy']:.2f}%|{100*r['wacc']:.2f}%|{100*r['spread']:+.2f}|")
    b=x['budget'];lines+=['',f"Budget rule (Intro p16): {b['rule']}. R1 revenue arm for the next budget is ${b['revenue_arm']:,.2f}. Exact next budget is unavailable; {b['boundary']}",'',
                          '## Segmentation (Intro pp7–10)','']
    lines += ['- '+r['id']+': '+r['positioning']+'; competitors '+', '.join(r['competitors']) for r in x['segments']]
    lines+=['','## Remaining boundaries and conflicts','']+['- '+s for s in x['caveats']]
    return '\n'.join(lines)+'\n'
