'use strict';
const assortmentKeys=['low_breadth','low_depth','high_breadth','high_depth'];
let assortmentInitialized=false,assortmentLoading=false,assortmentTeam=null,assortmentBaseline=null,assortmentAssumptions=null;
let assortmentChanges={},assortmentReport=null,assortmentStale=true,assortmentPending=false,assortmentSequence=0,assortmentTimer;
let assortmentSource='',assortmentChoosing=false;
const assortmentInvalid=new Set();
let assortmentRawInvalid={};
function mountAssortmentReadiness() {
  if(page!=='assortment')return;
  let root=$('#assortment-readiness');
  if(!root){$('#content').insertAdjacentHTML('beforeend','<div id="assortment-readiness"></div>');root=$('#assortment-readiness');}
  const readiness=assortmentReport?.readiness||data.assortment_readiness;
  let recommendation=$('#assortment-recommendation');
  if(!recommendation){$('.page-head').insertAdjacentHTML('afterend','<div id="assortment-recommendation"></div>');recommendation=$('#assortment-recommendation');}
  recommendation.innerHTML=renderAssortmentRecommendation(readiness,assortmentBaseline);
  if(assortmentReport&&data.marketing?.available&&!$('#segment-alignment')){
    $('#assortment-results > section')?.insertAdjacentHTML('afterend',renderSegmentAlignment(data.marketing,assortmentBaseline,assortmentReport.candidate.decisions,assortmentReport.segment_alignment));
  }
  const warnings=[...(assortmentReport?.candidate.warnings||[])];
  if(assortmentReport?.outside_industry_range.length)warnings.push('Outside observed industry ranges: '+assortmentReport.outside_industry_range.join(', ')+'. Effects are unvalidated extrapolations; those ranges are not verified simulator limits.');
  root.innerHTML=renderAssortmentReadiness(readiness,assortmentReport?.limitations||readiness.limitations,warnings,{control_selector:'.assortment-controls'});
  // Consolidate the old results disclosure into the complete end-of-page block.
  const old=[...document.querySelectorAll('#assortment-results > section')].find(s=>s.querySelector('h2')?.textContent.startsWith('What this engine can'));
  old?.remove();
  $('#assortment-results > .warning')?.remove();
}
function assortmentExplanation() {
  return `<section class="panel assortment-textbook">${panelHead('Breadth vs depth — the textbook explanation','Conventional retail terminology; exact simulation meanings still require the simulator help text.')}<div class="grid-equal"><div><h3>Breadth = how many different product lines or categories?</h3><p>A broad assortment covers more different needs. A grocery store with groceries, home goods and personal care is broader than a specialist selling only coffee. More breadth can attract more shopping missions, but can dilute positioning and create complexity.</p><h3>Depth = how much choice within a product line?</h3><p>A deep coffee assortment offers more brands, roast types, sizes and formats within coffee. Depth is <strong>not automatically stock units per SKU</strong>. It can improve fit and availability, but may increase choice overload, slow-moving inventory and markdown risk depending on stocking policy.</p></div><div><h3>How to interpret your four settings</h3><ul><li><strong>Lower-cost breadth:</strong> variety across lower-cost product lines.</li><li><strong>Lower-cost depth:</strong> choice within those lower-cost lines.</li><li><strong>Higher-cost breadth:</strong> variety across higher-cost product lines.</li><li><strong>Higher-cost depth:</strong> choice within those higher-cost lines.</li></ul><p>The supplied screenshot uses a <strong>1–100 index</strong>. It does not establish percentages or actual category/SKU counts. A setting of 65 does not mean 65% of the budget, 65 categories, or 65 SKUs. The four values do <strong>not</strong> have to add to 100; multiplying breadth by depth does not reveal SKU count.</p></div></div><details><summary>Expected strategic trade-offs vs what this model actually calculates</summary><p>In retail theory, broader assortments can support one-stop convenience and a broader proposition; deeper assortments can support specialist authority and customer fit. Too much of either may hurt discovery, service or inventory economics. Those effects are not guaranteed or identified from the supplied files.</p><p>In our existing Kahn v2 engine, breadth increases modeled Brand and Experience; depth increases modeled Frictionless; these four settings do not directly change Low price while markups stay fixed. Both product segments currently have the same per-index coefficients. Segment-specific assortment preferences, costs, cannibalization, inventory and choice-overload effects are not calibrated.</p></details></section>`;
}
function assortmentPage() {
  if(!assortmentInitialized)return head('FOUR DECISIONS. ONE LOCKED PLAN.','Assortment Lab','Understand breadth and depth without changing the rest of your team’s decisions.')+assortmentExplanation()+`<section class="panel"><p>${assortmentLoading?'Reading the team workbook…':'Ready to load your team draft.'}</p>${!assortmentLoading?'<button data-assortment-action="retry">Load team plan</button>':''}</section>`;
  const factors=data.factors.filter(f=>assortmentKeys.includes(f.key));
  return head('FOUR DECISIONS. ONE LOCKED PLAN.','Assortment Lab','Only breadth and depth are editable. Every comparison holds the other 12 decisions and all model assumptions fixed.','<button data-assortment-action="learn">Breadth & depth explained</button><button class="primary" data-assortment-action="offline" '+(assortmentStale?'disabled':'')+'>↓ Download offline lab</button><button data-assortment-action="export" '+(assortmentStale?'disabled':'')+'>↓ Export comparison</button>')+
    `<div class="info"><strong>Locked baseline:</strong> ${esc(assortmentSource)}. ${assortmentTeam?.available&&assortmentSource.includes('team workbook')?'The workbook’s Column B is labeled “'+esc(assortmentTeam.column_label)+'”; we treat it as your team’s planning draft, not as verified outcomes.':''} This page does not change Decision studio or the Excel file.</div><div class="assortment-layout"><div><section class="panel assortment-controls">${panelHead('Adjust only these four settings','1–100 indices · not verified percentages')}<div class="actions"><button data-assortment-action="reset">Reset four to locked baseline</button><button data-assortment-action="industry">Try industry averages</button></div>${factors.map(f=>`<div class="assortment-control"><label for="a4-${f.key}">${esc(f.label)}</label><div class="assortment-input-line"><input id="a4-${f.key}" aria-label="${esc(f.label)}" data-assortment-key="${f.key}" type="number" min="1" max="100" step="any" value="${assortmentChanges[f.key]}"><span>index / 100</span></div><input type="range" aria-label="${esc(f.label)} slider" data-assortment-key="${f.key}" min="1" max="100" step="1" value="${assortmentChanges[f.key]}"><small>Locked baseline ${assortmentBaseline[f.key]} · industry average ${f.industry.average}<br>Observed range ${f.industry.minimum}–${f.industry.maximum} (not a required target)</small></div>`).join('')}<div class="actions"><button data-assortment-action="save" class="primary" ${assortmentStale?'disabled':''}>Save this alternative</button><button data-assortment-action="choose">Replace locked plan…</button></div>${assortmentChoosing?`<div class="info"><label for="assortment-source">Choose the approved full plan to freeze</label><select id="assortment-source">${assortmentTeam?.available?'<option value="team">Team workbook · Column B</option>':''}<option value="studio">Current Decision studio plan</option>${scenarios.map(s=>`<option value="saved:${s.id}">Saved: ${esc(s.name)}</option>`).join('')}</select><button data-assortment-action="lock" style="margin-top:10px">Lock this full plan</button><p>Replacing the baseline resets the four settings. Other decisions cannot be edited here.</p></div>`:''}</section><section class="panel">${panelHead('The other 12 decisions are frozen','Review the exact team inputs used in every calculation.')}<div class="table-wrap"><table><thead><tr><th>Locked input</th><th>Value</th></tr></thead><tbody>${data.factors.filter(f=>!assortmentKeys.includes(f.key)).map(f=>`<tr><td>${esc(f.label)}</td><td><strong>${displayFactor(assortmentBaseline[f.key],f)}</strong></td></tr>`).join('')}</tbody></table></div><details><summary>Frozen model assumptions</summary><p>Score response ${assortmentAssumptions.score_response}; demand response ${pct(assortmentAssumptions.demand_response)}; price elasticity ${assortmentAssumptions.price_elasticity}; revenue stress ±${pct(assortmentAssumptions.uncertainty)}. To change these, update the studio/model settings and explicitly replace the locked plan.</p></details></section></div><div><div id="assortment-status" class="${assortmentStale?'warning':'info'}" role="status">${assortmentStatus()}</div><div id="assortment-results">${assortmentReport?assortmentResults():'<section class="panel"><p>Calculating the locked-plan comparison…</p></section>'}</div></div></div><div id="assortment-learning">${assortmentExplanation()}</div>`;
}
function assortmentStatus() {
  if(assortmentInvalid.size)return 'Enter a valid index between 1 and 100 in every field. Results below belong to the last valid calculation.';
  if(assortmentPending)return 'Updating the four-input comparison… Previous results are not current until this completes.';
  if(assortmentStale)return 'Settings changed. Comparison is not current yet; save/export is disabled.';
  return `Comparison up to date · locked-plan fingerprint ${assortmentReport?.baseline_fingerprint||''} · the other 12 inputs are unchanged.`;
}
function assortmentResults() {
  const r=assortmentReport,b=r.baseline,c=r.candidate,bm=r.baseline_financial,cm=r.candidate_financial;
  const sign=(value,percentage=false)=>`<span class="${value<0?'negative':'positive'}">${percentage?`${value>=0?'+':''}${(value*100).toFixed(3)} pp`:delta(value)}</span>`;
  return `<div class="warning"><strong>Profit and demand estimates exclude unknown assortment costs.</strong> The five-field investment total stays fixed when you move these settings; that does not make changes free, profitable or affordable. There is no calibrated SKU/inventory cost formula.</div><section class="panel">${panelHead('Kahn positioning: locked plan vs test','These are both modeled outcomes, not observed team results.')}<div class="table-wrap"><table><thead><tr><th>Quadrant</th><th>Locked plan</th><th>Your four-input test</th><th>Change</th></tr></thead><tbody>${Object.entries(qNames).map(([q,label])=>`<tr><td>${label}</td><td>${b.scores[q].toFixed(4)}</td><td><strong>${c.scores[q].toFixed(4)}</strong></td><td class="${r.score_changes[q]<0?'negative':'positive'}">${pointDelta(r.score_changes[q])}</td></tr>`).join('')}</tbody></table></div><details><summary>Observed Round 0 and structural stress ranges</summary><p>Round 0 is the company-wide anchor, not the outcome of this locked team plan. Ranges are structural stresses, not confidence intervals.</p><div class="table-wrap"><table><thead><tr><th>Quadrant</th><th>Observed Round 0</th><th>Test stress envelope</th></tr></thead><tbody>${Object.keys(qNames).map(q=>`<tr><td>${qNames[q]}</td><td>${observedScores()[q].toFixed(3)}</td><td>${c.kahn.intervals[q].map(v=>v.toFixed(3)).join('–')}</td></tr>`).join('')}</tbody></table></div></details></section><section class="panel">${panelHead('Financial impact before unknown assortment costs','Volume-related COGS is modeled; incremental assortment and inventory costs are not.')}<div class="table-wrap"><table><thead><tr><th>Metric</th><th>Locked plan</th><th>Test</th><th>Change</th></tr></thead><tbody>${[['Net revenue','revenue'],['Volume-related COGS','cogs'],['Gross profit','gross_profit'],['Gross margin','gross_margin'],['Net income before unknown assortment costs','net_income'],['Known investment spending','explicit_spend'],['Known budget headroom','remaining']].map(([label,key])=>`<tr class="${key==='net_income'?'highlight-row':''}"><td>${label}</td><td>${key==='gross_margin'?pct(bm[key]):money(bm[key])}</td><td class="${cm[key]<0?'negative':''}">${key==='gross_margin'?pct(cm[key]):money(cm[key])}</td><td>${sign(r.financial_changes[key],key==='gross_margin')}</td></tr>`).join('')}</tbody></table></div><p class="small muted">${r.financial_changes.net_income>0?`The test’s modeled profit uplift is ${money(r.financial_changes.net_income,false)}. Any extra recurring assortment cost above that would eliminate the modeled advantage over the locked plan—not necessarily make the business profitable. Inventory cash requirements are additional and unknown.`:'There is no positive modeled profit uplift available to absorb extra assortment costs in this test.'}</p>${!c.feasible?'<div class="warning">Your locked team plan already exceeds the five-field spending budget. Adjusting breadth/depth cannot fix that known spending overrun.</div>':''}<details><summary>Revenue and COGS by product segment</summary><p>The current model applies a company-wide demand response to both segments. Changing lower-cost breadth alone does not imply only lower-cost revenue changes.</p><div class="table-wrap"><table><thead><tr><th>Segment</th><th>Metric</th><th>Locked plan</th><th>Test</th></tr></thead><tbody>${['low','high'].map(segment=>['revenue','cogs','gross_profit'].map(metric=>`<tr><td>${segment==='low'?'Lower-cost':'Higher-cost'}</td><td>${metric.replaceAll('_',' ')}</td><td>${money(r.segments.baseline[segment][metric])}</td><td>${money(r.segments.candidate[segment][metric])}</td></tr>`).join('')).join('')}</tbody></table></div></details></section><section class="panel">${panelHead('Which setting caused the modeled change?','Exact four-input attribution, including score-bound and financial interactions.')}<div class="table-wrap"><table><thead><tr><th>Input</th>${Object.values(qNames).map(n=>`<th>Δ ${n}</th>`).join('')}<th>Δ Revenue</th><th>Δ Profit*</th></tr></thead><tbody>${r.attribution.map(row=>`<tr><td>${esc(data.factors.find(f=>f.key===row.key).label)}</td>${Object.keys(qNames).map(q=>`<td>${pointDelta(row.scores[q])}</td>`).join('')}<td>${delta(row.financial.revenue)}</td><td>${delta(row.financial.net_income)}</td></tr>`).join('')}</tbody></table></div><p class="small muted">Columns reconcile to the total modeled difference before display rounding. *Profit excludes unknown assortment costs. Attribution explains this model, not real-world causation.</p><details><summary>What if I add/remove 10 index points to just one setting?</summary><div class="table-wrap"><table><thead><tr><th>Single-setting probe</th><th>Δ Brand</th><th>Δ Experience</th><th>Δ Frictionless</th><th>Δ Profit*</th></tr></thead><tbody>${r.sensitivities.map(row=>['increase','decrease'].map(direction=>row[direction]?`<tr><td>${esc(data.factors.find(f=>f.key===row.key).label)} ${direction==='increase'?'+':'−'}10</td>${['BRAND','EXPERIENCE','FRICTIONLESS'].map(q=>`<td>${pointDelta(row[direction].scores[q])}</td>`).join('')}<td>${delta(row[direction].net_income)}</td></tr>`:'').join('')).join('')}</tbody></table></div></details></section><section class="panel">${panelHead('What this engine can—and cannot—tell you','Uncalibrated model · '+esc(c.model_version))}<ul class="assortment-limitations">${r.limitations.map(text=>`<li>${esc(text)}</li>`).join('')}</ul>${r.outside_industry_range.length?`<div class="warning">Outside observed industry ranges: ${r.outside_industry_range.map(esc).join(', ')}. These effects are unvalidated extrapolations, not evidence that the input is prohibited.</div>`:''}<details><summary>Full plan warnings</summary><ul>${c.warnings.map(w=>`<li>${esc(w)}</li>`).join('')}</ul></details></section>`;
}
function lockAssortment(plan,modelAssumptions,source) {
  ++assortmentSequence;clearTimeout(assortmentTimer);assortmentInvalid.clear();assortmentRawInvalid={};
  assortmentBaseline=Object.freeze({...plan});assortmentAssumptions=Object.freeze({...modelAssumptions});
  assortmentChanges=Object.fromEntries(assortmentKeys.map(k=>[k,plan[k]]));
  assortmentSource=source;assortmentChoosing=false;assortmentReport=null;assortmentStale=true;assortmentPending=false;
}
async function initializeAssortment() {
  if(assortmentLoading)return;
  assortmentLoading=true;
  try {
    try {assortmentTeam=await api('assortment/team');}catch(e){assortmentTeam={available:false};notify('Team workbook could not be loaded: '+e.message);}
    if(assortmentTeam.available)lockAssortment(assortmentTeam.decisions,assortmentTeam.assumptions,'team workbook · decision_making_team11_0.xlsx · Column B');
    else lockAssortment(decisions,assumptions,'current Decision studio snapshot (verify your team’s approved values)');
    assortmentInitialized=true;if(page==='assortment')render();
    await computeAssortment();
  } finally {assortmentLoading=false;if(page==='assortment'&&!assortmentInitialized)render();}
}
function updateAssortmentStatus() {
  const status=$('#assortment-status');if(status){status.textContent=assortmentStatus();status.className=assortmentStale?'warning':'info';}
  $$('[data-assortment-action="save"],[data-assortment-action="export"],[data-assortment-action="offline"]').forEach(b=>b.disabled=assortmentStale);
}
async function computeAssortment() {
  if(assortmentInvalid.size)return;
  const seq=++assortmentSequence;assortmentPending=true;assortmentStale=true;updateAssortmentStatus();
  try {
    const response=await api('assortment',{baseline:assortmentBaseline,changes:{...assortmentChanges},assumptions:assortmentAssumptions});
    if(seq!==assortmentSequence)return;
    assortmentReport=response;assortmentStale=false;
    if(page==='assortment'){
      const expanded=$$('#assortment-results details').map(d=>d.open);
      $('#assortment-results').innerHTML=assortmentResults();
      $$('#assortment-results details').forEach((d,i)=>d.open=expanded[i]||false);
      mountAssortmentReadiness();
    }
  } catch(e){if(seq===assortmentSequence)notify('Assortment comparison failed: '+e.message);}
  finally {if(seq===assortmentSequence){assortmentPending=false;updateAssortmentStatus();}}
}
document.addEventListener('input',event=>{
  const field=event.target,key=field.dataset.assortmentKey;if(!key)return;
  clearTimeout(assortmentTimer);++assortmentSequence;assortmentStale=true;assortmentPending=false;
  const value=field.valueAsNumber;
  if(!Number.isFinite(value)||value<1||value>100){assortmentInvalid.add(key);assortmentRawInvalid[key]=field.value;field.setAttribute('aria-invalid','true');updateAssortmentStatus();return;}
  assortmentInvalid.delete(key);delete assortmentRawInvalid[key];assortmentChanges[key]=value;
  $$('[data-assortment-key="'+key+'"]').forEach(input=>{input.value=value;input.removeAttribute('aria-invalid');});
  updateAssortmentStatus();assortmentTimer=setTimeout(()=>void computeAssortment(),180);
});
document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-assortment-action]');if(!button)return;
  const action=button.dataset.assortmentAction;
  try {
    if(action==='retry'){await initializeAssortment();return;}
    if(action==='learn'){$('#assortment-learning').scrollIntoView({behavior:'smooth'});return;}
    if(action==='choose'){assortmentChoosing=!assortmentChoosing;render();return;}
    if(action==='lock'){
      const source=$('#assortment-source').value;
      if(source==='team')lockAssortment(assortmentTeam.decisions,assortmentTeam.assumptions,'team workbook · decision_making_team11_0.xlsx · Column B');
      else if(source==='studio')lockAssortment(decisions,assumptions,'current Decision studio snapshot');
      else {const scenario=scenarios.find(s=>s.id===Number(source.split(':')[1]));if(!scenario)throw new Error('Saved scenario not found.');lockAssortment(scenario.decisions,scenario.assumptions,'saved scenario · '+scenario.name);}
      render();await computeAssortment();return;
    }
    if(action==='reset'||action==='industry'){
      clearTimeout(assortmentTimer);++assortmentSequence;assortmentInvalid.clear();assortmentRawInvalid={};
      assortmentChanges=Object.fromEntries(assortmentKeys.map(k=>[k,action==='reset'?assortmentBaseline[k]:data.factors.find(f=>f.key===k).industry.average]));
      assortmentStale=true;render();await computeAssortment();return;
    }
    if(assortmentStale)throw new Error('Wait for a valid, current four-input comparison before saving or exporting.');
    if(action==='offline'){
      button.disabled=true;
      try {
        const bundle=await api('assortment/offline',{baseline:assortmentReport.baseline.decisions,changes:Object.fromEntries(assortmentKeys.map(k=>[k,assortmentReport.candidate.decisions[k]])),assumptions:assortmentAssumptions,source:assortmentSource});
        const url=URL.createObjectURL(new Blob([bundle.html],{type:'text/html;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=bundle.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
        notify('Playable offline HTML downloaded. Send the file itself; no server or installation is needed.');
      } finally {button.disabled=assortmentStale;}
    }
    if(action==='save'){
      const name=prompt('Name this assortment alternative:');if(!name?.trim())return;
      await api('scenarios',{name:name.trim(),decisions:assortmentReport.candidate.decisions,assumptions:assortmentAssumptions});scenarios=await api('scenarios');notify('Saved alternative with all 12 fixed inputs preserved. Studio and workbook are unchanged.');
    }
    if(action==='export'){
      const output={title:'Getchell’s four-input Assortment Lab comparison',exported_at:new Date().toISOString(),source:assortmentSource,...assortmentReport};
      const url=URL.createObjectURL(new Blob([JSON.stringify(output,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='getchells-assortment-comparison.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
  }catch(e){notify(e.message);}
});
