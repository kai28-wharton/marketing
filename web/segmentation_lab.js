'use strict';
// Discussion-only arithmetic. None of these controls modify the decision model.
const segmentationDebateDefaults=()=>({left:'SEGMENT 3',right:'SEGMENT 5',rival:'ZEPHARA',normalized:false,note:'',
 cases:[{segment:'SEGMENT 3',cost:1000000,margin:20,lift:5},{segment:'SEGMENT 5',cost:1000000,margin:20,lift:5}]});
let segmentationDebate=segmentationDebateDefaults();
function segmentationFocusShare(s){const p=s.preferences;return (p.BRAND+p['SHOPPING EXPERIENCE'])/Object.values(p).reduce((a,v)=>a+v,0);}
function segmentationHurdle(revenue,a){
 if(![revenue,a.cost,a.margin,a.lift].every(v=>typeof v==='number'&&Number.isFinite(v))||revenue<=0||a.cost<0||a.cost>1e9||a.margin<0||a.margin>100||a.lift< -100||a.lift>100)return null;
 const incrementalRevenue=revenue*a.lift/100,contribution=incrementalRevenue*a.margin/100,net=contribution-a.cost;
 const requiredRevenue=a.cost===0?0:a.margin>0?a.cost/(a.margin/100):null;
 return {incrementalRevenue,contribution,net,requiredRevenue,requiredLift:requiredRevenue===null?null:requiredRevenue/revenue,
         roi:a.cost===0?null:net/a.cost};
}
function segmentationCoreCounterfactual(){const d=data.segment_decision,core=d.rows.find(s=>s.id==='SEGMENT 3'),other=d.rows.filter(s=>s.id!=='SEGMENT 3'&&segmentationGroup.includes(s.id)),sum=k=>other.reduce((a,s)=>a+s[k],0);
 return `<details class="seg-counterfactual"><summary>Debate removing Segment 3: what is represented with versus without it?</summary>`+
 table(['Discussion portfolio','Market consumers','Existing aggregate CLV','Existing company revenue'],[
 ['Selected others, without 3',num(sum('size')),money(sum('clv')),money(sum('revenue'))],
 ['Same group, with 3',num(sum('size')+core.size),money(sum('clv')+core.clv),money(sum('revenue')+core.revenue)],
 ['Difference: Segment 3 footprint',num(core.size),money(core.clv),money(core.revenue)]])+
 note(`S3 has ${pct(segmentationFocusShare(core))} of its exported needs weight in Brand + Shopping Experience. Its existing revenue grew ${pct(core.growth)} and aggregate CLV grew ${pct(core.clv_growth)}. Excluding it from a growth focus does not mean this revenue or CLV disappears; the table is a footprint comparison, not an estimate of losses or incremental profit.`)+`</details>`;
}
function segmentationOptions(selected){return data.segment_decision.rows.map(s=>`<option value="${esc(s.id)}" ${selected===s.id?'selected':''}>${esc(s.id)}</option>`).join('');}
function segmentationComparison(){const d=data.segment_decision,a=d.rows.find(s=>s.id===segmentationDebate.left),b=d.rows.find(s=>s.id===segmentationDebate.right),normalized=segmentationDebate.normalized,den=s=>normalized?Object.values(s.preferences).reduce((a,v)=>a+v,0):1;
 const criteria=[['Market consumers',a.size,b.size,num],['Existing aggregate CLV',a.clv,b.clv,money],['Existing company revenue',a.revenue,b.revenue,money],['Population growth',a.size_growth,b.size_growth,pct],['Company revenue growth',a.growth,b.growth,pct],['Brand + Experience needs share',segmentationFocusShare(a),segmentationFocusShare(b),pct]];
 const own=d.competitors.find(c=>c.name==="GETCHELL'S"),rival=d.competitors.find(c=>c.name===segmentationDebate.rival);
 return table(['Evidence',a.id,b.id,'A minus B'],criteria.map(([name,av,bv,fmt])=>[esc(name),fmt(av),fmt(bv),signed(av-bv,fmt)]))+
 note('Needs share = (Brand + Shopping Experience) ÷ sum of all eight raw needs. Growth/share differences above are percentage-point differences, not relative growth. This is descriptive concentration, not customer share, purchase probability, utility or profitability.')+
 bars(data.marketing.attributes.map(k=>({label:k,values:[a.preferences[k]/den(a),b.preferences[k]/den(b)]})),{title:'A versus B: '+(normalized?'within-segment normalized needs':'raw preference intensity'),format:normalized?pct:num,series:[a.id,b.id]})+
 table(['Profile',a.id,b.id],[['Named rivals (Intro p8)',esc(a.competitors.join(', ')),esc(b.competitors.join(', '))],['Strongest case',`<div class="wrap">${esc(a.case)}</div>`,`<div class="wrap">${esc(b.case)}</div>`],['Main risk',`<div class="wrap">${esc(a.risk)}</div>`,`<div class="wrap">${esc(b.risk)}</div>`]])+
 `<h3>Our company capability versus ${esc(rival.name)}</h3>`+
 table(['Quadrant',"Getchell’s",rival.name,'Our score minus rival','CSV floor gap'],qNames.map(q=>[q,num(own.scores[q]),num(rival.scores[q]),signed(own.scores[q]-rival.scores[q]),signed(d.floors.find(f=>f.quadrant===q).active_gap)]))+
 note('These are company-wide scores, not measured segment-specific utility. A positive gap is not a forecast of customer switching; changing the rival or needs view changes the discussion, not actual capabilities.');
}
function segmentationCaseControls(a,i){return `<fieldset class="seg-case"><legend>Alternative ${i===0?'A':'B'} · illustrative assumptions</legend>`+
 `<label for="seg-case-${i}-segment">Segment</label><select id="seg-case-${i}-segment" data-seg-case="${i}" data-seg-field="segment">${segmentationOptions(a.segment)}</select>`+
 [['cost','Incremental period spending (USD)',0,1e9],['margin','Incremental contribution margin (%)',0,100],['lift','Assumed incremental revenue (% of current segment revenue)',-100,100]].map(([k,label,min,max])=>`<label for="seg-case-${i}-${k}">${esc(label)}</label><input id="seg-case-${i}-${k}" data-seg-case="${i}" data-seg-field="${k}" type="number" min="${min}" max="${max}" step="any" value="${a[k]??''}" placeholder="Enter an assumption">`).join('')+`</fieldset>`;}
