"""Completed-simulation pages, controls, mobile layout and offline exports."""
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from legacy_browser_smoke import CDP, CHROME
import app


def main():
    approved=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    workbooks=[p for p in (app.ROOT/'decision_making').rglob('*.xlsx') if not p.name.startswith('~$')]
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in workbooks}
    routes={'overview':'Executive overview','stp':'STP decision: how we chose target segments','segmentation':'Customer segmentation analysis',
            'marketvalue':'Market value analysis','wacc':'WACC impact analysis'}
    with tempfile.TemporaryDirectory(prefix='getchells-final-',dir=approved) as directory:
        profile=Path(directory);server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
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
            with urlopen(f'http://127.0.0.1:{port}/json/list') as response:
                target=next(p for p in json.load(response) if p['type']=='page')
            client=CDP(target['webSocketDebuggerUrl']);client.call('Page.enable');client.call('Runtime.enable')
            client.call('Page.navigate',{'url':base+'/#overview'})
            client.wait("document.querySelector('h1')?.textContent==='Executive overview'")
            assert client.js('data.current_round')==8
            assert client.js('data.final_review.snapshot_count')==9
            assert client.js("document.querySelector('#content').textContent.includes('Late execution, incomplete parity')")
            assert client.js("document.querySelector('#content').textContent.includes('$1038.04M')")
            assert client.js("document.querySelector('.round-pill').textContent.includes('FINAL R1–R8 REVIEW')")
            for route,title in routes.items():
                client.js(f"location.hash='{route}'");client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                assert not client.js("document.querySelector('#content').textContent.includes('Round 9 planning')"),route
                assert client.js("![...document.querySelectorAll('svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))"),route
                if route=='overview':
                    assert client.js("document.querySelectorAll('#exec-objective-timeline tbody tr').length===4")
                    assert client.js("document.querySelectorAll('#exec-objective-timeline .review-badge').length===32")
                    assert client.js("document.querySelector('#exec-objective-timeline').textContent.includes('R0 baseline')")
                    assert client.js("document.querySelector('#content').textContent.includes('CUSTOMER LIFETIME VALUE')")
                    assert client.js("document.querySelector('#content').textContent.includes('$818.47M')")
                    assert client.js("document.querySelector('#content').textContent.includes('$1851.25M')")
                    assert client.js("document.querySelector('#content').textContent.includes('2.26×')")
                    for chart in ('exec-target-mix-chart','exec-growth-chart','exec-value-chart','exec-income-chart','exec-clv-chart','exec-debt-chart','exec-wacc-chart'):
                        assert client.js(f"document.querySelectorAll('#{chart} svg').length===1"),chart
                    assert client.js("document.querySelector('#exec-growth-chart').textContent.includes('31.6%')")
                    assert client.js("document.querySelector('#exec-objective-timeline').textContent.includes('1/8')")
                if route=='stp':
                    assert client.js("document.querySelectorAll('#stp-fit-chart svg').length===1")
                    assert client.js("document.querySelectorAll('#stp-need-map .stp-map-point').length===6")
                    assert client.js("document.querySelectorAll('#stp-competitor-map .stp-map-point').length===7")
                    assert client.js("document.querySelectorAll('#stp-competitor-map [data-label=\"FAIR VALUE\"]').length===0")
                    assert client.js("document.querySelectorAll('#stp-scale-chart svg').length===1")
                    assert client.js("document.querySelectorAll('.stp-needs-table .heat-cell').length===48")
                    assert client.js("document.querySelector('#content').textContent.includes('R8 winners are not used')")
                    assert client.js("document.querySelector('#content').textContent.includes('0.30')")
                if route=='segmentation':
                    assert client.js("document.querySelector('#content').textContent.includes('S6 second')")
                    assert not client.js("document.querySelector('#content').textContent.includes('S5 second')")
                    assert client.js("document.querySelector('#content').textContent.includes('S3+S6')")
                    assert client.js("document.querySelectorAll('#segment-mix-chart svg').length===1")
                    assert client.js("document.querySelectorAll('#segment-growth-chart svg').length===1")
                    assert client.js("document.querySelectorAll('.heat-table .heat-cell').length===48")
                    assert client.js("document.querySelectorAll('#segment-phase-chart svg').length===1")
                    assert client.js("document.querySelectorAll('#segment-spend-chart svg').length===1")
                    assert client.js("document.querySelectorAll('#segment-capability-chart svg').length===1")
                    assert client.js("document.querySelectorAll('.seg-priority-grid article').length===4")
                    assert client.js("document.querySelector('#content').textContent.includes('103.2%')")
                    assert client.js("document.querySelector('#content').textContent.includes('$6.63M')")
                    assert client.js("document.querySelector('#content').textContent.includes('30.7%')")
                    client.js("document.querySelector('#segment-analysis-metric').value='clv';document.querySelector('#segment-analysis-metric').dispatchEvent(new Event('change',{bubbles:true}))")
                    assert client.js("document.querySelector('#segment-analysis-chart svg').getAttribute('aria-label').includes('CLV')")
                if route=='marketvalue':
                    assert client.js("document.querySelector('#market-value-equation').textContent.includes('1.5896')")
                    assert client.js("document.querySelector('#content').textContent.includes('Final Kahn score models')")
                    assert client.js("document.querySelector('#content').textContent.includes('six-peer average')")
                    assert client.js("document.querySelectorAll('.fit-scatter svg').length")>=5
                    assert not client.js("document.querySelector('#content').textContent.includes('Earlier-only conditional checks')")
                if route=='wacc':
                    assert client.js("document.querySelector('#wacc-model-equation').textContent.includes('10.9222')")
                    assert client.js("document.querySelectorAll('.fit-scatter svg').length")==1
                    assert client.js("document.querySelectorAll('#wacc-factor-select option').length")==16
                    client.js("document.querySelector('#wacc-factor-select').value='service';document.querySelector('#wacc-factor-select').dispatchEvent(new Event('change',{bubbles:true}))")
                    assert client.js("document.querySelector('#wacc-factor-detail').textContent.includes('Customer Service')")
                for width,height,mobile in [(1440,1100,False),(390,844,True)]:
                    client.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':mobile})
                    assert client.js('document.documentElement.scrollWidth<=innerWidth'),route+': overflow'
                    client.js('window.scrollTo(0,0)')
                    shot=client.call('Page.captureScreenshot',{'format':'png'})
                    (approved/f'getchells-final-{route}-{width}.png').write_bytes(base64.b64decode(shot['data']))
                client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
                if route=='segmentation':
                    for chart in ('segment-mix-chart','segment-phase-chart','segment-spend-chart'):
                        client.js(f"document.querySelector('#{chart}').scrollIntoView({{block:'center'}})")
                        shot=client.call('Page.captureScreenshot',{'format':'png'})
                        (approved/f'getchells-{chart}-1440.png').write_bytes(base64.b64decode(shot['data']))
                if route=='stp':
                    for chart in ('stp-need-map','stp-scale-chart','stp-competitor-map'):
                        client.js(f"document.querySelector('#{chart}').scrollIntoView({{block:'center'}})")
                        shot=client.call('Page.captureScreenshot',{'format':'png'})
                        (approved/f'getchells-{chart}-1440.png').write_bytes(base64.b64decode(shot['data']))
                if route=='overview':
                    for chart in ('exec-objective-timeline','exec-target-mix-chart','exec-value-chart'):
                        client.js(f"document.querySelector('#{chart}').scrollIntoView({{block:'center'}})")
                        shot=client.call('Page.captureScreenshot',{'format':'png'})
                        (approved/f'getchells-{chart}-1440.png').write_bytes(base64.b64decode(shot['data']))
            for endpoint,default in [('/marketing-report','Executive overview'),('/customer-segmentation-analysis','Customer segmentation analysis'),
                                     ('/market-value-report','Market value analysis'),('/wacc-report','WACC impact analysis')]:
                path=profile/(endpoint.strip('/')+'.html')
                with urlopen(base+endpoint) as response:path.write_bytes(response.read())
                client.call('Page.navigate',{'url':path.as_uri()})
                client.wait(f"document.querySelector('h1')?.textContent==='{default}'")
                assert client.js('data.simulation_complete')
                assert not client.js("'decisions' in data.team || 'draft' in data.strategy")
                for route,title in routes.items():
                    client.js(f"location.hash='{route}'");client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                    assert not client.js("document.querySelector('#content').textContent.includes('Could not load')")
            path=profile/'final-report.html'
            with urlopen(base+'/final-report') as response:path.write_bytes(response.read())
            client.call('Page.navigate',{'url':path.as_uri()})
            client.wait("document.querySelector('h1')?.textContent==='Getchell’s final marketing and finance review'")
            assert client.js("document.querySelectorAll('h1').length===1")
            assert client.js("document.querySelectorAll('.report-detail').length===6")
            assert client.js("document.querySelectorAll('.report-detail[open]').length===0")
            brief_words=client.js("document.querySelector('#content').innerText.trim().split(/\\s+/).length")
            assert brief_words<1200,brief_words
            assert client.js("document.querySelector('#overview').innerText.includes('2.26×')")
            assert client.js("document.querySelector('#stp').innerText.includes('S6 · secondary')")
            assert client.js("document.querySelector('#segmentation').innerText.includes('103.2%')")
            assert client.js("document.querySelector('#segmentation').innerText.includes('30.7%')")
            assert client.js("document.querySelectorAll('#report-target-mix-chart svg').length===1")
            assert client.js("document.querySelectorAll('#report-value-chart svg').length===1")
            assert client.js("document.querySelectorAll('#report-wacc-chart svg').length===1")
            client.js("document.querySelector('.report-evidence-toggle').click()")
            assert client.js("document.querySelectorAll('.report-detail[open]').length===6")
            assert client.js("document.querySelector('.report-evidence-toggle').getAttribute('aria-expanded')==='true'")
            expanded_words=client.js("document.querySelector('#content').innerText.trim().split(/\\s+/).length")
            assert expanded_words>brief_words*2,(brief_words,expanded_words)
            client.js("document.querySelector('.report-evidence-toggle').click()")
            assert client.js("document.querySelectorAll('.report-detail[open]').length===0")
            assert client.js("document.querySelectorAll('.report-section').length===5")
            assert client.js("document.querySelectorAll('.report-nav a').length===5")
            assert client.js("JSON.stringify([...document.querySelectorAll('.report-section')].slice(0,3).map(x=>x.id))===JSON.stringify(['overview','stp','segmentation'])")
            assert client.js("document.querySelectorAll('#stp-fit-chart svg').length===1")
            assert client.js("document.querySelectorAll('#exec-objective-timeline .review-badge').length===32")
            assert client.js("document.querySelectorAll('.executive-finance-grid svg').length===5")
            assert client.js("document.querySelector('#exec-clv-chart').textContent.includes('R0')")
            assert client.js("document.querySelector('#overview').textContent.includes('2.26×')")
            assert client.js("document.querySelectorAll('#segment-mix-chart svg').length===1")
            assert client.js("document.querySelectorAll('#segment-growth-chart svg').length===1")
            assert client.js("document.querySelector('#segmentation').textContent.includes('S6 second')")
            assert client.js("document.querySelector('#stp').textContent.includes('S3 → S6')")
            assert not client.js("document.querySelector('#content').textContent.includes('S5 second')")
            assert client.js("document.querySelectorAll('.heat-table .heat-cell').length===48")
            assert client.js("document.querySelector('#market-value-equation').textContent.includes('1.5896')")
            assert client.js("document.querySelector('#wacc-model-equation').textContent.includes('10.9222')")
            client.js("location.hash='#marketvalue'")
            client.wait("document.querySelector('h1')?.textContent==='Getchell’s final marketing and finance review'")
            assert client.js("document.querySelectorAll('.report-section').length===5")
            assert client.js("document.querySelectorAll('.verdict-grid .verdict-list li > strong').length===8")
            assert client.js("document.querySelector('#second-chance')===null")
            assert not client.js("document.querySelector('#content').textContent.includes('What we would do differently')")
            assert not client.js("document.querySelector('.report-nav').textContent.includes('Lessons')")
            for width,height,mobile in [(1440,1100,False),(390,844,True)]:
                client.call('Emulation.setDeviceMetricsOverride',{'width':width,'height':height,'deviceScaleFactor':1,'mobile':mobile})
                assert client.js('document.documentElement.scrollWidth<=innerWidth'),'combined: overflow'
                client.js('window.scrollTo(0,0)')
                shot=client.call('Page.captureScreenshot',{'format':'png'})
                (approved/f'getchells-final-combined-{width}.png').write_bytes(base64.b64decode(shot['data']))
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.call('Emulation.setEmulatedMedia',{'media':'print'})
            assert client.js("[...document.querySelectorAll('.report-detail')].every(x=>getComputedStyle(x).display==='none')")
            client.call('Emulation.setEmulatedMedia',{'media':''})
            client.js("document.querySelector('.report-evidence-toggle').click()")
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth<=innerWidth'),'expanded combined: overflow'
            print(f'Report words: {brief_words} in brief view; {expanded_words} with detailed evidence expanded.')
            assert not client.errors,client.errors
            assert before=={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in workbooks}
            print('PASS: final R1–R8 overview, enhanced S3+S6 review, updated value/WACC models, combined shareable report, mobile controls, offline exports and unchanged workbooks.')
        finally:
            if client:client.sock.close()
            process.terminate();process.wait(timeout=15)
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
