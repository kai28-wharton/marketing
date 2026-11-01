"""Round 4 workspace: Round 3 submission/marketing, explicit missing finance."""
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
    from round_review import dataset
    if dataset().get('history_analysis'):
        from analysis_browser_smoke import main as analysis_main
        return analysis_main()
    approved=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    with tempfile.TemporaryDirectory(prefix='getchells-round4-',dir=approved) as directory:
        profile=Path(directory)
        server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
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
            with urlopen(f'http://127.0.0.1:{port}/json/list') as response:
                target=next(p for p in json.load(response) if p['type']=='page')
            client=CDP(target['webSocketDebuggerUrl']);client.call('Page.enable');client.call('Runtime.enable')
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.call('Page.navigate',{'url':base})
            client.wait("document.querySelector('h1')?.textContent==='Executive overview'")
            assert client.js('[data.previous_round,data.current_round,data.planning_round]')==[2,3,4]
            assert client.js("document.querySelector('.round-pill').textContent.includes('ROUND 4 · R3 ACTUALS')")
            assert client.js("document.body.innerText.includes('$565.53M')")
            assert client.js("document.body.innerText.includes('Round 3 financial exports are missing')")
            assert client.js("!document.body.innerText.includes('$255.27M')")
            assert client.js("document.body.innerText.includes('Round 4 budget: unconfirmed')")
            routes={'overview':'Executive overview','marketing':'Marketing Intelligence','segmentation':'Customer segmentation decision','financials':'Financial health','insights/brand':'Decision Insights','insights/finance':'Decision Insights','insights/segments':'Decision Insights','decisions':'Decision studio','recommendations':'Round 4 decision making page'}
            for route,title in routes.items():
                client.js(f"location.hash='{route}'");client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                if route.startswith('insights/'):
                    client.wait(f"!!document.querySelector('#insight-panel-{route.split('/')[1]}')")
                assert client.js("![...document.querySelectorAll('svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))"),route
                client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
                assert client.js('document.documentElement.scrollWidth<=innerWidth'),route+' mobile overflow'
                client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
                shot=client.call('Page.captureScreenshot',{'format':'png'})
                (approved/('getchells-round4-'+route.replace('/','-')+'.png')).write_bytes(base64.b64decode(shot['data']))
            assert client.js("document.body.innerText.includes('Round 4 budget: unconfirmed')")
            assert client.js("document.querySelector('nav [data-page=recommendations]').textContent.includes('Round 4')")
            client.js("location.hash='financials'");client.wait("document.querySelector('h1')?.textContent==='Financial health'")
            assert client.js("document.body.innerText.includes('Financial statements through Round 2')")
            assert client.js("document.body.innerText.includes('not Round 3 results')")
            client.js("location.hash='decisions'");client.wait("!!document.querySelector('#impact-form')")
            assert client.js("document.querySelectorAll('[data-factor]').length")==16
            assert client.js("document.querySelector('#factor-high_markup').value")== '60'
            assert client.js("document.querySelector('#factor-service').value")== '11350000'
            assert client.js("document.querySelector('#apply-impact').disabled")
            assert not client.js("!!document.querySelector('#optimizer-form')")
            client.js("document.querySelector('#factor-service').value=12000000;document.querySelector('#factor-service').dispatchEvent(new Event('input',{bubbles:true}))")
            assert client.js("document.querySelector('#apply-impact').disabled")
            assert client.js("document.querySelector('#current-budget-summary').textContent.includes('75,281,166')")
            client.js("document.querySelector('#use-budget-arm').click()")
            assert client.js('currentScenarioBudget')==79_174_036.2
            client.js("document.querySelector('#reset-plan').click()")
            assert client.js("document.querySelector('#factor-service').value")== '11350000'
            assert client.js("document.querySelector('#apply-impact').disabled")
            client.js("location.hash='segmentation'");client.wait("!!document.querySelector('#segmentation-lens')")
            assert client.js("document.body.innerText.includes('Raw Round 3 CSV values')")
            assert client.js("document.body.innerText.includes('R2 CASH')")
            assert not client.js("document.body.innerText.includes('ZEPHARA is a stronger rival on both')")
            client.js("document.querySelector('#segmentation-lens').value='clv';document.querySelector('#segmentation-lens').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#segmentation-ranking').textContent.includes('Existing aggregate CLV')")
            for endpoint,page,title in [('/marketing-report','marketing','Marketing Intelligence'),('/customer-segmentation-report','segmentation','Customer segmentation decision')]:
                path=profile/(page+'.html')
                with urlopen(base+endpoint) as response:path.write_bytes(response.read())
                client.call('Page.navigate',{'url':path.as_uri()})
                client.wait(f"document.querySelector('h1')?.textContent==='{title}'")
                assert client.js('data.planning_round')==4
                assert client.js('data.availability.financial_round')==2
                assert not client.js("'decisions' in data.team || 'draft' in data.strategy")
                client.js("location.hash='segmentation'");client.wait("!!document.querySelector('#segmentation-lens')")
                assert client.js("document.body.innerText.includes('Round 3 financial exports are missing')")
            assert not client.errors,client.errors
            print('PASS: all Round 4 pages, actual Round 3 decisions/marketing, missing-finance safeguards, manual budget editing/reset, mobile layouts and offline reports.')
        finally:
            if client:client.sock.close()
            process.terminate();process.wait(timeout=15)
            server.shutdown();server.server_close();thread.join()


if __name__=='__main__':main()