function segmentationHurdleResults(){const d=data.segment_decision,calculations=segmentationDebate.cases.map(a=>{const s=d.rows.find(s=>s.id===a.segment);return {s,a,r:segmentationHurdle(s.revenue,a)};});
 const format=v=>money(v,false),cell=(c,key,fmt=format)=>c.r?fmt(c.r[key]):'Enter valid assumptions';
 const header=['Illustrative period arithmetic',...calculations.map((c,i)=>(i===0?'A':'B')+' · '+c.s.id)];
 const metrics=[['Current observed revenue (scale reference)',...calculations.map(c=>format(c.s.revenue))],
 ['Assumed incremental revenue',...calculations.map(c=>cell(c,'incrementalRevenue'))],['Contribution before incremental spending',...calculations.map(c=>cell(c,'contribution'))],
 ['Contribution after incremental spending',...calculations.map(c=>cell(c,'net'))],['Break-even incremental revenue',...calculations.map(c=>c.r&&c.r.requiredRevenue===null?'No finite hurdle at 0% margin':cell(c,'requiredRevenue'))],
 ['Break-even lift versus current revenue',...calculations.map(c=>c.r&&c.r.requiredLift===null?'No finite hurdle at 0% margin':cell(c,'requiredLift',pct))],
 ['Return on incremental spending (not company ROIC)',...calculations.map(c=>c.r&&c.r.roi===null?'Undefined at zero spending':cell(c,'roi',pct))],
 ['Assumed spending / observed company cash',...calculations.map(c=>c.r?pct(c.a.cost/d.finance.cash_current):'Enter valid assumptions')]];
 const valid=calculations.every(c=>c.r);let conclusion='Both alternatives need complete, finite assumptions before comparison.';
 if(valid){const delta=calculations[0].r.net-calculations[1].r.net;
 conclusion=Math.abs(delta)<.005?'The alternatives tie under these assumptions.':`Alternative ${delta>0?'A':'B'} produces ${money(Math.abs(delta),false)} more illustrative period contribution after spending. This is an assumption result, not a recommended segment or a forecast.`;}
 return table(header,metrics)+note(esc(conclusion))+
 `<h3>Margin sensitivity: hold each alternative’s spending fixed</h3>`+
 table(['Hypothetical incremental margin','A: break-even revenue lift','B: break-even revenue lift'],[10,20,30].map(m=>[m+'%',...calculations.map(c=>{const r=segmentationHurdle(c.s.revenue,{...c.a,margin:m});return r?pct(r.requiredLift):'Enter valid assumptions';})]))+
 note('Formula: contribution after spending = current segment revenue × assumed lift × assumed incremental contribution margin − incremental spending. Break-even revenue = spending ÷ contribution margin. No finite break-even at zero margin with positive spending. These are independent alternatives, not additive plans. Negative lift uses the same assumed contribution margin symmetrically.')+
 note('Defaults ($1M, 20%, 5%) are illustrative—not measured margins, an approved budget, a suggested allocation or a spending-to-sales response. Use one consistent test period for both alternatives. Excludes retention/CLV effects, cannibalization, incremental inventory, capital, financing, tax and opportunity cost. Contribution margin must be after variable fulfillment/discount costs; it is not the company gross margin. Spending/cash is context, not a liquidity or budget approval.');
}
function segmentationDebateTools(){return `<div class="seg-lab">`+
 (data.discussion_saved_at?`<p class="review-copy">Discussion snapshot saved ${esc(new Date(data.discussion_saved_at).toLocaleString())}. Edits here remain local; download again to save a new copy. Observed data remains the export-${data.current_round} snapshot, not a live feed.</p>`:'')+
 panel('Debate lab · compare any two segments','Compare the case for Segment 3 directly against a larger CLV pool, or debate 5 versus 6 without hiding the trade-offs.',
 `<div class="review-controls"><div><label for="seg-compare-left">Segment A</label><select id="seg-compare-left" data-seg-debate="left">${segmentationOptions(segmentationDebate.left)}</select></div><div><label for="seg-compare-right">Segment B</label><select id="seg-compare-right" data-seg-debate="right">${segmentationOptions(segmentationDebate.right)}</select></div><div><label for="seg-compare-rival">Capability benchmark</label><select id="seg-compare-rival" data-seg-debate="rival">${data.segment_decision.competitors.filter(c=>c.name!=="GETCHELL'S").map(c=>`<option ${segmentationDebate.rival===c.name?'selected':''}>${esc(c.name)}</option>`).join('')}</select></div><label><input type="checkbox" id="seg-compare-normalized" data-seg-debate="normalized" ${segmentationDebate.normalized?'checked':''}> Normalize needs within each segment</label></div><div id="seg-comparison-results">${segmentationComparison()}</div>`)+
 panel('Debate lab · what would the investment have to earn?','These financial alternatives have their own segment selectors. Copy the compared segments or change them independently. This is a break-even calculator, not a simulator prediction; no measured segment contribution margin is supplied.',
 `<p><button type="button" id="segmentation-copy-comparison">Use compared segments in financial alternatives</button></p><div class="review-grid" id="seg-case-controls">${segmentationDebate.cases.map(segmentationCaseControls).join('')}</div><div id="seg-hurdle-results" aria-live="polite">${segmentationHurdleResults()}</div>`)+
 panel('Team hypothesis · capture what would change your mind','This note and the discussion controls are saved into the downloaded HTML. They never change the submitted plan.',
 `<label for="seg-debate-note">Team hypothesis / missing evidence (up to 1,500 characters)</label><textarea id="seg-debate-note" rows="3" maxlength="1500" placeholder="Example: We would promote 6 over 5 if an existing-store test delivers better contribution without a price war.">${esc(segmentationDebate.note)}</textarea>`)+`</div>`;}
