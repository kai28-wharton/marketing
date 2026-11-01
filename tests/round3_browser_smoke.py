"""Latest export-2 / Round-3 workspace, API prediction and offline browser checks."""
import base64
import json
import subprocess
import sys
import tempfile
import threading
import time
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen
from legacy_browser_smoke import CDP, CHROME

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app


def main():
    from round_review import dataset
    original_dataset=dataset
    patcher=patch('round_review.dataset',side_effect=lambda round_id=None:original_dataset(2 if round_id is None else round_id))
    patcher.start()
    approved=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    with tempfile.TemporaryDirectory(prefix='getchells-round3-',dir=approved) as directory:
        profile=Path(directory);server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        process=subprocess.Popen([CHROME,'--headless','--disable-gpu','--no-first-run','--no-default-browser-check',
                                  '--remote-debugging-port=0','--remote-allow-origins=*','--user-data-dir='+directory,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
            try:client.wait("document.querySelector('h1')?.textContent==='Executive overview'")
            except AssertionError:raise AssertionError(client.errors or client.js('document.body.innerText'))
            assert client.js('data.current_round')==2
            assert client.js('data.planning_round')==3
            assert client.js("document.querySelector('.round-pill').textContent.includes('ROUND 3 · R2 ACTUALS')")
            assert client.js("['$561.28M','$10.77M','$255.27M'].every(s=>document.body.innerText.includes(s))")
            assert client.js("!document.body.innerText.includes('A weaker brand')")
            titles={'overview':'Executive overview','marketing':'Marketing Intelligence','segmentation':'Customer segmentation decision','financials':'Financial health','insights/brand':'Decision Insights','insights/finance':'Decision Insights','insights/segments':'Decision Insights','decisions':'Decision studio','recommendations':'Round 3 decision making page'}
            for route,title in titles.items():
                client.js(f"location.hash='{route}'");client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                if route.startswith('insights/'):
                    client.wait(f"!!document.querySelector('#insight-panel-{route.split('/')[1]}')")
                assert client.js("![...document.querySelectorAll('svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))")
                client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
                assert client.js('document.documentElement.scrollWidth<=innerWidth'),route+' mobile overflow'
                client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
                shot=client.call('Page.captureScreenshot',{'format':'png'})
                (approved/('getchells-current-'+route.replace('/','-')+'.png')).write_bytes(base64.b64decode(shot['data']))
            assert client.js("['$74,631,166','$74,000,000','$631,166','The 16-factor decision sheet'].every(s=>document.body.innerText.includes(s))")
            assert client.js("document.querySelectorAll('details summary').length>=16")
            assert client.js("document.querySelector('nav [data-page=recommendations]').textContent.includes('Round 3 decision making page')")
            assert client.js("['Why are so many lower-cost / higher-cost inputs unchanged?','Store count is a decision—not a fixed constraint','Open 1 · funded alternative','Close 5 · conditional'].every(s=>document.body.textContent.includes(s))"),client.js("document.body.textContent")
            assert client.js("!document.querySelector('#load-recommendation')")
            client.js("location.hash='marketing'");client.wait("!!document.querySelector('#segment-select')")
            assert client.js("document.querySelectorAll('[data-marketing-point]').length")==6
            assert client.js("document.body.innerText.includes('marketCLV-round2.csv')")
            assert client.js("document.querySelector('#segment-select').value")=='SEGMENT 3'
            assert client.js("document.body.innerText.includes('FOCUS GROUP')")
            assert client.js("document.body.innerText.includes('WIN SEGMENTS 3 + 5')")
            assert client.js("document.body.innerText.includes('Segment focus group: win 3+5')")
            assert client.js("document.body.innerText.includes('DEFEND · EXISTING VALUE & BREADTH EQUITY')")
            assert client.js("document.body.innerText.includes('1.90')")
            assert client.js("document.body.innerText.includes('Rank #1 is the goal')")
            assert client.js("document.body.innerText.includes('which segment is actually lowest on CLV')")
            assert client.js("document.body.innerText.includes('Strategy verdict: Experience + Brand is the best available strategy')")
            assert client.js("document.body.innerText.includes('Why not the other two pairings?')")
            assert client.js("document.body.innerText.includes('Playbook mapping (MV p9)')")
            assert client.js("document.body.innerText.includes('Competitors already targeting each segment')")
            assert client.js("document.body.innerText.includes('Fit test: Brand and shopping-experience intensity')")
            assert client.js("document.body.innerText.includes('does not hold')")
            assert client.js("document.querySelectorAll('#marketing-scale-fit [data-marketing-point], #marketing-scale-fit [data-segment]').length")>=18
            client.js("document.querySelector('[data-marketing-point=\"SEGMENT 4\"]').dispatchEvent(new MouseEvent('click',{bubbles:true}))")
            assert client.js("document.querySelector('#segment-select').value")=='SEGMENT 4'
            client.js("location.hash='segmentation'");client.wait("!!document.querySelector('#segmentation-lens')")
            assert client.js("document.querySelector('nav [data-page=segmentation]').getAttribute('aria-current')")=='page'
            assert client.js("document.body.innerText.includes('Getchell’s financial capacity')")
            assert client.js("document.body.innerText.includes('5 versus 6')")
            assert client.js("document.body.innerText.includes('not a guaranteed win')")
            assert client.js("document.querySelectorAll('[data-segmentation-member]').length")==5
            client.js("document.querySelector('#segmentation-example').click()")
            assert client.js("document.querySelector('#segmentation-one-liner').innerText.includes('Targeting segments 2, 4, 5 suggests a strong in-store offer')")
            assert client.js("document.querySelector('#segmentation-portfolio').innerText.includes('$705.93M')")
            client.js("document.querySelector('#segmentation-lens').value='clv';document.querySelector('#segmentation-lens').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#segmentation-ranking tbody tr th').textContent")=='SEGMENT 2'
            client.js("document.querySelector('#segmentation-lens').value='SHOPPING EXPERIENCE';document.querySelector('#segmentation-lens').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#segmentation-ranking tbody tr th').textContent")=='SEGMENT 5'
            client.js("document.querySelector('[data-segmentation-member=\"SEGMENT 6\"]').click()")
            assert client.js("segmentationGroup.includes('SEGMENT 6')")
            assert client.js("data.strategy.policy.secondary_segment")=='SEGMENT 5'
            assert client.js('plan.online')==8_000_000
            assert abs(client.js("segmentationFocusShare(data.segment_decision.rows.find(s=>s.id==='SEGMENT 3'))")-.7/1.35)<1e-10
            assert client.js("segmentationHurdle(10000000,{cost:1000000,margin:20,lift:10}).net")==-800000
            assert client.js("segmentationHurdle(10000000,{cost:1000000,margin:20,lift:10}).requiredRevenue")==5000000
            assert client.js("segmentationHurdle(10000000,{cost:1000000,margin:0,lift:10}).requiredRevenue") is None
            assert client.js("segmentationHurdle(10000000,{cost:0,margin:0,lift:0}).requiredLift")==0
            assert client.js("segmentationHurdle(10000000,{cost:0,margin:20,lift:10}).roi") is None
            assert client.js("segmentationHurdle(10000000,{cost:0,margin:20,lift:-10}).net")==-200000
            for invalid in ['null','NaN','Infinity','-1']:
                assert client.js(f"segmentationHurdle(10000000,{{cost:{invalid},margin:20,lift:10}})") is None
            assert client.js("segmentationHurdle(10000000,{cost:10,margin:101,lift:10})") is None
            assert client.js("segmentationHurdle(10000000,{cost:10,margin:20,lift:-101})") is None
            client.js("document.querySelector('[data-segmentation-member=\"SEGMENT 3\"]').click()")
            assert not client.js("segmentationGroup.includes('SEGMENT 3')")
            assert client.js("document.querySelector('#segmentation-portfolio').innerText.includes('not abandoned')")
            assert client.js("data.strategy.policy.primary_segment")=='SEGMENT 3'
            client.js("document.querySelector('#seg-compare-right').value='SEGMENT 6';document.querySelector('#seg-compare-right').dispatchEvent(new Event('change',{bubbles:true}))")
            client.js("document.querySelector('#seg-compare-normalized').click()")
            assert client.js("document.querySelector('#seg-comparison-results').innerText.includes('51.9%')")
            client.js("document.querySelector('#seg-compare-rival').value='BESTCO';document.querySelector('#seg-compare-rival').dispatchEvent(new Event('change',{bubbles:true}))")
            client.js("document.querySelector('#segmentation-copy-comparison').click()")
            assert client.js("document.querySelector('#seg-case-1-segment').value")=='SEGMENT 6'
            client.js("document.querySelector('#seg-case-1-margin').value='';document.querySelector('#seg-case-1-margin').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#seg-hurdle-results').innerText.includes('Enter valid assumptions')")
            client.js("document.querySelector('#seg-case-1-margin').value=30;document.querySelector('#seg-case-1-margin').dispatchEvent(new Event('input',{bubbles:true}))")
            note='Debate note: </script><script>window.__segInjected=true</script> & compare 3 versus 6'
            client.js("document.querySelector('#seg-debate-note').value="+json.dumps(note)+";document.querySelector('#seg-debate-note').dispatchEvent(new Event('input',{bubbles:true}))")
            downloads=profile/'downloads';downloads.mkdir()
            client.call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(downloads)})
            client.js("document.querySelector('#segmentation-download').click()")
            client.wait("document.querySelector('#segmentation-download-status').textContent.startsWith('Download prepared')")
            downloaded=downloads/'getchells-customer-segmentation-decision.html'
            for _ in range(100):
                if downloaded.exists():break
                time.sleep(.05)
            assert downloaded.exists(),'Actual HTML download did not complete'
            assert '"report_page":"segmentation"' in downloaded.read_text()
            client.call('Page.reload');client.wait("document.querySelector('h1')?.textContent==='Customer segmentation decision'")
            client.js("location.hash='decisions'");client.wait("!!document.querySelector('#impact-form')")
            assert client.js("document.body.innerText.includes('rank #1 in Experience')")
            assert client.js("document.querySelectorAll('[data-factor]').length")==16
            assert client.js('plan.experience')==15_000_000
            assert client.js('plan.coverage')==236
            assert client.js('result.net_income')==10_768_169
            assert client.js('currentScenarioBudget') is None
            assert client.js("document.querySelector('#current-budget-summary').innerText.includes('Unavailable')")
            client.js("document.querySelector('#use-budget-arm').click()")
            assert abs(client.js('currentScenarioBudget')-78_579_215.96)<.01
            assert client.js("document.querySelector('#current-budget-summary').innerText.includes('$7,157,216')")
            client.js("document.querySelector('#factor-online').value=8500000;document.querySelector('#factor-online').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js('impactStale')
            assert client.js("document.querySelector('#current-budget-summary').innerText.includes('$71,922,000')")
            client.js("document.querySelector('#impact-form').requestSubmit()")
            client.wait('!impactBusy && !impactStale && result.decisions.online===8500000')
            assert client.js('result.scores.FRICTIONLESS')>3.1
            assert client.js('result.market_value') is None
            assert client.js('data.team.decisions.online')==8_000_000
            client.js("document.querySelector('#reset-plan').click()")
            assert client.js('plan.online')==8_000_000
            assert client.js('result.net_income')==10_768_169
            client.js("location.hash='insights/segments'");client.wait("!!document.querySelector('#insight-panel-segments')")
            client.call('Page.reload');client.wait("!!document.querySelector('#insight-panel-segments')")
            with urlopen(base+'/marketing-report') as response:html=response.read()
            report=profile/'marketing-current.html';report.write_bytes(html)
            client.call('Network.enable');client.call('Network.emulateNetworkConditions',{'offline':True,'latency':0,'downloadThroughput':0,'uploadThroughput':0})
            client.call('Page.navigate',{'url':report.as_uri()});client.wait("document.querySelector('h1')?.textContent==='Marketing Intelligence'")
            assert client.js('data.current_round')==2
            assert client.js("document.querySelector('#report-generated').textContent.includes('export 2')")
            assert client.js("document.body.innerText.includes('$561.28M')")
            assert client.js("document.body.innerText.includes('Strategy verdict: Experience + Brand is the best available strategy')")
            assert client.js("document.body.innerText.includes('Segment focus group: win 3+5')")
            assert not client.js("!!document.querySelector('nav,script[src],link[rel=stylesheet],[data-factor]')")
            client.js("document.querySelector('#segment-select').value='SEGMENT 6';document.querySelector('#segment-select').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('.segment-brief').innerText.includes('$220.34M')")
            client.js("location.hash='segmentation'");client.wait("document.querySelector('h1')?.textContent==='Customer segmentation decision'")
            client.js("document.querySelector('#segmentation-example').click()")
            assert client.js("document.querySelector('#segmentation-one-liner').innerText.includes('Targeting segments 2, 4, 5')")
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth<=innerWidth')
            client.call('Page.navigate',{'url':downloaded.as_uri()})
            client.wait("document.querySelector('h1')?.textContent==='Customer segmentation decision'")
            assert client.js("document.querySelector('#seg-compare-right').value")=='SEGMENT 6'
            assert client.js("document.querySelector('#seg-compare-rival').value")=='BESTCO'
            assert client.js("document.querySelector('#seg-compare-normalized').checked")
            assert client.js("document.querySelector('#seg-case-1-margin').value")=='30'
            assert client.js("document.querySelector('#seg-case-1-segment').value")=='SEGMENT 6'
            assert client.js("document.querySelector('#seg-debate-note').value")==note
            assert not client.js("!!window.__segInjected")
            assert not client.js("segmentationGroup.includes('SEGMENT 3')")
            assert not client.js("'decisions' in data.team || 'draft' in data.strategy")
            assert client.js('document.documentElement.scrollWidth<=innerWidth')
            client.js("document.querySelector('#seg-case-0-margin').value=0;document.querySelector('#seg-case-0-margin').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#seg-hurdle-results').innerText.includes('No finite hurdle')")
            offline_downloads=profile/'offline-downloads';offline_downloads.mkdir()
            client.call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(offline_downloads)})
            client.js("document.querySelector('#segmentation-download').click()")
            client.wait("document.querySelector('#segmentation-download-status').textContent.startsWith('Download prepared')")
            offline_download=offline_downloads/'getchells-customer-segmentation-decision.html'
            for _ in range(100):
                if offline_download.exists():break
                time.sleep(.05)
            assert offline_download.exists(),'Offline re-download did not complete'
            client.call('Page.navigate',{'url':offline_download.as_uri()})
            client.wait("document.querySelector('h1')?.textContent==='Customer segmentation decision'")
            assert client.js("document.querySelector('#seg-case-0-margin').value")=='0'
            client.js("document.querySelector('#segmentation-reset').click()")
            assert client.js("segmentationGroup.join(',')")=='SEGMENT 3,SEGMENT 5'
            assert client.js("document.querySelector('#seg-case-1-margin').value")=='20'
            client.call('Page.reload');client.wait("document.querySelector('h1')?.textContent==='Customer segmentation decision'")
            assert client.js("document.querySelector('#seg-case-0-margin').value")=='0'
            assert not client.errors,client.errors
            print('PASS: all current pages, correct timeline, R2 actuals and submitted baseline, CSV fair value, current segment CLV, mobile/deep links, confirmed R3 decision budget, conditional prediction/reset and offline report.')
        finally:
            if client:client.sock.close()
            process.terminate();process.wait(timeout=15)
            server.shutdown();server.server_close();thread.join()
            patcher.stop()


if __name__=='__main__':main()
