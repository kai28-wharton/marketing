'use strict';
(() => {
  const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const money=(v,compact=false)=>(v<0?'−':'')+'$'+(compact?(Math.abs(v)/1e6).toFixed(2)+'M':Math.abs(v).toLocaleString('en-US',{maximumFractionDigits:0}));
  const change=v=>(v>=0?'+':'−')+money(Math.abs(v));
  const points=v=>(v>=0?'+':'')+v.toFixed(4),pct=v=>(v*100).toFixed(2)+'%';
  const keys=['low_breadth','low_depth','high_breadth','high_depth'];
  const quadrants=['BRAND','EXPERIENCE','FRICTIONLESS','LOW PRICE'];
  const names={BRAND:'Brand',EXPERIENCE:'Experience',FRICTIONLESS:'Frictionless','LOW PRICE':'Low price'};
  const spendKeys=['online','service','experience','vendor','analytics'];
  const clamp=(v,lo=0,hi=1)=>Math.min(hi,Math.max(lo,v));
  let S,values,report;
  const invalid=new Set();

  function capacities(plan,halfScale=1,channelShift=0) {
    const config=S.configuration,reference=config.reference;
    const half=Object.fromEntries(Object.entries(config.half_saturation).map(([k,v])=>[k,v*halfScale]));
    const share=clamp(config.online_share+channelShift,.05,.95),sat=(x,h)=>x>0?x/(x+h):0;
    const load=share+(1-share)*plan.coverage/reference.coverage;
    const service=sat(plan.service/Math.max(.05,load),half.service);
    const perStoreHalf=half.experience/Math.max(1,config.half_saturation.coverage);
    const storeQuality=plan.coverage>0?sat(plan.experience/plan.coverage,perStoreHalf):0;
    const out={online:sat(plan.online,half.online),service,store_quality:storeQuality,reach:sat(plan.coverage,half.coverage)};
    for(const key of ['vendor','analytics']){
      const raw=sat(plan[key],half[key]),anchor=sat(reference[key],half[key]);
      const gainRoom=1-.85*config.operating_scores[key];
      out[key]=anchor+(raw-anchor)*(raw>anchor?gainRoom:1);
    }
    out.service_experience=service*storeQuality;
    out.analytics_experience=out.analytics*storeQuality;
    out.online_analytics=out.online*out.analytics;
    out.vendor_analytics=out.vendor*out.analytics;
    return {levels:out,share};
  }
  function scorePoint(plan,strength=S.assumptions.score_response,halfScale=1,channelShift=0) {
    const reference=S.configuration.reference;
    const {levels,share}=capacities(plan,halfScale,channelShift);
    const anchors=capacities(reference,halfScale,channelShift).levels;
    const features=Object.fromEntries(Object.entries(levels).map(([k,v])=>[k,2*(v-anchors[k])]));
    for(const k of ['store_quality','service_experience','analytics_experience','reach'])features[k]*=1-share;
    features.online*=share;
    features.quality=((plan.private_quality-reference.private_quality)+(plan.national_quality-reference.national_quality))/2;
    features.breadth=(plan.low_breadth+plan.high_breadth-reference.low_breadth-reference.high_breadth)/100;
    features.depth=(plan.low_depth+plan.high_depth-reference.low_depth-reference.high_depth)/100;
    features.private=(plan.low_private+plan.high_private-reference.low_private-reference.high_private)/100;
    features.markup=.76*(plan.low_markup-reference.low_markup)+.24*(plan.high_markup-reference.high_markup);
    const scores={};
    for(const q of quadrants){
      let raw=0;for(const [key,weight] of Object.entries(S.weights[q]))raw+=features[key]*weight;
      raw*=strength;
      const anchor=clamp(S.observed_scores[q],.001,9.999),slope=Math.max(.05,anchor*(1-anchor/10));
      const odds=Math.log(anchor/(10-anchor))+raw/slope;
      scores[q]=raw?10/(1+Math.exp(-clamp(odds,-60,60))):S.observed_scores[q];
    }
    return scores;
  }
  function evaluate(plan,detailed=true) {
    const scores=scorePoint(plan),a=S.assumptions,income=S.income,reference=S.configuration.reference;
    let gain=0;for(const [q,w] of [['BRAND',.35],['EXPERIENCE',.35],['FRICTIONLESS',.2],['LOW PRICE',.1]])gain+=(scores[q]-S.observed_scores[q])*w;
    const segments={};let revenue=0,cogs=0;
    for(const [prefix,label] of [['low','Lower Cost'],['high','Higher Cost']]){
      const price=(1+plan[prefix+'_markup']/100)/(1+reference[prefix+'_markup']/100);
      const units=Math.max(.1,1+a.demand_response*gain-a.price_elasticity*(price-1));
      const sales=income[label+' Revenue']*price*units,cost=income[label+' COGS']*units;
      segments[prefix]={revenue:sales,cogs:cost,gross_profit:sales-cost};revenue+=sales;cogs+=cost;
    }
    const gross=revenue-cogs,spent=spendKeys.reduce((sum,k)=>sum+plan[k],0);
    const spendingDelta=spent-spendKeys.reduce((sum,k)=>sum+reference[k],0);
    const net=income['Net Income']+gross-income['Gross Profit']-spendingDelta;
    const result={decisions:{...plan},scores,segments,revenue,cogs,gross_profit:gross,gross_margin:gross/revenue,
      net_income:net,explicit_spend:spent,remaining:S.budget-spent,feasible:spent<=S.budget};
    if(detailed){
      const stresses=[];
      for(const response of [.6,1.4])for(const half of [.75,1.25])for(const shift of [-.1,.1])stresses.push(scorePoint(plan,a.score_response*response,half,shift));
      result.intervals=Object.fromEntries(quadrants.map(q=>[q,[Math.max(0,Math.min(scores[q],...stresses.map(s=>s[q]))-S.historical_evidence[q].stress_floor),Math.min(10,Math.max(scores[q],...stresses.map(s=>s[q]))+S.historical_evidence[q].stress_floor)]]));
    }
    return result;
  }
  const financialKeys=['revenue','cogs','gross_profit','gross_margin','net_income','explicit_spend','remaining'];
  const financial=r=>Object.fromEntries(financialKeys.map(k=>[k,r[k]]));
  function validateValues(changes) {
    if(!changes||Object.keys(changes).sort().join('|')!==[...keys].sort().join('|'))throw new Error('Supply only the four breadth/depth settings.');
    for(const key of keys)if(typeof changes[key]!=='number'||!Number.isFinite(changes[key])||changes[key]<1||changes[key]>100)throw new Error('Every index must be a finite number between 1 and 100.');
  }
  function analyze(changes) {
    validateValues(changes);
    const base=evaluate(S.baseline),candidate=evaluate({...S.baseline,...changes});
    const bm=financial(base),cm=financial(candidate);
    const scoreChanges=Object.fromEntries(quadrants.map(q=>[q,candidate.scores[q]-base.scores[q]]));
    const deltas=Object.fromEntries(financialKeys.map(k=>[k,cm[k]-bm[k]]));
    const cache=[];
    for(let mask=0;mask<16;mask++){
      const plan={...S.baseline};keys.forEach((k,i)=>{if(mask&(1<<i))plan[k]=changes[k];});
      cache[mask]=evaluate(plan,false);
    }
    const attribution=keys.map((key,i)=>{
      const row={key,scores:Object.fromEntries(quadrants.map(q=>[q,0])),financial:Object.fromEntries(financialKeys.map(k=>[k,0]))};
      for(let mask=0;mask<16;mask++){
        if(mask&(1<<i))continue;
        const size=mask.toString(2).replace(/0/g,'').length,combinations=[1,3,3,1][size],weight=1/(4*combinations);
        for(const q of quadrants)row.scores[q]+=weight*(cache[mask|(1<<i)].scores[q]-cache[mask].scores[q]);
        for(const k of financialKeys)row.financial[k]+=weight*(cache[mask|(1<<i)][k]-cache[mask][k]);
      }
      return row;
    });
    const probes=keys.map(key=>{
      const row={key};
      for(const [direction,step] of [['increase',10],['decrease',-10]]){
        if(changes[key]+step<1||changes[key]+step>100){row[direction]=null;continue;}
        const trial=evaluate({...S.baseline,...changes,[key]:changes[key]+step},false);
        row[direction]={scores:Object.fromEntries(quadrants.map(q=>[q,trial.scores[q]-candidate.scores[q]])),net_income:trial.net_income-candidate.net_income};
      }
      return row;
    });
    const outside=S.factors.filter(f=>keys.includes(f.key)&&(changes[f.key]<f.industry.minimum||changes[f.key]>f.industry.maximum)).map(f=>f.label);
    return {baseline:base,candidate,score_changes:scoreChanges,financial_changes:deltas,attribution,sensitivities:probes,outside_industry_range:outside,
      segment_alignment:computeSegmentAlignment(S.marketing,S.baseline,candidate.decisions)};
  }
  const label=key=>S.factors.find(f=>f.key===key).label;
  function renderControls() {
    $('#controls').innerHTML=keys.map(key=>{const f=S.factors.find(f=>f.key===key);return `<div class="control"><label for="n-${key}">${escape(f.label)}</label><div class="input-line"><input id="n-${key}" type="number" min="1" max="100" step="any" data-key="${key}" aria-label="${escape(f.label)}" value="${values[key]}"><span>index / 100</span></div><input type="range" min="1" max="100" step="1" data-key="${key}" aria-label="${escape(f.label)} slider" value="${values[key]}"><small>Locked baseline ${S.baseline[key]} · industry average ${f.industry.average}<br>Observed range ${f.industry.minimum}–${f.industry.maximum}; not a required target.</small></div>`;}).join('');
  }
  function renderResults() {
    const r=report,b=r.baseline,c=r.candidate;
    const shown=(v,key)=>key==='gross_margin'?pct(v):money(v,true);
    const delta=(v,key)=>key==='gross_margin'?(v>=0?'+':'')+(v*100).toFixed(4)+' pp':change(v);
    const metrics=[['Revenue','revenue'],['Volume-related COGS','cogs'],['Gross profit','gross_profit'],['Gross margin','gross_margin'],['Net income before unknown assortment costs','net_income'],['Known investment spending','explicit_spend'],['Known budget headroom','remaining']];
    $('#results').innerHTML=`<section class="panel"><h2>Kahn positioning</h2><p class="small muted">Both columns are modeled outcomes. Observed Round 0 is a separate anchor.</p><div class="scroll"><table><thead><tr><th>Quadrant</th><th>Locked plan</th><th>Your test</th><th>Change</th></tr></thead><tbody>${quadrants.map(q=>`<tr><th scope="row">${names[q]}</th><td>${b.scores[q].toFixed(4)}</td><td><strong>${c.scores[q].toFixed(4)}</strong></td><td class="${r.score_changes[q]<0?'negative':'positive'}">${points(r.score_changes[q])}</td></tr>`).join('')}</tbody></table></div><details><summary>Observed scores and structural stress ranges</summary><p>Not confidence intervals or calibrated prediction errors.</p><div class="scroll"><table><thead><tr><th>Quadrant</th><th>Observed Round 0</th><th>Test stress envelope</th></tr></thead><tbody>${quadrants.map(q=>`<tr><td>${names[q]}</td><td>${S.observed_scores[q].toFixed(3)}</td><td>${c.intervals[q].map(v=>v.toFixed(3)).join('–')}</td></tr>`).join('')}</tbody></table></div></details></section><section class="panel"><h2>Financial impact before unknown assortment costs</h2><div class="scroll"><table><thead><tr><th>Metric</th><th>Locked plan</th><th>Test</th><th>Change</th></tr></thead><tbody>${metrics.map(([title,key])=>`<tr class="${key==='net_income'?'highlight':''}"><th scope="row">${title}</th><td>${shown(b[key],key)}</td><td class="${c[key]<0?'negative':''}">${shown(c[key],key)}</td><td>${delta(r.financial_changes[key],key)}</td></tr>`).join('')}</tbody></table></div><p class="small muted">${r.financial_changes.net_income>0?`Modeled profit uplift: ${money(r.financial_changes.net_income)}. Extra recurring assortment costs above that erase the modeled advantage over the locked plan; that threshold does not establish profitability or fund inventory cash requirements.`:'This test has no positive modeled profit uplift to absorb additional assortment costs.'}</p>${!c.feasible?'<div class="warning">The locked plan already exceeds its known spending budget. Changing these four settings does not fix that overrun.</div>':''}<details><summary>Segment revenue and COGS</summary><p>The current engine applies a company-wide demand response to both segments; lower-cost breadth does not affect only lower-cost revenue.</p><div class="scroll"><table><thead><tr><th>Segment</th><th>Metric</th><th>Locked plan</th><th>Test</th></tr></thead><tbody>${['low','high'].map(s=>['revenue','cogs','gross_profit'].map(k=>`<tr><td>${s==='low'?'Lower-cost':'Higher-cost'}</td><td>${k.replace(/_/g,' ')}</td><td>${money(b.segments[s][k],true)}</td><td>${money(c.segments[s][k],true)}</td></tr>`).join('')).join('')}</tbody></table></div></details></section><section class="panel"><h2>Which of the four settings drove the change?</h2><p class="small muted">Exact four-factor attribution. Columns reconcile before rounding; attribution explains the model, not real-world causation.</p><div class="scroll"><table><thead><tr><th>Input</th>${quadrants.map(q=>`<th>Δ ${names[q]}</th>`).join('')}<th>Δ Revenue</th><th>Δ Profit*</th></tr></thead><tbody>${r.attribution.map(row=>`<tr><th scope="row">${escape(label(row.key))}</th>${quadrants.map(q=>`<td>${points(row.scores[q])}</td>`).join('')}<td>${change(row.financial.revenue)}</td><td>${change(row.financial.net_income)}</td></tr>`).join('')}</tbody></table></div><details><summary>Single-setting probes: add or remove 10 index points</summary><div class="scroll"><table><thead><tr><th>Probe</th><th>Δ Brand</th><th>Δ Experience</th><th>Δ Frictionless</th><th>Δ Profit*</th></tr></thead><tbody>${r.sensitivities.map(row=>['increase','decrease'].map(direction=>row[direction]?`<tr><td>${escape(label(row.key))} ${direction==='increase'?'+':'−'}10</td>${['BRAND','EXPERIENCE','FRICTIONLESS'].map(q=>`<td>${points(row[direction].scores[q])}</td>`).join('')}<td>${change(row[direction].net_income)}</td></tr>`:'').join('')).join('')}</tbody></table></div></details><p class="small muted">*Before unknown assortment costs. No optimum is established without those costs.</p></section>${r.outside_industry_range.length?`<div class="warning">Outside observed industry ranges: ${r.outside_industry_range.map(escape).join(', ')}. Effects here are unvalidated extrapolations; observed ranges are not hard simulator limits.</div>`:''}`;
  }
  function update() {
    if(invalid.size){$('#status').textContent='Enter a valid 1–100 index in every field. Results below are the last valid calculation.';$('#status').className='warning';$('#download-html').disabled=true;$('#download-json').disabled=true;return;}
    report=analyze(values);
    const warnings=[...S.baseline_warnings];
    if(report.outside_industry_range.length)warnings.push('Outside observed industry ranges: '+report.outside_industry_range.join(', ')+'. Effects are unvalidated extrapolations; those ranges are not verified simulator limits.');
    $('#recommendation-top').innerHTML=renderAssortmentRecommendation(S.readiness,S.baseline);
    $('#readiness-end').innerHTML=renderAssortmentReadiness(S.readiness,S.limitations,warnings,{control_selector:'#controls',snapshot_notice:'Observed data and frozen assumptions are embedded in this file and do not refresh automatically. Generate a new file when the approved plan or data changes. This HTML contains team financial data; share only with intended recipients.'});
    const expanded=$$('#results details').map(d=>d.open);renderResults();
    if(S.marketing?.available)$('#results > section').insertAdjacentHTML('afterend',renderSegmentAlignment(S.marketing,S.baseline,report.candidate.decisions,report.segment_alignment));
    $$('#results details').forEach((d,i)=>d.open=expanded[i]||false);
    $('#status').textContent='Up to date · all calculations ran locally · the other 12 decisions and model assumptions are unchanged.';$('#status').className='info';$('#download-html').disabled=false;$('#download-json').disabled=false;
  }
  function safeJSON(value) {return JSON.stringify(value).replace(/</g,'\\u003c').replace(/>/g,'\\u003e').replace(/&/g,'\\u0026').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');}
  function download(content,type,name) {
    const url=URL.createObjectURL(new Blob([content],{type})),link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }
  function fatal(error) {$('#fatal').hidden=false;$('#fatal').textContent='The offline lab could not initialize: '+error.message;$$('button,input').forEach(element=>element.disabled=true);}
  try {
    S=JSON.parse($('#lab-data').textContent);Object.freeze(S.baseline);Object.freeze(S.assumptions);
    values={...S.initial_values};validateValues(values);
    const baselineCheck=evaluate(S.baseline),initialCheck=evaluate({...S.baseline,...values});
    for(const q of quadrants)if(Math.abs(baselineCheck.scores[q]-S.verification.baseline_scores[q])>1e-10||Math.abs(initialCheck.scores[q]-S.verification.initial_scores[q])>1e-10)throw new Error('Embedded model verification failed. Obtain a fresh offline file.');
    if(Math.abs(baselineCheck.net_income-S.verification.baseline_net_income)>.05||Math.abs(initialCheck.net_income-S.verification.initial_net_income)>.05)throw new Error('Embedded financial verification failed. Obtain a fresh offline file.');
    $('#snapshot-meta').textContent='Snapshot '+new Date(S.generated_at).toLocaleString()+' · '+S.model_version+' · locked-plan fingerprint '+S.baseline_fingerprint;
    $('#source-label').textContent=S.source;
    $('#fixed-spend').textContent=money(baselineCheck.explicit_spend,true);$('#fixed-headroom').textContent=money(baselineCheck.remaining,true);
    $('#locked-inputs').innerHTML=S.factors.filter(f=>!keys.includes(f.key)).map(f=>`<tr><th scope="row">${escape(f.label)}</th><td>${f.unit==='$'?money(S.baseline[f.key]):escape(S.baseline[f.key].toLocaleString('en-US',{maximumFractionDigits:2}))+(f.unit==='%'?'%':'')}</td></tr>`).join('');
    $('#assumptions').textContent='Score response '+S.assumptions.score_response+'; demand response '+pct(S.assumptions.demand_response)+'; price elasticity '+S.assumptions.price_elasticity+'; revenue stress assumption ±'+pct(S.assumptions.uncertainty)+'. All are frozen in this copy.';
    $('#sources').innerHTML=[S.source,...S.sources,'prediction.py: Kahn v2 response functions','app.py: financial sensitivity engine','assortment.py: four-input analysis'].map(t=>`<li><code>${escape(t)}</code></li>`).join('');
    renderControls();update();
    $('#controls').addEventListener('input',event=>{
      const field=event.target,key=field.dataset.key;if(!keys.includes(key))return;
      const value=field.valueAsNumber;
      if(!Number.isFinite(value)||value<1||value>100){invalid.add(key);field.setAttribute('aria-invalid','true');update();return;}
      invalid.delete(key);values[key]=value;$$('[data-key="'+key+'"]').forEach(input=>{input.value=value;input.removeAttribute('aria-invalid');});update();
    });
    $('#reset').addEventListener('click',()=>{values=Object.fromEntries(keys.map(k=>[k,S.baseline[k]]));invalid.clear();renderControls();update();});
    $('#industry').addEventListener('click',()=>{values=Object.fromEntries(keys.map(k=>[k,S.factors.find(f=>f.key===k).industry.average]));invalid.clear();renderControls();update();});
    $('#print').addEventListener('click',()=>window.print());
    $('#download-json').addEventListener('click',()=>{if(invalid.size)return;download(JSON.stringify({title:'Getchell’s offline Assortment Lab comparison',exported_at:new Date().toISOString(),source:S.source,baseline_fingerprint:S.baseline_fingerprint,model_version:S.model_version,assumptions:S.assumptions,limitations:S.limitations,...report},null,2),'application/json','getchells-assortment-comparison.json');});
    $('#download-html').addEventListener('click',()=>{
      if(invalid.size)return;
      const snapshot={...S,initial_values:{...values},copy_saved_at:new Date().toISOString(),verification:{...S.verification,initial_scores:report.candidate.scores,initial_net_income:report.candidate.net_income}};
      const copy=document.documentElement.cloneNode(true);copy.querySelector('#lab-data').textContent=safeJSON(snapshot);
      download('<!doctype html>\n'+copy.outerHTML,'text/html;charset=utf-8','getchells-assortment-lab-offline.html');
    });
    // Pure functions are exposed for numerical-parity tests, not editable UI inputs.
    window.OfflineAssortment=Object.freeze({evaluate,analyze,getValues:()=>({...values}),getReport:()=>report});
  }catch(error){fatal(error);}
})();
