"""Cross-file Brand review: observed evidence, mechanisms and counterevidence.

No causal coefficients, segment/offering cross-tabs or marginal spending returns
are inferred. The legacy reference plan is deliberately not used as input history.
"""
import hashlib
from pathlib import Path
from round_review import COMPANY


def money(value):
    return f'${value/1_000_000:,.2f}M'


def percent(value):
    return f'{100*value:.2f}%'


def source_audit(root):
    """Inventory every supplied text source and check overlapping CSV cells.

    Repeated R0 rows in R1 exports are consistency checks, not new observations.
    Files are read, hashed and surfaced even if their evidence is only contextual.
    """
    from app import read_csv, number
    sources=[];overlaps=[];conflicts=[]
    for path in sorted((root/'materials').rglob('*')):
        if path.suffix not in ('.csv','.md','.pdf'):continue
        text=path.read_text(encoding='utf-8-sig') if path.suffix!='.pdf' else ''
        rows=read_csv(path) if path.suffix=='.csv' else None
        sources.append(dict(file=str(path.relative_to(root)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            rows=len(rows) if rows is not None else None,
                            role=('Reviewed simulation rules and strategy, page-cited in SIMULATION_REVIEW.md; raw PDF not exported' if path.suffix=='.pdf' else
                                  'Company positioning context' if path.name=='company.md' else
                                  'Competitor strategy context, not measured R1 outcomes' if path.name=='competitors.md' else
                                  'Decision definitions and unresolved semantics' if path.suffix=='.md' else
                                  'Reported segment CLV for the rows present in this export; availability is package-specific' if 'marketCLV' in path.name else
                                  'Financial evidence' if 'finance' in path.parts else 'Marketing evidence'),
                            available=bool(path.stat().st_size)))
        if rows is None or 'round0' not in path.parts:continue
        newer=Path(str(path).replace('/round0/','/round1/').replace('-round0.csv','-round1.csv'))
        if not newer.exists():continue
        new_rows=read_csv(newer)
        key_fields=next(fields for fields in [('Name',),('ROUND',),('Preference','Round'),('Category','Round'),
                                              ('Quadrant',),('Product',),('COMPANY',)] if all(k in rows[0] for k in fields))
        index={tuple(r[k] for k in key_fields):r for r in new_rows}
        checked=0
        for row in rows:
            other=index.get(tuple(row[k] for k in key_fields))
            if other is None:continue
            for col in row.keys() & other.keys() - set(key_fields):
                checked+=1
                try:equal=abs(number(row[col])-number(other[col]))<1e-8
                except ValueError:equal=row[col]==other[col]
                if not equal:conflicts.append(dict(file=str(path.relative_to(root)),column=col,prior=row[col],reexport=other[col]))
        overlaps.append(dict(prior=str(path.relative_to(root)),current=str(newer.relative_to(root)),cells_checked=checked))
    # Auxiliary quadrant exports must agree with the main Kahn history, too.
    main=read_csv(root/'materials/round1/marketing/kahn-round1.csv')
    indexed={r['Quadrant']:r for r in main};aux_checked=0
    for quadrant in ('BRAND','FRICTIONLESS','LOW PRICE'):
        path=root/'materials/round1/marketing'/f'{quadrant}-round1.csv'
        for row in read_csv(path):
            target=indexed[f"Round {row['ROUND']} {quadrant}"]
            for company,value in row.items():
                if company=='ROUND':continue
                aux_checked+=1
                if float(value)!=float(target[company]):
                    conflicts.append(dict(file=str(path.relative_to(root)),column=company,prior=value,reexport=target[company]))
    return dict(materials=sources,material_files=len(sources),overlaps=overlaps,
                overlap_cells=sum(r['cells_checked'] for r in overlaps),auxiliary_cells=aux_checked,conflicts=conflicts,
                boundary='Repeated historical rows and auxiliary quadrant exports are not independent samples. Narrative competitor profiles are context, not verified explanations of this round. Source agreement does not validate causal attribution.')


def build_holistic(data,root):
    from app import read_csv, number
    root=Path(root);a,b=data['rounds']['0'],data['rounds']['1'];i0,i1=a['income'],b['income']
    s0,s1=a['scorecard'],b['scorecard'];p=data['team']['decisions']
    positions={r['attribute']:r for r in data['marketing']['positions']}
    finance=data['insights']['finance'];brand=data['insights']['brand']
    def pos(attr):
        r=positions[attr]
        return f"{attr}: {r['prior']:g} → {r['current']:g}"
    def expense(line):
        return (f"Reported {line} expense {money(i0[line])} → {money(i1[line])}; "
                f"revenue intensity {percent(i0[line]/i0['Net Revenue'])} → {percent(i1[line]/i1['Net Revenue'])}.")
    industry={}
    for rnd in (0,1):
        export=0 if rnd==0 else 2
        industry[rnd]={r['Decision']:{k.lower():number(r[k]) for k in ('Average','Minimum','Maximum')}
                       for r in read_csv(root/'decision_making'/f'round_{export}'/f'industryDecisions-round{export}.csv') if int(r['Round'])==rnd}
    access=next(t['rows'] for t in data['marketing']['raw_tables'] if 'revenueByAccessPoint' in t['file'])
    own_access=next(r for r in access if r['COMPANY']==COMPANY)
    channels=[dict(channel=c,prior=float(own_access['Round-0 '+c]),current=float(own_access['Round-1 '+c]),
                   growth=float(own_access['Round-1 '+c])/float(own_access['Round-0 '+c])-1) for c in ('ONLINE','STORE')]
    offerings=[]
    for tier,label in [('low','Lower Cost'),('high','Higher Cost')]:
        cost_name='Cost of '+label+' Products'
        m0=i0[label+' Revenue']/i0[label+' COGS']-1;m1=i1[label+' Revenue']/i1[label+' COGS']-1
        price0=s0[cost_name]*(1+m0);price1=s1[cost_name]*(1+m1)
        offerings.append(dict(key=tier,label=label,prior_revenue=i0[label+' Revenue'],current_revenue=i1[label+' Revenue'],
                              growth=i1[label+' Revenue']/i0[label+' Revenue']-1,
                              prior_effective_markup=m0,current_effective_markup=m1,submitted_markup=p[tier+'_markup']/100,
                              prior_cost=s0[cost_name],current_cost=s1[cost_name],cost_growth=s1[cost_name]/s0[cost_name]-1,
                              prior_price_proxy=price0,current_price_proxy=price1,price_proxy_growth=price1/price0-1,
                              prior_margin=1-i0[label+' COGS']/i0[label+' Revenue'],current_margin=1-i1[label+' COGS']/i1[label+' Revenue']))
    # Each row explicitly includes both a Brand mechanism and its financial cost.
    evidence={
        'low_markup': ('Value / price trade-off',
            'Markup changes the cost-plus selling price and contribution per sale; perceived value may affect the proposition, but is not an identified Brand-score term.',
            f"Effective markup from revenue/COGS is {percent(offerings[0]['prior_effective_markup'])} → {percent(offerings[0]['current_effective_markup'])}. "+pos('LOWER COST PRICE')+'.',
            f"Lower-cost unit-cost metric rises {percent(offerings[0]['cost_growth'])}; the cost-plus selling-price proxy rises {percent(offerings[0]['price_proxy_growth'])} despite lower markup. Margin falls to {percent(offerings[0]['current_margin'])}.",
            'A lower markup is not necessarily a lower ticket price. Low Price Kahn falls 4.9 → 4.7, but no price elasticity or causal Brand loss is identified.'),
        'high_markup': ('Demand / margin trade-off',
            'A lower higher-cost markup can support purchases while reducing contribution and potentially changing the premium/value signal.',
            f"Effective markup is {percent(offerings[1]['prior_effective_markup'])} → {percent(offerings[1]['current_effective_markup'])}. "+pos('HIGHER COST PRICE')+'.',
            f"Higher-cost revenue grows {percent(offerings[1]['growth'])}; gross margin falls {100*(offerings[1]['prior_margin']-offerings[1]['current_margin']):.2f} pp. Its selling-price proxy falls {percent(-offerings[1]['price_proxy_growth'])}.",
            'Growing higher-cost purchases contradict a claim of observed premium-customer flight. Price signaling remains a hypothesis, not proof.'),
        'low_breadth': ('Assortment interaction',
            'More categories support one-stop shopping but can dilute within-category choice if depth and execution capacity do not keep pace.',
            pos('LOWER COST BREADTH')+'; '+pos('LOWER COST DEPTH')+'.',
            'Definitions explicitly link breadth to larger inventory requirements. Aggregate inventory grew; no category-level stock allocation is supplied.',
            'Breadth is not depth. Wider selection across categories is not proof of stronger selection within each category; no SKU count is inferred from the index.'),
        'high_breadth': ('Assortment interaction',
            'Maintaining many higher-cost categories with little depth may weaken specialist credibility even when the category footprint is retained.',
            pos('HIGHER COST BREADTH')+'; '+pos('HIGHER COST DEPTH')+'.',
            'High category breadth can retain stock/funding needs; the added inventory cost of a depth repair is unmeasured.',
            'The breadth position is unchanged; it is not an observed worsening on its own. Prior breadth input is not verified.'),
        'low_depth': ('Strongest score-linked evidence',
            'Depth determines choice within a category. Lower observed depth is the largest deterioration after higher-cost depth in the reconstructed Brand score.',
            pos('LOWER COST DEPTH')+'; conditional score contribution −1.00 point.',
            'Restoring choice may require stock and funding. The extra inventory per depth-index point is unavailable, not zero.',
            'Current input is verified; the previous team input is not. The −1.00 is a position-to-score reconstruction, not the isolated effect of changing B4.'),
        'high_depth': ('Strongest score-linked evidence',
            'Loss of within-category higher-cost choice is the leading measured proposition deterioration and first mechanism to test.',
            pos('HIGHER COST DEPTH')+'; conditional score contribution −1.90 points.',
            f"The affected offering is growing {percent(offerings[1]['growth'])}, but has lower margin; rebuilding depth without stock discipline could consume scarce cash.",
            'The −1.90 cannot be interpreted as the proven effect of setting B8 to 10. No official input-to-position transformation is supplied.'),
        'low_private': ('Observed bundle offset; input ambiguous',
            'Private-brand architecture could affect distinctiveness and product mix; the supplied Private Brand definition duplicates the quality definition.',
            pos('LOWER COST PRIVATE BRAND')+'; conditional score offset +0.15.',
            'The 44% is Excel formatting, not a verified private-label sales/stock share; no mix-margin or unit-cost allocation can be made.',
            'Do not blame a shift to private label: the observed private-brand position improves. Cannot separate this input from quality or national-brand effects.'),
        'high_private': ('Observed bundle offset; input ambiguous',
            'A private/national-brand balance could change premium credibility, but the meaning of this parameter must first be clarified.',
            pos('HIGHER COST PRIVATE BRAND')+'; conditional score offset +0.15.',
            'The 70% setting is not a verified higher-cost private-label revenue share. Exposure and margin by brand type are unavailable.',
            'A 70% setting is not evidence that national brands were removed or that customers rejected them; the reported position rose.'),
        'private_quality': ('Quality / cost interaction',
            'Definition-supported higher private-brand quality raises unit cost and could strengthen the proposition; realized quality/defect evidence is absent.',
            'Both private-brand positions rise 2.0 → 2.3; both product unit-cost metrics rise.',
            'With cost-plus prices, a cost increase can increase ticket prices as well as COGS. Costs cannot be split between quality, vendor, inflation and mix.',
            'Quality 6 is verified in the current plan, not a verified 5 → 6 historical input change. The +0.30 position offset is not quality-only impact.'),
        'national_quality': ('Quality / cost interaction',
            'National-brand quality can affect credibility, ticket price and cost. The source has an unlabeled national-quality definition interpreted as this factor.',
            'Current national quality is 6; no separate national-brand position, sales, availability or satisfaction series is supplied.',
            'Unit-cost increases are observed, but private/national exposures and separate cost changes are not supplied.',
            'No evidence establishes that national-brand quality fell or that the assortment lost national-brand appeal. Do not allocate an invented Brand coefficient.'),
        'coverage': ('Execution context, not direct deterioration',
            'Store reach supports access, but effective service and merchandise selection must match the physical footprint.',
            pos('RETAIL COVERAGE')+f"; store revenue grows {percent(channels[1]['growth'])}.",
            'Opening/closing stores has capex, recovery and write-off consequences. Current 200 stores is a workbook input; prior count is not independently verified.',
            'Unchanged coverage position does not identify store openings, closures or store-level execution. Do not use mall-decline narrative as a measured R1 cause.'),
        'online': ('Channel execution, weak direct evidence',
            'Online infrastructure can improve access and convenience; it does not by itself replace missing product choice.',
            pos('ONLINE INVEST')+'; Frictionless falls 3.4 → 3.3. '+expense('Online Expense'),
            f"Current investment {money(p['online'])} versus expense {money(i1['Online Expense'])}; the difference is not automatically verified cash capex.",
            'Online revenue grows despite its share slipping. Weak position response is a reason to investigate allocation/timing, not proof that spending caused Brand loss.'),
        'service': ('Possible execution amplifier',
            'Store associates and call-center capacity must support the expanding business and category promise.',
            pos('CUSTOMER SERVICE')+'. '+expense('Customer Service'),
            f"Current decision {money(p['service'])} is not reported expense {money(i1['Customer Service'])}. Expenses rose, but more slowly than sales.",
            'Falling service intensity is not evidence of fewer staff per transaction or worse satisfaction. Experience Kahn improves, so a blanket execution collapse is unsupported.'),
        'experience': ('Observed counterweight',
            'Store ambience and convenience support experiential differentiation, which is central to the company narrative.',
            pos('SHOPPING EXPERIENCE')+'; Experience Kahn rises 5.8 → 6.0. '+expense('Shopping Experience'),
            f"Current investment {money(p['experience'])} versus expense {money(i1['Shopping Experience'])}; capitalized amounts and timing require verification.",
            'The measured experience direction is positive. More ambience spending is not an evidence-based first repair for a choice/depth problem.'),
        'vendor': ('Possible cost / availability amplifier',
            'Buying activity supports sourcing costs and inventory management; reduced capacity could matter when assortment and sales expand.',
            expense('Vendor Management')+f" Reported Vendor Management Score stays {s0['Vendor Management Score']:g}% → {s1['Vendor Management Score']:g}%.",
            'Unit costs and absolute inventory rise, but reported days of inventory improves 90 → 81. Savings support current earnings; availability impacts are unobserved.',
            'The unchanged 100% score and better inventory days do not support an established vendor failure. Spend intensity alone is not productivity or causality.'),
        'analytics': ('Possible targeting amplifier',
            'Customer data should help curate a wider range for differing segment needs; lower spending could reduce learning capacity.',
            expense('Customer Analytics')+f" Reported Customer Analytics Score stays {s0['Customer Analytics Score']:g}% → {s1['Customer Analytics Score']:g}%.",
            'Analytics is expensed. The reduction saves current expense, but its marginal targeting and retention returns are not supplied.',
            'Unchanged 100% score and growing company CLV are counterevidence to a proven analytics-driven collapse. No segment churn or causal response is observed.'),
    }
    factors=[]
    for f in data['factors']:
        key=f['key'];level,mechanism,observed,economics,boundary=evidence[key]
        source_files=['materials/decision_making_factors.md','materials/round1/marketing/productPosition-round1.csv']
        source_files+=['materials/round1/finance/'+n+'-round1.csv' for n in ('incomeStatement','scorecard')]
        factors.append(dict(key=key,label=f['label'],cell=data['team']['cells'][key],submitted=p[key],unit=f['unit'],
                            industry_round0=industry[0][f['label']],industry_round1=industry[1][f['label']],
                            evidence_level=level,mechanism=mechanism,observed=observed,economics=economics,boundary=boundary,
                            prior_input=None,prior_input_status='Previous submitted workbook unavailable; no historical input delta asserted',
                            sources=source_files))
    actual_peers=[r for r in brand['peers'] if r['company'] not in (COMPANY,'FAIR VALUE')]
    brand_peers={r['company']:r for r in brand['peers']}
    competitors=[dict(company=c['name'],revenue_growth=c['growth'],prior_revenue_share=c['prior_share'],revenue_share=c['share'],
                      brand_prior=brand_peers[c['name']]['prior'],brand_current=brand_peers[c['name']]['current'],
                      brand_change=brand_peers[c['name']]['change']) for c in data['marketing']['companies']]
    shares=next(t['rows'] for t in data['marketing']['raw_tables'] if 'revenueMarketShare' in t['file'])
    reported_offering_shares=[dict(offering=r['Product'],prior=float(r['Round-0 Share']),current=float(r['Round-1 Share']))
                             for r in shares if r['Product'].startswith(COMPANY+' ')]
    pricing=next(t['rows'] for t in data['marketing']['raw_tables'] if '/pricing-' in t['file'])
    cost_comparison=[dict(company=r['COMPANY'],low_cost_growth=float(r['Round-1 LOWER COST'])/float(r['Round-0 LOWER COST'])-1,
                          high_cost_growth=float(r['Round-1 HIGHER COST'])/float(r['Round-0 HIGHER COST'])-1) for r in pricing]
    segments=[]
    historical_clv={r['ROUND']:r for r in read_csv(root/'materials/round0/marketing/marketCLV-round0.csv')}
    for s in data['marketing']['segments']:
        segments.append(dict(id=s['id'],growth=s['growth'],revenue=s['revenue'],revenue_share=s['revenue_share'],
                             prior_revenue_share=s['prior_revenue']/i0['Net Revenue'],
                             raw_brand=s['preferences']['BRAND'],brand_weight=s['normalized_preferences']['BRAND'],
                             depth_weight=s['normalized_preferences']['DEPTH'],breadth_weight=s['normalized_preferences']['BREADTH'],
                             top_preferences=s['top_preferences'],size_growth=s['size_growth'],
                             historical_round0_clv=float(historical_clv['0'][s['id']]),current_clv=None))
    audit=source_audit(root)
    result=dict(version='holistic-brand-2',source=data['team']['source'],sha256=data['team']['sha256'],
                thesis='The observed loss is most consistent with weakened within-category choice in a broader department-store proposition—not a general sales, quality or experience collapse. Price/cost and execution-capacity trade-offs may amplify that mismatch; their individual causal effects are not identified.',
                review_corrections=[
                    'The previous four-position bridge describes how the reported score moved; it is not a causal allocation among sixteen decisions. Its formula was discovered and checked on the same rounded rows.',
                    'The verified current depth inputs are 25/10, but earlier team depth inputs are not independently verified. Old screenshot values must not be called the actual prior submission.',
                    'Prior effective markups ARE independently recoverable from financial revenue/COGS, unlike most prior decision inputs: approximately 54%/66% versus current 50%/52%.',
                    'Reported vendor and analytics expenses fell, but their scores stayed at 100%; service expense rose. These observations qualify any claim of execution failure.',
                    'Brand score loss is not a measured dollar loss, reduced brand awareness, churn or destroyed CLV. Revenue, reported CLV, net income and market value all rose.'],
                factors=factors,offerings=offerings,channels=channels,segments=segments,source_audit=audit,
                competitors=competitors,reported_offering_shares=reported_offering_shares,cost_comparison=cost_comparison,
                actual_peer_mean_change=sum(r['change'] for r in actual_peers)/len(actual_peers),
                actual_peer_count=len(actual_peers),actual_peers_all_improved=all(r['change']>0 for r in actual_peers),
                history=[dict(round=r['ROUND'],brand=float(r[COMPANY])) for r in read_csv(root/'materials/round1/marketing/BRAND-round1.csv')],
                financial=dict(revenue_growth=i1['Net Revenue']/i0['Net Revenue']-1,
                               clv_prior=s0['Customer Lifetime Value'],clv_current=s1['Customer Lifetime Value'],
                               clv_growth=s1['Customer Lifetime Value']/s0['Customer Lifetime Value']-1,
                               net_income_prior=i0['Net Income'],net_income_current=i1['Net Income'],
                               equity_value_prior=s0['Market Value'],equity_value_current=s1['Market Value'],
                               reported_unit_share_prior=s0['Market Share by Units Sold']/100,reported_unit_share_current=s1['Market Share by Units Sold']/100,
                               reported_revenue_share_prior=s0['Market Share by Revenue']/100,reported_revenue_share_current=s1['Market Share by Revenue']/100,
                               inventory_change=b['balance']['Inventory']-a['balance']['Inventory'],
                               inventory_growth=b['balance']['Inventory']/a['balance']['Inventory']-1,
                               inventory_days_prior=s0['Days of Inventory'],inventory_days_current=s1['Days of Inventory'],
                               margin_prior=a['ratios']['gross_margin'],margin_current=b['ratios']['gross_margin'],
                               margin_rate_effect_pp=finance['within_effect_pp'],margin_mix_effect_pp=finance['mix_effect_pp'],
                               cash_current=b['balance']['Cash'],cash_change=finance['cash_change'],current_ratio=finance['current_ratio'],
                               quick_ratio=finance['quick_ratio'],working_capital=finance['working_capital'],
                               interest_cover=finance['interest_cover'],ten_day_stock_funding=finance['ten_days_inventory_funding'],
                               ten_day_cash_share=finance['ten_days_inventory_cash_share']),
                strategy_context=[
                    'company.md describes a recognizable department store spanning designer labels to bargains, with a historic inventory-turnover weakness. Wider categories with fewer choices within them could conflict with that promise; this is a strategic interpretation, not a measured customer response.',
                    'competitors.md positions Zephara around curated prestige/service, Bestco around tightly selected value, and Cadabra around frictionless access. These are alternative value propositions, not evidence that their specific actions caused Getchell’s loss this round.',
                    'Getchell’s Experience remains strong at 6.0 (second among the seven retailers); Low Price 4.7 and Frictionless 3.3 did not become stronger compensating positions. A broad but shallow offer risks strategic ambiguity rather than proving a low-price or convenience repositioning succeeded.'],
                priorities=[
                    dict(priority=1,title='Verify the score and submitted-plan provenance',keys=['low_depth','high_depth','low_private','high_private'],
                         action='Obtain the simulator definition of Brand, the immutable submitted-plan export and the Private Brand field definition before relying on a causal input attribution.',
                         readout='Distinguish depth/quality/mix rules, any competitor normalization, reporting lags and rounding; do not resubmit experiments as live decisions without approval.'),
                    dict(priority=2,title='Test higher-cost depth first, then lower-cost depth',keys=['high_depth','low_depth'],
                         action='In an isolated simulator/sandbox, compare the unchanged 16-input control with higher-cost depth 10 → 15, and separately lower-cost depth 25 → 30. Hold the other fifteen inputs and external conditions constant.',
                         readout='Record reported depth positions, Brand, category revenue, gross profit, inventory, cash and borrowing. Repeat before estimating response; no predicted Brand lift or optimal depth is claimed.'),
                    dict(priority=3,title='Test breadth × depth coherence and unit economics',keys=['low_breadth','high_breadth','low_markup','high_markup'],
                         action='After single-factor tests, use an explicit factorial control to compare breadth/depth combinations and then isolated markup tests, only in a resettable sandbox.',
                         readout='Measure whether curation improves choice, contribution and cash efficiency. Require actual selling prices and category stocks; broadening and deepening everywhere is not the default.'),
                    dict(priority=4,title='Protect useful execution, investigate bottlenecks',keys=['private_quality','national_quality','online','service','experience','coverage','vendor','analytics'],
                         action='Preserve the measured Experience gain; investigate service workload, buying capacity, availability and analytics targeting before reallocating blanket Brand-repair spending. Clarify private-brand settings before testing mix/quality.',
                         readout='Seek stockouts, supplier terms, workload, conversion, returns and segment × offering × channel contribution. No 100%-score spending increase is assumed to generate an incremental benefit.')],
                boundaries=[
                    'One simultaneous team decision bundle and one subsequent transition cannot identify sixteen causal effects or their interactions. Peer decisions are only industry aggregates, not matched retailer-level treatment histories.',
                    'Reported product positions are outputs, not SKU counts, decision indices or consumer satisfaction measures. The score identity is exploratory and in-sample.',
                    'Intro p8 identifies Segment 3 as Brand/Experience and gives the competitor targets. No segment × offering × channel purchase table is supplied, so segments cannot be labeled premium buyers or used to allocate the Brand decline.',
                    'All six segments grow and company CLV rises. Round 0 segment CLV is historical; Round 1 segment CLV, retention, awareness and contribution are unavailable. Reported size units are undefined.',
                    'Pricing exports match the finance cost metrics. Cost × (1 + effective markup) is a conditional selling-price proxy, not observed transaction price; product mix may change.',
                    'Finance constrains the affordability of repair; low cash or margins are not demonstrated causes of the Brand score. Cash-bridge capex remains a proxy, and market value is not spendable cash.',
                    'Industry averages/minima/maxima contextualize the plan only. Round 1 aggregates are not a prior team plan, recommended target or proof of marginal underinvestment.'])
    # Newer, explicit PDF mechanics supersede the earlier Markdown ambiguities.
    rules={r['key']:r for r in data['simulation']['factor_rules']}
    result['thesis']=data['simulation']['revised_brand']
    result['review_corrections'] += data['simulation']['definition_updates']
    for row in factors:
        row['documented_rule']=rules[row['key']]['rule'];row['rule_citation']=rules[row['key']]['citation']
        if row['key'] in ('low_private','high_private'):
            row['evidence_level']='Documented mix / valuation mechanism; numeric impact unknown'
            row['mechanism']=rules[row['key']]['rule']
            row['economics']='Mix is confirmed by MV p12 and can support margins, loyalty and the CLV/private-brand valuation method. The setting is not measured sales share; numeric economics remain unavailable.'
            row['boundary']='The PDF resolves the Markdown definition conflict. It does not supply realized brand-type exposures or separate mix-versus-quality causal effects. Reported private-brand positions improved.'
        if row['key']=='analytics':
            row['evidence_level']='Documented online/experience multiplier'
            row['mechanism']='MV p13: analytics is a pure multiplier of online and shopping experience, with no standalone demand term. Cuts may weaken the return on both investments even if its operating score remains 100%.'
        if row['key']=='vendor':
            row['evidence_level']='Documented retained structural cost lever'
            row['mechanism']='MV p13: fully expensed but highly retained cost improvements compound over time. The 100% operating score does not prove that lower spending preserves future sourcing capability.'
        if row['key']=='coverage':row['mechanism']=rules['coverage']['rule']
        row['sources'] += [d['file'] for d in data['simulation']['documents']]
    result['boundaries'][0]+=' The supplied slides establish qualitative pathways, not causal numerical coefficients.'
    result['priorities'][0]['action']='Confirm Brand-score aggregation and version-specific FAIR VALUE calculation. Obtain the immutable submitted-plan export. The PDF now identifies Private Brand as mix; response coefficients still require evidence.'
    result['priorities'][0]['readout']='Verify score aggregation, competitor normalization, reporting lags and rounding. Documented qualitative rules do not identify causal input coefficients.'
    result['priorities'][2]['action']='Use the documented two-quadrant playbook and target-segment fit before testing breadth/depth and markup. Intro p24 permits one R1 undo, not unlimited resettable experiments.'
    result['priorities'][3]['action']='Protect Experience, pair online/experience with analytics, and evaluate retained vendor benefits over time. Do not interpret 100% scores as proof cuts are safe. Test mix and quality with cost discipline.'
    return result


def write_report(data,path):
    x=data['insights']['brand']['parameter_impact'];h=x['holistic'];f=h['financial']
    lines=['# Holistic Brand-loss review','',h['thesis'],'',
           '## New primary-source review',data['simulation']['goal'],data['simulation']['strategy'],data['simulation']['priority'],
           'See **SIMULATION_REVIEW.md** for the page-cited PDF rules, fair-value conflict, three-route valuation, ROIC/WACC diagnostic and missing parameters. Earlier depth-only recommendations are subordinate to this two-quadrant/targeting review.','',
           f"Workbook: `{h['source']}` · Column B · SHA-256 `{h['sha256']}`.",
           'The workbook source above uses the renamed file; this report remains a historical export-1 diagnosis, not the current-period recommendation.','',
           '## 1. Review of the earlier diagnosis','']+['- '+s for s in h['review_corrections']]
    lines+=['','## 2. What the Brand loss measures','',
            'Brand was 6.3 in rounds −2, −1 and 0, then 3.7 in round 1 (−2.60, −41.3%). Rank fell from first to fifth among seven actual retailers; FAIR VALUE is a benchmark, not an eighth firm.',
            f"All six actual competitors improved; their mean change was +{h['actual_peer_mean_change']:.3f}. This is a descriptive comparison, not a causal control group.",'',
            x['formula'],'',
            '|Observed output|R0|R1|Reconstructed Brand change|','|---|---:|---:|---:|']
    lines += [f"|{r['attribute']}|{r['prior_position']:.2f}|{r['current_position']:.2f}|{r['brand_change']:+.2f}|" for r in x['contributions']]
    lines += ['',f"Net {x['reconstructed_change']:+.2f}; gross depth loss −2.90, private-position offset +0.30. The level residual is −0.05 in each round. {x['discovery_status']}",'',
              '## 3. Strategic interpretation','']+['- '+s for s in h['strategy_context']]
    lines+=['','**Working hypothesis:** category breadth expanded on the lower-cost side while within-category depth positions fell sharply on both sides. Product quality/private-brand positions did not compensate enough in the reconstructed score. Price/cost trade-offs and execution capacity may amplify a less coherent proposition, but have no identified shares of the −2.60 loss.','',
            '## 4. Connect all sixteen decisions','',
            'Prior actual input values are unavailable. The tables below use current cell values, observed output changes and reported industry context—not invented prior decision deltas. Industry R0/R1 averages are not targets.','',
            '|Factor / cell|Current input|Industry avg R0 / R1|Evidence priority|','|---|---:|---:|---|']
    for r in h['factors']:
        fmt=money if r['unit']=='$' else lambda v:f'{v:g}'+('%' if r['unit']=='%' else '')
        lines.append(f"|{r['label']} · {r['cell']}|{fmt(r['submitted'])}|{fmt(r['industry_round0']['average'])} / {fmt(r['industry_round1']['average'])}|{r['evidence_level']}|")
    for r in h['factors']:
        lines += ['',f"### {r['label']} — {r['cell']}",'- **Mechanism:** '+r['mechanism'],'- **Observed:** '+r['observed'],
                  '- **Financial connection:** '+r['economics'],'- **Counterevidence / limit:** '+r['boundary'],
                  '- **PDF rule:** '+r['documented_rule']+' ('+r['rule_citation']+')']
    lines+=['','## 5. Cost, price and financial capacity','',
            '|Offering|Revenue growth|Effective markup R0 → R1|Unit-cost growth|Cost-plus price proxy R0 → R1|Price proxy growth|Margin R0 → R1|',
            '|---|---:|---|---:|---|---:|---|']
    for r in h['offerings']:
        lines.append(f"|{r['label']}|{percent(r['growth'])}|{percent(r['prior_effective_markup'])} → {percent(r['current_effective_markup'])}|{percent(r['cost_growth'])}|${r['prior_price_proxy']:.2f} → ${r['current_price_proxy']:.2f}|{percent(r['price_proxy_growth'])}|{percent(r['prior_margin'])} → {percent(r['current_margin'])}|")
    lines+=['',h['boundaries'][4],
            f"Higher-cost revenue mix increased; it **helped** total margin by {f['margin_mix_effect_pp']:+.3f} pp. Within-offering margin changes contributed {f['margin_rate_effect_pp']:+.3f} pp. The margin squeeze was not caused by a move toward a worse-margin offering.",
            f"Total sales grew {percent(f['revenue_growth'])}; net income improved {money(f['net_income_prior'])} → {money(f['net_income_current'])}. Reported company CLV rose {percent(f['clv_growth'])}; equity market value rose {money(f['equity_value_prior'])} → {money(f['equity_value_current'])}. These are counterevidence to a blanket commercial collapse, not proof Brand has no longer-term cost.",
            f"Inventory rose {money(f['inventory_change'])} ({percent(f['inventory_growth'])}) while reported inventory days improved {f['inventory_days_prior']:g} → {f['inventory_days_current']:g}. Cash fell {money(-f['cash_change'])} to {money(f['cash_current'])}; current ratio is {f['current_ratio']:.3f}×, quick ratio {f['quick_ratio']:.3f}×, working capital {money(f['working_capital'])}, interest cover {f['interest_cover']:.2f}×.",
            f"Illustrative extra 10 days of stock at R1 COGS/365 requires {money(f['ten_day_stock_funding'])}, {percent(f['ten_day_cash_share'])} of cash, before financing. MV p14 specifies no inventory holding expense. This is not a simulator inventory-days forecast or an estimate of depth-restoration cost.",'',
            '### Competitor and share cross-check','',
            '|Retailer|Brand R0 → R1|Brand change|Revenue growth|Derived revenue share R0 → R1|',
            '|---|---|---:|---:|---|']
    for r in h['competitors']:
        lines.append(f"|{r['company']}|{r['brand_prior']:g} → {r['brand_current']:g}|{r['brand_change']:+.2f}|{percent(r['revenue_growth'])}|{percent(r['prior_revenue_share'])} → {percent(r['revenue_share'])}|")
    lines += ['',f"Scorecard unit share rose {percent(f['reported_unit_share_prior'])} → {percent(f['reported_unit_share_current'])}; reported revenue share rose {percent(f['reported_revenue_share_prior'])} → {percent(f['reported_revenue_share_current'])}. Derived shares above use the seven-company revenue universe; reported rounding/denominator differences are retained.",
              '; '.join(f"{r['offering']}: rounded revenue share {percent(r['prior'])} → {percent(r['current'])}" for r in h['reported_offering_shares'])+'. These offering shares use the whole reported revenue universe, not share within that cost tier.',
              'All seven pricing exports show rising cost metrics. That broad cost environment prevents attributing Getchell’s cost increases to its quality/vendor decisions alone. The cost growth by retailer is:',
              '|Retailer|Lower-cost metric growth|Higher-cost metric growth|','|---|---:|---:|']
    lines += [f"|{r['company']}|{percent(r['low_cost_growth'])}|{percent(r['high_cost_growth'])}|" for r in h['cost_comparison']]
    lines+=['','## 6. Customer and channel implications','',
            '|Segment|R1 company revenue|Revenue growth|Revenue share R0 → R1|Normalized BRAND / DEPTH / BREADTH|',
            '|---|---:|---:|---|---|']
    for r in h['segments']:
        lines.append(f"|{r['id']}|{money(r['revenue'])}|{percent(r['growth'])}|{percent(r['prior_revenue_share'])} → {percent(r['revenue_share'])}|{percent(r['brand_weight'])} / {percent(r['depth_weight'])} / {percent(r['breadth_weight'])}|")
    lines+=['',
            'Segment 3 has the strongest normalized explicit BRAND weight (22.22%) but still grew 24.28%; its revenue share fell, not its sales. Segment 5 grew 18.41%, with strong shopping-experience preference. Segments 1/2 have stronger depth weights than Segment 3; Segment 6 has the weakest depth weight yet grew 37.52%. These comparisons inform tests but cannot establish lost purchases or identify which segments buy higher-cost goods.',
            'Preference weights are normalized within each segment’s eight-attribute sum, not customer percentages or demand elasticities. Revenue is Getchell’s segment revenue, not total addressable market. Historical segment CLV and reported size do not provide current segment retention or profit.',
            '; '.join(f"{r['channel']} revenue {money(r['prior'])} → {money(r['current'])} ({percent(r['growth'])} growth)" for r in h['channels'])+'. Both channels grew; online share slipped from 51.3% to 50.3%.','',
            '## 7. Decision priorities and evidence needed','']
    for r in h['priorities']:
        lines += [f"### {r['priority']}. {r['title']}",r['action'],r['readout'],'']
    lines+=['No automatic adoption. A viable test must preserve approved cash/funding and profit constraints. Do not restore all depth or raise all spending merely to maximize an unverified score relationship.','',
            '## 8. Limits','']+['- '+s for s in h['boundaries']]
    audit=h['source_audit']
    lines+=['','## 9. Complete source coverage','',
            f"Reviewed {audit['material_files']} supplied CSV/Markdown/PDF files under materials, plus the workbook and both industry-decision files. Checked {audit['overlap_cells']} overlapping R0/R1 cells and {audit['auxiliary_cells']} auxiliary Kahn cells; conflicts: {len(audit['conflicts'])}. This overlap audit does not erase the separate documented-versus-exported FAIR VALUE conflict.",audit['boundary'],'']
    lines+=['- `'+r['file']+'` — '+r['role'] for r in audit['materials']]
    lines+=['- `'+data['team']['source']+'` — all sixteen explicit Column B cells',
             '- `decision_making/round_0/industryDecisions-round0.csv` — historical export-0 industry context',
             '- `decision_making/round_2/industryDecisions-round2.csv` — re-exported historical aggregate context','']
    Path(path).write_text('\n'.join(lines),encoding='utf-8')
