"""Archived export-1 browser workflow; current checks are in browser_smoke.py."""
import base64
import json
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from legacy_browser_smoke import CDP, CHROME

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app


def main():
    approved=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    with tempfile.TemporaryDirectory(prefix='getchells-round1-',dir=approved) as directory:
        profile=Path(directory)
        server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        process=subprocess.Popen([CHROME,'--headless','--disable-gpu','--no-first-run','--no-default-browser-check',
                                  '--remote-debugging-port=0','--remote-allow-origins=*','--user-data-dir='+directory,'about:blank'],
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        client=None
        try:
            port_file=profile/'DevToolsActivePort'
            for _ in range(100):
                if port_file.exists():break
                time.sleep(.1)
            port=int(port_file.read_text().splitlines()[0])
            with urlopen(f'http://127.0.0.1:{port}/json/list') as response:target=next(p for p in json.load(response) if p['type']=='page')
            client=CDP(target['webSocketDebuggerUrl']);client.call('Page.enable');client.call('Runtime.enable')
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.call('Page.navigate',{'url':base})
            client.wait("document.querySelector('h1')?.textContent==='Executive overview'")
            assert client.js("document.querySelector('#overview-marketing-position').closest('.panel').querySelector('h2').textContent")=='Marketing position: protect experience, diagnose Brand'
            assert client.js("document.querySelectorAll('#overview-marketing-position table').length")==1
            assert client.js("document.querySelectorAll('#overview-marketing-position svg').length")==1
            assert client.js("[...document.querySelectorAll('#overview-marketing-position thead th')].map(n=>n.textContent).join(',')")=='Quadrant,Round 0,Round 1,Change,Rank,R1 leader,Fair value,Gap'
            assert client.js("['3.500','4.300','5.100','3.600','+0.200','-1.800','+1.100'].every(t=>document.querySelector('#overview-marketing-position').textContent.includes(t))")
            assert client.js("!document.querySelector('#overview-marketing-position').textContent.includes('Exported floor R1')")
            assert client.js("document.querySelector('#overview-marketing-position').textContent.includes('Fair value = the CSV’s FAIR VALUE benchmark')")
            assert client.js("document.querySelectorAll('nav [data-page]').length")==6
            assert client.js("[...document.querySelectorAll('nav [data-page]')].map(a=>a.dataset.page).join(',')")=='overview,marketing,financials,insights,decisions,recommendations'
            assert client.js("['$481.93M','$8.40M','$248.97M','3.7'].every(t=>document.body.innerText.includes(t))")
            assert client.js("!document.querySelector('nav').innerText.match(/Assortment|Scenario|Year 2/)")
            for page,title in [('marketing','Marketing Intelligence'),('financials','Financial health'),('insights/brand','Decision Insights'),('decisions','Decision studio'),('recommendations','Round 1 decision recommendation')]:
                client.js(f"location.hash='{page}'");client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                assert client.js("document.querySelectorAll('svg').length")>=1 or page in ('decisions','recommendations')
                client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
                assert client.js('document.documentElement.scrollWidth<=innerWidth'),page+' mobile overflow'
                client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            untouched=client.js('JSON.stringify(plan)')
            assert client.js("document.body.innerText.includes('ROUND 1 DECISIONS → ROUND 2 OUTCOMES')")
            assert client.js("document.body.innerText.includes('not submission-ready')")
            assert client.js("document.body.innerText.includes('$71,422,000') && document.body.innerText.includes('$1,608,000')")
            assert client.js("document.body.innerText.includes('full parity is deferred in Round 2')")
            assert client.js("document.body.innerText.includes('$27,608,000') && document.body.innerText.includes('$14,000,000')")
            assert client.js("document.body.innerText.includes('Brand already meets CSV fair value')")
            assert client.js("!document.body.innerText.includes('BUDGET STATUS') && !document.body.innerText.includes('Both funding cuts')")
            assert client.js("data.strategy.recommendations.length")==16
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            (approved/'getchells-round1-recommendations.png').write_bytes(base64.b64decode(shot['data']))
            client.call('Page.reload')
            client.wait("document.querySelector('h1')?.textContent==='Round 1 decision recommendation'")
            assert client.js('JSON.stringify(plan)')==untouched
            client.js("location.hash='insights/brand'")
            client.wait("!!document.querySelector('#insight-panel-brand')")
            assert client.js("document.querySelectorAll('[role=tab]').length")==3
            assert client.js("document.body.innerText.includes('Depth positions account for the observed score decline—not its proven cause')")
            assert client.js("document.body.innerText.includes('Carrying high-quality brands (private/national) = Brand')")
            assert client.js("document.body.innerText.includes('Quality is a documented driver—not a zero-impact factor')")
            assert client.js("[...document.querySelectorAll('[data-brand-reason]')].map(n=>n.dataset.brandReason).join(',')")=='high_depth,low_depth'
            assert client.js("['-1.90','-1.00','+0.30','65.5%','34.5%','-2.60'].every(t=>document.querySelector('#insight-panel-brand').innerText.includes(t))")
            assert client.js("document.querySelectorAll('.brand-explanation').length")==2
            assert client.js("[...document.querySelectorAll('.brand-explanation')].every(n=>{const a=n.querySelector('.brand-what').getBoundingClientRect(),b=n.querySelector('.brand-why').getBoundingClientRect();return b.left>a.right&&Math.abs(a.top-b.top)<1})"),'Brand conclusions and evidence should be side by side on desktop'
            assert client.js("document.querySelector('[data-brand-support=high_depth]').innerText.includes('1.2 − 5 = -3.80')")
            assert client.js("document.querySelector('[data-brand-support=high_depth]').innerText.includes('-3.80 × 0.5 = -1.90')")
            assert client.js("document.querySelector('[data-brand-support=low_depth]').innerText.includes('1.7 − 3.7 = -2.00')")
            assert client.js("['6.35','3.75','-0.05','residual cancels','quality → Brand, not this numerical formula'].every(t=>document.querySelector('#brand-reconciliation .brand-why').innerText.includes(t))")
            assert client.js('data.insights.brand.parameter_impact.within_005')==14
            assert client.js('data.team.decisions.low_depth')==25
            assert client.js("!document.querySelector('[data-brand-factor],#simulation-rules,#holistic-source-audit')")
            assert client.js("!document.querySelector('#insight-panel-brand').innerText.match(/Cost-plus pricing|controlled test designs|Legacy model audit|Fund the repair|two-quadrant strategies/)")
            assert client.js("document.querySelector('#insight-panel-brand a[href=\"#decisions\"]')!==null")
            client.js("document.querySelector('#brand-evidence').open=true")
            assert client.js("document.querySelector('#brand-evidence').innerText.includes('Sheet1!B4') && document.querySelector('#brand-evidence').innerText.includes('Sheet1!B8')")
            assert client.js("document.querySelector('#brand-evidence').innerText.includes('not independently validated')")
            client.js("document.querySelector('[data-brand-reason=high_depth] [data-evidence]').dispatchEvent(new PointerEvent('pointerover',{bubbles:true}))")
            client.wait("!!document.querySelector('#number-evidence')")
            assert client.js("document.querySelector('[role=tooltip]').innerText.includes('0.5 × (1.2 − 5) = -1.90')")
            assert client.js("document.querySelector('[role=tooltip]').innerText.includes('not supplied by slide 14')")
            client.js("document.querySelector('[data-evidence]').dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")
            assert client.js("!document.querySelector('#number-evidence')")
            client.call('Page.bringToFront')
            client.js("document.activeElement.blur();document.querySelector('[data-evidence]').focus()")
            assert client.js("document.querySelector('[role=tooltip]').innerText.includes('Sheet1!B10 = 6')")
            assert client.js("document.querySelector('[role=tooltip]').innerText.includes('historical 5 → 6 change is not verified')")
            assert client.js("document.querySelector('[data-evidence]').getAttribute('aria-describedby')==='number-evidence'")
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            client.js("document.querySelector('[data-evidence]').click()")
            assert client.js("(()=>{const r=document.querySelector('[role=tooltip]').getBoundingClientRect();return r.left>=0&&r.right<=innerWidth&&r.top>=0&&r.bottom<=innerHeight})()"),'Evidence popup mobile overflow'
            assert client.js('document.documentElement.scrollWidth<=innerWidth'),'Expanded Brand evidence mobile overflow'
            assert client.js("[...document.querySelectorAll('.brand-explanation')].every(n=>{const a=n.querySelector('.brand-what').getBoundingClientRect(),b=n.querySelector('.brand-why').getBoundingClientRect();return b.top>=a.bottom&&Math.abs(a.left-b.left)<1})"),'Brand evidence should stack below conclusions on mobile'
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.js("document.querySelector('#insight-tab-finance').click()")
            client.wait("!!document.querySelector('#insight-panel-finance')")
            assert client.js("document.querySelector('#insight-tab-finance').getAttribute('aria-selected')")=='true'
            assert client.js("document.body.innerText.includes('−$4.60M') && document.body.innerText.includes('2.68 pp')")
            for tab in ('brand','finance','segments'):
                client.js(f"location.hash='insights/{tab}'")
                client.wait(f"!!document.querySelector('#insight-panel-{tab}')")
                client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
                assert client.js('document.documentElement.scrollWidth<=innerWidth'),'Insights '+tab+' mobile overflow'
                assert client.js("![...document.querySelectorAll('svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))")
                client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
                shot=client.call('Page.captureScreenshot',{'format':'png'})
                (approved/f'getchells-insights-{tab}.png').write_bytes(base64.b64decode(shot['data']))
            assert client.js("document.body.innerText.includes('Segment 6') && document.body.innerText.includes('Segment 4')")
            assert client.js("document.body.innerText.includes('4.17%') && document.body.innerText.includes('cost tier ≠ quadrant strategy')")
            client.js("document.querySelector('#segment-diagnostics').open=true")
            client.js("document.querySelector('#insight-crosswalk').value='product';document.querySelector('#insight-crosswalk').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js('insightLens')=='product'
            assert client.js("document.querySelector('#segment-diagnostics').open")
            client.js("document.querySelector('#insight-segment').value='SEGMENT 2';document.querySelector('#insight-segment').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js('insightSegment')=='SEGMENT 2'
            assert client.js('JSON.stringify(plan)')==untouched
            client.js("document.querySelector('#insight-tab-segments').dispatchEvent(new KeyboardEvent('keydown',{key:'ArrowLeft',bubbles:true}))")
            client.wait("!!document.querySelector('#insight-panel-finance')")
            assert client.js('document.activeElement.id')=='insight-tab-finance'
            client.call('Page.reload');client.wait("!!document.querySelector('#insight-panel-finance')")
            client.js("location.hash='decisions'");client.wait("!!document.querySelector('#impact-form')")
            assert client.js("document.querySelectorAll('[data-factor]').length")==16
            assert client.js("document.querySelectorAll('.studio-group').length")==4
            assert client.js("!document.querySelector('#studio-optimizer').open && !document.querySelector('#studio-probes').open")
            assert client.js("document.querySelector('#strategy-checks').textContent.includes('Experience: our strongest quadrant')")
            assert client.js("document.querySelector('#strategy-checks').innerText.includes('Needs attention')")
            assert client.js('plan.online')==6_500_000
            assert client.js('result.scores.BRAND')==3.7
            assert client.js("document.querySelectorAll('.review-kahn>div').length")==4
            assert client.js('result.net_income')==8_399_905
            assert client.js("document.querySelector('#studio-budget-baseline').textContent")=='$69,814,000'
            assert client.js("document.querySelector('#studio-budget-extra').textContent")=='$1,608,000'
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$1,608,000'
            assert client.js("Object.keys(data.team.decisions).every(k=>plan[k]===data.team.decisions[k])")
            assert client.js("document.querySelectorAll('#studio-recommendation-comparison tbody tr').length")==16
            client.js("document.querySelector('#factor-experience').value=14000000;document.querySelector('#factor-experience').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$608,000'
            assert client.js("document.querySelector('#factor-experience').closest('.studio-factor').classList.contains('draft-changed')")
            assert client.js("document.querySelector('#factor-delta-experience').textContent.includes('+$1,000,000')")
            assert client.js('result.decisions.experience')==13_000_000,'Budget updates without recalculating predictions'
            client.js("document.querySelector('#factor-vendor').value=27608000;document.querySelector('#factor-vendor').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$0'
            client.js("document.querySelector('#factor-vendor').value=27609000;document.querySelector('#factor-vendor').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$1,000'
            assert client.js("document.querySelector('#studio-budget-left').classList.contains('negative')")
            client.js("document.querySelector('#factor-vendor').value='';document.querySelector('#factor-vendor').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='Unavailable'
            client.js("document.querySelector('#reset-plan').click()")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$1,608,000'
            client.js("document.querySelector('#factor-online').value=7500000;document.querySelector('#factor-online').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js('impactStale')
            assert client.js("document.querySelector('#impact-status').innerText.includes('STALE')")
            client.js("document.querySelector('#impact-form').requestSubmit()")
            client.wait('!impactBusy && !impactStale && result.decisions.online===7500000')
            assert client.js('result.scores.FRICTIONLESS>3.3')
            assert client.js("document.querySelector('#impact-status').innerText.includes('Conditional')")
            assert client.js('data.team.decisions.online')==6_500_000
            assert client.js('result.market_value') is None
            assert client.js("document.querySelector('#impact-results').innerText.includes('Unquantified')")
            assert client.js('probes.length')==16
            assert client.js("document.body.innerText.includes('Definitions reviewed:')")
            assert client.js("document.querySelectorAll('[data-economic]').length")>=10
            client.js("document.querySelector('#studio-optimizer').open=true;document.querySelector('#economic-inventory_holding_rate').closest('details').open=true")
            client.js("document.querySelector('#optimizer-budget').value=72000000;document.querySelector('#optimizer-cash').value=2000000;document.querySelector('#opt-max-online').value=8000000;document.querySelector('#optimizer-form').requestSubmit()")
            client.wait("document.querySelector('#optimizer-output').innerText.includes('blocked')")
            assert client.js("document.querySelector('#optimizer-output').innerText.includes('new_capital_depreciation_rate')")
            for key,value in [('inventory_holding_rate',0),('inventory_financing_rate',.08),('new_capital_depreciation_rate',.1)]:
                client.js(f"document.querySelector('#economic-{key}').value={value};document.querySelector('#economic-{key}').dispatchEvent(new Event('input',{{bubbles:true}}))")
            assert client.js('impactStale')
            client.js("document.querySelector('#impact-form').requestSubmit()")
            client.wait('!impactBusy && !impactStale && result.economics.inventory_holding_rate===0')
            client.js("document.querySelector('#optimizer-form').requestSubmit()")
            client.wait("document.querySelector('#optimizer-output').innerText.includes('Calculation-verified')")
            assert client.js("document.querySelector('#optimizer-output').innerText.includes('predictive accuracy not established')")
            assert client.js('plan.online')==7_500_000,'Optimizer must not adopt a candidate'
            client.js("document.querySelector('#optimizer-goal').value='market_value';document.querySelector('#optimizer-form').requestSubmit()")
            client.wait("document.querySelector('#optimizer-output').innerText.includes('not fixed P/E')")
            client.js("document.querySelector('#optimizer-goal').value='profit'")
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            (approved/'getchells-round1-studio.png').write_bytes(base64.b64decode(shot['data']))
            client.js("document.querySelector('#probe-direction').value='decrease';document.querySelector('#probe-direction').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#probe-direction').value")=='decrease'
            client.js("document.querySelector('#factor-high_depth').value=15;document.querySelector('#factor-high_depth').dispatchEvent(new Event('input',{bubbles:true}));document.querySelector('#impact-form').requestSubmit()")
            client.wait("!impactBusy && !impactStale && result.unresolved_model_channels.includes('brand_depth_response')")
            assert client.js("document.querySelector('[data-brand-score] strong').textContent.includes('3.70')")
            assert client.js("document.querySelector('[data-brand-score] .partial-score-label').textContent")=='Partial'
            assert client.js("document.querySelector('#brand-prediction-note').textContent.includes('10 → 15')")
            assert client.js("document.querySelector('#brand-prediction-note').textContent.includes('not the full prediction')")
            assert client.js("result.score_diagnostics.BRAND.full_prediction") is None
            client.js("document.querySelector('#optimizer-form').requestSubmit()")
            client.wait("document.querySelector('#optimizer-output').innerText.includes('Brand depth response')")
            client.js("document.querySelector('#factor-high_depth').value=-1;document.querySelector('#factor-high_depth').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#factor-high_depth').getAttribute('aria-invalid')")=='true'
            assert client.js('impactStale')
            client.js("document.querySelector('#reset-plan').click()")
            assert client.js('result.net_income')==8_399_905
            assert not client.js('impactStale')
            assert client.js("document.querySelector('#impact-status').innerText.includes('Conditional')")
            client.js("location.hash='recommendations'")
            client.wait("!!document.querySelector('#load-recommendation')")
            client.js("document.querySelector('#load-recommendation').click()")
            client.wait("page==='decisions' && !impactBusy && !impactStale && result.decisions.high_depth===10")
            assert client.js("Object.keys(data.strategy.draft).every(k=>plan[k]===data.strategy.draft[k]&&result.decisions[k]===data.strategy.draft[k])")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$0'
            assert client.js("document.querySelector('#studio-budget-spend').textContent")=='$71,422,000'
            assert client.js("!result.unresolved_model_channels.includes('brand_depth_response')")
            assert client.js("document.querySelector('[data-brand-score] strong').textContent.includes('3.70')")
            assert client.js("!document.querySelector('#brand-prediction-note')")
            assert client.js("[...document.querySelectorAll('#strategy-checks tbody tr')].find(r=>r.textContent.includes('Brand: CSV fair-value parity')).textContent.includes('Pass in local model')")
            assert client.js("data.team.decisions.high_depth===10 && data.team.decisions.low_depth===25")
            client.js("document.querySelector('#reset-plan').click()")
            assert client.js("document.querySelector('#studio-budget-left').textContent")=='$1,608,000'
            client.js("location.hash='marketing'");client.wait("!!document.querySelector('#segment-select')")
            assert client.js("document.querySelector('#segment-select').value")=='SEGMENT 6'
            assert client.js("document.querySelector('#marketing-strategy').innerText.includes('Segment 6 → 4')")
            assert client.js("document.querySelectorAll('[data-marketing-point]').length")==6
            assert client.js("document.querySelector('#marketing-strategy-plots').innerText.includes('up but left')")
            assert client.js("document.querySelector('#marketing-strategy-plots').innerText.includes('No future point')")
            assert client.js("document.querySelector('[data-marketing-point=\"SEGMENT 6\"]').getAttribute('aria-pressed')")=='true'
            studioPlan=client.js('JSON.stringify(plan)')
            client.js("document.querySelector('[data-marketing-point=\"SEGMENT 5\"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))")
            assert client.js("document.querySelector('#segment-select').value")=='SEGMENT 5'
            assert client.js("document.activeElement.id")=='segment-select'
            assert client.js("document.querySelector('.segment-brief').innerText.includes('Protect Experience-led retention')")
            client.js("document.querySelector('[data-marketing-point=\"SEGMENT 4\"]').dispatchEvent(new MouseEvent('click',{bubbles:true}))")
            assert client.js("document.querySelector('#segment-select').value")=='SEGMENT 4'
            assert client.js("document.querySelector('.segment-brief').innerText.includes('fastest-growing')")
            client.js("document.querySelector('#segment-lens').value='growth';document.querySelector('#segment-lens').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js('lens')=='growth'
            assert client.js('JSON.stringify(plan)')==studioPlan
            assert client.js("document.body.innerText.includes('FAIR VALUE') && document.body.innerText.includes('Unavailable')")
            assert client.js("![...document.querySelectorAll('svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))")
            screenshot=client.call('Page.captureScreenshot',{'format':'png'})
            (approved/'getchells-round1-marketing.png').write_bytes(base64.b64decode(screenshot['data']))
            client.js("document.querySelector('#marketing-strategy-plots').scrollIntoView()")
            screenshot=client.call('Page.captureScreenshot',{'format':'png'})
            (approved/'getchells-marketing-strategy-plots.png').write_bytes(base64.b64decode(screenshot['data']))
            # Download from the actual live route, then open file:// with network disabled.
            with urlopen(base+'/marketing-report') as response:html=response.read()
            report=profile/'getchells-marketing-intelligence.html';report.write_bytes(html)
            client.call('Network.enable')
            client.call('Network.emulateNetworkConditions',{'offline':True,'latency':0,'downloadThroughput':0,'uploadThroughput':0})
            client.call('Page.navigate',{'url':report.as_uri()})
            client.wait("document.querySelector('h1')?.textContent==='Marketing Intelligence'")
            assert not client.js("!!document.querySelector('nav,script[src],link[rel=stylesheet],iframe')")
            assert not client.js("!!document.querySelector('[data-factor]')")
            assert client.js("document.body.innerText.includes('$481.93M')")
            assert client.js("document.querySelectorAll('[data-marketing-point]').length")==6
            assert client.js("document.querySelector('#marketing-strategy').innerText.includes('Segment 6 → 4')")
            client.js("document.querySelector('#segment-select').value='SEGMENT 6';document.querySelector('#segment-select').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('.segment-brief h3').innerText.includes('SEGMENT 6')")
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth<=innerWidth'),'Offline marketing mobile overflow'
            client.call('Page.reload');client.wait("!!document.querySelector('#segment-select')")
            assert client.js("document.querySelector('#segment-select').value")=='SEGMENT 6'
            assert not client.errors,client.errors
            print('PASS: six-page navigation, strategy recommendations, STP evidence, crosswalk controls, keyboard/deep-link/mobile checks, and no plan mutation.')
            print('PASS: current Round 1 actuals, all sixteen factors, isolated sensitivity, invalid/stale guards, reset, segment controls and mobile layouts.')
            print('PASS: current marketing HTML opens file:// with network disabled; no other pages, external assets or decision controls.')
        finally:
            if client:client.sock.close()
            process.terminate();process.wait(timeout=15)
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