function segmentationDebateSnapshot(){return {version:1,group:[...segmentationGroup],lens:segmentationLens,debate:JSON.parse(JSON.stringify(segmentationDebate))};}
function restoreSegmentationDebate(){const state=data.segmentation_debate;if(!state||state.version!==1||!data.segment_decision)return;
 const ids=data.segment_decision.rows.map(s=>s.id),base=segmentationDebateDefaults(),s=state.debate||{};
 if(Array.isArray(state.group))segmentationGroup=[...new Set(state.group.filter(id=>ids.includes(id)&&id!=='SEGMENT 1'))];
 if(data.segment_decision.lenses.some(l=>l.id===state.lens))segmentationLens=state.lens;
 for(const k of ['left','right'])if(ids.includes(s[k]))base[k]=s[k];
 if(data.segment_decision.competitors.some(c=>c.name===s.rival&&c.name!=="GETCHELL'S"))base.rival=s.rival;
 base.normalized=s.normalized===true;base.note=typeof s.note==='string'?s.note.slice(0,1500):'';
 if(Array.isArray(s.cases)&&s.cases.length===2)base.cases=s.cases.map((a,i)=>{
 const result={...base.cases[i]};if(!a||typeof a!=='object')return result;
 if(ids.includes(a.segment))result.segment=a.segment;
 for(const k of ['cost','margin','lift'])result[k]=typeof a[k]==='number'&&Number.isFinite(a[k])?a[k]:null;
 return result;});
 segmentationDebate=base;
}
function serializeSegmentationReport(html,state){const doc=new DOMParser().parseFromString(html,'text/html'),script=doc.querySelector('#review-data');
 if(!script)throw new Error('Report data missing. Reload the page and try again.');
 const payload=JSON.parse(script.textContent);payload.report_page='segmentation';payload.segmentation_debate=state;
 payload.discussion_saved_at=new Date().toISOString();
 script.textContent=JSON.stringify(payload).replace(/&/g,'\\u0026').replace(/</g,'\\u003c').replace(/>/g,'\\u003e').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
 doc.querySelector('#content').textContent='Loading saved segmentation discussion…';
 doc.title='Getchell’s · Customer segmentation decision';
 return '<!doctype html>\n'+doc.documentElement.outerHTML;
}
async function downloadSegmentationReport(){const button=$('#segmentation-download'),status=$('#segmentation-download-status'),state=segmentationDebateSnapshot();
 button.disabled=true;status.textContent='Preparing your interactive HTML snapshot…';
 try{let html;if(offline)html=document.documentElement.outerHTML;else{const response=await fetch('/customer-segmentation-report');if(!response.ok)throw new Error('Report could not be generated. Please try again.');html=await response.text();}
 const content=serializeSegmentationReport(html,state),blob=new Blob([content],{type:'text/html;charset=utf-8'}),url=URL.createObjectURL(blob),link=document.createElement('a');
 link.href=url;link.download='getchells-customer-segmentation-decision.html';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
 status.textContent='Download prepared. Open or share the HTML file itself; data, controls and discussion assumptions work offline. No submitted decision inputs are exported.';
 }catch(error){status.textContent=error.message;}finally{button.disabled=false;}
}
document.addEventListener('change',e=>{const key=e.target.dataset.segDebate;if(key){segmentationDebate[key]=key==='normalized'?e.target.checked:e.target.value;$('#seg-comparison-results').innerHTML=segmentationComparison();}
 if(e.target.dataset.segField==='segment'){segmentationDebate.cases[Number(e.target.dataset.segCase)].segment=e.target.value;$('#seg-hurdle-results').innerHTML=segmentationHurdleResults();}
});
document.addEventListener('input',e=>{if(e.target.id==='seg-debate-note')segmentationDebate.note=e.target.value.slice(0,1500);
 const key=e.target.dataset.segField;if(!key||key==='segment')return;
 segmentationDebate.cases[Number(e.target.dataset.segCase)][key]=Number.isFinite(e.target.valueAsNumber)?e.target.valueAsNumber:null;
 e.target.setAttribute('aria-invalid',String(!e.target.checkValidity()));$('#seg-hurdle-results').innerHTML=segmentationHurdleResults();
});
document.addEventListener('click',e=>{
 if(e.target.closest('#segmentation-download'))downloadSegmentationReport();
 if(e.target.closest('#segmentation-copy-comparison')){segmentationDebate.cases[0].segment=segmentationDebate.left;segmentationDebate.cases[1].segment=segmentationDebate.right;$('#seg-case-controls').innerHTML=segmentationDebate.cases.map(segmentationCaseControls).join('');$('#seg-hurdle-results').innerHTML=segmentationHurdleResults();}
 if(e.target.closest('#segmentation-reset')){segmentationGroup=['SEGMENT 3','SEGMENT 5'];segmentationLens='SHOPPING EXPERIENCE';segmentationDebate=segmentationDebateDefaults();render();$('#segmentation-reset')?.focus();}
});
