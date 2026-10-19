"""Team-directed STP and next-submission recommendations, not a fitted optimum.

Keep reported evidence, team policy, and analyst-selected test sizes distinct.
Nothing in this module changes a workbook, model coefficient, or live decision.
"""

SPENDING=('online','service','experience','vendor','analytics')
CONFIRMED_BUDGET=71_422_000  # User-confirmed Round 1 allocation ceiling, not inferred from the slides.
ROLES={
    'SEGMENT 1':('Not an acquisition priority','Online/price-led; large Frictionless gap makes a new acquisition push costly. Continue serving existing customers.'),
    'SEGMENT 2':('Defend existing business','Largest current revenue pool; breadth/access matter. Low Price fits, but this is not primarily an Experience segment.'),
    'SEGMENT 3':('Maintain credible Brand parity','Experience fits, but explicit Brand intensity is highest. Do not fund a return to Brand leadership or abandon these customers.'),
    'SEGMENT 4':('Selective secondary target','Mixed needs; strongest current revenue growth, but retail AND online convenience matter. Not a pure price/experience segment.'),
    'SEGMENT 5':('Protect Experience-led retention','Large existing revenue pool and highest raw shopping-experience intensity; Frictionless deficit remains a retention risk, not observed churn.'),
    'SEGMENT 6':('Primary acquisition candidate','Slide 8 explicitly pairs Low Price with Experience and in-store preference. Raw depth intensity is low; avoid rebuilding depth everywhere.'),
}


