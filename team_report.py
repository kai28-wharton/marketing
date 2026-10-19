"""Build a self-contained, offline HTML learning-team report from live calculations."""
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from forecast import project, forecast_plan


def money(v):
    return ('−' if v < 0 else '') + f'${abs(v):,.0f}'


def pct(v):
    return f'{v:.1%}'


def build_report(payload, data, reference, evaluate):
    controlled = dict(reference, online=2_500_000, service=15_300_000, experience=10_200_000)
    if payload is None:
        payload = {'decisions': controlled}
    projection = project(payload, data, reference, evaluate)
    working = projection['working']
    cases = {c['key']: c for c in projection['comparisons']}
    fixed_keys = ('service', 'experience', 'vendor', 'analytics')
    priority_plan = dict(controlled, online=data['budget']-sum(controlled[k] for k in fixed_keys))
    priority = forecast_plan(priority_plan, working['assumptions'], working['planning'], data, reference, evaluate)
    base, test, brand = (cases[k] for k in ('reference', 'controlled', 'brand'))
    test_year, actual = test['periods'][2], test['periods'][0]
    priority_year = priority['periods'][2]
    timestamp = datetime.now(timezone.utc).strftime('%d %B %Y, %H:%M UTC')
    e = lambda value: escape(str(value), quote=True)
    format_factor = lambda f, v: money(v) if f['unit'] == '$' else f"{v:g}" + ('%' if f['unit'] == '%' else '')

    rationale = {
        'coverage': 'Keep 200 stores. Opening/closing and inventory costs are unknown; expansion can dilute service and experience spending per store.',
        'online': 'Test convenience improvements. Online sales are 51.3%; this does not establish incremental investment ROI.',
        'service': 'Modest service-spend increase. $15.3M exceeds the observed industry maximum of $15M; verify the simulator allows it.',
        'experience': 'Support the shopping experience. The assumed Brand benefit from this small increase is negligible.',
        'vendor': 'Hold spending steady. The observed Vendor Management Score is already 100%; neither extra spend nor a cut has a proven return.',
        'analytics': 'Hold spending steady. The observed Customer Analytics Score is 100%; its incremental ROI remains unknown.',
    }
    rows = []
    for key in ('coverage', 'online', 'service', 'experience', 'vendor', 'analytics'):
        f = next(f for f in data['factors'] if f['key'] == key)
        rows.append(f"<tr><th scope='row'>{e(f['label'])}</th><td>{e(format_factor(f,reference[key]))}</td>"
                    f"<td><strong>{e(format_factor(f,controlled[key]))}</strong></td><td>{e(format_factor(f,priority_plan[key]))}</td><td>{e(rationale[key])}</td></tr>")
    decision_table = ''.join(rows)
    alternatives = [('Screenshot reference', base), ('Controlled test — starting experiment', test),
                    ('Frictionless-first — fixed safeguards', priority), ('Brand quality 6 — unknown cost', brand),
                    ('Submitted page draft', working)]
    case_rows = ''.join(
        f"<tr><th scope='row'>{e(name)}</th><td>{e(money(c['periods'][2]['explicit_spend']))}</td>"
        f"<td>{e(money(c['periods'][2]['remaining']))}</td>"
        + ''.join(f"<td>{c['periods'][2]['scores'][q]:.4f}</td>" for q in ('BRAND','EXPERIENCE','FRICTIONLESS'))
        + f"<td class='{'negative' if c['periods'][2]['net_income']<0 else ''}'>{e(money(c['periods'][2]['net_income']))}</td>"
          f"<td>{'OVER BUDGET' if not c['feasible'] else 'Known spend within budget'}"
          f"{' · unknown implementation costs' if c['unpriced_changes'] else ''}</td></tr>"
        for name, c in alternatives)
    financial_metrics = [('Revenue', 'revenue', money), ('Cost of goods sold', 'cogs', money),
                         ('Gross profit', 'gross_profit', money), ('Gross margin', 'gross_margin', pct),
                         ('Operating expenses', 'operating_expenses', money), ('EBIT', 'ebit', money),
                         ('Interest expense', 'interest', money), ('Income taxes', 'taxes', money),
                         ('Net income', 'net_income', money), ('Return on sales', 'return_on_sales', pct)]
    financial_rows = ''.join(f"<tr><th scope='row'>{e(label)}</th>" + ''.join(
        f"<td class='{'negative' if p[key]<0 else ''}'>{e(fmt(p[key]))}</td>" for p in working['periods']) + '</tr>'
        for label, key, fmt in financial_metrics)
    kahn_rows = ''.join(
        f"<tr><th scope='row'>{e(q.title())}</th><td>{actual['scores'][q]:.4f}</td>"
        f"<td>{test['periods'][1]['scores'][q]:.4f}</td><td>{test_year['scores'][q]:.4f}</td>"
        f"<td>{test_year['scores'][q]-actual['scores'][q]:+.4f}</td>"
        f"<td>{test_year['score_ranges'][q][0]:.3f}–{test_year['score_ranges'][q][1]:.3f}</td></tr>"
        for q in ('BRAND','EXPERIENCE','FRICTIONLESS','LOW PRICE'))
    appendix_rows = ''.join(
        f"<tr><th scope='row'>{e(f['label'])}</th><td>{e(format_factor(f,reference[f['key']]))}</td>"
        f"<td>{e(format_factor(f,working['decisions'][f['key']]))}</td>"
        f"<td>{e(format_factor(f,f['industry']['average']))}</td>"
        f"<td>{'Included in explicit spending' if f['priced'] else 'Implementation cost unknown'}</td></tr>"
        for f in data['factors'])
    warning_items = ''.join(f'<li>{e(w)}</li>' for w in working['warnings'])
    methodology = ''.join(f'<li>{e(text)}</li>' for text in projection['methodology'])
    source_items = ''.join(f'<li><code>{e(s)}</code></li>' for s in data['sources'])
    gaps = ', '.join(f'{name}.md' for name, text in data['documents'].items() if not text)
    settings, assumptions = working['planning'], working['assumptions']
    profile = ''.join(f'<tr><th scope="row">{e(label)}</th><td>{e(value)}</td></tr>' for label, value in [
        ('Model version', working['model_version']), ('Annual market/unit-demand growth', pct(settings['market_growth'])),
        ('Annual unit-COGS inflation', pct(settings['cogs_inflation'])), ('Year-1 benefit realization', pct(settings['year1_realization'])),
        ('Year-2 catch-up of remaining benefit', pct(settings['year2_catchup'])),
        ('Score response', assumptions['score_response']), ('Demand response per weighted score point', pct(assumptions['demand_response'])),
        ('Price elasticity', assumptions['price_elasticity']), ('Revenue/profit stress fraction', '±'+pct(assumptions['uncertainty']))])

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Getchell's learning-team decision report: checked investment inputs, Kahn positioning, financial trade-offs and two-period scenarios.">
<title>Getchell’s | Marketing decision report</title>
<style>
:root{{--ink:#203b32;--green:#246c54;--muted:#64776c;--line:#dce5db;--paper:#f5f7f1;--amber:#80581e;--red:#a64437}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.7 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1160px;margin:auto;padding:45px 32px}}header{{background:#203f33;color:white;padding:38px;border-radius:12px}}header p{{color:#d7e2cf;max-width:920px}}h1{{font-size:36px;line-height:1.2;letter-spacing:-1px;margin:12px 0 18px}}h2{{font-size:23px;line-height:1.4;margin:0 0 15px}}h3{{font-size:17px}}.eyebrow{{font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#cdddab}}.meta{{font-size:12px;opacity:.9}}section{{background:white;border:1px solid var(--line);border-radius:10px;padding:29px;margin:23px 0;break-inside:auto}}.lead{{font-size:19px;line-height:1.65}}.notice{{padding:17px 20px;border-radius:7px;background:#fff4df;border:1px solid #ead5b3;color:var(--amber);margin:18px 0}}.info{{background:#eff5e8;border:1px solid #d9e5cd;padding:17px 20px;border-radius:7px}}.negative{{color:var(--red)}}.muted,small{{color:var(--muted)}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:22px 0}}.metric{{background:#f4f7ee;border:1px solid var(--line);padding:20px;border-radius:7px}}.metric strong{{display:block;font-size:29px;letter-spacing:-.7px;margin:8px 0}}.metric span{{font-size:12px}}.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:13px;line-height:1.6}}th,td{{padding:13px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}thead th{{background:#eef4e7;font-size:11px;letter-spacing:.5px}}tbody th{{font-weight:600}}td{{font-variant-numeric:tabular-nums}}tr:last-child td,tr:last-child th{{border-bottom:0}}.question{{border-left:4px solid #9ab36a;padding:10px 20px;background:#f5f8ee;font-size:18px}}.pill{{display:inline-block;padding:4px 10px;border:1px solid #d8e2c8;border-radius:20px;font-size:11px;color:#dcebbf}}.toc{{display:flex;flex-wrap:wrap;gap:9px;margin:20px 0}}.toc a{{color:var(--green);background:white;border:1px solid var(--line);border-radius:5px;padding:8px 12px;text-decoration:none;font-size:12px}}li{{margin:8px 0}}code{{font-size:12px;overflow-wrap:anywhere}}footer{{font-size:12px;color:var(--muted);margin:35px 0}}.caption{{font-size:12px;color:var(--muted)}}.checklist li{{padding-left:4px}}@media(max-width:700px){{main{{padding:20px 13px}}header,section{{padding:23px 18px}}h1{{font-size:28px}}.metrics{{grid-template-columns:1fr}}.question{{font-size:16px}}}}@media print{{body{{background:white;font-size:10pt}}main{{max-width:none;padding:0}}header{{background:white;color:#203b32;border-bottom:3px solid #246c54;padding:15px 0;border-radius:0}}header p,.eyebrow{{color:#405c4a}}section{{padding:17px 0;border:0;border-top:1px solid #dce5db;border-radius:0}}.toc{{display:none}}.scroll{{overflow:visible}}table{{font-size:8pt}}th,td{{padding:7px 4px}}thead{{display:table-header-group}}tr,.metrics,.notice,.info{{break-inside:avoid}}h2,h3{{break-after:avoid}}.pill{{color:#203b32}}}}
</style></head><body><main>
<header><div class="eyebrow">GETCHELL’S · LEARNING TEAM BRIEF</div><h1>Brand, customer service & frictionless growth</h1>
<p>A checked decision report—not a claim that the simulation’s optimal decisions are known.</p><span class="pill">SELF-CONTAINED · OPENS OFFLINE</span>
<p class="meta">Generated {e(timestamp)} · Model {e(working['model_version'])} · Decision budget {e(money(data['budget']))}</p></header>
<nav class="toc" aria-label="Report sections"><a href="#answer">Team answer</a><a href="#numbers">Six decision inputs</a><a href="#outcomes">Kahn outcomes</a><a href="#alternatives">Alternatives</a><a href="#year2">Year 2</a><a href="#limits">Limits & validation</a><a href="#appendix">All inputs</a></nav>
<section id="answer"><h2>1 / Answer to the learning-team question</h2>
<blockquote class="question">“If we would like to improve Brand and customer service, while increasing Frictionless, what are the optimal numbers to use?”</blockquote>
<p class="lead"><strong>We cannot establish a defensible global optimum with the available evidence.</strong> The original $68M allocation is a controlled test to compare, not a proven optimum or a final spending recommendation.</p>
<p>Under default assumptions it slightly increases modeled Experience and Frictionless, but does <strong>not meaningfully improve Brand</strong>, and increases the modeled loss. The tables below recalculate the alternatives under this report’s chosen assumptions. A bigger convenience allocation consumes all known budget headroom; compare its financial trade-off rather than choosing the highest score alone.</p>
<div class="metrics"><div class="metric"><span>CONTROLLED TEST · KNOWN SPENDING</span><strong>{e(money(test_year['explicit_spend']))}</strong><span>{e(money(test_year['remaining']))} known headroom</span></div>
<div class="metric"><span>BRAND CHANGE · YEAR 2 VS ACTUAL</span><strong>{test_year['scores']['BRAND']-actual['scores']['BRAND']:+.4f}</strong><span>Negligible in this model; not a measured effect</span></div>
<div class="metric"><span>YEAR 2 NET INCOME · CONTROLLED TEST</span><strong class="{'negative' if test_year['net_income']<0 else ''}">{e(money(test_year['net_income']))}</strong><span>vs {e(money(actual['net_income']))} observed Round 0</span></div></div>
<div class="notice"><strong>Customer service spending is an input, not an observed service-quality rating.</strong> This model uses the broader Experience quadrant as a proxy; it cannot establish actual service satisfaction or staffing adequacy.</div>
<p><strong>Team decision:</strong> agree how much improvement is required in each quadrant, how much additional loss is acceptable, and which decisions the simulator actually allows before choosing a final allocation. A budget ceiling alone does not justify spending all of it.</p></section>
<section id="numbers"><h2>2 / Checked figures for the six requested decisions</h2>
<div class="scroll"><table><thead><tr><th>Decision</th><th>Screenshot reference</th><th>Controlled test</th><th>Frictionless-first alternative</th><th>Reason / caveat</th></tr></thead><tbody>{decision_table}
<tr><th>Known spending total</th><td>{e(money(base['periods'][2]['explicit_spend']))}</td><td><strong>{e(money(test_year['explicit_spend']))}</strong></td><td>{e(money(priority_year['explicit_spend']))}</td><td>Sum of five monetary fields; coverage is a store count, not a dollar amount.</td></tr>
<tr><th>Known budget remaining</th><td>{e(money(base['periods'][2]['remaining']))}</td><td>{e(money(test_year['remaining']))}</td><td>{e(money(priority_year['remaining']))}</td><td>Unknown quality, assortment and store implementation costs are excluded.</td></tr></tbody></table></div>
<p>The original controlled test adds $500,000 online, $300,000 service and $200,000 shopping experience: <strong>$1,000,000 total</strong>. Vendor management, analytics, coverage and other product decisions remain unchanged.</p>
<div class="info"><strong>What “Frictionless-first” means:</strong> hold coverage at 200 and service/experience/vendor/analytics at the controlled-test amounts; allocate the remaining known budget to online investment. That gives <strong>{e(money(priority_plan['online']))}</strong> online. The current model is non-decreasing in online spending under those fixed safeguards, so this achieves the highest modeled Frictionless <em>only within that one-variable allocation</em> (possibly tied if response/realization is zero). It is not a global, profit-maximizing or empirically validated optimum.</div></section>
<section id="outcomes"><h2>3 / What the controlled test changes in the Kahn matrix</h2>
<div class="scroll"><table><thead><tr><th>Quadrant</th><th>Observed Round 0</th><th>Year 1 estimate</th><th>Year 2 estimate</th><th>Year 2 change</th><th>Year 2 structural stress</th></tr></thead><tbody>{kahn_rows}</tbody></table></div>
<p class="caption">Four decimal places expose tiny model changes; they do not indicate measurement precision. Stress ranges are structural scenarios, not statistical confidence intervals or calibrated error bounds.</p>
<p><strong>Brand:</strong> the six-field controlled test mostly protects the existing position. National brand quality 5 → 6 is a separate conditional test (shown below), but its implementation cost is unknown. Do not assume the remaining $1.814M funds it.</p>
<p><strong>Coverage:</strong> holding 200 stores avoids assuming expansion is free and avoids spreading the same service/experience funds across more stores. This is a structural modeling safeguard, not proof that 200 is the optimal store count.</p></section>
<section id="alternatives"><h2>4 / Compare the trade-offs—not just the highest score</h2>
<div class="scroll"><table><thead><tr><th>Scenario</th><th>Annual known spend</th><th>Known headroom</th><th>Brand · Y2</th><th>Experience · Y2</th><th>Frictionless · Y2</th><th>Net income · Y2</th><th>Cost status</th></tr></thead><tbody>{case_rows}</tbody></table></div>
<p>Every comparison uses the same report assumptions. The “submitted page draft” may differ from the original recommendation; its full inputs appear in the appendix. These are scenario comparisons, <strong>not an unconstrained search for an optimum</strong>.</p>
<div class="notice">The conditional brand-quality alternative excludes its unknown quality cost. Its apparent budget status and profit are therefore incomplete. Service spending of $15.3M is above the observed industry maximum; verify the simulator’s actual limit before using either example.</div></section>
<section id="year2"><h2>5 / Year 1 and Year 2 financial projection — submitted draft</h2>
<p>{e(projection['convention'])} The same decision plan is used in both projected periods.</p>
<div class="scroll"><table><thead><tr><th>Metric</th>{''.join(f'<th>{e(p["period"])}</th>' for p in working['periods'])}</tr></thead><tbody>{financial_rows}</tbody></table></div>
<p><strong>Default Year 2 equals Year 1:</strong> zero external growth/inflation and full Year-1 benefit realization do not create a second copy of the score improvement. The decision spending recurs; it is not added twice to one period’s operating expense.</p>
<h3>Assumptions used in this report</h3><div class="scroll"><table><tbody>{profile}</tbody></table></div>
<p>For example, Year-1 realization of 50% with a Year-2 catch-up of 50% realizes 75% of the total modeled change by Year 2. Interest and historical operating costs otherwise remain fixed, and projected taxes are assumed zero. No projected cash balance or financing plan is inferred.</p></section>
<section id="limits"><h2>6 / Evidence, limitations & decision checklist</h2>
<p>There are three Kahn-score observations per retailer but <strong>zero paired historical decision/outcome rounds</strong> suitable for fitting causal response coefficients. There is no measured out-of-sample predictive accuracy. The screenshot says Round 1, despite its round0 filename.</p>
<ul>{warning_items}</ul>
<h3>Before selecting final numbers</h3><ol class="checklist"><li>Verify actual spending/coverage/quality bounds, especially the $15M observed service maximum.</li><li>Obtain the cost formulas for store coverage, quality and assortment; budget their costs before comparing returns.</li><li>Set explicit Brand, Experience and Frictionless targets and a financial-loss/cash constraint. Decide whether “customer service” means spending, actual satisfaction or the Experience proxy.</li><li>Collect decisions paired with next-round scores and financial results; calibrate and test against a held-out round before claiming reliable prediction.</li><li>Review liquidity: observed current assets are below current liabilities. The decision budget is not available cash.</li></ol>
<h3>Projection methodology</h3><ol>{methodology}</ol>
<h3>Sources</h3><ul>{source_items}<li><code>prediction.py</code> — explicit Kahn v2 assumptions, weights and stress method</li><li><code>forecast.py</code> — two-period calculations</li><li><code>team_report.py</code> — report generation</li></ul>
<p>{e('Missing narrative context: '+gaps+'.' if gaps else 'Company and competitor narrative files are present; this report does not independently validate their claims.')}</p></section>
<section id="appendix"><h2>7 / Reproducibility appendix — submitted draft</h2>
<p>The six-field recommendations above hold other inputs at the screenshot reference, except the separately marked national-quality-6 test. The submitted draft below can include additional changes and should not be confused with that reference recommendation.</p>
<div class="scroll"><table><thead><tr><th>Decision</th><th>Screenshot reference</th><th>Submitted draft</th><th>Industry average</th><th>Cost treatment</th></tr></thead><tbody>{appendix_rows}</tbody></table></div></section>
<footer>GETCHELL’S LEARNING TEAM · Snapshot generated {e(timestamp)}. This HTML has embedded styling and no external assets, scripts, tracking or paid API calls. Share this file directly; the recipient does not need the web application. Use your browser’s Print → Save as PDF for a printable copy. Estimates are illustrative, not guaranteed outcomes.</footer>
</main></body></html>"""


if __name__ == '__main__':
    import app
    output = Path(__file__).resolve().parent / 'reports' / 'getchells-marketing-decision-report.html'
    output.parent.mkdir(exist_ok=True)
    output.write_text(build_report(None, app.load_data(), app.BASE, app.evaluate), encoding='utf-8')
    print(output)
