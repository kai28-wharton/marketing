"""Evidence-led segment focus for the team's Experience + Brand strategy.

Reported aggregate CLV, market consumers and raw preference intensities remain
separate measures. Target roles are recommendations, not a learned profit rank.
No decision inputs, financial assumptions or live submissions are changed.
"""


def build_stp(data):
    current=data['current_round'];market=data['marketing'];rows=market['segments']
    floors={r['quadrant']:r for r in data['simulation']['fair_value'] if r['round']==current}
    profiles={r['id']:r for r in data['simulation']['segments']}
    total_size=sum(s['size'] for s in rows)
    total_clv=sum(s['clv'] for s in rows) if all(s['clv'] is not None for s in rows) else None
    roles={
        'SEGMENT 1':('Serve; no acquisition priority','Frictionless / Low Price profile; shopping-experience intensity is 0.00 and Brand 0.05. Large population alone does not justify stretching the new proposition.'),
        'SEGMENT 2':('Defend existing revenue and value','An important existing revenue and aggregate CLV pool, but breadth/retail/value needs dominate. Preserve a credible offer; do not confuse size with fit for Brand-led acquisition.'),
        'SEGMENT 3':('Primary Brand + Experience target','Intro p8 explicitly identifies Brand / Experience. Highest raw Brand intensity (0.30) and strong shopping experience (0.40) best match the chosen two-quadrant proposition; smaller population and aggregate CLV limit scale.'),
        'SEGMENT 4':('Selective adjacent reserve','Mixed preferences, moderate Brand (0.12) / shopping experience (0.20), and strong retail/online needs. Faster population growth is attractive, but does not make this the core Brand + Experience target.'),
        'SEGMENT 5':('Secondary Experience target; expansion gated','Highest shopping-experience intensity (0.43), larger population and aggregate CLV than Segment 3. Its Frictionless / Experience slide profile makes convenience parity a condition for a broad acquisition push; protect existing customers now.'),
        'SEGMENT 6':('Defend existing customers; no longer primary','The previous Low Price / Experience acquisition focus is superseded. Brand intensity is only 0.10; maintain value, retail access and service rather than abandoning a large existing customer base.'),
    }
    segments=[]
    for s in rows:
        role,reason=roles[s['id']]
        segments.append(dict(s,role=role,reason=reason,positioning=profiles[s['id']]['positioning'],
                             competitors=profiles[s['id']]['competitors'],
                             market_population_share=s['size']/total_size,
                             reported_clv_share=s['clv']/total_clv if total_clv else None,
                             expansion_gate='Frictionless must reach the moving CSV floor; require contribution/retention evidence' if s['id']=='SEGMENT 5' else None))
    focus=[s for s in segments if s['id'] in ('SEGMENT 3','SEGMENT 5')]
    exp=floors['EXPERIENCE'];brand=floors['BRAND'];low=floors['LOW PRICE'];friction=floors['FRICTIONLESS']
    policy=dict(primary='EXPERIENCE',secondary='BRAND',primary_segment='SEGMENT 3',secondary_segment='SEGMENT 5',
                reserve_segment='SEGMENT 4',defend_segments=['SEGMENT 2','SEGMENT 6'],
                experience_goal='Rank #1 among actual retailers, not merely our strongest quadrant',
                experience_min=exp['own'],experience_peer=exp['leader'],experience_peer_reference=exp['leader_value'],
                brand_goal='Defend competitive Brand leadership' if brand['rank']==1 else 'Narrow the gap to the Brand leader; parity alone is not the competitive objective',
                brand_reference_floor=brand['active_floor'],brand_leader=brand['leader'],brand_leader_reference=brand['leader_value'],
                low_price_reference_floor=low['active_floor'],frictionless_min=friction['active_floor'],
                frictionless_parity_required=True,fair_value_basis='Reported CSV FAIR VALUE; refresh after each resolved round',
                positioning='A distinctive branded assortment with the best shopping experience, supported by fair prices and dependable convenience—not price leadership.',
                timing='Retained team strategy reviewed against current outcomes; historical submitted inputs remain unchanged.')
    objectives=[
        dict(quadrant='EXPERIENCE',role='Lead',own=exp['own'],rank=exp['rank'],leader=exp['leader'],leader_value=exp['leader_value'],
             fair_value=exp['active_floor'],fair_gap=exp['active_gap'],leader_gap=exp['leader_value']-exp['own'],
              target=f"Rank #1 against actual competitors. Current leader reference: {exp['leader_value']:.2f}; sole leadership requires exceeding peers' future scores."),
        dict(quadrant='BRAND',role='Very competitive',own=brand['own'],rank=brand['rank'],leader=brand['leader'],leader_value=brand['leader_value'],
             fair_value=brand['active_floor'],fair_gap=brand['active_gap'],leader_gap=brand['leader_value']-brand['own'],
              target='Defend the current #1 Brand standing (ties count as #1) while restoring Experience; do not assume leadership will persist.' if brand['rank']==1 else 'Improve the Brand score and narrow the leader gap while protecting Experience. No arbitrary percentage target or guaranteed response is invented.'),
        dict(quadrant='LOW PRICE',role='Maintain fair value',own=low['own'],rank=low['rank'],leader=low['leader'],leader_value=low['leader_value'],
             fair_value=low['active_floor'],fair_gap=low['active_gap'],leader_gap=low['leader_value']-low['own'],
             target='Preserve the moving CSV floor; being last in rank does not require a price war when parity is already met. Monitor customer value and contribution.'),
        dict(quadrant='FRICTIONLESS',role='Restore and maintain fair value',own=friction['own'],rank=friction['rank'],leader=friction['leader'],leader_value=friction['leader_value'],
             fair_value=friction['active_floor'],fair_gap=friction['active_gap'],leader_gap=friction['leader_value']-friction['own'],
              target=f"Close the current {max(0,-friction['active_gap']):.2f}-point parity shortfall and maintain the moving CSV floor. This remains a required safeguard."),
    ]
    exp_own=exp['own'];exp_rank=exp['rank'];exp_leader=exp['leader'];exp_leader_value=exp['leader_value']
    brand_own=brand['own'];brand_rank=brand['rank'];brand_leader=brand['leader'];brand_leader_value=brand['leader_value']
    low_own=low['own'];low_rank=low['rank'];low_floor=low['active_floor'];low_gap=low['active_gap']
    fri_own=friction['own'];fri_rank=friction['rank'];fri_leader=friction['leader'];fri_leader_value=friction['leader_value'];fri_floor=friction['active_floor'];fri_gap=friction['active_gap']
    kahn=data.get('kahn',[])
    def rival_scores(name):
        return {r['quadrant']:r['value'] for r in kahn if r['round']==current and r['company']==name}
    z=rival_scores(exp_leader);bc=rival_scores('BESTCO')
    rival_standing={'SEGMENT 1':'CADABRA leads Frictionless by a wide margin; Segment 1 is not a Brand / Experience fit.',
                    'SEGMENT 2':'Price and breadth players; defend existing revenue rather than reposition the core proposition here.',
                    'SEGMENT 3':f"{exp_leader} is the Experience leader ({exp_leader_value:.1f}) and near the top on Brand ({z.get('BRAND'):.1f}): a contested fit core, so test before scaling.",
                    'SEGMENT 4':'AIM, ZEPHARA and KTBENNEY already serve a mixed-needs segment; keep this a selective reserve, not a third equal priority.',
                    'SEGMENT 5':'Same rival as Segment 3; the larger Experience pool is attractive but convenience-gated, so expansion stays conditional.',
                    'SEGMENT 6':f"BESTCO is a named value/access rival (Low Price {bc.get('LOW PRICE'):.1f}, Frictionless {bc.get('FRICTIONLESS'):.1f}, Experience {bc.get('EXPERIENCE'):.1f}): defend existing equity; no measured segment ownership is supplied."}
    byid={s['id']:s for s in segments}
    def tier_stats(ids):
        sel=[byid[i] for i in ids]
        return dict(market_consumers=sum(s['size'] for s in sel),market_population_share=sum(s['size'] for s in sel)/total_size,
                    reported_clv=sum(s['clv'] for s in sel) if total_clv else None,
                    reported_clv_share=sum(s['clv'] for s in sel)/total_clv if total_clv else None,
                    company_revenue=sum(s['revenue'] for s in sel),company_revenue_share=sum(s['revenue_share'] for s in sel))
    focus_group=dict(
        statement='Focus on a tiered group of segments, not a single segment. The decks’ “one” rule concerns Kahn quadrants (be best in one, leverage a second), not how many customer segments to serve. Win the segments our Brand + Experience quadrants can actually satisfy, defend the existing equity in segments that value value/breadth instead, keep one selective reserve, and serve the residual.',
        tiers=[
            dict(id='win',label='WIN · Brand + Experience',segments=['SEGMENT 3','SEGMENT 5'],
                 why='Segment 3 is the only true Brand + Experience fit (Brand 0.30, Shopping Experience 0.40); Segment 5 has the strongest Experience pull (0.43) with a larger pool and higher aggregate CLV. Together they are the credibility anchor and the scale extension. Segment 5 acquisition is gated on restoring Frictionless parity.',
                 **tier_stats(['SEGMENT 3','SEGMENT 5'])),
            dict(id='defend',label='DEFEND · existing value & breadth equity',segments=['SEGMENT 2','SEGMENT 6'],
                 why='Important existing equity pools with breadth/retail/value needs and Brand intensity only 0.10. Review current size/CLV rankings rather than assuming these are always the two largest. Maintain credible value and access.',
                 **tier_stats(['SEGMENT 2','SEGMENT 6'])),
            dict(id='reserve',label='RESERVE · selective tests',segments=['SEGMENT 4'],
                 why=f"Mixed retail/online/low-price needs with moderate Experience; current population growth {byid['SEGMENT 4']['size_growth']:.1%}. Test opportunistically with existing capabilities, not as a third equal priority.",
                 **tier_stats(['SEGMENT 4'])),
            dict(id='serve',label='SERVE · no acquisition priority',segments=['SEGMENT 1'],
                 why='Shopping-experience intensity is 0.00 and Brand 0.05; a Brand + Experience proposition cannot satisfy these needs.',
                 **tier_stats(['SEGMENT 1'])),
        ],
        boundary='Tiers are a fit-and-defense ordering, not a profit ranking. Market consumers count the whole segment, aggregate CLV is our customer equity attributed by segment, and revenue mix is not penetration. Segment 5 expansion still requires Frictionless parity plus contribution and retention evidence.')
    verdict=dict(
                 decision='Experience + Brand is the best available two-quadrant strategy under the MarketValue_Slides definitions.',
        summary=('MV p8 documents that moving on two quadrants while holding parity on the other two is the value sweet spot, and that one- or four-quadrant moves are inferior. '
                 'Experience + Brand is the only pairing whose two needs match a single segment’s top-two raw intensities (Segment 3: Shopping Experience 0.40, Brand 0.30), and its levers are the mostly expensed, low-capital ones (MV pp12–13). '
                 'It also targets the CLV / private-brand-adjusted valuation route directly (MV pp6, 11). It passes the shape and fit tests; execution must sustain competitive Brand, reach Experience leadership and restore Frictionless CSV parity.'),
        criteria=[
            dict(rule='Two differentiators with parity on the other two',slide='MV p8',verdict='Pass',
                 evidence=f'Experience and Brand are the two differentiators; Low Price ({low_gap:+.2f} above floor) and Frictionless are held at reported CSV fair value. One-, three- and four-quadrant moves are documented as lower-value.'),
            dict(rule='Match the strategy to the segment’s actual needs',slide='MV p9 step 1; Intro pp7–9',verdict='Pass',
                 evidence='Segment 3 is the only segment whose two largest raw needs are exactly Shopping Experience (0.40) and Brand (0.30); no other segment pairs our two quadrants at the top.'),
            dict(rule='Do it efficiently—ROIC, not revenue alone',slide='MV p7; MV pp12–13',verdict='Conditional',
                 evidence='Experience, service and analytics are mostly expensed or partly capitalised, building current FCF and horizon T; brand quality raises COGS, so pair it with vendor management and avoid capital-heavy breadth/depth or store expansion without demand.'),
            dict(rule='Charge a fair amount for the value delivered',slide='MV p9 step 3',verdict='Conditional',
                  evidence=f'Low Price gap to its {low_floor:.1f} CSV floor is {low_gap:+.2f}. Frictionless gap to its {fri_floor:.1f} floor is {fri_gap:+.2f}; leaving a reduce-pain quadrant under fair value risks losing the customers the strategy depends on.'),
            dict(rule='Extend into a second credible quadrant',slide='MV p8; MV p9 step 4',verdict='Conditional',
                  evidence=f'Experience ranks #{exp_rank}: {exp_own:.1f} vs {exp_leader} {exp_leader_value:.1f}. Brand ranks #{brand_rank}: {brand_own:.1f} vs leader reference {brand_leader_value:.1f}, floor {brand["active_floor"]:.1f}. '+('Brand is currently joint/sole #1; protect that gain while repairing Experience and convenience.' if brand_rank==1 else 'Brand still needs to become more competitive while Experience targets leadership.')),
            dict(rule='Do not neglect non-target customers',slide='MV p9 step 5',verdict='Pass',
                 evidence='Defend existing Segments 2 and 6 and keep credible fair-value Low Price and Frictionless offers rather than abandoning non-target buyers.'),
            dict(rule='Convince the market you can repeat it',slide='MV p9 step 6; MV pp3–4',verdict='Conditional',
                 evidence='A strong, durable brand lowers perceived risk and therefore WACC, and two-quadrant coherence supports a shorter, less-discounted horizon T. This requires the Brand improvement to persist across rounds, not a one-round spike.'),
            dict(rule='Target the CLV / brand-adjusted valuation route',slide='MV pp6, 11',verdict='Pass',
                 evidence='Brand, customer data and vendor relationships are treated as real competitive assets even though expensed; the simulation gives full credit through the CLV / private-brand-adjusted valuation method, which can be the greatest of the three values even with modest profit.'),
            dict(rule='Anticipate competitive moves',slide='Intro pp8–9',verdict='Risk',
                  evidence=f'Segment 3’s rival {exp_leader} leads Experience ({exp_leader_value:.1f}) and has Brand {z.get("BRAND"):.1f} versus our {brand_own:.1f}. Treat this as a contested fit core and re-check rival investment each round.'),
        ],
        alternatives=[
            dict(pair='Brand + Experience',role='Chosen',segments='3 core; 5 conditional; 4 reserve; defend 2/6',
                 case='Best documented fit and efficiency: the only pairing that matches one segment’s top-two needs, uses mostly expensed levers, and directly supports the CLV / brand valuation route.'),
            dict(pair='Low Price + Experience',role='Rejected',segments='6; selective 4',
                  case=f'Segment 6 fits Low Price / Experience, but markup cuts act immediately with no persistence (MV p12) and compress FCF, our Frictionless gap ({fri_gap:+.2f}) undermines the convenience a value claim needs, and BESTCO is a named rival—not proof of segment ownership.'),
            dict(pair='Frictionless + Experience',role='Not chosen now',segments='5',
                 case=f'Segment 5 has the strongest Experience pull (0.43) and higher aggregate CLV, but Frictionless is our weakest quadrant ({fri_own:.1f} vs {fri_leader} {fri_leader_value:.1f}) and online capacity is partly capitalised, adding debt and WACC pressure when built from a weak position (MV pp4, 12).'),
        ],
        playbook=[
            dict(step='Steps 1–3 · Build current-period FCF',rule='Pick customers you can satisfy; serve them efficiently; charge a fair amount.',action='Segment 3 core; hold Low Price and Frictionless at CSV fair value.'),
            dict(step='Steps 4–5 · Build horizon T',rule='Extend into a second credible quadrant without neglecting non-target customers.',action='Make Brand genuinely competitive; defend Segments 2/6 with credible offers.'),
            dict(step='Step 6 · Build the WACC advantage',rule='Prove you can retain these customers round after round.',action='Sustain and evidence retention and satisfaction so the discount rate can fall.'),
            dict(step='Step 7 · Guard the objective',rule='Prioritise customers and offering over short-term financials early.',action='Do not trade the Brand/Experience build for a one-round margin or value print.'),
        ],
        competitors=[dict(segment=s['id'],rivals=', '.join(s['competitors']),standing=rival_standing[s['id']],role=s['role']) for s in segments],
        sources=['materials/MarketValue_Slides.pdf · pp2–14','materials/PivotOrPerish_Intro wemba.pdf · pp7–10, 14–17'],
        boundary='A source-grounded strategy judgment, not a validated simulator forecast. The deck documents mechanisms and thresholds but no calibrated coefficients, so a changed allocation is not guaranteed to move these scores or market value. No spending-to-score or spending-to-value response is estimated.')
    return dict(policy=policy,segments=segments,objectives=objectives,verdict=verdict,focus_group=focus_group,
                focus_summary=dict(segment_ids=['SEGMENT 3','SEGMENT 5'],market_consumers=sum(s['size'] for s in focus),
                                   market_population_share=sum(s['size'] for s in focus)/total_size,
                                   reported_clv=sum(s['clv'] for s in focus) if total_clv else None,
                                   reported_clv_share=sum(s['clv'] for s in focus)/total_clv if total_clv else None,
                                   company_revenue=sum(s['revenue'] for s in focus),company_revenue_share=sum(s['revenue_share'] for s in focus)),
                criteria=['Fit: use the documented segment profile and all eight raw needs, not a fabricated weighted utility score.',
                          'Scale: market size measures total segment consumers, not our unique customers or acquisition opportunity.',
                          'Value: reported segment CLV is aggregate customer equity, not per-customer CLV, margin or customer acquisition ROI.',
                          'Feasibility: the current Frictionless shortfall limits the Segment 5 expansion case even though its Experience fit and CLV scale are attractive.'],
                required_evidence=['Segment contribution, acquisition cost, retention and satisfaction before committing spend.',
                                   'Brand-specific and experience-specific customer outcomes; segment × offering × channel purchases.',
                                   'Authorized tests showing an affordable path to Experience leadership and Frictionless CSV parity.',
                                   f'Confirm Round {data["planning_round"]} budget and inventory/capital/financing capacity; no new allocation is authorized here.'],
                sources=[f'materials/round{current}/marketing/marketSize-round{current}.csv',
                         f'materials/round{current}/marketing/marketCLV-round{current}.csv',
                         f'materials/round{current}/marketing/preference-round{current}.csv',
                         f'materials/round{current}/marketing/marketRevenue-round{current}.csv',
                         f'materials/round{current}/marketing/kahn-round{current}.csv',
                         'materials/PivotOrPerish_Intro wemba.pdf · pp7–10, 14–17',
                         'materials/MarketValue_Slides.pdf · pp2–14'],
                boundary='Segment 3 is the recommended core fit; Segment 5 is a conditional secondary/retention focus, not a proven acquisition optimum. Market consumers, aggregate segment CLV, revenue and preference intensity have different meanings. No per-buyer CLV, profitability, utility, elasticity or causal score response is inferred.')