def build_strategy(data):
    current=data['team']['decisions'];rules={r['key']:r for r in data['simulation']['factor_rules']}
    profiles={r['id']:r for r in data['simulation']['segments']}
    segments=[]
    for s in data['marketing']['segments']:
        role,reason=ROLES[s['id']]
        segments.append(dict(id=s['id'],role=role,reason=reason,
                             positioning=profiles[s['id']]['positioning'],competitors=profiles[s['id']]['competitors'],
                             revenue=s['revenue'],revenue_share=s['revenue_share'],revenue_growth=s['growth'],
                             market_consumers=s['size'],market_growth=s['size_growth'],clv=s['clv'],
                             raw_preferences=s['preferences'],preference_sum=sum(s['preferences'].values())))
    policy=dict(primary='EXPERIENCE',secondary='LOW PRICE',primary_segment='SEGMENT 6',secondary_segment='SEGMENT 4',
                experience_min=data['rounds']['1']['scores']['EXPERIENCE'],
                low_price_min=data['rounds']['1']['scores']['LOW PRICE'],
                brand_reference_floor=next(r['active_floor'] for r in data['simulation']['fair_value'] if r['round']==1 and r['quadrant']=='BRAND'),
                fair_value_basis='CSV FAIR VALUE column; update with each resolved round',
                experience_peer='ZEPHARA',
                experience_peer_reference=next(r['value'] for r in data['kahn'] if r['round']==1 and r['company']=='ZEPHARA' and r['quadrant']=='EXPERIENCE'),
                frictionless_min=data['rounds']['1']['scores']['FRICTIONLESS'],frictionless_parity_required_round2=False,
                meaning='Experience stays our highest-priority and strongest-scoring quadrant; this does not mean #1 among retailers.',
                positioning='An enjoyable, helpful in-store shop with credible everyday value, enabled by efficient buying—not premium Brand leadership or indiscriminate discounting.')
    # Protect service/analytics/online; prioritize Experience, then allocate remaining dollars to vendor.
    # These are analyst-selected settings for testing, not estimated response coefficients or an optimum.
    reference=sum(current[k] for k in SPENDING)
    changes={'experience':1_000_000,'vendor':CONFIRMED_BUDGET-reference-1_000_000}
    rationales={
        'low_markup':('Hold; test price separately','Keep the existing cost-plus spread while validating demand. A separate 50% → 48% test needs 4.17% more units merely to preserve offering gross-profit dollars at fixed unit cost; extra opex, inventory and finance are excluded.','Units, gross-profit dollars, Low Price and cash; do not adopt from revenue growth alone.'),
        'high_markup':('Hold','The effective markup already fell from 66% to 52%; higher-cost revenue grew. No segment × offering data justify another broad cut.','Offering contribution and units; segment membership is not a cost-tier label.'),
        'low_breadth':('Hold; rationalize only with category evidence','Segment 6 values breadth more than depth (raw 0.23 vs 0.03). Preserve useful one-stop choice; do not expand the already broad offer automatically.','Category contribution, stockouts, inventory funding and basket size.'),
        'high_breadth':('Hold','No evidence identifies unprofitable categories. Shrinking the higher-cost offer is not synonymous with entering Low Price.','Category-level contribution and customer needs before any reduction.'),
        'low_depth':('Hold; no current Brand parity deficit','Brand 3.70 already exceeds CSV fair value 3.50 by 0.20. The earlier 25 → 30 repair candidate assumed the conflicting 75% slide rule; it is no longer required for current parity. Preserve useful availability and avoid unsupported inventory expansion.','Monitor Brand against the next round’s CSV floor, stockouts and contribution. Test a small depth increase only if the buffer erodes or customer evidence supports it.'),
        'high_depth':('Hold; protect the existing Brand buffer','The historical depth-position loss is real, but does not imply a present fair-value shortfall. Remove the automatic 10 → 15 repair candidate; do not finance inventory solely to close the superseded 3.90 threshold.','Maintain Brand ≥ the reported CSV floor (R1 reference 3.50); input-to-Brand response remains unknown. If a later repair is needed, test depth levers separately and review stock financing.'),
        'low_private':('Hold','Private-brand mix may support value and loyalty, but the setting is not a realized sales share or a verified cost saving.','Realized mix, margin, quality and repeat purchase before any increase.'),
        'high_private':('Hold','Avoid simultaneous mix and quality changes; CLV/private-brand valuation benefits remain relevant even without Brand leadership.','Brand parity, offering contribution and realized mix.'),
        'private_quality':('Hold; no premium-quality escalation','Keep credible value/quality while focusing on Experience. Cutting quality to fund price risks willingness to pay and Brand parity.','Unit cost, customer satisfaction, returns and Brand floor.'),
        'national_quality':('Hold','No verified historical quality decline or measured demand elasticity supports changing this setting now.','Quality perception and cost-plus selling prices; not quality spending for Brand rank.'),
        'coverage':('Hold; no expansion','In-store preference is not evidence that more stores create returns. Existing liquidity is weak; stores change access, not preferences.','Store-level return/capital, demand and financing before openings; $1.75M per new store excludes working capital.'),
        'online':('Hold; phased Frictionless recovery','Preserve $6.5M while prioritizing Brand parity, Experience and Low Price. Full Frictionless fair value is explicitly deferred for Round 2—not removed from the game rules.','Seek no deterioration from 3.30, monitor conversion and convenience, and revisit the remaining parity risk next round. Holding spend does not guarantee the score.'),
        'service':('Hold; protect delivery capacity','Keep $15M rather than funding the pivot with a service cut. Service supports both Experience and Frictionless, so protect satisfaction while the experience investment rises.','Queues, complaints, service position and target-segment satisfaction; reject a plan that damages the core experience.'),
        'experience':('Conditional +$1.0M allocation','Raise shopping experience from $13M to $14M, with analytics protected. This prioritizes closing the 0.40-point R1 gap to ZEPHARA; $1M is a discussion increment, not a fitted amount required to close it.','Experience ≥6.0 and our strongest quadrant; R2 ZEPHARA minus our R2 Experience <0.40. A higher own score alone is insufficient if ZEPHARA improves faster.'),
        'vendor':('Allocate remaining $608,000 to Low Price capability','After $1M extra Experience and preserving online/service/analytics, allocate the remaining $608,000 to vendor management ($27.608M). The exact amount is budget arithmetic, not an optimum or guaranteed cost saving.','Low Price >4.70; actual unit costs, availability, inventory, gross-profit dollars and cash after vendor expense. Benefits persist but the numerical response is unknown.'),
        'analytics':('Hold; protect the multiplier','Keep $8.314M rather than weakening the multiplier while increasing Experience. Analytics also supports the retained online investment.','Experience/online effectiveness, segment satisfaction and contribution; an unchanged reported 100% score does not identify marginal returns.'),
    }
    recommendations=[]
    for f in data['factors']:
        key=f['key'];action,why,check=rationales[key];proposed=current[key]+changes.get(key,0)
        recommendations.append(dict(key=key,label=f['label'],unit=f['unit'],cell=data['team']['cells'][key],
                                    current=current[key],proposed=proposed,change=proposed-current[key],
                                    action=action,why=why,check=check,pathway=rules[key]['pathway'],citation=rules[key]['citation']))
    draft={r['key']:r['proposed'] for r in recommendations}
    spend=sum(draft[k] for k in SPENDING);reference=sum(current[k] for k in SPENDING)
    return dict(policy=policy,segments=segments,recommendations=recommendations,draft=draft,
                decision_round=1,outcome_round=2,reference_round=1,
                status='Conditional discussion draft—not submission-ready, optimized or validated.',
                objectives=[
                    dict(quadrant='BRAND',target='Maintain CSV fair value; preserve the existing buffer',reference='R1: 3.70 vs 3.50 floor; gap +0.20',action='Hold both depth inputs for now. The previous −0.20 deficit came from the superseded 75% rule. Check the actual R2 CSV floor before further repair spending.'),
                    dict(quadrant='EXPERIENCE',target='Shrink the gap to ZEPHARA; keep our strongest quadrant',reference='R1: 6.00 vs ZEPHARA 6.40; gap 0.40',action='Protect service/analytics; raise Experience allocation. Compare both retailers’ R2 scores: peer minus ours <0.40.'),
                    dict(quadrant='LOW PRICE',target='Improve the score, not merely preserve parity',reference='R1: 4.70',action='Increase vendor capability first; target >4.70. Hold markups initially; test cuts separately only if contribution and cash support them.'),
                    dict(quadrant='FRICTIONLESS',target='Balance and preserve; full parity deferred for R2',reference='R1: 3.30 vs CSV floor 5.10; gap −1.80',action='Hold online/service/analytics. Use ≥3.30 as a monitoring guardrail, not a guaranteed result. Below-fair-value risk remains accepted for this phase.')],
                funding=dict(spend=spend,reference=reference,change=spend-reference,
                             revenue_arm=data['simulation']['budget']['revenue_arm'],
                             above_revenue_arm=max(0,spend-data['simulation']['budget']['revenue_arm']),
                              approved_budget=CONFIRMED_BUDGET,headroom=CONFIRMED_BUDGET-spend,
                              budget_source='User-confirmed Round 1 total allocation budget',incremental_cash=None),
                sequence=[
                    'Use the confirmed $71.422M allocation ceiling; separately verify cash/credit capacity for inventory, capitalization and financing before committing.',
                    'Confirm Brand’s existing +0.20 buffer over CSV fair value. Hold depth at 25/10; only test increases if the next reported floor or customer/contribution evidence warrants repair.',
                    'Test Experience $13M → $14M with service and analytics unchanged; test vendor $27M → $27.608M separately, then evaluate the combined plan and interactions.',
                    'Compare R2 Experience with R2 ZEPHARA, seek Low Price >4.70, and monitor Frictionless against 3.30. Frictionless fair value is not a hard R2 team gate, but remains a game risk.',
                    'If results disappoint, redesign within the same budget; do not assume another depth/quality increase or a blanket markup cut is free. Use only authorized simulator tests.'],
                gates=[
                    'Brand gate: maintain the actual R2 CSV FAIR VALUE benchmark (R1 floor 3.50, current buffer +0.20). Do not substitute 75% or exactly 67% of a leader. No input-to-score formula guarantees the buffer persists.',
                    'Experience gate: ≥6.0 and our strongest quadrant; shrink ZEPHARA minus Getchell’s from 0.40 using both R2 scores, not a frozen competitor forecast.',
                    'Low Price gate: improve above 4.70 with acceptable contribution and funding. Vendor spending alone is not evidence of score improvement.',
                    'Frictionless phase choice: seek no regression from 3.30, but full fair value is not required by the team in R2. The documented two-quadrant/parity game rule is unchanged; monitor its customer and valuation risk.',
                    'Business safeguard: assess target-segment contribution/satisfaction and defend existing Segments 2/5; segment profit and current CLV are missing.',
                    'Funding safeguard: five spending inputs sum to the confirmed $71.422M ceiling. Depth-related inventory, capitalization and interest still need separate cash/credit review; budget compliance is not cash approval.',
                    'Validation safeguard: local sensitivities are uncalibrated. No guaranteed score, rank, sales, profit or market-value outcome; use authorized tests only.'],
                sources=['materials/PivotOrPerish_Intro wemba.pdf · pp7–10, 14–17',
                         'materials/MarketValue_Slides.pdf · pp8–14',
                         'materials/round1/marketing/ · preferences, market size, company segment revenue and Kahn exports',
                         data['team']['source']+' · Column B'],
                boundary='Team intent explains the chosen direction, not a measured causal allocation of the last round. Raw preferences are intensities, market consumers are not our customers, and company segment revenue share is not market penetration. Current segment CLV, segment contribution and segment × offering × channel purchases are unavailable.')
