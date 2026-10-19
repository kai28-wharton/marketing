'use strict';
// Independent drafts: opening this page never changes the Decision studio plan.
let projectionPlan=null, projectionAssumptions=null, projectionSettings={market_growth:0,cogs_inflation:0,year1_realization:1,year2_catchup:.5};
let projectionOutput=null, projectionBusy=false, projectionStale=false, projectionName='Controlled service + convenience test';
const projectionKeys=['online','service','experience','vendor','analytics','coverage','national_quality'];
function initializeProjection() {
  if(!projectionPlan)projectionPlan={...data.baseline,online:2500000,service:15300000,experience:10200000};
  if(!projectionAssumptions)projectionAssumptions={...assumptions};
}
function projectionField(f) {
  return `<div class="factor-row"><div><label for="w-${f.key}">${esc(f.label)}</label><small>Industry avg ${displayFactor(f.industry.average,f)} · ${f.priced?'explicit spending':'implementation cost unknown'}</small></div><div class="input-wrap"><input id="w-${f.key}" data-projection-factor="${f.key}" type="number" value="${projectionPlan[f.key]}" min="${f.min}" max="${f.max}" step="any" required><span class="input-unit">${f.unit==='$'?'USD':f.unit==='index'?'':f.unit}</span></div></div>`;
}
function whatifPage() {
  initializeProjection();
  return head('PLAN BEYOND THE NEXT ROUND','What-if scenarios & Year 2','Test the controlled investment example, challenge a brand-quality assumption, or build your own two-period plan.','<button class="primary" data-projection-action="html" '+(!projectionOutput||projectionStale?'disabled':'')+'>↓ Shareable HTML report</button><button data-projection-action="export" '+(!projectionOutput||projectionStale?'disabled':'')+'>↓ Export JSON</button>')+
    `<div class="info"><strong>Period convention:</strong> Round 0 is observed. Year 1 means Round 1; Year 2 means Round 2—not a verified calendar-year duration. The same nominal decision plan repeats in both projected periods. These are assumption-based projections, not validated forecasts.</div><form id="projection-form"><div class="grid-equal"><section class="panel">${panelHead('Choose and edit a test plan','This draft is separate from Decision studio.')}<fieldset ${projectionBusy?'disabled':''} style="border:0;padding:0;margin:0;min-width:0"><label for="projection-preset" class="small">Load an example</label><select id="projection-preset" style="margin:8px 0 12px"><option value="" selected>${esc(projectionName)}</option><option value="controlled">Controlled test — $68M explicit spend</option><option value="reference">Original screenshot plan — $67M</option><option value="brand">Conditional brand-quality test — unknown quality cost</option></select><button type="button" data-projection-action="copy-working">Copy current studio plan & assumptions</button>${projectionKeys.map(key=>projectionField(data.factors.find(f=>f.key===key))).join('')}<details style="margin-top:18px"><summary>Other decision inputs (editable)</summary>${data.factors.filter(f=>!projectionKeys.includes(f.key)).map(projectionField).join('')}</details></fieldset></section><section class="panel">${panelHead('Two-period assumptions','Defaults isolate the decision change; no automatic market growth.')}<fieldset ${projectionBusy?'disabled':''} style="border:0;padding:0;margin:0;min-width:0">${[['market_growth','Annual market/unit-demand growth','Compounds from Round 0. Zero means no external market growth.',-20,20],['cogs_inflation','Annual cost-per-unit inflation','Compounds segment COGS per unit; no automatic price increase.',-10,30],['year1_realization','Year 1 benefit realization','Share of the total modeled Kahn change realized in Year 1. Spending is incurred in full.',0,100],['year2_catchup','Year 2 remaining-benefit catch-up','Share of the unrealized Kahn change captured in Year 2. No repeated score bonus if Year 1 is already 100%.',0,100]].map(([key,label,description,min,max])=>`<div class="model-assumption"><div><label for="p-${key}"><strong>${label}</strong></label><p>${description}</p></div><div class="input-wrap"><input id="p-${key}" data-projection-setting="${key}" type="number" min="${min}" max="${max}" step="any" value="${projectionSettings[key]*100}" required><span class="input-unit">%</span></div></div>`).join('')}<div class="info">Model assumptions copied into this draft: response ${projectionAssumptions.score_response}, demand ${pct(projectionAssumptions.demand_response)}, elasticity ${projectionAssumptions.price_elasticity}, revenue stress ±${pct(projectionAssumptions.uncertainty)}. Use “Copy current studio plan & assumptions” to refresh them after changing the model settings.</div><div class="warning">The brand-quality example is conditional: national quality 5 → 6 has an unknown implementation cost. Apparent budget headroom does not establish affordability. Service spending above $15M exceeds the observed industry maximum; the simulator’s actual cap is unverified.</div><button type="submit" class="primary full">${projectionBusy?'Calculating…':'Run Year 1 & Year 2 projection ↗'}</button></fieldset><p id="projection-draft-status" class="small ${projectionStale?'negative':'muted'}" role="status">${projectionStale?'Inputs changed. Run again to update the results below.':projectionOutput?'Results reflect the last submitted draft.':'Preparing the controlled-test example…'}</p><p class="small muted">No external AI calls. All calculations use your local data and Kahn model v2.</p></section></div></form><div id="projection-results">${projectionOutput?projectionReport():''}</div>`;
}
function projectionReport() {
  const output=projectionOutput, working=output.working, periods=working.periods, year2=periods[2];
  const metrics=[['Revenue','revenue',money],['Cost of goods sold','cogs',money],['Gross profit','gross_profit',money],['Gross margin','gross_margin',pct],['Operating expenses','operating_expenses',money],['EBIT','ebit',money],['Interest expense','interest',money],['Income taxes (projected: assumed zero)','taxes',money],['Net income','net_income',money],['Return on sales','return_on_sales',pct],['Explicit decision spending','explicit_spend',money],['Explicit budget remaining','remaining',money]];
  const alternatives=[{name:'Your submitted draft',...working},...output.comparisons];
  return `<div class="cards">${card('YEAR 2 REVENUE',money(year2.revenue),'Illustrative · '+esc(working.model_version))}${card('YEAR 2 NET INCOME',money(year2.net_income),'Includes recurring spending changes',year2.net_income<0?'negative':'positive')}${card('YEAR 2 EXPLICIT HEADROOM',money(year2.remaining),working.unpriced_changes.length?'Unpriced changes: total cost unknown':'Same nominal decision budget each period',year2.feasible?'positive':'negative')}${card('TWO-PERIOD NET INCOME',money(working.cumulative_projected_net_income),'Year 1 + Year 2; not a cash balance',working.cumulative_projected_net_income<0?'negative':'positive')}</div>${!year2.feasible?'<div class="error-box">OVER BUDGET: this draft exceeds the known annual spending limit.</div>':''}<section class="panel">${panelHead('Financial projection','Actual → next round → following round',tag('ILLUSTRATIVE','amber'))}<div class="table-wrap"><table><thead><tr><th>Metric</th>${periods.map(p=>`<th>${esc(p.period)}</th>`).join('')}</tr></thead><tbody>${metrics.map(([label,key,format])=>`<tr class="${['net_income','revenue'].includes(key)?'highlight-row':''}"><td>${label}</td>${periods.map(p=>`<td class="number ${p[key]<0?'negative':''}">${p[key]===null?'Not supplied':format(p[key])}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="small muted">Year 2 revenue stress: ${money(year2.revenue_range[0])}–${money(year2.revenue_range[1])}; net-income stress: ${money(year2.profit_range[0])}–${money(year2.profit_range[1])}. User-set stresses, not statistical confidence intervals.</p></section><section class="panel">${panelHead('Kahn positioning over two periods','Scores move toward one target; unchanged decisions do not create repeated improvements.')}<div class="table-wrap"><table><thead><tr><th>Quadrant</th><th>Round 0 actual</th><th>Year 1 estimate</th><th>Year 2 estimate</th><th>Year 2 structural stress</th></tr></thead><tbody>${Object.entries(qNames).map(([key,label])=>`<tr><td>${label}</td><td>${periods[0].scores[key].toFixed(3)}</td><td>${periods[1].scores[key].toFixed(3)}</td><td><strong>${year2.scores[key].toFixed(3)}</strong></td><td>${year2.score_ranges[key].map(v=>v.toFixed(3)).join('–')}</td></tr>`).join('')}</tbody></table></div><p class="small muted">Benefit realization: Year 1 ${pct(periods[1].realization)}; Year 2 ${pct(year2.realization)} of total modeled change. Bounds and response speeds are assumptions; stress ranges are not calibrated prediction intervals.</p></section><section class="panel">${panelHead('Compare the original recommendation and alternatives','All rows use this draft’s same model and two-period assumptions.')}<div class="table-wrap"><table><thead><tr><th>Plan</th><th>Annual explicit spend</th><th>Year 2 revenue</th><th>Year 2 net income</th><th>Brand</th><th>Experience</th><th>Frictionless</th><th>Cost check</th></tr></thead><tbody>${alternatives.map(s=>{const p=s.periods[2];return `<tr><td>${esc(s.name)}</td><td>${money(p.explicit_spend)}</td><td>${money(p.revenue)}</td><td class="${p.net_income<0?'negative':''}">${money(p.net_income)}</td><td>${p.scores.BRAND.toFixed(3)}</td><td>${p.scores.EXPERIENCE.toFixed(3)}</td><td>${p.scores.FRICTIONLESS.toFixed(3)}</td><td>${tag(s.feasible?'KNOWN SPEND OK':'OVER BUDGET',s.feasible?'green':'red')}${s.unpriced_changes.length?' '+tag('UNKNOWN COSTS','amber'):''}</td></tr>`;}).join('')}</tbody></table></div></section><section class="panel">${panelHead('Before you use these numbers','Understand the accounting and modeling limits.')}<div class="warning">${working.warnings.map(w=>`<div>• ${esc(w)}</div>`).join('')}</div><details><summary>Full projection methodology</summary><ol>${output.methodology.map(text=>`<li>${esc(text)}</li>`).join('')}</ol></details><div class="actions" style="margin-top:20px"><button data-projection-action="export" ${projectionStale?'disabled':''}>↓ Export full projection</button><button data-projection-action="adopt" ${projectionStale?'disabled':''}>Copy submitted decisions to studio →</button></div><p class="small muted">Copying transfers decisions and model assumptions only. Year-2 market growth, cost inflation and benefit timing remain in this tab; Decision studio still displays its full-response sensitivity estimate. This is not final submission to the simulator.</p></section>`;
}
function markProjectionStale() {
  projectionStale=true;
  const status=$('#projection-draft-status');if(status){status.textContent='Inputs changed. Run again to update the results below.';status.className='small negative';}
  $$('[data-projection-action="export"],[data-projection-action="html"],[data-projection-action="adopt"]').forEach(b=>b.disabled=true);
}
async function runProjection(readForm=false) {
  if(projectionBusy)return;
  try {
    if(readForm){
      if(!$('#projection-form').reportValidity())return;
      projectionPlan=Object.fromEntries($$('[data-projection-factor]').map(f=>[f.dataset.projectionFactor,f.valueAsNumber]));
      projectionSettings=Object.fromEntries($$('[data-projection-setting]').map(f=>[f.dataset.projectionSetting,f.valueAsNumber/100]));
      projectionName='Custom draft';
    }
    projectionBusy=true;if(page==='whatif')render();
    projectionOutput=await api('project',{decisions:projectionPlan,assumptions:projectionAssumptions,planning:projectionSettings});
    projectionStale=false;
  } catch(e){projectionStale=true;notify('Projection failed: '+e.message);}
  finally {projectionBusy=false;if(page==='whatif')render();}
}
document.addEventListener('submit',event=>{if(event.target.id==='projection-form'){event.preventDefault();void runProjection(true);}});
document.addEventListener('input',event=>{
  const field=event.target;
  if(!field.matches('[data-projection-factor],[data-projection-setting]'))return;
  // Preserve valid draft edits when navigating away before running a projection.
  if(field.validity.valid&&Number.isFinite(field.valueAsNumber)){
    if(field.dataset.projectionFactor)projectionPlan[field.dataset.projectionFactor]=field.valueAsNumber;
    else projectionSettings[field.dataset.projectionSetting]=field.valueAsNumber/100;
  }
  markProjectionStale();
});
document.addEventListener('change',event=>{
  if(event.target.id!=='projection-preset'||!event.target.value)return;
  const key=event.target.value;
  projectionPlan={...data.baseline};
  if(key!=='reference')Object.assign(projectionPlan,{online:2500000,service:15300000,experience:10200000});
  if(key==='brand')projectionPlan.national_quality=6;
  projectionName={reference:'Original screenshot plan',controlled:'Controlled service + convenience test',brand:'Conditional brand-quality test — unpriced'}[key];
  projectionStale=true;render();
});
document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-projection-action]');if(!button||projectionBusy)return;
  const action=button.dataset.projectionAction;
  try{
    if(action==='copy-working'){projectionPlan={...decisions};projectionAssumptions={...assumptions};projectionName='Copied Decision studio plan';projectionStale=true;render();return;}
    if(projectionStale||!projectionOutput){notify('Run the projection before exporting or copying submitted decisions.');return;}
    if(action==='html'){
      button.disabled=true;
      try {
        const working=projectionOutput.working;
        const report=await api('report',{decisions:working.decisions,assumptions:working.assumptions,planning:working.planning});
        const url=URL.createObjectURL(new Blob([report.html],{type:'text/html;charset=utf-8'}));
        const link=document.createElement('a');link.href=url;link.download=report.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
        notify('Self-contained HTML report downloaded. Your team can open it without the app.');
      } finally {button.disabled=projectionStale;}
    }
    if(action==='export'){
      const blob=new Blob([JSON.stringify({title:'Getchell’s Year 1 & Year 2 what-if projection',exported_at:new Date().toISOString(),...projectionOutput,sources:data.sources},null,2)],{type:'application/json'});
      const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='getchells-year2-projection.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify('Projection exported with decisions, assumptions, comparisons and warnings.');
    }
    if(action==='adopt'){decisions={...projectionOutput.working.decisions};assumptions={...projectionOutput.working.assumptions};optimization=null;invalidFields.clear();await settled();location.hash='decisions';notify('Copied decisions to studio. Year-2 planning assumptions remain separate.');}
  }catch(e){notify(e.message);}
});
