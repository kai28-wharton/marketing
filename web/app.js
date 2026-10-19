'use strict';
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = (v, compact = true) => `${v < 0 ? '−' : ''}$${compact ? (Math.abs(v) / 1e6).toFixed(2) + 'M' : Math.abs(v).toLocaleString('en-US', {maximumFractionDigits:0})}`;
const pct = v => (v * 100).toFixed(1) + '%';
const delta = v => `${v >= 0 ? '+' : '−'}${money(Math.abs(v))}`;
const qNames = {BRAND:'Brand', EXPERIENCE:'Experience', FRICTIONLESS:'Frictionless', 'LOW PRICE':'Low price'};
const pages = {overview:'Executive overview', marketing:'Marketing Intelligence', decisions:'Decision studio', assortment:'Assortment Lab', positioning:'Kahn positioning', financials:'Financial health', scenarios:'Scenario lab', whatif:'What-if & Year 2', chat:'Ask the assistant', model:'Model & sources'};
let data, decisions, assumptions, result, scenarios = [], optimization = null;
const invalidFields = new Set();
let page = 'overview', evaluationSequence = 0, timer, toastTimer;
const chatPrompts = ['Walk me through the entire app', 'Why are we making a loss?', 'How much budget is remaining?', 'Compare Getchell’s with Cadabra', 'What if online investment were $5M?', 'How does optimization work?'];
let chatMessages = [], chatBusy = false, chatContext = '';
try {
  const saved = JSON.parse(sessionStorage.getItem('getchells-chat') || '[]');
  if (Array.isArray(saved)) chatMessages = saved.filter(m => m && ((m.role === 'user' && typeof m.text === 'string') || (m.role === 'assistant' && Array.isArray(m.sections) && m.sections.every(s=>s && typeof s.text==='string' && typeof s.title==='string' && Array.isArray(s.sources))))).slice(-40);
  chatContext = [...chatMessages].reverse().find(m=>m.role==='assistant')?.context || '';
} catch { /* Session storage is optional; chat still works without it. */ }

