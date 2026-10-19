"""Grounded, rule-based local Q&A. No model, network requests or plan mutations."""
import re


TOPICS = {'guide', 'finance', 'budget', 'positioning', 'projection', 'year2', 'optimization', 'marketing',
          'scenarios', 'assumptions', 'sources', 'factors', 'unsupported'}


def money(value):
    return ('−' if value < 0 else '') + f'${abs(value):,.0f}'


def answer(payload, data, evaluate):
    question = payload.get('question')
    if not isinstance(question, str) or not question.strip() or len(question) > 2000:
        raise ValueError('Ask a question between 1 and 2,000 characters.')
    context = payload.get('context', '')
    if not isinstance(context, str) or (context and context not in TOPICS):
        raise ValueError('Unknown conversation topic.')
    question = question.strip()
    q = question.lower().replace('’', "'")
    working = evaluate(payload.get('decisions'), payload.get('assumptions'), data)
    decisions = working['decisions']
    sections = []
    topics = []

    def add(topic, title, text, sources, page, kind='Explanation'):
        if topic in topics:
            return
        topics.append(topic)
        sections.append(dict(title=title, text=text, sources=sources, page=page, kind=kind))

    def has(*phrases):
        return any(phrase in q for phrase in phrases)

    income = {r['name']: r['value'] for r in data['income']}
    balance = {r['name']: r['value'] for r in data['balance']}
    requested_metrics = [r for group in ['income', 'balance', 'scorecard'] for r in data[group] if r['name'].lower() in q]
    named_companies = {r['company'] for r in data['kahn']
                       if re.search(r'\b' + re.escape(r['company'].lower()) + r'\b', q)}
    aliases = {
        'online': ('online', 'ecommerce', 'e-commerce'),
        'service': ('customer service',), 'experience': ('shopping experience',),
        'vendor': ('vendor',), 'analytics': ('analytics',),
        'coverage': ('retail coverage', 'stores', 'store count'),
        'private_quality': ('private brand quality',),
        'national_quality': ('national brand quality',),
        'low_markup': ('lower cost markup', 'lower-cost markup', 'low markup'),
        'high_markup': ('higher cost markup', 'higher-cost markup', 'high markup'),
    }
    matched = [f for f in data['factors'] if any(s in q for s in aliases.get(f['key'], (f['label'].lower(),))) ]
    # General product terms identify both segments when no specific label matched.
    if not matched:
        for word, suffix in [('markup', '_markup'), ('breadth', '_breadth'), ('depth', '_depth'), ('private brand share', '_private')]:
            if word in q:
                matched.extend(f for f in data['factors'] if f['key'].endswith(suffix))

    hypothetical = has('what if', 'what-if', 'increase', 'decrease', 'change ', 'set ')
    if hypothetical and matched:
        target = re.search(r'(?:\bto\b|\bat\b|=|\bwere\b|\bwas\b)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(million|thousand|m\b|k\b)?', q)
        if not target:
            target = re.search(r'\$\s*(\d[\d,]*(?:\.\d+)?)\s*(million|thousand|m\b|k\b)?', q)
        if target and len(matched) == 1 and not re.search(r'\bby\s+\$?\d', q):
            value = float(target.group(1).replace(',', ''))
            multiplier = {'m': 1e6, 'million': 1e6, 'k': 1e3, 'thousand': 1e3}.get(target.group(2), 1)
            factor = matched[0]
            trial = dict(decisions, **{factor['key']: value * multiplier})
            try:
                simulated = evaluate(trial, working['assumptions'], data)
                text = (f"Temporary test: {factor['label']} = {money(trial[factor['key']]) if factor['unit'] == '$' else trial[factor['key']]} (working plan unchanged).\n\n"
                        f"Explicit spending: {money(simulated['spent'])}; remaining: {money(simulated['remaining'])}. "
                        f"Budget check: {'within budget' if simulated['feasible'] else 'OVER BUDGET'}.\n"
                        f"Illustrative revenue: {money(simulated['revenue'])} ({money(simulated['revenue'] - working['revenue'])} vs working estimate).\n"
                        f"Illustrative net income: {money(simulated['net_income'])} ({money(simulated['net_income'] - working['net_income'])} vs working estimate).\n"
                        + '\n'.join(f"{k.title()}: {v:.2f} (working estimate {working['scores'][k]:.2f}; structural stress {simulated['kahn']['intervals'][k][0]:.2f}–{simulated['kahn']['intervals'][k][1]:.2f})" for k, v in simulated['scores'].items())
                        + '\n\nThis is an uncalibrated sensitivity estimate, not a simulator prediction. '
                        + f"Model: {simulated['model_version']}. Score stress ranges are not confidence intervals. "
                        + ('Implementation costs for changed unpriced decisions are excluded. ' if simulated['unpriced_changes'] else '')
                        + 'Uses your current assumptions; no decisions were saved or changed.')
                add('projection', 'Your temporary what-if test', text,
                    ['app.py: evaluate()', 'working plan and current assumptions', 'materials/incomeStatement-round0.csv'], 'decisions', 'Illustrative estimate')
            except ValueError as exc:
                add('projection', 'That test is outside the planning bounds', str(exc) + '\nThe working plan is unchanged.', ['app.py: validate()'], 'decisions')
        else:
            add('projection', 'Use one explicit target per question',
                'Try “What if online investment were $5M?” I can test one clearly identified decision at an absolute target. '
                'For multiple changes, use Decision studio and save a scenario. I do not apply changes from chat.',
                ['assistant.py: local what-if parser'], 'decisions')

    followup = q.rstrip('?.! ') in {'why', 'explain', 'explain more', 'tell me more', 'more detail', 'how so', 'what does that mean'}
    forced = context if followup else ''
    if has('segment','customer preference','market size','market revenue','penetration','marketing intelligence') or forced=='marketing':
        m=data.get('marketing',{})
        if m.get('available'):
            selected=[s for s in m['segments'] if s['id'].lower() in q] or m['segments']
            text=(f"The six segment revenue values total {money(m['totals']['segment_revenue'])}, exactly matching Getchell’s revenue. Treat them as company revenue by segment, not whole-market revenue.\n\n"
                  +'\n'.join(f"• {s['id']}: company revenue {money(s['revenue'])} ({s['revenue_share']:.1%} of company total); strongest raw preferences: "+', '.join(f"{a} {s['preferences'][a]:.2f}" for a in s['top_preferences']) for s in selected)
                  +'\n\nPreference values do not sum to one and are not customer percentages. Reported size units are unverified; customer penetration cannot be computed without buyer counts and a matched denominator. '
                  'The files do not tell us which segments buy lower- versus higher-cost offerings. Getchell’s depth positions are already numerically highest in both offerings, so investigate customer-specific breadth gaps rather than automatically adding depth. '
                  'Assortment Lab’s new alignment diagnostic is descriptive and does not recalibrate Kahn scores or financial forecasts. See Marketing Intelligence for all nine source tables and reconciliation checks.')
            add('marketing','Customer segmentation: evidence and boundaries',text,m['sources'],'marketing','Observed data + interpretation')
        else:
            add('marketing','Marketing source data unavailable',m.get('message','No marketing data available.'),[],'marketing')
    if has('how do i use', 'how to use', 'walk me through', 'entire app', 'application work', 'what can you', 'get started', 'help me understand') or forced == 'guide':
        add('guide', 'A practical tour of the application',
            '1. Executive overview: start with observed financial health, Kahn positioning and the priority risks.\n'
            '2. Financial health: inspect statements, operating metrics and industry benchmarks.\n'
            '3. Kahn positioning: compare eight retailers and three rounds of Brand, Experience, Low price and Frictionless scores.\n'
            '4. Decision studio: adjust all 16 inputs; check the five-field spending budget and illustrative estimates.\n'
            '5. Model & sources: review formulas, missing data and the sensitivity assumptions before relying on comparisons.\n'
            '6. Scenario lab: save named alternatives, lock investments, run an allocation search, then explicitly adopt a candidate if appropriate.\n'
            '7. What-if & Year 2: compare the controlled test and brand-quality alternative across two planning periods, with explicit growth, cost inflation and benefit timing.\n'
            '8. Marketing Intelligence: inspect six preference profiles, segment histories, competitor offerings/channels, product positions and all nine raw source tables.\n'
            '9. Assortment Lab: change only breadth/depth around the locked team plan and compare descriptive segment alignment separately from uncalibrated forecasts.\n'
            '10. Export a decision brief or full Year-2 projection for team review. Saved scenarios persist locally; unsaved drafts reset on a fresh page load.\n\n'
            'I can explain supported topics and run simple one-factor what-if tests, but I am rule-based, not a general-purpose AI. I never change your plan.',
            ['README.md', 'web/app.js'], 'overview')

    if has('budget', 'headroom', 'remaining', 'available to', 'spend total') or forced == 'budget':
        add('budget', 'Your current planning budget',
            f"Budget: {money(data['budget'])}\nAllocated: {money(working['spent'])}\nRemaining: {money(working['remaining'])}\n"
            f"Status: {'within the explicit spending budget' if working['feasible'] else 'OVER BUDGET'}.\n\n"
            + '\n'.join(f"• {f['label']}: {money(decisions[f['key']])}" for f in data['factors'] if f['priced'])
            + '\n\nOnly these five investment fields have explicit budget costs. Assortment, quality and store changes have unknown costs. '
            'This budget is not a cash balance or a cash-flow forecast. The original image plan totals $67M with $2.814M available.',
            ['decision_making/Getchells_round0_decisionmakingplan.png', 'working plan', 'app.py: BUDGET and SPEND'], 'decisions', 'Plan arithmetic')

    if requested_metrics or has('financial', 'finance', 'revenue', 'net income', 'profit', 'loss', 'liquidity', 'cash', 'debt', 'interest', 'balance sheet', 'income statement', 'margin', 'scorecard', 'current ratio', 'working capital', 'ebit') or forced == 'finance':
        text = (f"Observed Round 0:\n• Revenue: {money(income['Net Revenue'])}\n"
                f"• Gross profit: {money(income['Gross Profit'])} ({income['Gross Profit']/income['Net Revenue']:.1%} margin)\n"
                f"• Operating expenses: {money(income['Operating Expenses'])}\n"
                f"• EBIT (gross profit − operating expenses): {money(income['Gross Profit']-income['Operating Expenses'])}\n"
                f"• Interest expense: {money(income['Interest Expense'])}\n• Net income: {money(income['Net Income'])}\n"
                f"• Cash: {money(balance['Cash'])}\n• Total liabilities: {money(balance['Total Liabilities'])}\n"
                f"• Current ratio: {balance['Total Current Assets']/balance['Total Current Liabilities']:.2f}×\n\n"
                'Operating profit is below interest expense; the statements show a net loss. '
                'Current liabilities exceed current assets, indicating liquidity pressure. These observations do not establish which marketing action will fix the loss.')
        # Include requested exact line items and scorecard metrics, not only the overview.
        direct = requested_metrics
        if direct:
            text = 'Requested observed metrics:\n' + '\n'.join(f"• {r['name']}: {r['display']}" for r in direct) + '\n\n' + text
        definitions = {'gross margin': 'Gross margin = gross profit / revenue; it is not price markup over cost.',
                       'current ratio': 'Current ratio = current assets / current liabilities. Below 1 means current liabilities exceed current assets.',
                       'working capital': 'Working capital = current assets − current liabilities.',
                       'interest coverage': 'Interest coverage = EBIT / interest expense. Below 1 means EBIT does not cover the period’s interest.',
                       'ebit': 'EBIT here = gross profit − operating expenses, before interest and taxes.',
                       'asset turnover': 'Asset turnover relates sales to assets. The scorecard value is imported, not recomputed; its period/average-asset convention is unknown.',
                       'days of inventory': 'Days of inventory describes how long inventory is held before sale; the simulator’s exact calculation is unavailable.',
                       'customer lifetime value': 'Customer lifetime value estimates customer value over time. The CSV provides the figure, but not its formula or horizon.'}
        meanings = [v for k, v in definitions.items() if k in q]
        if meanings:
            text = '\n'.join(meanings) + '\n\n' + text
        add('finance', 'Financial facts, not forecast results', text,
            ['materials/incomeStatement-round0.csv', 'materials/balanceSheet-round0.csv', 'materials/scorecard-round0.csv'], 'financials', 'Observed data + derived ratios')

    if named_companies or has('kahn', 'matrix', 'position', 'competitor', 'brand', 'frictionless', 'strategy', 'recommend', 'success', 'strength', 'weakness', 'experience score', 'experience quadrant') or forced == 'positioning':
        rows = data['kahn']
        lines = []
        for quadrant in ['BRAND', 'EXPERIENCE', 'LOW PRICE', 'FRICTIONLESS']:
            peers = [r for r in rows if r['round'] == 0 and r['quadrant'] == quadrant]
            ours = next(r['value'] for r in peers if r['company'] == "GETCHELL'S")
            rank = 1 + sum(r['value'] > ours for r in peers)
            leader = max(peers, key=lambda r: r['value'])
            lines.append(f"• {quadrant.title()}: {ours:.1f}, rank #{rank} of 8. Leader: {leader['company']} ({leader['value']:.1f}).")
        named = sorted({r['company'] for r in rows if r['company'].lower() in q and r['company'] != "GETCHELL'S"})
        comparison = ''
        for company in named:
            comparison += '\n' + company + ': ' + ', '.join(f"{r['quadrant'].title()} {r['value']:.1f}" for r in rows if r['round'] == 0 and r['company'] == company) + '.'
        add('positioning', 'Kahn positioning and the strategic interpretation',
            'The 2×2 combines product benefits vs customer experience with increasing pleasure vs reducing pain:\n'
            '• Brand = product benefits / increase pleasure.\n• Experience = customer experience / increase pleasure.\n'
            '• Low price = product benefits / reduce pain.\n• Frictionless = customer experience / reduce pain.\n\n'
            + '\n'.join(lines) + comparison + '\n\n'
            'Interpretation: protect Brand leadership and strengthen Experience, with selective Frictionless experiments. '
            'This is a strategic interpretation, not a rule from the CSV or a guarantee of profit. Competitor decisions and causal response formulas are not available.',
            ['decision_making/kahn-round0.csv', 'web/app.js: positioning()'], 'positioning', 'Observed scores + interpretation')

    if has('year 2', 'year two', 'year2', 'round 2', 'two-period', 'two year') or forced == 'year2':
        add('year2', 'Understand the What-if & Year 2 tab',
            'Open What-if & Year 2 to compare the screenshot plan, the $68M controlled service/convenience test, and a conditional national-brand-quality 5→6 test. '
            'You can edit all 16 decisions and set market growth, unit-cost inflation and benefit timing.\n\n'
            'Period convention: Round 0 actual → Year 1 / Round 1 → Year 2 / Round 2. The same nominal decision spending repeats in both projected periods. '
            'Default growth/inflation is zero and Year-1 realization is 100%, so default Year 2 equals Year 1: the same score gains are not added twice. '
            'If Year-1 realization is 50% and Year-2 catch-up is 50%, Year 2 realizes 75% of the total modeled score change.\n\n'
            'Drafts are separate from Decision studio. Run the projection after editing; export it to retain its inputs/results, or explicitly copy submitted decisions to the studio. '
            'The studio does not inherit growth, inflation or timing settings. Quality/store costs remain unknown; no future cash balance or market share is predicted. '
            'I do not see the separate what-if draft or its planning settings through chat. Use that tab for its actual projected numbers. All estimates remain uncalibrated.',
            ['forecast.py', 'web/whatif.js', 'README.md: Two-period what-if projections'], 'whatif')

    if not ('year2' in topics) and (has('predict', 'forecast', 'next round', 'estimate', 'impact') or forced == 'projection'):
        add('projection', 'What the next-round panel actually means',
            f"Under your current working decisions and assumptions:\n• Illustrative revenue: {money(working['revenue'])}\n"
            f"• Illustrative net income: {money(working['net_income'])}\n• Profit change vs Round-0 anchor: {money(working['profit_delta'])}\n"
            f"• Revenue stress range: {money(working['revenue_range'][0])} to {money(working['revenue_range'][1])}\n\n"
            'The app anchors to Round-0 financials and applies illustrative decision changes relative to the screenshot plan. '
            'Unchanged decisions reproduce Round 0 by construction; that is not a validated next-round forecast. '
            'The stress range is not a statistical confidence interval. Unknown implementation costs, financing, competitor reactions and time lags are excluded.',
            ['app.py: evaluate()', 'working plan and current assumptions', 'materials/incomeStatement-round0.csv'], 'model', 'Illustrative estimate')

    if has('optim', 'allocation search', 'lock', 'candidate') or forced == 'optimization':
        add('optimization', 'How the allocation search works',
            'In Scenario lab, choose Balanced, Positioning, or Profit; lock any investments you want unchanged; then run the search. '
            'It changes only online, service, shopping experience, vendor management and analytics spending. Product decisions remain unchanged.\n\n'
            'Guardrails: stay under $69.814M; preserve starting modeled Brand and Experience; honor locks; use planning floors of $2M online, $10M service, $8M experience, $20M vendor and $5M analytics (or starting spend if lower).\n\n'
            'Balanced weights positioning/profit at 65%/35%; Positioning 95%/5%; Profit 15%/85%. '
            'Positioning weights Brand 40%, Experience 40%, Frictionless 15%, Low price 5%; profit is divided by $10M. '
            'The search is a reproducible local heuristic, not a guaranteed global optimum. Candidates depend on uncalibrated assumptions and are applied only if you explicitly adopt them.',
            ['app.py: optimize()', 'README.md'], 'scenarios')

    if has('scenario', 'save', 'load', 'export', 'persist') or forced == 'scenarios':
        add('scenarios', 'Save, compare and share a plan',
            'Use Save scenario in Decision studio, or name and save the working plan in Scenario lab. '
            'Each saved scenario keeps its decisions, assumptions and estimated results in the local SQLite database. '
            'Load restores its decisions and assumptions, then recomputes against current source data. '
            'Saved comparisons show the stored estimates, so changed source files can make them differ from a newly loaded result.\n\n'
            'Export decision brief downloads JSON with all decisions, assumptions, sources and caveats. '
            'This is a local workspace, not authenticated multi-user collaboration. An unsaved working plan resets on page reload.',
            ['README.md', 'app.py: /api/scenarios', 'web/app.js: exportBrief()'], 'scenarios')

    if has('assum', 'formula', 'elasticity', 'coefficient', 'calibrat', 'confidence', 'uncertainty', 'model work') or forced == 'assumptions':
        a = working['assumptions']
        add('assumptions', 'Understand and challenge the model',
            f"Current assumptions:\n• Score response: {a['score_response']}\n• Demand response per weighted score point: {a['demand_response']:.1%}\n"
            f"• Price elasticity: {a['price_elasticity']}\n• Revenue stress range: ±{a['uncertainty']:.0%}\n\n"
            'Kahn v2 uses bounded, saturating investment capacities, online/physical channel mix, per-store spending dilution, and explicit interaction terms. '
            'Vendor/analytics upside is damped at their observed 100% operating scores. A smooth bounded response maps effects into assumed 0–10 Kahn scores. '
            'Exact grouped Shapley values explain score changes; structural stress ranges are not confidence intervals. Weighted score changes feed illustrative demand. '
            'Markup changes alter modeled price and volume; segment COGS scales with volume. '
            'Estimated profit starts at Round-0 net income, adds gross-profit changes, and subtracts changes in explicit investment spending.\n\n'
            'All response coefficients are assumptions, not learned simulator rules. See Model & sources for every formula and editable control. '
            'Quality, assortment and coverage implementation costs are unknown; score bounds and some input limits are planning assumptions.',
            ['prediction.py: configuration(), capabilities(), point(), predict()', 'app.py: DEFAULT_ASSUMPTIONS and evaluate()', 'web/app.js: Model & sources'], 'model')

    if has('source', 'background', 'missing', 'company.md', 'competitors.md', 'data file', 'paid', 'api key', 'chatgpt', 'chatbot', 'ai model') or forced == 'sources':
        docs = '\n'.join(f"• {name}.md: " + (text[:1500] if text else 'empty; no narrative available.') for name, text in data['documents'].items())
        add('sources', 'Data coverage and assistant limits',
            'The app reads four Round-0 financial/operating CSV files and the Kahn CSV. Screenshot decision values were manually transcribed. '
            'The image says Round 1 despite its round0 filename.\n\n' + docs + '\n\n'
            'This assistant matches supported question topics and computes answers locally from the data and your working plan. '
            'It is not connected to ChatGPT or any external AI service, does not use API keys, and makes no paid model calls. '
            'It cannot browse the web, infer hidden simulator formulas, guarantee outcomes, or change your decisions. '
            'Chat history stays in this browser tab’s session storage; clear it using Clear chat. Previous answers are snapshots, not live values.',
            data['sources'] + ['assistant.py'], 'model')

    if matched and not hypothetical:
        descriptions = {'_markup': 'Markup over cost; not the same as gross margin.', '_breadth': 'Assortment breadth; exact simulator response is unavailable.',
                        '_depth': 'Assortment depth; exact simulator response is unavailable.', '_private': 'Private-brand share of the assortment.'}
        lines = []
        for f in matched:
            fmt = money if f['unit'] == '$' else lambda v: f"{v:g}" + ('%' if f['unit'] == '%' else '')
            detail = next((text for suffix, text in descriptions.items() if f['key'].endswith(suffix)), '')
            lines.append(f"{f['label']}:\n• Working plan: {fmt(decisions[f['key']])}\n• Screenshot reference: {fmt(f['baseline'])}\n"
                         f"• Industry average: {fmt(f['industry']['average'])}; observed range: {fmt(f['industry']['minimum'])}–{fmt(f['industry']['maximum'])}.\n"
                         + ('• Included in the five-field spending budget.' if f['priced'] else '• Implementation cost unknown; not included in the explicit spending total.')
                         + ('\n' + detail if detail else ''))
        add('factors', 'Decision inputs and industry benchmarks', '\n\n'.join(lines) + '\n\nIndustry ranges are observations, not required settings or optimal targets.',
            ['materials/industryDecisions-round0.csv', 'decision_making/Getchells_round0_decisionmakingplan.png', 'working plan'], 'decisions', 'Observed benchmark + working plan')

    if not sections:
        add('unsupported', 'I don’t have a reliable answer to that question',
            'This local assistant supports application guidance, financial facts, budgets, Kahn positioning, decision benchmarks, assumptions, scenarios, '
            'optimization explanations and simple one-factor what-if tests. It is rule-based, not a general-purpose AI. '
            'Try one of the suggested questions, or rephrase around a specific metric or page. I will not invent missing data or simulator rules.',
            ['assistant.py: supported topics'], 'model')
    # Specific one-factor answers should lead, with at most two supplementary sections.
    return dict(sections=sections[:3], context=topics[0], engine='local-rule-based',
                disclaimer='Local rule-based Q&A · no external AI calls · answers do not change your working plan',
                suggestions=['Walk me through the entire app', 'Why are we making a loss?',
                             'How much budget is remaining?', 'Compare Getchell’s with Cadabra',
                             'What if online investment were $5M?', 'How does optimization work?'])
