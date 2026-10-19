"""Current-export evidence for a team discussion, not a profit optimizer."""


def build_segment_decision(data):
    current=data['current_round'];segments=data['strategy']['segments']
    total_size=sum(s['size'] for s in segments)
    total_clv=sum(s['clv'] for s in segments)
    total_revenue=sum(s['revenue'] for s in segments)
    cases={
        'SEGMENT 1':dict(role='Serve, not a growth priority',
            case='Largest population, but Online and Customer Service lead its needs; Shopping Experience is zero. Size does not establish fit.',
            risk='CADABRA leads Frictionless; chasing this pool would stretch the Brand + Experience proposition.',
            change='Reconsider only with evidence that a credible online/value offer can be delivered profitably without diluting the two differentiators.'),
        'SEGMENT 2':dict(role='First defense priority; selective breadth-led tests',
            case='Largest aggregate CLV and current company revenue. Breadth 0.36 and Retail 0.32 dominate; our existing breadth positions give a concrete reason to retain this business.',
            risk='Shopping Experience is only 0.16 and Brand 0.10. Store reach and assortment availability—not ambience alone—are required. Extra depth or stores can tie up scarce cash.',
            change='Move up the acquisition list if existing stores and breadth can convert demand with positive incremental contribution and little added inventory/capital.'),
        'SEGMENT 3':dict(role='Keep as Brand + Experience anchor',
            case='Only segment whose two largest raw needs are Shopping Experience and Brand. Both differentiation investments speak directly to its preferences.',
            risk='Smallest population and only 1.0% population growth limit scale; ZEPHARA is stronger on both focus quadrants. Clearest fit does not mean safe market share.',
            change='Keep the anchor, but test retention/conversion and Brand credibility before assuming leadership or increasing spend.'),
        'SEGMENT 4':dict(role='Selective mixed-channel test, not equal-scale commitment',
            case='Retail 0.27 and Online 0.24 lead; population growth and current revenue growth make it worth small tests through existing capabilities.',
            risk='Lowest aggregate CLV and second-smallest population; its mixed access/value needs may spread investment across stores, online and price. Population growth is not the fastest.',
            change='Promote only if a low-capital test produces better incremental contribution and retention than the 5/6 alternatives; fast percentage growth alone is insufficient.'),
        'SEGMENT 5':dict(role='Preferred Experience-led growth extension, conditional',
            case='Highest Shopping Experience intensity (0.43), with more consumers and aggregate CLV than Segment 3. Low Price intensity is only 0.12, reducing the rationale for a price-led proposition.',
            risk='Brand is only 0.13; the slide profile is Frictionless / Experience. Population growth is nearly flat and ZEPHARA is the named rival. Our Frictionless deficit remains a binding safeguard.',
            change='Scale after restoring the moving CSV Frictionless floor and verifying incremental contribution, acquisition cost and retention. Until then protect existing customers.'),
        'SEGMENT 6':dict(role='Strongest challenger to 5; defend and test selectively',
            case='Bigger population and aggregate CLV than 5, stronger population and company-revenue growth, and Shopping Experience 0.25 is second among the four debated segments. We already exceed BESTCO on Experience.',
            risk='Retail 0.30 leads; Brand only 0.10 and Low Price 0.20 make this a value/access-led extension, not a strong Brand fit. BESTCO is stronger on Frictionless and Low Price.',
            change='Promote ahead of 5 if an existing-store/value test wins on incremental contribution and retention without a price war, major store capex or sacrificing the Brand + Experience core.'),
    }
    rows=[]
    for s in segments:
        rows.append(dict(s,**cases[s['id']],size_share=s['size']/total_size,
                         clv_share=s['clv']/total_clv,clv_growth=s['clv']/s['prior_clv']-1))
    by_id={s['id']:s for s in rows}
    candidates=['SEGMENT 2','SEGMENT 4','SEGMENT 5','SEGMENT 6']
    def ordering(key):
        return sorted(candidates,key=lambda sid:by_id[sid]['preferences'][key] if key in ('BRAND','SHOPPING EXPERIENCE') else by_id[sid][key],reverse=True)
    lenses=[dict(id=key,label=label,order=ordering(key),meaning=meaning) for key,label,meaning in [
        ('SHOPPING EXPERIENCE','Experience-led growth fit','Raw Shopping Experience weight only. This is not a total utility, profitability or acquisition-ROI rank.'),
        ('size','Market size','Total consumers in the entire market segment, not our customers or untapped demand.'),
        ('clv','Existing aggregate CLV','Reported company customer equity attributed to the segment, not per-buyer value or obtainable market value.'),
        ('revenue','Existing revenue to protect','Current company segment revenue, not contribution, market penetration or a measured loss-at-risk.'),
        ('size_growth','Market population growth','Current versus prior market population. Keep separate from our segment revenue growth.'),
        ('growth','Our segment revenue growth','Observed company sales growth; changes in price, share and customers are not causally separated.'),
        ('BRAND','Brand fit','Raw Brand weight; ties remain ties. No invented combined score or spending weight.')]]
    floors=[r for r in data['simulation']['fair_value'] if r['round']==current]
    companies={r['company'] for r in data['kahn'] if r['round']==current and r['company']!='FAIR VALUE'}
    competitors=[]
    for name in sorted(companies):
        scores={r['quadrant']:r['value'] for r in data['kahn'] if r['round']==current and r['company']==name}
        business=next(r for r in data['marketing']['companies'] if r['name']==name)
        competitors.append(dict(name=name,scores=scores,revenue=business['revenue'],growth=business['growth'],
                                named_segments=[s['id'] for s in rows if name in s['competitors']]))
    return dict(rows=rows,candidates=candidates,lenses=lenses,floors=floors,competitors=competitors,
                finance=data['insights']['finance'],
                totals=dict(size=total_size,clv=total_clv,revenue=total_revenue),
                recommendation='Keep Segment 3 as the fit anchor; prefer 5 for conditional Experience-led expansion, test 6 as the strongest challenger, protect 2 first on existing equity, and keep 4 selective. This is a judgment by objective—not a proven profit ranking.',
                pairwise=[
                    dict(pair='5 versus 6',case='5 wins on Experience and Brand intensity; 6 wins on size, aggregate CLV, population growth and observed company-revenue growth.',decision='Choose 5 for coherence with the current proposition. Choose 6 instead only with evidence that value/access can be delivered more profitably through existing capacity. Both face rival and parity risks.'),
                    dict(pair='2 versus 6',case='2 has slightly more consumers, more aggregate CLV and more current revenue; 6 has stronger Experience intensity and faster population/revenue growth.',decision='2 leads defense; 6 leads an Experience-led growth comparison. Breadth availability supports 2, but does not justify indiscriminate inventory expansion.'),
                    dict(pair='4 versus 5',case='4 has faster population and company-revenue growth and stronger Retail/Online weights; 5 has more consumers, aggregate CLV, revenue and substantially stronger Experience intensity.',decision='5 is the scale/Experience extension. 4 earns a small mixed-channel test, not automatic promotion because of growth.'),
                    dict(pair='4 versus 6',case='6 has more consumers, CLV, revenue, stronger Experience intensity and faster population and company-revenue growth. 4 has slightly higher Brand and much higher Online intensity.',decision='6 has the stronger scale/Experience case. 4 can still win a specific low-cost channel test; no inference of profit dominance is justified.')],
                sources=data['strategy']['sources'],
                boundary='Observed export data and slide-grounded judgments, not a forecast. Preference intensities are copied from the CSV, not estimated elasticities or percentages. No segment profit, acquisition cost, retention, unique-buyer count, spending response or numeric rank penalty is supplied. CSV FAIR VALUE governs parity; no slide percentage replaces it.')
