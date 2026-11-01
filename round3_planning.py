"""User-funded Round 3 recommendation; explicit policy choices, not fitted optima.

The workbook remains untouched. Budget arithmetic and cash sensitivities are
checkable; unknown assortment/vendor/store responses are never set to zero to
certify a plan or manufacture a Kahn/market-value optimum.
"""

ROUND3_BUDGET=74_631_166
SPENDING=('online','service','experience','vendor','analytics')


def challenge_product_decisions(data, choices, explanations):
    """Bounded two-sided challenges, not response-fitted optimization."""
    from review_model import evaluate
    steps={'low_markup':2,'high_markup':2,'low_breadth':5,'high_breadth':5,
           'low_depth':5,'high_depth':5,'low_private':5,'high_private':5,
           'private_quality':1,'national_quality':1}
    criteria={
        'markup':'Change only if realized unit demand and contribution beat the fixed-cost gross-profit break-even, after operating and financing costs.',
        'breadth':'Expand only for incremental profitable category demand; reduce only when avoided inventory funding exceeds lost contribution and one-stop access value.',
        'depth':'Add choice only when incremental contribution funds stock and interest; reduce only if availability and target-customer choice are preserved.',
        'private':'Change only after realized private/national purchases, unit margin and retention support the shift. The input mix is not observed sales mix.',
        'quality':'Raise only when willingness to pay and retention cover higher unit costs and funding; lower only if cost savings exceed lost contribution and Brand damage.'}
    rows=[]
    for f in data['factors']:
        k=f['key']
        if k not in steps:continue
        baseline=data['team']['decisions'][k];step=steps[k]
        # Always include the actual submitted value, both directions and recommendation.
        values=sorted({max(f['min'],baseline-step),baseline,min(f['max'],baseline+step),choices[k]})
        group=k.split('_')[-1]
        candidates=[]
        for value in values:
            trial=dict(choices,**{k:value});d=evaluate(trial,data)
            candidates.append(dict(value=value,selected=value==choices[k],
                                   unit_change_break_even=baseline/value-1 if group=='markup' and value>0 else None,
                                   unresolved=sorted(set(d['unresolved_economics']+d['unresolved_model_channels']))))
        rows.append(dict(key=k,label=f['label'],unit=f['unit'],baseline=baseline,recommended=choices[k],
                         candidates=candidates,criterion=criteria[group],reason=explanations[k][1],
                         verdict='Conditional change' if choices[k]!=baseline else 'Provisional hold — optimum not established'))
    return rows


def build_store_packages(data, choices):
    """Compare funded openings and closures without inventing disposal proceeds."""
    from round_review import COMPANY
    base=data['team']['decisions'];budget=ROUND3_BUDGET
    scenarios=[
        ('Hold 236 · recommended',dict(choices),'Keep repair funding and retail access. No evidence currently establishes that a store-count change adds value.'),
        ('Close 5 · conditional',dict(choices,coverage=231),'Same strategic allocation; spending per remaining store rises mechanically, not necessarily service quality. Adopt only if avoided operating cash costs exceed lost contribution, exit costs and access damage.'),
        ('Close 10 · higher access risk',dict(choices,coverage=226),'More concentrated delivery but greater access exposure for Segments 2/6. Neither cash recovery nor operating savings are verified.'),
        ('Open 1 · funded alternative',dict(choices,coverage=237,online=9_250_000),'Divert $1.75M of online repair to one opening. Fits the conservative ceiling, but weakens repair of the observed Frictionless deficit; requires incremental demand and return evidence.'),
        ('Open 5 · funded alternative',dict(choices,coverage=241,online=8_000_000,service=14_000_000,experience=15_000_000,vendor=20_250_000),'Funds $8.75M openings by abandoning online/service/Experience increases and cutting vendor further. Budget-feasible, but conflicts with repair priorities and risks cost/availability capability.')]
    out=[]
    store_revenue=next(c['store'] for c in data['marketing']['companies'] if c['name']==COMPANY)
    for name,plan,why in scenarios:
        change=int(plan['coverage']-base['coverage']);capex=max(0,change)*1_750_000
        spend=sum(plan[k] for k in SPENDING)
        out.append(dict(name=name,decisions=plan,stores=int(plan['coverage']),change=change,spend=spend,
                        opening_capex=capex,capital_inclusive_total=spend+capex,reserve=budget-spend-capex,
                        service_per_store=plan['service']/plan['coverage'],experience_per_store=plan['experience']/plan['coverage'],
                        closure_proceeds=None if change<0 else 0,closure_exit_cost=None if change<0 else 0,
                        observed_average_store_revenue=store_revenue/base['coverage'],
                        revenue_exposure_proxy=abs(change)*store_revenue/base['coverage'],
                        net_cash_feasible=None,why=why))
    return out