async function api(path, payload) {
  const response = await fetch('/api/' + path, payload === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || `Request failed (${response.status})`);
  return body;
}
function notify(text) { $('#notice').textContent = text; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('#notice').textContent = '', 6500); }
function head(eyebrow, title, subtitle, actions = '') { return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p class="subtitle">${subtitle}</p></div><div class="actions">${actions}</div></div>`; }
function card(label, value, foot, cls = '', badge = '') { return `<div class="card"><div class="card-label">${label}${badge}</div><div class="card-value ${cls}">${value}</div><div class="card-foot">${foot}</div></div>`; }
function panelHead(title, description, badge = '') { return `<div class="panel-heading"><div><h2>${title}</h2><p>${description}</p></div>${badge}</div>`; }
function tag(text, color = '') { return `<span class="tag ${color}">${text}</span>`; }
function lookup(group, name) { return data[group].find(r => r.name === name)?.value || 0; }
function observedScores(round = 0, company = "GETCHELL'S") { return Object.fromEntries(data.kahn.filter(r => r.round === round && r.company === company).map(r => [r.quadrant, r.value])); }
function rank(q, company = "GETCHELL'S") { const rows = data.kahn.filter(r => r.round === 0 && r.quadrant === q); const value = rows.find(r => r.company === company).value; return 1 + rows.filter(r => r.value > value).length; }
function scoreBars(scores, compare = false) {
  const base = observedScores();
  return `<div class="score-bars">${Object.entries(qNames).map(([q, label]) => `<div><div class="score-bar-head"><span>${label}</span><strong>${scores[q].toFixed(2)}${compare ? ` <small class="${scores[q] >= base[q] ? 'positive' : 'negative'}">(${(scores[q] - base[q] >= 0 ? '+' : '') + (scores[q] - base[q]).toFixed(2)})</small>` : ''}</strong></div><div class="bar"><span style="width:${scores[q] * 10}%"></span></div></div>`).join('')}</div>`;
}
function matrix() {
  const scores = observedScores();
  const notes = {BRAND:'Differentiated, desirable products', EXPERIENCE:'Engaging, enjoyable shopping', 'LOW PRICE':'Reduce the monetary cost', FRICTIONLESS:'Reduce time and shopping effort'};
  return `<div class="axis-top"><span>PRODUCT BENEFITS</span><span>CUSTOMER EXPERIENCE</span></div><div class="matrix-wrap"><div class="axis-side"><span>REDUCE PAIN</span><span>INCREASE PLEASURE</span></div><div class="matrix">${['BRAND','EXPERIENCE','LOW PRICE','FRICTIONLESS'].map(q => `<div class="quadrant ${['BRAND','EXPERIENCE'].includes(q) ? 'strong' : ''}"><div class="q-name">${q}</div><div class="q-rank">#${rank(q)} of 8</div><div class="q-score">${scores[q].toFixed(1)} <small>/ 10*</small></div><p>${notes[q]}</p></div>`).join('')}</div></div><div class="legend"><span><i></i>Getchell’s observed Round 0</span><span><i class="light"></i>Strategic pillars</span></div><p class="small muted">*10-point display scale is a planning assumption; the CSV does not specify the score ceiling.</p>`;
}
function insights() {
  const entries = [
    ['↗','Protect what makes Getchell’s different','Brand leads at 6.3. Experience is second at 5.8, behind Zephara’s 6.5. Build from these strengths.',false],
    ['!','Profitability needs attention',`A ${money(Math.abs(lookup('income','Net Income')))} loss follows ${money(lookup('income','Interest Expense'))} in interest expense. Growth alone is not the objective.`,true],
    ['⇄','Test convenience, don’t assume its return','Online investment is $2M versus a $9.61M industry average, while online sales are 51.3%. Test targeted investment rather than blindly matching peers.',false],
    ['!','Keep liquidity visible',`The current ratio is ${(lookup('balance','Total Current Assets')/lookup('balance','Total Current Liabilities')).toFixed(2)}×. The decision budget is not a cash-flow forecast.`,true]
  ];
  return entries.map(([icon,title,text,warn]) => `<div class="insight"><div class="insight-icon ${warn?'warn':''}">${icon}</div><div><h3>${title}</h3><p>${text}</p></div></div>`).join('');
}
function overview() {
  return head('THE BIG PICTURE', 'Better decisions. Stronger positioning.', 'A shared view of your business, your competitive edge, and the trade-offs ahead.', '<button data-action="export">↓ Export decision brief</button>') +
    `<div class="hero"><div><div class="eyebrow">YOUR STRATEGIC NORTH STAR</div><h2>Win on brand. Elevate the experience.<br>Make every investment count.</h2><p>Getchell’s leads on Brand and has a strong Experience position. Use Kahn’s framework to protect those advantages while testing a financially disciplined next round.</p></div><a href="#decisions" class="button">Open decision studio ↗</a></div>` +
    `<div class="cards">${card('NET REVENUE',money(lookup('income','Net Revenue')),'Round 0 · observed', '',tag('ACTUAL','green'))}${card('NET INCOME',money(lookup('income','Net Income')),'−1.7% return on sales','negative')}${card('REVENUE MARKET SHARE','13.5%','13.0% share by units sold')}${card('PLANNING HEADROOM',money(result.remaining),`${money(data.budget)} screenshot budget`,result.remaining<0?'negative':'positive')}</div>` +
    `<div class="grid-2"><section class="panel">${panelHead('Your competitive position','Kahn retail success matrix · Round 0', '<a href="#positioning" class="tag">Explore matrix ↗</a>')}${matrix()}</section><section class="panel">${panelHead('What deserves your attention','Evidence-led priorities, not automatic recommendations')}${insights()}</section></div>` +
    `<section class="panel">${panelHead('From insight to a decision','A focused workflow for your team')}<div class="grid-equal"><div><h3>01 / Build and challenge your plan</h3><p class="small muted">Edit all 16 decision levers, benchmark against industry ranges, and see the budget and illustrative impact update together.</p><a class="button" href="#decisions">Build your plan →</a></div><div><h3>02 / Compare before you commit</h3><p class="small muted">Save alternatives with their assumptions. Run a constrained spending search and export a decision brief for team discussion.</p><a class="button" href="#scenarios">Explore scenarios →</a></div></div></section>`;
}
function displayFactor(value, f) { return f.unit === '$' ? money(value) : `${value.toLocaleString('en-US',{maximumFractionDigits:2})}${f.unit==='%'?'%':''}`; }
function pointDelta(v) { return `${v>=0?'+':''}${v.toFixed(3)}`; }
function kahnDetails() {
  const k=result.kahn, base=observedScores();
  if(!k?.intervals)return '';
  return `<section id="kahn-details" class="panel">${panelHead('Kahn impact explorer','Nonlinear, channel-aware sensitivity model · '+k.version,tag('UNCALIBRATED','amber'))}<div class="cards">${Object.keys(qNames).map(q=>`<div class="card"><div class="card-label">${qNames[q].toUpperCase()}</div><div class="card-value">${result.scores[q].toFixed(2)} <small class="small ${result.scores[q]>=base[q]?'positive':'negative'}">${pointDelta(result.scores[q]-base[q])}</small></div><div class="card-foot">Structural stress: ${k.intervals[q][0].toFixed(2)}–${k.intervals[q][1].toFixed(2)}<br><br>Frozen-peer rank #${k.ranks[q].point} · stress range #${k.ranks[q].best}–${k.ranks[q].worst}</div></div>`).join('')}</div><p class="small muted">Stress ranges are not confidence intervals. Peer ranks hold competitors at Round 0, not their next-round results. The point estimate remains anchored to Round 0 when decisions are unchanged.</p><div class="info">Investment returns saturate rather than rise indefinitely. Service scales with channel workload; shopping experience depends on spending per store. Retail expansion improves modeled reach but can dilute service and experience. Vendor and analytics upside is damped because their observed operating scores are already 100%.</div><details><summary>What drives the change? Exact grouped attribution</summary><p>Each row allocates its share of interactions. Columns sum to the model’s score change (before display rounding). These are model explanations, not measured causal effects.</p><div class="table-wrap"><table><thead><tr><th>Driver</th>${Object.values(qNames).map(n=>`<th>${n}</th>`).join('')}</tr></thead><tbody>${k.attribution.map(row=>`<tr><td>${esc(row.label)}</td>${Object.keys(qNames).map(q=>`<td class="${row.contributions[q]<0?'negative':'positive'}">${pointDelta(row.contributions[q])}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details><hr class="divider"><details><summary>Marginal tests: add or remove $1M / 25 stores</summary><p>One change at a time from this working plan. Dollar tests may exceed the budget; they are sensitivity probes, not feasible recommendations. Retail costs are unknown.</p><div class="table-wrap"><table><thead><tr><th>Change</th>${Object.values(qNames).map(n=>`<th>Δ ${n}</th>`).join('')}</tr></thead><tbody>${k.sensitivities.map(row=>['increase','decrease'].map(direction=>row[direction]?`<tr><td>${esc(row.label)} ${direction==='increase'?'+':'−'}${row.priced?'$1M':'25 stores'}</td>${Object.keys(qNames).map(q=>`<td>${pointDelta(row[direction].score_changes[q])}</td>`).join('')}</tr>`:'').join('')).join('')}</tbody></table></div></details><hr class="divider"><details><summary>Evidence, stress method & model assumptions</summary><p>${esc(k.status)} We have 3 Kahn rounds and <strong>0 paired decision/outcome rounds</strong>; coefficients cannot be causally fitted or backtested from these files.</p><p>${esc(k.interval_method)}</p><ul>${k.notes.map(note=>`<li>${esc(note)}</li>`).join('')}</ul><p>Sources: scorecard-round0.csv (channel share and operating scores), industryDecisions-round0.csv (scale assumptions), kahn-round0.csv (anchor and historical stress floors). No historical score trend is treated as proof of a decision’s effect.</p></details>${k.extrapolations.length?`<div class="warning">Outside industry observations: ${k.extrapolations.map(r=>esc(r.label)).join(', ')}. Predictions here are unvalidated extrapolations.</div>`:''}</section>`;
}
function budgetPanel() {
  return `<div class="panel">${panelHead('Your decision budget','Five explicit spending decisions',tag(result.feasible?'WITHIN BUDGET':'OVER BUDGET',result.feasible?'green':'red'))}<div class="budget-number ${result.remaining<0?'negative':''}">${money(result.spent)}</div><div class="small muted">allocated of ${money(data.budget)}</div><div class="bar ${result.feasible?'':'red'}"><span style="width:${Math.min(100,result.spent/data.budget*100)}%"></span></div><div class="budget-line"><span>Available to allocate</span><strong class="${result.remaining<0?'negative':'positive'}">${money(result.remaining)}</strong></div><hr class="divider">${data.factors.filter(f=>f.priced).map(f=>`<div class="budget-line"><span>${esc(f.label)}</span><strong>${money(decisions[f.key])}</strong></div>`).join('')}<div class="warning">This is the screenshot’s decision budget, not cash. Assortment, quality and store changes have unknown costs.</div></div><div class="panel"><div class="forecast-label">Illustrative impact · not a forecast</div><h2 style="margin-top:10px">Next-round sensitivity</h2><p class="small muted">Round-0 anchor + modeled decision changes</p><div class="forecast-row"><span>Revenue estimate</span><strong>${money(result.revenue)}</strong></div><div class="forecast-row"><span>Net income estimate</span><strong class="${result.net_income<0?'negative':'positive'}">${money(result.net_income)}</strong></div><div class="forecast-row"><span>Profit change vs anchor</span><strong>${delta(result.profit_delta)}</strong></div><p class="small muted">Revenue stress band: ${money(result.revenue_range[0])} – ${money(result.revenue_range[1])}. This is a user-set stress range, not a confidence interval.</p><hr class="divider">${scoreBars(result.scores,true)}<a href="#model" class="button full" style="margin-top:17px">Review model assumptions →</a></div>`;
}
function decisionPage() {
  const groups = [...new Set(data.factors.map(f=>f.group))];
  return head('PLAN THE NEXT MOVE','Decision studio','Tune all 16 decisions. Changes are evaluated against the screenshot plan, not inferred historical decisions.', '<button data-action="reset">Reset plan</button><button class="primary" data-action="save-current">Save scenario +</button>') +
    `<div class="info">Planning reference: the image is labeled <strong>Round 1</strong>, although its filename says round0. Industry ranges are observed benchmarks, not simulator input limits. Except for visible slider bounds, input bounds are provisional planning guardrails.</div><div class="decision-layout"><div>${groups.map((group,i)=>`<section class="panel"><div class="section-label"><span>0${i+1}</span><h2>${group}</h2></div>${data.factors.filter(f=>f.group===group).map(f=>`<div class="factor-row"><div><label for="factor-${f.key}">${esc(f.label.split(': ').pop())}</label><small>Industry avg ${displayFactor(f.industry.average,f)} · range ${displayFactor(f.industry.minimum,f)}–${displayFactor(f.industry.maximum,f)}</small>${!f.priced && decisions[f.key]!==f.baseline?'<small class="danger-text">Changed: implementation cost unknown</small>':''}</div><div class="input-wrap"><input aria-label="${esc(f.label)}" id="factor-${f.key}" data-factor="${f.key}" type="number" min="${f.min}" max="${f.max}" step="${f.unit==='$'?100000:f.unit==='%'?.1:1}" value="${decisions[f.key]}"><span class="input-unit">${f.unit==='$'?'USD':f.unit==='index'?'':f.unit}</span></div></div>`).join('')}</section>`).join('')}<div class="warning">${result.warnings.map(w=>`<div>• ${esc(w)}</div>`).join('')}</div></div><aside class="sticky" id="budget-panel">${budgetPanel()}</aside></div>`;
}
function positioning() {
  const companies = [...new Set(data.kahn.map(r=>r.company))];
  return head('THE KAHN FRAMEWORK','Compete where it matters.','Lead in a meaningful quadrant, reinforce it with a complementary strength, and monitor your weaknesses.') +
    `<div class="grid-equal"><section class="panel">${panelHead('Retail success matrix','Observed Getchell’s positioning · Round 0')}${matrix()}</section><section class="panel">${panelHead('Trajectory of your advantage','Observed history, not modeled estimates')}<div class="grid-equal">${['BRAND','EXPERIENCE','FRICTIONLESS','LOW PRICE'].map(q=>`<div><h3>${qNames[q]}</h3><div class="trend">${[-2,-1,0].map(r=>`<div class="trend-column"><strong>${observedScores(r)[q].toFixed(1)}</strong><div class="column" style="height:${observedScores(r)[q]*8}px"></div><span>R${r}</span></div>`).join('')}</div></div>`).join('')}</div></section></div>` +
    `<section class="panel">${panelHead('The competitive landscape','Eight retailers · observed Round 0 scores',tag('SOURCE: KAHN CSV','green'))}<div class="table-wrap"><table><thead><tr><th>Retailer</th>${Object.values(qNames).map(n=>`<th>${n}</th>`).join('')}<th>Strongest quadrant</th></tr></thead><tbody>${companies.map(c=>{const s=observedScores(0,c); const strongest=Object.keys(s).sort((a,b)=>s[b]-s[a])[0];return `<tr class="${c==="GETCHELL'S"?'highlight-row':''}"><td>${esc(c)} ${c==="GETCHELL'S"?tag('YOU','green'):''}</td>${Object.keys(qNames).map(q=>`<td>${s[q].toFixed(1)}</td>`).join('')}<td>${qNames[strongest]}</td></tr>`;}).join('')}</tbody></table></div></section><div class="info">Strategic interpretation: defend Brand and Experience; test Frictionless improvements selectively. The matrix measures positioning, not profit, and higher scores do not establish financial returns.</div>`;
}
function financials() {
  const currentRatio=lookup('balance','Total Current Assets')/lookup('balance','Total Current Liabilities');
  const ebit=lookup('income','Gross Profit')-lookup('income','Operating Expenses');
  return head('KNOW YOUR STARTING POINT','Financial health','Round-0 financial statements, operational metrics and industry benchmarks. These are observed, not projections.')+
    `<div class="cards">${card('GROSS MARGIN',pct(lookup('income','Gross Profit')/lookup('income','Net Revenue')),`${money(lookup('income','Gross Profit'))} gross profit`)}${card('CURRENT RATIO',currentRatio.toFixed(2)+'×','Current assets / current liabilities','negative')}${card('INTEREST COVERAGE',(ebit/lookup('income','Interest Expense')).toFixed(2)+'×','EBIT / interest expense','negative')}${card('WORKING CAPITAL',money(lookup('balance','Total Current Assets')-lookup('balance','Total Current Liabilities')),'Current assets less current liabilities','negative')}</div><div class="warning">Liquidity and debt are material constraints. The ${money(data.budget)} decision budget must not be interpreted as deployable cash. Store expansion, inventory changes, financing and future cash flows are not modeled.</div><div class="grid-equal">${[['income','Income statement'],['balance','Balance sheet']].map(([key,title])=>`<section class="panel">${panelHead(title,'USD · Round 0')}<div class="table-wrap"><table><thead><tr><th>Line item</th><th>Amount</th></tr></thead><tbody>${data[key].map(r=>`<tr class="${['Net Revenue','Gross Profit','Net Income','Total Assets','Total Liabilities','Shareholder’s Equity'].includes(r.name)?'highlight-row':''}"><td>${esc(r.name)}</td><td class="number ${r.value<0?'negative':''}">${esc(r.display)}</td></tr>`).join('')}</tbody></table></div></section>`).join('')}</div><section class="panel">${panelHead('Operating scorecard','Imported values are preserved exactly; ratio definitions may be simulator-specific.')}<div class="table-wrap"><table><thead><tr><th>Metric</th><th>Round 0</th></tr></thead><tbody>${data.scorecard.map(r=>`<tr><td>${esc(r.name)}</td><td class="number ${r.value<0?'negative':''}">${esc(r.display)}</td></tr>`).join('')}</tbody></table></div></section><section class="panel">${panelHead('Your plan vs the industry','Industry averages and observed min/max are benchmarks, not recommendations.')}<div class="table-wrap"><table><thead><tr><th>Decision</th><th>Current plan</th><th>Industry average</th><th>Observed min</th><th>Observed max</th></tr></thead><tbody>${data.factors.map(f=>`<tr><td>${esc(f.label)}</td><td><strong>${displayFactor(decisions[f.key],f)}</strong></td><td>${displayFactor(f.industry.average,f)}</td><td>${displayFactor(f.industry.minimum,f)}</td><td>${displayFactor(f.industry.maximum,f)}</td></tr>`).join('')}</tbody></table></div></section>`;
}
function comparisonRows(items) {
  return items.map(s=>`<tr><td><strong>${esc(s.name)}</strong><br><small class="muted">${s.created ? new Date(s.created).toLocaleDateString() : 'Working plan'} · response ${s.assumptions.score_response}<br>Model ${esc(s.result.model_version||'kahn-1.0')}${s.result.model_version!==result.model_version?' · different version: load to recalculate':''}</small></td><td>${money(s.result.spent)}</td><td class="${s.result.net_income<0?'negative':'positive'}">${money(s.result.net_income)}</td><td>${s.result.scores.BRAND.toFixed(2)}</td><td>${s.result.scores.EXPERIENCE.toFixed(2)}</td><td>${s.result.scores.FRICTIONLESS.toFixed(2)}</td><td>${tag(s.result.feasible?'IN BUDGET':'OVER BUDGET',s.result.feasible?'green':'red')}${s.result.unpriced_changes.length?' '+tag('UNPRICED','amber'):''}</td><td>${s.id?`<button data-load="${s.id}">Load</button>`:'—'}</td></tr>`).join('');
}
function scenarioPage() {
  return head('EXPLORE THE TRADE-OFFS','Scenario lab','Save alternatives, compare assumptions, and search for a stronger allocation. No external AI calls are used.', '<button data-action="export">↓ Export decision brief</button>')+
    `<section class="panel">${panelHead('Save your working plan','Scenarios persist in a local SQLite database, including their assumptions.')}<form id="save-form" class="scenario-toolbar"><input id="scenario-name" type="text" maxlength="100" placeholder="e.g. Brand-first, convenience test" aria-label="Scenario name" required><button class="primary" type="submit">Save scenario +</button></form></section><section class="panel optimization">${panelHead('Find a better spending mix','A constrained local search under your selected assumptions',tag('HEURISTIC · NOT A GUARANTEE','amber'))}<div class="grid-equal"><div><label for="goal" class="small">Optimization objective</label><select id="goal" style="margin-top:8px"><option value="balanced">Balanced — positioning + modeled profit</option><option value="positioning">Positioning — emphasize Kahn advantages</option><option value="profit">Profit — emphasize modeled profitability</option></select><p class="small muted">Locks keep selected investments unchanged. Product, price, quality and coverage decisions never change during this search.</p><div class="lock-grid">${data.factors.filter(f=>f.priced).map(f=>`<label class="checkbox"><input type="checkbox" value="${f.key}" data-lock> Lock ${esc(f.label)}</label>`).join('')}</div><button class="primary" data-action="optimize" ${result.feasible?'':'disabled'}>Run allocation search ↗</button></div><div><h3>Guardrails, not magic</h3><p class="small muted">Respect the $69.814M budget. Preserve the starting modeled Brand and Experience scores. Use transparent planning floors: online $2M, service $10M, experience $8M, vendor $20M, analytics $5M (or your starting value if lower).</p><p class="small muted">Balanced weights: 65% positioning / 35% profit; positioning: 95% / 5%; profit: 15% / 85%. Positioning combines Brand 40%, Experience 40%, Frictionless 15%, Low price 5%. Profit is scaled by $10M. These choices are policy assumptions, not learned results.</p></div></div>${optimization?`<hr class="divider"><h3>Candidate allocation</h3><div class="metric-strip"><div><span class="small muted">Modeled profit change vs working plan</span><strong>${delta(optimization.result.net_income-result.net_income)}</strong></div><div><span class="small muted">Candidate Experience</span><strong>${optimization.result.scores.EXPERIENCE.toFixed(2)}</strong></div><div><span class="small muted">Available headroom</span><strong>${money(optimization.result.remaining)}</strong></div></div><div class="table-wrap"><table><thead><tr><th>Investment</th><th>Working plan</th><th>Candidate</th><th>Change</th></tr></thead><tbody>${data.factors.filter(f=>f.priced).map(f=>`<tr><td>${f.label}</td><td>${money(decisions[f.key])}</td><td>${money(optimization.result.decisions[f.key])}</td><td>${delta(optimization.result.decisions[f.key]-decisions[f.key])}</td></tr>`).join('')}</tbody></table></div><p class="small muted">${esc(optimization.method)} Review sensitivity and operational implications before adopting.</p><button class="primary" data-action="adopt">Use candidate as working plan</button>`:''}</section><section class="panel">${panelHead('Compare your alternatives','All financial estimates below are illustrative. Different assumptions can change the ranking.')}<div class="table-wrap"><table><thead><tr><th>Scenario</th><th>Spend</th><th>Est. net income</th><th>Brand</th><th>Experience</th><th>Frictionless</th><th>Checks</th><th></th></tr></thead><tbody>${comparisonRows([{name:'Working plan',assumptions,result},...scenarios])}</tbody></table></div>${!scenarios.length?'<div class="empty">No saved alternatives yet. Save your first scenario above.</div>':''}</section>`;
}
function modelPage() {
  return head('TRANSPARENCY FIRST','Model, assumptions & sources','Know what is measured, what is assumed, and what is missing before you make a decision.')+
    `<div class="warning"><strong>Not a calibrated next-round prediction.</strong> One round of financials, three positioning observations, and cross-sectional industry benchmarks cannot identify causal returns or simulator rules. The model is a discussion tool. It cannot guarantee improved scores, profit or simulation results.</div><section class="panel">${panelHead('Sensitivity controls','Changing these updates your working plan. Saved scenarios retain their original settings.')}<form id="assumptions-form">${[['score_response','Score response strength','Multiplier on illustrative decision-to-positioning effects.',0,2,.05],['demand_response','Demand response per weighted score point','0.025 means 2.5% unit-demand lift for a one-point weighted positioning gain.',0,.1,.005],['price_elasticity','Price elasticity','Unit demand sensitivity to percentage changes in modeled prices.',0,3,.1],['uncertainty','Revenue stress range','± this fraction of estimated revenue; also applied to profit. Not a statistical confidence interval.',.01,.5,.01]].map(([key,label,desc,min,max,step])=>`<div class="model-assumption"><div><label for="a-${key}"><strong>${label}</strong></label><p>${desc}</p></div><input id="a-${key}" data-assumption="${key}" type="number" value="${assumptions[key]}" min="${min}" max="${max}" step="${step}" required></div>`).join('')}<div class="actions" style="margin-top:20px"><button class="primary" type="submit">Apply assumptions</button><button type="button" data-action="reset-assumptions">Restore defaults</button></div></form></section><section class="panel">${panelHead('How the estimates work','All coefficients below are illustrative, not fitted to the simulation.')}<pre>Anchor: Round-0 company revenue, COGS, net income and Kahn scores.
Reference decisions: the screenshot plan (not verified Round-0 historical inputs).

Kahn v2: capacity(x,h) = x / (x+h); h = industry average (assumed scale).
Online capacity uses online investment; reach uses retail coverage.
Online share s = observed online sales / 100 (currently 0.513).
Service load = s + (1−s) × stores/reference stores.
Service capacity = capacity(service spend / load, industry service average).
In-store quality = capacity(experience spend / stores,
                           industry experience average / industry coverage average).
At zero stores, in-store quality is zero.
Vendor/analytics: positive capacity changes × (1 − 0.85 × observed operating score);
                 cuts retain their full assumed downside.
Joint capacities are products: online×analytics, service×store quality,
                             analytics×store quality, vendor×analytics.
Features = 2 × (planned capacity − reference capacity).
Store quality, reach, service×experience and analytics×experience features × (1−s).
Online feature × s. Other product features retain explicit assumed coefficients.

Brand weights: vendor .8; analytics .45; store quality .25; vendor×analytics .2;
               quality .32; breadth .3; private-brand share −.15.
Experience: store quality 3; service 1.6; analytics .65; online .3;
            service×experience .7; analytics×experience .4; breadth .12.
Frictionless: online 3; service .65; analytics .7; vendor .6; reach 1.1;
              online×analytics .8; depth .2.
Low price: vendor .55; analytics .15; markup −.07; private-brand share .18.
Product normalization: average quality change; summed breadth/depth/private-share
changes / 100; markup = .76 × lower change + .24 × higher change.

Raw = score response × sum(weight × feature).
Score = 10 × sigmoid(logit(anchor/10) + raw / [anchor × (1−anchor/10)]).
The response is smooth, bounded, and baseline-preserving; bounds are assumed.
Exact grouped Shapley attributes all interactions across 6 levers + product inputs.
Stress envelopes vary response strength, saturation scales and channel mix;
historical max absolute score steps widen the envelope. Not confidence intervals.

Weighted gain = 35% Brand + 35% Experience + 20% Frictionless + 10% Low price.
Demand lift = demand response × weighted score gain.
For each product segment:
  Price ratio = (1 + planned markup / 100) / (1 + reference markup / 100).
  Unit ratio = max(0.1, 1 + demand lift − elasticity × (price ratio − 1)).
  Revenue = anchor segment revenue × price ratio × unit ratio.
  COGS = anchor segment COGS × unit ratio.
Net income = anchor net income + change in gross profit − change in five-field spend.

Stress bands = estimate ± estimated revenue × stress fraction.
These are stress cases, not probabilities or confidence intervals.</pre><p class="small muted">Unchanged decisions reproduce the Round-0 anchor by construction. There is no calibrated time trend. Changed product quality, assortment, private brand and store coverage have unknown implementation/inventory costs. Financing, taxes, physical capacity constraints, competitor reactions and delayed returns are not modeled. Diminishing returns are structural assumptions, not calibrated saturation curves. Full implementation: prediction.py.</p></section><div class="grid-equal"><section class="panel">${panelHead('Source materials','CSV files are read by the backend. The image values were manually transcribed.')}<ul class="file-list">${data.sources.map(s=>`<li>${esc(s)}</li>`).join('')}</ul></section><section class="panel">${panelHead('Context & data gaps','These gaps should be resolved before finalizing a plan.')}${['company','competitors'].map(key=>`<h3>${key==='company'?'Company background':'Competitor background'}</h3>${data.documents[key]?`<pre>${esc(data.documents[key])}</pre>`:`<div class="warning">materials/${key}.md is empty. No background narrative was available.</div>`}`).join('')}<p class="small muted">Need: simulator help/tooltips, true decision cost formulas, customer segment preferences, prior-round decisions/outcomes, competitor plans, and cash-flow/financing rules.</p></section></div>`;
}
function chatPage() {
  return head('YOUR LOCAL WORKSPACE GUIDE','Ask. Understand. Decide.','Explore your company’s numbers, understand the application, and challenge a plan before you commit.', '<button data-action="clear-chat">Clear chat</button>') +
    `<div class="info"><strong>Local, rule-based Q&A — not ChatGPT.</strong> No external AI calls or paid APIs. Answers cite their sources. The assistant can explain supported topics and run simple one-factor tests; it never edits or saves your working plan.</div><div class="chat-layout"><section class="panel chat-panel"><div class="chat-heading"><div class="chat-avatar">G<span>?</span></div><div><h2>Getchell’s workspace assistant</h2><p class="small muted">Grounded in your data · transparent about its limits</p></div><span class="live-dot"></span></div><div id="chat-transcript" class="chat-transcript" role="log" aria-label="Conversation" aria-live="polite" aria-busy="${chatBusy}">${chatMessages.length?chatMessages.map(m=>m.role==='user'?`<article class="chat-message user-message"><div class="message-label">YOU <span>Plan snapshot · ${esc(m.time || '')}</span></div><div class="message-text">${esc(m.text)}</div></article>`:`<article class="chat-message assistant-message"><div class="message-label">LOCAL ASSISTANT <span>${esc(m.time || '')} · answer snapshot</span></div>${m.sections.map(s=>`<section class="chat-answer-section"><span class="tag ${s.kind==='Illustrative estimate'?'amber':'green'}">${esc(s.kind || 'Explanation')}</span><h3>${esc(s.title)}</h3><div class="message-text">${esc(s.text)}</div><details class="chat-sources"><summary>Sources (${s.sources.length})</summary><ul>${s.sources.map(source=>`<li>${esc(source)}</li>`).join('')}</ul></details>${pages[s.page]?`<a class="chat-page-link" href="#${esc(s.page)}">Open ${pages[s.page]} →</a>`:''}</section>`).join('')}</article>`).join(''):`<div class="chat-welcome"><div class="eyebrow">A GOOD QUESTION IS A GOOD START</div><h2>Let’s make the workspace make sense.</h2><p>I can guide you through each page, explain financial risks, compare Kahn scores, and test a decision against the current assumptions.</p><p>Try asking: “What if online investment were $5M?” That runs a temporary sensitivity test without changing your plan.</p></div>`}${chatBusy?'<div class="chat-pending" role="status">Checking your local data and working plan…</div>':''}</div><form id="chat-form" class="chat-compose"><label class="sr-only" for="chat-question">Ask a question about the application or your data</label><textarea id="chat-question" name="question" rows="2" maxlength="2000" placeholder="Ask about the app, your financials, or a one-factor what-if…" required ${chatBusy?'disabled':''}></textarea><button class="primary" type="submit" ${chatBusy?'disabled':''}>${chatBusy?'Checking…':'Ask ↗'}</button></form><div class="chat-footnote">Enter to send · Shift+Enter for a new line · Saved in this tab’s session only</div></section><aside><section class="panel">${panelHead('Start with a question','Choose a topic, then ask in your own words.')}<div class="chat-prompts">${chatPrompts.map((text,i)=>`<button data-chat-prompt="${i}" ${chatBusy?'disabled':''}>${esc(text)} <span>↗</span></button>`).join('')}</div></section><section class="panel"><h3>Current working plan</h3><div class="budget-line"><span>Explicit spend</span><strong>${money(result.spent)}</strong></div><div class="budget-line"><span>Headroom</span><strong class="${result.feasible?'positive':'negative'}">${money(result.remaining)}</strong></div><p class="small muted">Each question uses your current decisions and assumptions. Previous answers are snapshots and do not update after plan changes.</p><a href="#decisions" class="button full">Open decision studio →</a></section><div class="warning">I can’t recover hidden simulator rules, guarantee next-round outcomes, browse the web, or answer arbitrary questions. Unsupported requests are flagged rather than guessed.</div></aside></div>`;
}
function persistChat() {
  try { sessionStorage.setItem('getchells-chat',JSON.stringify(chatMessages)); } catch { /* Optional local history. */ }
}
function scrollChat() { const log=$('#chat-transcript'); if(log)log.scrollTop=log.scrollHeight; }
async function askChat(question) {
  if(chatBusy||!question.trim())return;
  chatBusy=true;
  const time=new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  try {
    await settled();
    chatMessages.push({role:'user',text:question.trim(),time});
    chatMessages=chatMessages.slice(-39);persistChat();
    if(page==='chat'){render();scrollChat();}
    const response=await api('chat',{question:question.trim(),decisions:{...decisions},assumptions:{...assumptions},context:chatContext});
    chatContext=response.context;
    chatMessages.push({role:'assistant',sections:response.sections,context:response.context,time:new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})});
    persistChat();
  } catch(e) { notify(`Could not answer: ${e.message}. Please retry.`); }
  finally {chatBusy=false;if(page==='chat'){render();scrollChat();$('#chat-question')?.focus();}}
}
function render() {
  $('#breadcrumb').textContent=pages[page];
  $$('nav a').forEach(a=>{a.classList.toggle('active',a.dataset.page===page);if(a.dataset.page===page)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  $('#content').innerHTML=({overview,marketing:marketingPage,decisions:decisionPage,assortment:assortmentPage,positioning,financials,scenarios:scenarioPage,whatif:whatifPage,chat:chatPage,model:modelPage})[page]();
  mountMarketingContext();
  if(page==='marketing')mountMarketingDecisionEvidence();
  if(page==='assortment'&&!assortmentInitialized&&!assortmentLoading)void initializeAssortment();
  if(page==='assortment')mountAssortmentReadiness();
  if(page==='assortment'&&assortmentInitialized)Object.entries(assortmentRawInvalid).forEach(([key,value])=>{const input=$('#a4-'+key);if(input){input.value=value;input.setAttribute('aria-invalid','true');}});
  if(page==='whatif'&&!projectionOutput&&!projectionBusy&&!projectionStale)void runProjection();
  if(page==='decisions')$('.decision-layout').insertAdjacentHTML('beforebegin',kahnDetails());
  if(page==='chat')scrollChat();
}
async function refreshResult() {
  const seq=++evaluationSequence;
  const next=await api('evaluate',{decisions,assumptions});
  if(seq!==evaluationSequence) return false;
  result=next;
  return true;
}
async function settled() {
  clearTimeout(timer);
  if (invalidFields.size) throw new Error('Correct the highlighted decision values before saving or evaluating this plan.');
  if(!await refreshResult()) throw new Error('The plan changed during evaluation. Please retry.');
}
async function save(name) {
  await settled();
  await api('scenarios',{name,decisions,assumptions});
  scenarios=await api('scenarios');
  notify('Scenario saved locally with its decisions and assumptions.');
}
function exportBrief() {
  const doc={title:"Getchell's Round 1 decision brief", exported_at:new Date().toISOString(),
    status:result.feasible?'Within explicit spend budget; review unpriced changes before finalizing':'OVER BUDGET — do not finalize',
    strategy:'Protect Brand and Experience; test Frictionless selectively.',
    decisions:data.factors.map(f=>({item:f.label,value:decisions[f.key],unit:f.unit,industry_average:f.industry.average,cost_known:f.priced})),
    budget:data.budget, assumptions, illustrative_result:result, sources:data.sources,
    missing_context:Object.entries(data.documents).filter(([,v])=>!v).map(([k])=>`${k}.md is empty`)};
  const url=URL.createObjectURL(new Blob([JSON.stringify(doc,null,2)],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='getchells-decision-brief.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
document.addEventListener('input',event=>{
  const key=event.target.dataset.factor;
  if(!key)return;
  const field=event.target, f=data.factors.find(f=>f.key===key), v=field.valueAsNumber;
  clearTimeout(timer);++evaluationSequence;
  if(!Number.isFinite(v)||v<f.min||v>f.max){invalidFields.add(key);field.setAttribute('aria-invalid','true');notify(`${f.label}: enter a value between ${f.min} and ${f.max}.`);return;}
  invalidFields.delete(key);field.removeAttribute('aria-invalid');decisions[key]=v;optimization=null;
  timer=setTimeout(async()=>{
    try{
      if(await refreshResult()&&page==='decisions'){
        $('#budget-panel').innerHTML=budgetPanel();
        const expandedDetails=$$('#kahn-details > details').map(d=>d.open);
        $('#kahn-details').outerHTML=kahnDetails();
        $$('#kahn-details > details').forEach((d,i)=>d.open=expandedDetails[i]);
        $('.decision-layout > div > .warning').innerHTML=result.warnings.map(w=>`<div>• ${esc(w)}</div>`).join('');
        $$('[data-factor]').forEach(input=>{
          const factor=data.factors.find(f=>f.key===input.dataset.factor), label=input.closest('.factor-row').firstElementChild;
          label.querySelector('.danger-text')?.remove();
          if(!factor.priced&&decisions[factor.key]!==factor.baseline){
            const warning=document.createElement('small');warning.className='danger-text';warning.textContent='Changed: implementation cost unknown';label.append(warning);
          }
        });
      }
    }catch(e){notify(e.message);}
  },220);
});
document.addEventListener('submit',async event=>{
  if(event.target.id==='chat-form'){event.preventDefault();await askChat($('#chat-question').value);return;}
  if(!['save-form','assumptions-form'].includes(event.target.id))return;
  event.preventDefault();
  try{
    if(event.target.id==='save-form'){await save($('#scenario-name').value);render();}
    else{const candidate=Object.fromEntries($$('[data-assumption]').map(i=>[i.dataset.assumption,i.valueAsNumber]));const next=await api('evaluate',{decisions,assumptions:candidate});assumptions=candidate;result=next;optimization=null;render();notify('Working-plan assumptions updated.');}
  }catch(e){notify(e.message);}
});
document.addEventListener('click',async event=>{
  const button=event.target.closest('button');if(!button)return;
  const action=button.dataset.action;
  try{
    if(button.dataset.chatPrompt!==undefined){await askChat(chatPrompts[Number(button.dataset.chatPrompt)]);return;}
    if(button.dataset.load){const s=scenarios.find(s=>s.id===Number(button.dataset.load));decisions={...s.decisions};assumptions={...s.assumptions};optimization=null;invalidFields.clear();await settled();location.hash='decisions';render();notify(`Loaded “${s.name}”.`);return;}
    if(!action)return;
    button.disabled=true;
    if(action==='clear-chat'){if(chatBusy){notify('Wait for the current answer before clearing.');return;}chatMessages=[];chatContext='';persistChat();render();notify('Chat cleared from this tab.');}
    if(action==='reset'){decisions={...data.baseline};optimization=null;invalidFields.clear();await settled();render();notify('Restored the screenshot reference plan.');}
    if(action==='save-current'){const name=prompt('Name this scenario:');if(name?.trim()){await save(name.trim());}}
    if(action==='export'){await settled();exportBrief();notify('Decision brief downloaded, including assumptions and caveats.');}
    if(action==='optimize'){await settled();optimization=await api('optimize',{decisions,assumptions,goal:$('#goal').value,locked:$$('[data-lock]:checked').map(i=>i.value)});render();notify('Search complete. Candidate is not automatically applied.');}
    if(action==='adopt'){decisions={...optimization.result.decisions};optimization=null;await settled();render();notify('Candidate adopted as working plan. Save it to keep a copy.');}
    if(action==='reset-assumptions'){assumptions={...data.assumptions};optimization=null;await settled();render();notify('Default assumptions restored.');}
  }catch(e){notify(e.message);}finally{button.disabled=false;}
});
document.addEventListener('keydown',event=>{
  if(event.target.id==='chat-question'&&event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!chatBusy)$('#chat-form').requestSubmit();}
});
window.addEventListener('hashchange',async()=>{
  page=pages[location.hash.slice(1)]?location.hash.slice(1):'overview';
  if(!data)return;
  if(invalidFields.size){invalidFields.clear();notify('Invalid entries discarded; the last valid decision values were retained.');}
  try{await settled();render();}catch(e){notify(e.message);}
});
async function init(){
  try{[data,scenarios]=await Promise.all([api('data'),api('scenarios')]);decisions={...data.baseline};assumptions={...data.assumptions};await settled();page=pages[location.hash.slice(1)]?location.hash.slice(1):'overview';render();}
  catch(e){$('#content').innerHTML=`<div class="error-box"><h2>Couldn’t load the workspace</h2><p>${esc(e.message)}</p><p>Check that the Python backend is running and the source CSV files are present.</p><button onclick="location.reload()">Retry</button></div>`;}
}
init();
