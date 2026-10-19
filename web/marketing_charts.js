'use strict';
let marketingDecisionLens='revenue';
const segmentChartColors=['#7c3aed','#2563eb','#0891b2','#d97706','#db2777','#159c6c'];
const preferenceChartColors=['#d97706','#7c3aed','#159c6c','#c026d3','#2563eb','#ea580c','#db2777','#0891b2'];
const marketingLenses=[
  ['revenue','Current company revenue'],['clv','Reported aggregate CLV'],['size','Reported segment size'],['revenue_growth','Latest segment revenue growth'],
  ['BREADTH','Breadth emphasis (normalized)'],['DEPTH','Depth emphasis (normalized)'],['BRAND','Brand emphasis (normalized)'],
  ['ONLINE','Online emphasis (normalized)'],['RETAIL','Retail emphasis (normalized)'],['CUSTOMER SERVICE','Service emphasis (normalized)'],
  ['SHOPPING EXPERIENCE','Experience emphasis (normalized)'],['LOW PRICE','Low-price emphasis (normalized)']
];
function marketingDecisionData(m,segmentId,lens='revenue') {
  const selected=m.segments.find(s=>s.id===segmentId)||m.segments[0];
  const preference=m.attributes.includes(lens);
  const rankings=m.segments.map(s=>({id:s.id,value:preference?s.normalized_preferences[lens]:s[lens]}))
    .filter(r=>r.value!==null&&Number.isFinite(r.value)).sort((a,b)=>b.value-a.value);
  const first=selected.history[0];
  const trend=selected.history.map(r=>({round:r.round,
    size:first.size?r.size/first.size*100:null,revenue:first.revenue?r.revenue/first.revenue*100:null,
    clv:first.clv?r.clv/first.clv*100:null}));
  return {selected,rankings,trend,preference_lens:preference,
    mix_gap_pp:100*(selected.clv_share-selected.revenue_share),
    top_revenue:[...m.segments].sort((a,b)=>b.revenue-a.revenue)[0].id,
    top_clv:[...m.segments].sort((a,b)=>b.clv-a.clv)[0].id};
}
function marketingPropositionEvidence(m,preference) {
  const mapping={BREADTH:['LOWER COST BREADTH','HIGHER COST BREADTH'],DEPTH:['LOWER COST DEPTH','HIGHER COST DEPTH'],
    ONLINE:['ONLINE INVEST'],RETAIL:['RETAIL COVERAGE'],'CUSTOMER SERVICE':['CUSTOMER SERVICE'],
    'SHOPPING EXPERIENCE':['SHOPPING EXPERIENCE'],'LOW PRICE':['LOWER COST PRICE','HIGHER COST PRICE']};
  const rows=(mapping[preference]||[]).map(key=>m.positions.find(p=>p.attribute===key)).filter(Boolean);
  if(!rows.length)return 'No directly equivalent aggregate attribute is reported in the product-position table; inspect the source definitions before comparing it with Kahn.';
  return rows.map(p=>`${p.attribute}: Getchell’s ${p.own.toFixed(1)} (numerical rank #${p.rank_numeric}/${p.companies}); highest reported value ${p.leader_value.toFixed(1)} (${p.leader}).`).join(' ')+' These are reported positions on a separate scale, not Kahn scores or investment response rates.';
}
function marketingChartSvg(id,title,description,content,width=560,height=340,interactive=false) {
  return `<div class="marketing-chart-scroll"><svg class="marketing-analysis-svg ${id==='segment-composition'?'marketing-composition-svg':''}" viewBox="0 0 ${width} ${height}" ${interactive?'role="group"':'role="img"'} aria-labelledby="${id}-title ${id}-desc"><title id="${id}-title">${esc(title)}</title><desc id="${id}-desc">${esc(description)}</desc>${content}</svg></div>`;
}
function marketingChartDot(s,x,y,r,selected,index,labelOffset=[12,-12]) {
  return `<g class="marketing-chart-target ${s.id===selected?'is-selected':''}" data-chart-segment="${esc(s.id)}" role="button" tabindex="0" aria-label="Select ${esc(s.id)}" aria-pressed="${s.id===selected}"><title>${esc(s.id)} · select to inspect its decision brief</title><circle cx="${x}" cy="${y}" r="${r}" fill="${segmentChartColors[index]}" fill-opacity="${s.id===selected?1:.82}" stroke="${s.id===selected?'#45318a':'white'}" stroke-width="${s.id===selected?3:1.5}"/><text x="${x+labelOffset[0]}" y="${y+labelOffset[1]}" class="chart-segment-label">S${s.id.split(' ')[1]}</text></g>`;
}
function marketingPortfolioChart(m,selected) {
  const left=62,top=26,width=450,height=240,max=Math.max(.05,Math.ceil(Math.max(...m.segments.flatMap(s=>[s.revenue_share,s.clv_share]))*100/5)*5/100);
  const x=v=>left+v/max*width,y=v=>top+height-v/max*height;
  let svg='';
  for(let i=0;i<=5;i++){
    const value=max*i/5;
    svg+=`<line x1="${left}" x2="${left+width}" y1="${y(value)}" y2="${y(value)}" class="chart-grid"/><text x="${left-10}" y="${y(value)+4}" text-anchor="end" class="chart-tick">${(value*100).toFixed(0)}%</text><text x="${x(value)}" y="${top+height+22}" text-anchor="middle" class="chart-tick">${(value*100).toFixed(0)}%</text>`;
  }
  svg+=`<line x1="${x(0)}" y1="${y(0)}" x2="${x(max)}" y2="${y(max)}" class="chart-parity"/><text x="${left+width}" y="${top+height+53}" text-anchor="end" class="chart-axis-label">Share of Getchell’s current revenue</text><text x="16" y="${top+height/2}" transform="rotate(-90 16 ${top+height/2})" text-anchor="middle" class="chart-axis-label">Share of reported company CLV</text>`;
  const maxSize=Math.max(1,...m.segments.map(s=>s.size));
  for(const s of [...m.segments].sort((a,b)=>(a.id===selected)-(b.id===selected))){
    const i=m.segments.findIndex(r=>r.id===s.id),offset=s.id==='SEGMENT 2'?[-30,-16]:s.id==='SEGMENT 5'?[13,22]:[12,-12];
    svg+=marketingChartDot(s,x(s.revenue_share),y(s.clv_share),14*Math.sqrt(s.size/maxSize),selected,i,offset);
  }
  return marketingChartSvg('segment-portfolio','Segment portfolio: company revenue mix versus CLV mix','Each bubble is one segment. Bubble area is proportional to reported size. The diagonal is equal revenue and CLV mix, not a target or ROI benchmark.',svg,560,340,true);
}
function marketingNeedsChart(m,selected) {
  const left=65,top=28,width=445,height=235;
  const maxX=Math.max(.3,...m.segments.map(s=>s.normalized_preferences.BREADTH*1.15));
  const maxY=Math.max(.22,...m.segments.map(s=>s.normalized_preferences.DEPTH*1.15));
  const x=v=>left+v/maxX*width,y=v=>top+height-v/maxY*height;
  let svg='';
  for(let i=0;i<=4;i++){
    const a=maxX*i/4,b=maxY*i/4;
    svg+=`<line x1="${left}" x2="${left+width}" y1="${y(b)}" y2="${y(b)}" class="chart-grid"/><text x="${left-10}" y="${y(b)+4}" text-anchor="end" class="chart-tick">${(b*100).toFixed(1)}%</text><text x="${x(a)}" y="${top+height+22}" text-anchor="middle" class="chart-tick">${(a*100).toFixed(1)}%</text>`;
  }
  svg+=`<text x="${left+width}" y="${top+height+53}" text-anchor="end" class="chart-axis-label">Breadth / within-segment preference sum</text><text x="16" y="${top+height/2}" transform="rotate(-90 16 ${top+height/2})" text-anchor="middle" class="chart-axis-label">Depth / preference sum</text>`;
  for(const s of [...m.segments].sort((a,b)=>(a.id===selected)-(b.id===selected))){
    const offset=s.id==='SEGMENT 4'?[-27,22]:s.id==='SEGMENT 3'?[-28,-14]:[12,-12];
    svg+=marketingChartDot(s,x(s.normalized_preferences.BREADTH),y(s.normalized_preferences.DEPTH),s.id===selected?12:9,selected,m.segments.indexOf(s),offset);
  }
  return marketingChartSvg('segment-needs','Breadth versus depth customer emphasis','Axes are normalized shares of each segment’s raw preference sum. They are not population percentages, assortment settings or forecast response rates.',svg,560,340,true);
}
function marketingRankingChart(m,d,lens,selected) {
  const left=95,top=25,width=335,rowHeight=40;
  const vals=d.rankings.map(r=>r.value),min=Math.min(0,...vals),max=Math.max(0,...vals);
  const span=max-min||1,x=v=>left+(v-min)/span*width;
  const format=v=>d.preference_lens||lens==='revenue_growth'?(v*100).toFixed(1)+'%':lens==='size'?(v/1e6).toFixed(2)+'M':money(v);
  let svg=`<line x1="${x(0)}" x2="${x(0)}" y1="${top-5}" y2="${top+6*rowHeight}" class="chart-parity"/>`;
  d.rankings.forEach((r,i)=>{
    const y=top+i*rowHeight,index=m.segments.findIndex(s=>s.id===r.id),selectedRow=r.id===selected;
    svg+=`<g data-chart-segment="${esc(r.id)}" class="marketing-chart-target ${selectedRow?'is-selected':''}" role="button" tabindex="0" aria-label="Select ${esc(r.id)}: ${esc(format(r.value))}" aria-pressed="${selectedRow}"><title>${esc(r.id)}: ${esc(format(r.value))}</title><text x="${left-12}" y="${y+18}" text-anchor="end" class="chart-tick">${esc(r.id.replace('SEGMENT ','Segment '))}</text><rect x="${Math.min(x(0),x(r.value))}" y="${y}" width="${Math.max(2,Math.abs(x(r.value)-x(0)))}" height="27" rx="4" fill="${segmentChartColors[index]}" fill-opacity="${selectedRow?1:.5}"/><text x="${x(r.value)+8}" y="${y+18}" class="chart-value">${esc(format(r.value))}</text></g>`;
  });
  svg+=`<text x="${left}" y="${top+6*rowHeight+28}" class="chart-axis-label">${esc(marketingLenses.find(l=>l[0]===lens)?.[1]||lens)}</text>`;
  if(d.preference_lens)svg+=`<text x="${left}" y="${top+6*rowHeight+47}" class="chart-tick">Normalization can change rankings; original raw values remain below.</text>`;
  return marketingChartSvg('segment-ranking','Rank segments by the chosen decision lens','The chosen lens changes the ranking, not the forecast or team decisions. Preference lenses are normalized within each segment; revenue and CLV are company allocations.',svg,560,340,true);
}
function marketingTrendChart(d) {
  const left=60,top=28,width=450,height=230,rows=d.trend;
  const values=rows.flatMap(r=>[r.size,r.revenue,r.clv]).filter(v=>v!==null),low=Math.floor(Math.min(100,...values)/10)*10,high=Math.ceil(Math.max(110,...values)/10)*10;
  const y=v=>top+height-(v-low)/(high-low)*height,x=i=>left+i*width/Math.max(1,rows.length-1);
  let svg='';
  for(let i=0;i<=4;i++){
    const value=low+(high-low)*i/4;
    svg+=`<line x1="${left}" x2="${left+width}" y1="${y(value)}" y2="${y(value)}" class="chart-grid"/><text x="${left-10}" y="${y(value)+4}" text-anchor="end" class="chart-tick">${value.toFixed(0)}</text>`;
  }
  rows.forEach((r,i)=>svg+=`<text x="${x(i)}" y="${top+height+24}" text-anchor="middle" class="chart-tick">Round ${r.round}</text>`);
  for(const [key,color,dash] of [['size','#84916e','5 4'],['revenue','#246c54',''],['clv','#aa7b30','9 3']]){
    const valid=rows.map((r,i)=>({value:r[key],i})).filter(p=>p.value!==null);
    svg+=`<polyline points="${valid.map(p=>x(p.i)+','+y(p.value)).join(' ')}" fill="none" stroke="${color}" stroke-width="3" ${dash?'stroke-dasharray="'+dash+'"':''}/>`;
    valid.forEach(p=>svg+=`<circle cx="${x(p.i)}" cy="${y(p.value)}" r="4" fill="${color}"><title>${key}, Round ${rows[p.i].round}: index ${p.value.toFixed(2)}</title></circle>`);
  }
  svg+=`<text x="${left}" y="${top+height+54}" class="chart-axis-label">First reported round = 100 · indexed source series, not forecasts</text>`;
  return marketingChartSvg('segment-trend',d.selected.id+' indexed history','Reported size, company segment revenue and aggregate segment CLV are indexed to their first common observation. Growth divergence does not identify customer penetration or causality.',svg,560,340);
}
function marketingCompositionChart(m,selected) {
  const left=94,width=665,top=25,rowHeight=38;
  let svg='';
  m.segments.forEach((s,i)=>{
    const y=top+i*rowHeight;let offset=0;
    svg+=`<g class="marketing-chart-target ${s.id===selected?'is-selected':''}" role="button" tabindex="0" data-chart-segment="${esc(s.id)}" aria-label="Select ${esc(s.id)} normalized preference profile" aria-pressed="${s.id===selected}"><text x="${left-12}" y="${y+17}" text-anchor="end" class="chart-tick">${esc(s.id.replace('SEGMENT ','Segment '))}</text>`;
    m.attributes.forEach((attr,j)=>{
      const value=s.normalized_preferences[attr],length=value*width;
      svg+=`<rect x="${left+offset}" y="${y}" width="${length}" height="26" fill="${preferenceChartColors[j]}" fill-opacity="${s.id===selected?1:.65}"><title>${esc(s.id)} · ${esc(attr)}: ${(value*100).toFixed(2)}% of preference sum; raw ${s.preferences[attr].toFixed(2)}</title></rect>`;offset+=length;
    });
    if(s.id===selected)svg+=`<rect x="${left-2}" y="${y-2}" width="${width+4}" height="30" fill="none" stroke="#203b32" stroke-width="2"/>`;
    svg+='</g>';
  });
  for(let i=0;i<=4;i++)svg+=`<text x="${left+width*i/4}" y="${top+6*rowHeight+15}" text-anchor="middle" class="chart-tick">${i*25}%</text>`;
  svg+=`<text x="${left}" y="${top+6*rowHeight+44}" class="chart-axis-label">Share of each segment’s preference sum · assumed normalization, not customer percentages</text>`;
  return marketingChartSvg('segment-composition','Compare all six normalized preference profiles','Each row sums to 100% after explicitly normalizing the eight source preference values. This is not the percentage of customers, an investment allocation or an estimated utility function.',svg,820,320,true);
}
function renderMarketingCharts(m) {
  const d=marketingDecisionData(m,marketingSegment,marketingDecisionLens),s=d.selected;
  const change=v=>v===null?'Not available':(v>=0?'+':'')+pct(v);
  const actions={BREADTH:'Test unmet shopping missions and category coverage before adding more lines.',DEPTH:'Identify missing variants and verify incremental inventory/markdown costs before deepening the range.',BRAND:'Test the differentiated product promise; do not assume this means higher-cost purchasing.',ONLINE:'Investigate online discovery and shopping convenience before assuming assortment is the bottleneck.',RETAIL:'Check physical access and in-store execution, including coverage/service capacity.',
    'CUSTOMER SERVICE':'Test service friction and service quality, not spending alone.','SHOPPING EXPERIENCE':'Test the end-to-end experience and discovery, alongside inventory economics.','LOW PRICE':'Check perceived value and actual selling-price definitions before changing the offer.'};
  return `<section id="marketing-analysis" class="marketing-analysis"><div class="panel"><div class="marketing-eyebrow">SEGMENTATION DECISION DASHBOARD</div>${panelHead('Choose a customer focus—not just a bigger assortment','Click a segment in a chart or use the controls. All views stay in sync.')}<div class="marketing-chart-toolbar"><div><label for="marketing-analysis-segment">Selected segment</label><select id="marketing-analysis-segment">${m.segments.map(r=>`<option value="${esc(r.id)}" ${r.id===s.id?'selected':''}>${esc(r.id)}</option>`).join('')}</select></div><div><label for="marketing-decision-lens">Decision lens for the ranking chart</label><select id="marketing-decision-lens">${marketingLenses.map(([key,label])=>`<option value="${esc(key)}" ${key===marketingDecisionLens?'selected':''}>${esc(label)}</option>`).join('')}</select></div></div><div class="marketing-segment-chips" aria-label="Choose customer segment">${m.segments.map((r,i)=>`<button type="button" data-chart-segment="${esc(r.id)}" class="marketing-segment-chip ${r.id===s.id?'selected':''}" aria-pressed="${r.id===s.id}"><i style="background:${segmentChartColors[i]}"></i>${esc(r.id.replace('SEGMENT ','Segment '))}</button>`).join('')}</div><article class="marketing-decision-brief" id="marketing-decision-brief"><h3>${esc(s.id)} · decision brief</h3><div class="marketing-brief-facts"><span>Revenue mix <strong>${pct(s.revenue_share)}</strong></span><span>CLV mix <strong>${pct(s.clv_share)}</strong></span><span>Latest revenue growth <strong>${change(s.revenue_growth)}</strong></span><span>Reported-size growth <strong>${change(s.size_growth)}</strong></span></div><p><strong>Customer need:</strong> ${s.top_preferences.map(a=>`${esc(a)} ${s.preferences[a].toFixed(2)}`).join(' · ')} (raw source measures).</p><p><strong>Test to investigate:</strong> ${actions[s.top_preferences[0]]} Pair the test with a profit/cash constraint; these preferences do not quantify the return.</p><p><strong>Portfolio signal:</strong> CLV mix is ${Math.abs(d.mix_gap_pp).toFixed(2)} percentage points ${d.mix_gap_pp>=0?'above':'below'} current revenue mix. This compares two company allocations—not per-customer value, customer penetration or marginal ROI.</p><p class="small muted">Still needed: segment-by-offering/channel purchases, verified prices, incremental inventory/costs and a controlled or otherwise credible response estimate. No chart changes the team’s plan.</p></article></div><div class="marketing-chart-grid"><article class="panel marketing-chart-panel"><h2>1 / Revenue–CLV portfolio</h2><p class="marketing-copy">Where is current business concentrated versus reported lifetime value? Bubble area represents reported size, not verified buyer count.</p>${marketingPortfolioChart(m,s.id)}<p class="marketing-chart-takeaway"><strong>Use:</strong> compare defending current revenue with investigating a CLV-mix gap. The diagonal means equal mix, not an ideal allocation.</p></article><article class="panel marketing-chart-panel"><h2>2 / Rank by your decision lens</h2><p class="marketing-copy">Different questions produce different priorities. Revenue, CLV and reported size are totals; preference lenses use normalized within-segment weights.</p>${marketingRankingChart(m,d,marketingDecisionLens,s.id)}<p class="marketing-chart-takeaway"><strong>Leader under this lens:</strong> ${esc(d.rankings[0]?.id||'Not available')}. A rank is a descriptive input—not a budget recommendation.</p></article><article class="panel marketing-chart-panel"><h2>3 / Breadth versus depth emphasis</h2><p class="marketing-copy">Separate category-coverage needs from variant-selection needs. Normalization enables profile comparison but assumes the source weights can be scaled this way.</p>${marketingNeedsChart(m,s.id)}<p class="marketing-chart-takeaway"><strong>Use:</strong> investigate breadth for Segment 2; note Segment 6’s weak raw depth preference (0.02). This does not identify lower-/higher-cost purchasing.</p></article><article class="panel marketing-chart-panel"><h2>4 / ${esc(s.id)} growth trajectory</h2><p class="marketing-copy">Compare size, company revenue and aggregate CLV on a common index. Only three source rounds are available.</p>${marketingTrendChart(d)}<div class="marketing-line-legend"><span><i style="background:#84916e"></i>Reported size</span><span><i style="background:#246c54"></i>Company revenue</span><span><i style="background:#aa7b30"></i>Reported CLV</span></div><p class="marketing-chart-takeaway"><strong>Use:</strong> distinguish reported segment expansion from company revenue growth. Neither curve establishes buyer penetration or causal marketing effectiveness.</p></article></div><article class="panel marketing-chart-panel"><h2>5 / Preference composition across all six segments</h2><p class="marketing-copy">Identify which needs dominate each profile. Each row is divided by that segment’s preference sum; the raw values below remain unchanged.</p>${marketingCompositionChart(m,s.id)}<div class="marketing-line-legend">${m.attributes.map((a,i)=>`<span><i style="background:${preferenceChartColors[i]}"></i>${esc(a)}</span>`).join('')}</div><p class="marketing-chart-takeaway"><strong>Use:</strong> compare hypotheses for online/service (Segment 1), breadth/retail (Segment 2), and experience (Segments 3/5). The colored proportions are not population shares or a proposed spending split.</p></article><div class="info">Decision workflow: choose a business objective → inspect segment needs and momentum → formulate a specific test → check inventory/cash constraints in Assortment Lab. Charts are descriptive; no causal forecast or optimal customer allocation is being claimed. Charts can scroll sideways on small screens; exact source values remain in the tables below.</div></section>`;
}
function selectMarketingChartSegment(id) {
  if(!data.marketing?.segments.some(s=>s.id===id))return;
  marketingSegment=id;render();
}
function mountMarketingDecisionEvidence() {
  if(page!=='marketing'||!data.marketing?.available)return;
  const brief=document.getElementById('marketing-decision-brief');if(!brief)return;
  const selected=data.marketing.segments.find(s=>s.id===marketingSegment)||data.marketing.segments[0];
  const narrative=document.createElement('details');narrative.className='marketing-brief-narrative';
  const narrativeTitle=document.createElement('summary');narrativeTitle.textContent='Read the decision brief and suggested test';
  narrative.append(narrativeTitle);brief.querySelectorAll(':scope > p').forEach(p=>narrative.append(p));brief.append(narrative);
  const detail=document.createElement('details');detail.className='marketing-execution-evidence';
  const summary=document.createElement('summary');summary.textContent='Compare this customer need with reported product positions';
  const text=document.createElement('p');text.textContent=marketingPropositionEvidence(data.marketing,selected.top_preferences[0]);
  detail.append(summary,text);brief.append(detail);
}
document.addEventListener('change',event=>{
  if(event.target.id==='marketing-analysis-segment'){selectMarketingChartSegment(event.target.value);document.getElementById('marketing-analysis-segment')?.focus({preventScroll:true});}
  if(event.target.id==='marketing-decision-lens'){marketingDecisionLens=event.target.value;render();document.getElementById('marketing-decision-lens')?.focus({preventScroll:true});}
});
document.addEventListener('click',event=>{const target=event.target.closest('[data-chart-segment]');if(target)selectMarketingChartSegment(target.dataset.chartSegment);});
document.addEventListener('keydown',event=>{const target=event.target.closest('svg [data-chart-segment]');if(target&&(event.key==='Enter'||event.key===' ')){event.preventDefault();selectMarketingChartSegment(target.dataset.chartSegment);}});