def build_round3_planning(data):
    if data['planning_round']!=3:
        raise ValueError('This user-confirmed ceiling applies to Round 3 only.')
    from review_model import evaluate
    base=data['team']['decisions'];now=data['rounds'][str(data['current_round'])]
    rules={r['key']:r for r in data['simulation']['factor_rules']}
    # Round-numbered, analyst-selected test increments, NOT response estimates.
    choices=dict(base,high_depth=15,online=11_000_000,service=15_000_000,
                 experience=16_000_000,vendor=24_000_000,analytics=8_000_000)
    explanations={
        'low_markup':('Hold 50% markup',
            'Low Price already exceeds the reported floor by 1.0. Protect margin while defending 2/6; a broad discount does not target the Brand/Experience core.',
            '50→48 would require 50/48−1 = 4.17% more units just to preserve gross-profit dollars at fixed unit cost, before extra operating/finance costs.',
            'Only cut after a controlled price test demonstrates contribution and cash gains; a high segment population is not evidence of elasticity.'),
        'high_markup':('Hold 54% markup',
            'Preserve cost-plus economics for the branded offer. No segment-by-offering purchase data establish that 3 or 5 needs a higher-cost price cut.',
            '54→52 requires 54/52−1 = 3.85% more units to preserve offering gross-profit dollars at fixed cost.',
            'Observe units and contribution, not revenue alone. Quality/cost changes can also change selling prices even at unchanged markup.'),
        'low_breadth':('Hold 68 categories index',
            'Keep one-stop choice for existing Segment 2 and the breadth needs in 5/6. Current lower-cost breadth position is #2; do not expand already broad inventory indiscriminately.',
            'Change = 0. The exact 68 is the submitted baseline, not a newly estimated optimum.',
            'Rationalize only with category contribution, stockouts and working-capital evidence; no blanket breadth cut to finance Experience.'),
        'high_breadth':('Hold 50 categories index',
            'Current higher-cost breadth position is #1. Preserve that capability while testing depth selectively, rather than adding more categories.',
            'Change = 0; retaining 50 avoids a second simultaneous assortment experiment.',
            'Do not infer profitable categories from the aggregate position index; monitor inventory and category-level contribution.'),
        'low_depth':('Hold 30 depth index',
            'Preserve useful choice in the larger lower-cost business and avoid rebuilding inventory in both tiers at once.',
            'Change = 0; the previous submission already raised 25→30. The current lower-cost depth position is 1.9.',
            'Hold while separately testing higher-cost depth; no measured depth-to-Brand coefficient is supplied.'),
        'high_depth':('Conditional 10→15 controlled Brand/choice test',
            'Segment 3 alone has Brand and Experience as its top two needs. Higher-cost depth position is only 0.9 versus ZEPHARA 1.9, despite our breadth position of 4.0. Test choice within existing categories, not indiscriminate expansion.',
            '+5 index points is the existing one-factor probe size and an analyst-selected test step. It is a 50% increase in this input, NOT 50% more stock or a predicted score gain.',
            'Release 15 only after incremental inventory, financing and customer contribution are measured and funded. If unavailable, keep 10 in the executable fallback; full Brand prediction remains unknown.'),
        'low_private':('Hold 44% private-brand mix setting',
            'Avoid changing mix and depth simultaneously. Preserve the existing value assortment for 2/6 while assessing the Brand/Experience core.',
            'Change = 0. 44 is a mix setting, not an observed sales share or quality score.',
            'Require realized mix, contribution and repeat-purchase evidence before shifting private/national exposure.'),
        'high_private':('Hold 70% private-brand mix setting',
            'Retain the differentiated private-brand proposition and CLV/brand valuation pathway without assuming that more private mix always creates value.',
            'Change = 0; no verified mix-response or valuation coefficient supports a move to 75/80.',
            'Evaluate the depth test first; monitor realized mix and national-brand demand rather than treating 70% as measured customer purchases.'),
        'private_quality':('Hold quality 7',
            'Quality was already raised 6→7. Preserve Brand credibility for 3 without another unpriced unit-cost escalation to 8.',
            'Change = 0; the higher private-brand position is 2.8 versus ZEPHARA 3.1, not proof that one quality point closes the gap.',
            'Test willingness to pay, returns and costs before 8. Keep vendor/cost discipline; quality changes are not cost-free Brand points.'),
        'national_quality':('Hold quality 7',
            'Maintain a credible branded assortment. A second quality escalation has no identified incremental demand or margin benefit.',
            'Change = 0; unchanged national/private quality isolates the choice test and avoids assumed cost coefficients.',
            'Require brand-type purchase and quality-perception evidence before an increase or a damaging cut.'),
        'coverage':('Hold 236 stores; evaluate openings and closures explicitly',
            'The last submission added 36 stores (200→236). Improve execution in the existing network before adding capital; retain access valued by 2/6. No store-level contribution or verified closure recovery is supplied.',
            '236 adds zero new-store capital. Five openings cost 5×$1.75M = $8.75M before inventory. Closing stores does not recover the original opening cost automatically.',
            'Open only with demand, incremental return and financing evidence. Close only after lost contribution, cash recovery and write-off are quantified; no disposal proceeds fund this recommendation.'),
        'online':('Raise $8M→$11M for convenience repair',
            'Frictionless 3.1 is 1.9 below its 5.0 CSV floor. Protect the whole offer for all segments, especially conditional expansion in 5; almost half of current company sales are online.',
            '+$3M is a bounded 37.5% test, not a computed amount that guarantees parity. At the provisional 40/60 expense/capital split, +$1.2M expense and +$1.8M capital.',
            'Measure access, conversion and Frictionless; retain analytics support. Require financing for the full dollars, not just the expensed share.'),
        'service':('Restore $14M→$15M',
            'Service position deteriorated 3.2→2.7 while the 36-store expansion diluted delivery capacity. Restore the previously submitted $15M level to support Experience and convenience, rather than fund ambience through service cuts.',
            '+$1M (+7.14%). $15M/236 = about $63,559 per store versus prior $15M/200 = $75,000; this is not a full return to prior intensity.',
            'Verify queues, complaints and retention. Allocation is not accounting expense: latest expense is $16.806M on a $14M input; the marginal conversion is unverified.'),
        'experience':('Raise $15M→$16M',
            'Experience is the core differentiator for 3 and the scale case in 5; 6 also values it. Improve existing stores rather than dilute spending through new openings.',
            '+$1M (+6.67%), about $67,797 per store versus $63,559. Provisional 80/20 expense/capital split gives +$0.8M expense and +$0.2M capital.',
            'A prior spending increase coincided with a weaker Kahn score, so spend is not success. Goal remains rank #1, not a predicted result of this increment.'),
        'vendor':('Stage $26.422M→$24M; protect retained capability',
            'Release $2.422M to repair convenience and service while preserving a large vendor allocation. The slides describe persistent vendor benefits, but their retention rate is unknown. This is a cautious funding trade-off, not evidence of saturation at a 100.2 operating score.',
            'Cut = $2.422M (9.17%). A 0.653% increase on current COGS would consume the entire nominal spending saving; there is little room for loss of cost discipline.',
            'Monitor landed costs, stockouts, inventory and Low Price floor. If vendor capability deteriorates, restore funding and reduce discretionary tests; do not silently accept a weaker value safeguard.'),
        'analytics':('Hold $8M multiplier investment',
            'Preserve support for the larger online and Experience investments. Analytics amplifies these levers; it is not standalone demand.',
            'Change = 0; reported score 100.6 is not a measured zero marginal return, nor a reason to spend more automatically.',
            'Use segment retention/conversion and test effectiveness to justify future changes. Do not cut the multiplier while asking its paired investments to work harder.'),
    }
    recommendations=[]
    for f in data['factors']:
        k=f['key'];action,why,arithmetic,gate=explanations[k]
        recommendations.append(dict(key=k,label=f['label'],unit=f['unit'],cell=data['team']['cells'][k],
                                    current=base[k],proposed=choices[k],change=choices[k]-base[k],
                                    action=action,why=why,arithmetic=arithmetic,gate=gate,
                                    pathway=rules[k]['pathway'],citation=rules[k]['citation'],
                                    evidence_status='Source baseline hold' if choices[k]==base[k] else 'Analyst-selected conditional test'))
    spend=sum(choices[k] for k in SPENDING);reference=sum(base[k] for k in SPENDING)
    diagnostics=evaluate(choices,data)
    # Do not expose partial economic totals as a complete profit/cash forecast.
    goals=[]
    for objective in data['strategy']['objectives']:
        q=objective['quadrant'];score=None if q=='BRAND' and diagnostics['score_diagnostics']['BRAND']['status']=='partial' else diagnostics['scores'][q]
        goals.append(dict(objective,diagnostic=score,diagnostic_status='Unknown full Brand response' if score is None else 'Uncalibrated local prior only',
                          goal_verified=False))
    ratios={r['key']:r['ratio'] for r in data['accounting']}
    online_delta=choices['online']-base['online'];exp_delta=choices['experience']-base['experience']
    nominal_expense=online_delta*ratios['online']+exp_delta*ratios['experience']+sum(choices[k]-base[k] for k in ('service','vendor','analytics'))
    service_ratio_expense=nominal_expense+(choices['service']-base['service'])*(ratios['service']-1)
    capital=online_delta*(1-ratios['online'])+exp_delta*(1-ratios['experience'])
    alternatives=[]
    for name,settings,tradeoff in [
        ('Cash protection',dict(online=10_000_000,service=14_000_000,experience=15_000_000,vendor=26_000_000,analytics=8_000_000,high_depth=10),
         'Spend $73M; preserve more vendor capability and reserve, but no service restoration or higher-cost choice test. Lower repair ambition, not proof of greater value.'),
        ('Balanced repair · recommended',choices,
         'Spend $74M; add online/service/Experience, retain analytics, stage a 9.17% vendor reduction and one gated depth test. Best policy balance among these proposals, not a mathematical simulator optimum.'),
        ('Aggressive convenience',dict(online=14_000_000,service=15_000_000,experience=16_000_000,vendor=21_000_000,analytics=8_000_000,high_depth=15),
         'Same $74M spend, but cuts vendor 20.52% and adds more capital. Greater convenience exposure with more cost/retention risk; not proven to attain parity.')]:
        plan=dict(base,**settings);r=evaluate(plan,data);s=sum(plan[k] for k in SPENDING)
        alternatives.append(dict(name=name,spend=s,reserve=ROUND3_BUDGET-s,
                                 online=plan['online'],service=plan['service'],experience=plan['experience'],vendor=plan['vendor'],analytics=plan['analytics'],
                                 capital_delta=(plan['online']-base['online'])*(1-ratios['online'])+(plan['experience']-base['experience'])*(1-ratios['experience']),
                                 experience_prior=r['scores']['EXPERIENCE'],frictionless_prior=r['scores']['FRICTIONLESS'],tradeoff=tradeoff))
    store_options=[]
    for n in (-10,-5,0,5,10):
        count=int(base['coverage']+n);capex=max(0,n)*1_750_000
        store_options.append(dict(stores=count,change=n,opening_capex=capex,capex_cash_share=capex/now['balance']['Cash'],
                                  experience_per_store=choices['experience']/count,service_per_store=choices['service']/count,
                                  closure_proceeds=None if n<0 else 0,closure_writeoff=None if n<0 else 0,
                                  capital_inclusive_total=spend+capex,
                                  conservative_headroom=ROUND3_BUDGET-spend-capex,
                                  verdict='Recommended hold' if n==0 else 'Unknown disposal/write-off and lost access; do not book a saving' if n<0 else 'Requires separate capital financing; exceeds conservative all-in ceiling'))
    fallback=dict(choices,high_depth=base['high_depth'])
    return dict(period=3,budget=ROUND3_BUDGET,budget_source='User confirmed $74,631,166 for Round 3 in this conversation; not inferred from revenue or prior spend.',
                status='Conditional recommendation ready for team review; Kahn attainment, funding and response gates are NOT certified. Nothing is submitted.',
                method='Constraint-led analyst allocation with exact budget arithmetic and explicit alternative packages. No fitted all-16 response model exists, so no global, market-value or Kahn-feasible optimum is claimed.',
                decisions=choices,fallback=fallback,recommendations=recommendations,spend=spend,reserve=ROUND3_BUDGET-spend,
                baseline_spend=reference,spend_change=spend-reference,budget_increase=ROUND3_BUDGET-reference,
                revenue_arm=.14*now['income']['Net Revenue'],budget_vs_revenue_arm=ROUND3_BUDGET-.14*now['income']['Net Revenue'],
                 goals=goals,alternatives=alternatives,stores=store_options,
                 product_challenges=challenge_product_decisions(data,choices,explanations),
                 store_packages=build_store_packages(data,choices),
                 hold_summary=dict(reviewed=10,held=sum(choices[k]==base[k] for k in ('low_markup','high_markup','low_breadth','high_breadth','low_depth','high_depth','low_private','high_private','private_quality','national_quality')),
                                   boundary='Unchanged inputs are provisional risk-controlled choices, not proven optimal settings. Lack of response data does not favor the baseline mathematically; it prevents ranking the alternatives reliably.'),
                finance=dict(cash=now['balance']['Cash'],net_income=now['income']['Net Income'],interest=now['income']['Interest Expense'],
                             interest_cover=now['ratios']['interest_cover'],working_capital=now['ratios']['working_capital'],
                             nominal_expense_delta=nominal_expense,service_ratio_expense_delta=service_ratio_expense,
                             capital_delta=capital,vendor_cut=base['vendor']-choices['vendor'],
                             vendor_saving_cogs_threshold=(base['vendor']-choices['vendor'])/now['income']['Cost of Goods Sold'],
                             one_percent_cogs=.01*now['income']['Cost of Goods Sold'],
                             ten_days_inventory=now['income']['Cost of Goods Sold']/365*10),
                unresolved=sorted(set(diagnostics['unresolved_economics']+diagnostics['unresolved_model_channels'])),
                segment_case=[
                    dict(segment='3 · fit anchor',action='Protect quality/mix; test higher-cost depth and improve delivery of the Brand + Experience proposition. Its $132.69M aggregate CLV is smaller, not a reason to abandon the best two-need fit.'),
                    dict(segment='5 · conditional scale',action='Repair convenience plus Experience. No broad acquisition push until Frictionless parity and segment contribution are evidenced.'),
                    dict(segment='6 · defend / challenger',action='Retain retail access and fair value; test existing-store Experience selectively. Do not finance an unproven price war against BESTCO.'),
                    dict(segment='2 · first equity defense',action='Hold useful breadth and store access; vendor cost/availability discipline protects the largest existing CLV pool.'),
                    dict(segment='4 · selective reserve',action='Use existing store/online capability for bounded mixed-channel tests, not a third equal acquisition budget.')],
                gates=[
                    'Confirm the simulator budget scope and financing treatment. Five strategic boxes total $74M within the user ceiling; store capex, inventory, quality and financing are separate business-cash checks. The $631,166 allocation reserve is not guaranteed ending cash.',
                    'If the high-depth test cannot be funded and measured, keep 10 instead of 15. The fallback is a smaller experiment, NOT a certified path to competitive Brand or the other Kahn goals.',
                    'Verify Frictionless against the next reported CSV floor (current 5.0) and Low Price against its floor (current 3.6). No slide percentage replaces the export values.',
                    'Verify Experience rank #1 using actual future retailer scores, and narrow Brand’s current 0.8 leader gap. The local priors do not establish Experience leadership or Frictionless parity for any displayed package.',
                    'If vendor cost/availability deteriorates, restore vendor funding and retest the allocation rather than masking that cost with unknown coefficients. Measure incremental margin, inventory, retention and satisfaction.',
                    'Use only authorized simulator feedback. Do not repeatedly submit or assume unlimited undo. No workbook, external simulator or live submission is edited here.'],
                sources=[data['team']['source']+' · Column B; submitted baseline',
                         'materials/round2/finance/ · income, balance sheet and scorecard',
                         'materials/round2/marketing/ · Kahn, preferences, CLV and product positions',
                         'materials/PivotOrPerish_Intro wemba.pdf · pp7–17, 24',
                         'materials/MarketValue_Slides.pdf · pp4, 6–14',
                          'User-confirmed Round 3 budget and authorization to recommend all 16 factors, including store decisions'])
