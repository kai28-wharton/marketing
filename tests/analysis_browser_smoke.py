"""All current analysis pages, charts, controls, deep links and offline reports."""
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
from legacy_browser_smoke import CDP, CHROME

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app


def main():
    approved=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    workbook=app.ROOT/'decision_making/round_7/decision_making_team11_round7.xlsx'
    before=hashlib.sha256(workbook.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='getchells-analysis-',dir=approved) as directory:
        profile=Path(directory);server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        process=subprocess.Popen([CHROME,'--headless','--disable-gpu','--no-first-run','--no-default-browser-check','--remote-debugging-port=0','--remote-allow-origins=*','--user-data-dir='+directory,'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
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
            assert client.js('[data.current_round,data.planning_round]')==[6,7]
            assert client.js("document.querySelectorAll('.history-gap-grid svg').length")==4
            assert client.js("document.body.textContent.includes('$83,151,028')")
            assert client.js("document.body.textContent.includes('Zero is each round’s exported FAIR VALUE')")
            assert client.js("document.querySelector('nav [data-page=segmentation]').textContent.includes('Customer segmentation analysis')")
            routes={'overview':'Executive overview','segmentation':'Customer segmentation analysis','marketvalue':'Market value analysis','wacc':'WACC impact analysis','marketing':'Marketing Intelligence','financials':'Financial health','insights/brand':'Decision Insights','insights/finance':'Decision Insights','insights/segments':'Decision Insights','decisions':'Decision studio','recommendations':'Round 7 decision making page'}
            for route,title in routes.items():
                client.js(f"location.hash='{route}'");client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                if route=='decisions':
                    assert client.js("document.querySelector('#current-budget').value")=='83151028'
                    assert client.js("document.querySelector('#current-budget-summary').textContent.includes('1,601,518')")
                    assert not client.js("!!document.querySelector('#use-budget-arm')")
                    assert client.js("!!document.querySelector('#use-confirmed-budget')")
                assert client.js("![...document.querySelectorAll('svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))"),route
                client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
                assert client.js('document.documentElement.scrollWidth<=innerWidth'),route+' mobile overflow'
                client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
                if route in ('overview','segmentation','marketvalue','wacc'):
                    shot=client.call('Page.captureScreenshot',{'format':'png'})
                    (approved/('getchells-analysis-'+route+'.png')).write_bytes(base64.b64decode(shot['data']))
            client.js("location.hash='segmentation'");client.wait("!!document.querySelector('#segment-analysis-metric')")
            assert not client.js("!!document.querySelector('#segmentation-group')")
            client.js("document.querySelector('#segment-analysis-metric').value='clv';document.querySelector('#segment-analysis-metric').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#segment-analysis-chart svg').getAttribute('aria-label').includes('CLV')")
            assert client.js("document.body.textContent.includes('No segment-specific spending attribution')")
            client.call('Page.navigate',{'url':base+'/#marketvalue'})
            client.wait("document.querySelector('h1')?.textContent==='Market value analysis'")
            assert client.js("document.body.textContent.includes('Section 2 · Kahn matrix')")
            assert client.js("document.body.textContent.toLowerCase().includes('fifteen distinct workbook input series')")
            assert client.js("document.body.textContent.toLowerCase().includes('lagged input matrix')")
            assert client.js("document.querySelectorAll('[data-kahn-quadrant]').length")==4
            assert client.js("document.body.textContent.includes('Top 3:')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Vocabulary · actual decision parameters')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Private Brand Quality')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Vendor Management')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Assortment (breadth + depth)')")
            assert not client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Comparable standardized form')")
            client.js("document.querySelector('[data-kahn-quadrant=FRICTIONLESS]').click()")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Mechanism-constrained diagnostic')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Stage 1 · conditional investment-to-position diagnostic')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Reported score identity')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Persistence wins earlier-only check')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Model comparison · identical scored periods')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Earlier-only conditional checks')")
            assert not client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Pooled cross-check:')")
            assert not client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('service-position enabler')")
            assert client.js("['CADABRA','PRICEMART','AIM','KTBENNEY','ZEPHARA','BESTCO'].every(c=>document.querySelector('#kahn-quadrant-detail').textContent.includes(c))")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Customer Service position')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Online Investment position')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Customer Analytics')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Competitor comparison')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Peer average')")
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth<=innerWidth'),'Frictionless audit mobile overflow'
            client.js("document.querySelector('#kahn-quadrant-detail').scrollIntoView()")
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            (approved/'getchells-frictionless-audit-mobile.png').write_bytes(base64.b64decode(shot['data']))
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.js("document.querySelector('[data-kahn-quadrant=EXPERIENCE]').click()")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('EXPERIENCE')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Two-stage position model')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Stage 1 · investment money')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Shopping Experience position')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Direct score components')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Customer Analytics')")
            assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Competitor comparison')")
            assert client.js("document.querySelectorAll('#kahn-quadrant-detail .review-table').length")>=8
            assert client.js("document.body.textContent.includes('Section 3 · Market value fit')")
            assert client.js("document.querySelector('#market-value-equation').textContent.includes('ln(EBIT)')")
            assert client.js("document.body.textContent.includes('Hide-one-period MAPE')")
            assert client.js("document.body.textContent.includes('reported-position reconstruction')")
            assert client.js("document.body.textContent.includes('service position')")
            client.js("location.hash='wacc'");client.wait("!!document.querySelector('#wacc-factor-select')")
            assert client.js("document.querySelectorAll('#wacc-factor-select option').length")==16
            assert client.js("document.querySelector('#wacc-model-equation').textContent.includes('11.0213')")
            assert client.js("document.body.textContent.includes('Error (pp)')")
            assert client.js("document.body.textContent.includes('What is the hide-one-round check?')")
            assert client.js("document.body.textContent.includes('Best-performance confirmation')")
            assert client.js("document.querySelectorAll('[data-wacc-debate-group]').length")==5
            assert client.js("document.querySelectorAll('[data-wacc-lens]').length")==4
            client.js("document.querySelector('[data-wacc-debate-group=depth]').click()")
            assert client.js("document.querySelector('#wacc-debate-detail').textContent.includes('Depth')")
            client.js("document.querySelector('[data-wacc-lens=risk]').click()")
            assert client.js("document.querySelector('#wacc-debate-detail').textContent.includes('Why it can backfire')")
            client.js("document.querySelector('#wacc-debate-detail [data-wacc-inspect]').click()")
            assert client.js("document.querySelector('#wacc-factor-select').value")=='low_depth'
            assert client.js("document.querySelector('#wacc-factor-detail').textContent.includes('Lower Cost Products: Depth')")
            assert client.js("document.body.textContent.includes('Correlation evidence—co-movement, not impact')")
            client.js("document.querySelector('#wacc-factor-select').value='high_depth';document.querySelector('#wacc-factor-select').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#wacc-factor-detail').textContent.includes('Higher Cost Products: Depth')")
            client.js("document.querySelector('#wacc-ke').value=6.5;document.querySelector('#wacc-ke').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#wacc-reweight-results').textContent.includes('Illustrative WACC')")
            for endpoint,title in [('/marketing-report','Marketing Intelligence'),('/customer-segmentation-analysis','Customer segmentation analysis'),('/market-value-report','Market value analysis'),('/wacc-report','WACC impact analysis')]:
                path=profile/(endpoint.strip('/')+'.html')
                with urlopen(base+endpoint) as response:path.write_bytes(response.read())
                client.call('Page.navigate',{'url':path.as_uri()})
                client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                assert client.js('data.planning_round')==7
                assert not client.js("'decisions' in data.team || 'draft' in data.strategy")
                for route,heading in [('overview','Executive overview'),('segmentation','Customer segmentation analysis'),('marketvalue','Market value analysis'),('wacc','WACC impact analysis')]:
                    client.js(f"location.hash='{route}'");client.wait(f"document.querySelector('h1')?.textContent==='{heading}'")
                    if route=='marketvalue':
                        client.js("document.querySelector('[data-kahn-quadrant=FRICTIONLESS]').click()")
                        assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Persistence wins earlier-only check')")
                        assert client.js("document.querySelector('#kahn-quadrant-detail').textContent.includes('Relative Online Investment × relative Customer Analytics')")
            assert not client.errors,client.errors
            assert hashlib.sha256(workbook.read_bytes()).hexdigest()==before
            print('PASS: Round 7 longitudinal overview, segmentation analysis, market-value models, all other pages, mobile charts, controls/deep links, offline reports and unchanged workbook.')
        finally:
            if client:client.sock.close()
            process.terminate();process.wait(timeout=15)
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':
    from round_review import dataset
    if dataset()['current_round']>=8:
        from final_browser_smoke import main as final_main
        final_main()
    else:
        main()
