'use strict';
// Standalone harness: reuses the shared Marketing Intelligence page and charts
// without the rest of the application. Concatenated after marketing_charts.js
// and marketing.js, so their functions are already declared.
const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const money = (value, compact = true) => `${value < 0 ? '−' : ''}$${compact ? (Math.abs(value) / 1e6).toFixed(2) + 'M' : Math.abs(value).toLocaleString('en-US', {maximumFractionDigits:0})}`;
const pct = value => (value * 100).toFixed(1) + '%';
function head(eyebrow, title, subtitle, actions = '') { return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p class="subtitle">${subtitle}</p></div><div class="actions">${actions}</div></div>`; }
function card(label, value, foot, cls = '', badge = '') { return `<div class="card"><div class="card-label">${label}${badge}</div><div class="card-value ${cls}">${value}</div><div class="card-foot">${foot}</div></div>`; }
function panelHead(title, description, badge = '') { return `<div class="panel-heading"><div><h2>${title}</h2><p>${description}</p></div>${badge}</div>`; }
function tag(text, color = '') { return `<span class="tag ${color}">${text}</span>`; }
let data, page = 'marketing';
function render() {
  const content = document.getElementById('content');
  if (!content) return;
  content.innerHTML = marketingPage();
  mountMarketingDecisionEvidence();
  const share = document.getElementById('marketing-share-link');
  if (share) share.remove();
}
function boot() {
  try {
    data = JSON.parse(document.getElementById('marketing-data').textContent);
    if (!data.marketing?.available) throw new Error(data.marketing?.message || 'Marketing data is unavailable in this file.');
    const meta = document.getElementById('report-meta');
    if (meta) meta.textContent = `Generated ${new Date(data.generated_at).toLocaleString()} · ${data.marketing.segments.length} segments · ${data.marketing.companies.length} competitors`;
    render();
    document.getElementById('marketing-print')?.addEventListener('click', () => window.print());
  } catch (error) {
    const content = document.getElementById('content');
    if (content) content.innerHTML = `<div class="error-box"><h2>Couldn’t open this report</h2><p>${esc(error.message)}</p><p>The shared file embeds its own data; ask the sender to regenerate it from the Decision Lab.</p></div>`;
  }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
