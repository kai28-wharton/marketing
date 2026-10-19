"""Chrome numerical parity and truly-offline file workflow. No HTTP app server.
Run: python3 tests/offline_smoke.py
"""
import base64
import hashlib
import itertools
import json
import math
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from browser_smoke import CDP,CHROME
import app
from assortment import analyze,KEYS
from offline_assortment import build_offline_lab


def main():
    approved=Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    parent=str(approved) if approved.exists() else None
    with tempfile.TemporaryDirectory(prefix='getchells-offline-',dir=parent) as directory:
        root=Path(directory);profile=root/'profile';downloads=root/'downloads';downloads.mkdir()
        data=app.load_data();source=root/'original-lab.html'
        source.write_text(build_offline_lab(None,data,app.validate,app.evaluate))
        original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        process=subprocess.Popen([CHROME,'--headless','--disable-gpu','--no-first-run','--no-default-browser-check',
                                  '--remote-debugging-port=0','--remote-allow-origins=*','--user-data-dir='+str(profile),'about:blank'],
                                 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        client=None
        try:
            for _ in range(100):
                port_file=profile/'DevToolsActivePort'
                if port_file.exists():break
                time.sleep(.1)
            port=int(port_file.read_text().splitlines()[0])
            with urlopen(f'http://127.0.0.1:{port}/json/list') as response:
                target=next(t for t in json.load(response) if t['type']=='page')
            client=CDP(target['webSocketDebuggerUrl']);client.call('Runtime.enable');client.call('Page.enable')
            client.call('Network.enable')
            client.call('Network.emulateNetworkConditions',{'offline':True,'latency':0,'downloadThroughput':0,'uploadThroughput':0})
            client.call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(downloads)})
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.call('Page.navigate',{'url':source.as_uri()})
            client.wait('!!window.OfflineAssortment')
            assert client.js("document.querySelector('#fatal').hidden")
            assert client.js("!!(document.querySelector('#recommendation-top').compareDocumentPosition(document.querySelector('#controls')) & Node.DOCUMENT_POSITION_FOLLOWING)"), 'Offline recommendation must precede controls'
            assert client.js("!!(document.querySelector('.layout').compareDocumentPosition(document.querySelector('#readiness-end')) & Node.DOCUMENT_POSITION_FOLLOWING)"), 'Offline limitations must follow sensitivity analysis'
            assert client.js("document.querySelectorAll('.readiness-status.missing').length>=3")
            assert client.js("document.querySelector('#readiness-end').innerText.includes('$58,651,343')")
            assert client.js("['75.9%','39.8%','35.1%','90.9%'].every(v=>document.querySelector('#recommendation-top').innerText.includes(v))")
            assert client.js("document.querySelectorAll('input[type=number]').length")==4
            snapshot=client.js("JSON.parse(document.querySelector('#lab-data').textContent)")
            baseline=snapshot['baseline'];rng=random.Random(127)
            cases=[dict(zip(KEYS,values)) for values in itertools.product((1,100),repeat=4)]
            cases.extend([snapshot['initial_values'],dict(zip(KEYS,[65.25,31.5,40.75,48.125]))])
            cases.extend({k:rng.uniform(1,100) for k in KEYS} for _ in range(12))
            for changes in cases:
                expected=analyze({'baseline':baseline,'changes':changes,'assumptions':snapshot['assumptions']},data,app.validate,app.evaluate)
                actual=client.js('OfflineAssortment.analyze('+json.dumps(changes)+')')
                for q in expected['candidate']['scores']:
                    assert math.isclose(actual['candidate']['scores'][q],expected['candidate']['scores'][q],abs_tol=1e-11),(changes,q)
                    for i in (0,1):
                        assert math.isclose(actual['candidate']['intervals'][q][i],expected['candidate']['kahn']['intervals'][q][i],abs_tol=1e-11)
                for key in expected['financial_changes']:
                    assert math.isclose(actual['financial_changes'][key],expected['financial_changes'][key],abs_tol=1e-5),(changes,key)
                for key in ('revenue','cogs','gross_profit','net_income'):
                    assert math.isclose(actual['candidate'][key],expected['candidate'][key],abs_tol=1e-5),(changes,key)
                for a,b in zip(actual['attribution'],expected['attribution']):
                    for q in b['scores']:
                        assert math.isclose(a['scores'][q],b['scores'][q],abs_tol=1e-11)
                    assert math.isclose(a['financial']['net_income'],b['financial']['net_income'],abs_tol=1e-5)
                for a,b in zip(actual['segment_alignment']['rows'],expected['segment_alignment']['rows']):
                    assert a['segment']==b['segment']
                    assert math.isclose(a['alignment_change_pp'],b['alignment_change_pp'],abs_tol=1e-11)
            assert client.js("!!document.querySelector('#segment-alignment')")
            client.js("(()=>{const f=document.querySelector('#n-low_breadth');f.value=70;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            assert client.js("OfflineAssortment.getReport().candidate.decisions.low_breadth")==70
            assert client.js("OfflineAssortment.getReport().candidate.decisions.online")==9_000_000
            client.js("(()=>{const f=document.querySelector('#n-low_depth');f.value=0;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            assert client.js("document.querySelector('#download-html').disabled && document.querySelector('#download-json').disabled")
            client.js("(()=>{const f=document.querySelector('#n-low_depth');f.value=45;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            before_copy=client.js('OfflineAssortment.getReport().candidate.net_income')
            client.js("document.querySelector('#download-html').click()")
            saved=downloads/'getchells-assortment-lab-offline.html'
            for _ in range(100):
                if saved.exists():break
                time.sleep(.05)
            assert saved.exists()
            client.call('Page.navigate',{'url':saved.as_uri()});client.wait('!!window.OfflineAssortment')
            assert client.js("document.querySelector('#fatal').hidden")
            assert client.js('OfflineAssortment.getValues().low_breadth')==70
            assert client.js('OfflineAssortment.getValues().low_depth')==45
            assert math.isclose(client.js('OfflineAssortment.getReport().candidate.net_income'),before_copy,abs_tol=1e-6)
            client.js("document.querySelector('#download-json').click()")
            exported=downloads/'getchells-assortment-comparison.json'
            for _ in range(100):
                if exported.exists():break
                time.sleep(.05)
            result=json.loads(exported.read_text())
            assert result['candidate']['decisions']['low_breadth']==70
            assert result['candidate']['decisions']['online']==9_000_000
            assert result['financial_changes']['explicit_spend']==0
            client.js("document.querySelector('#reset').click()")
            assert client.js('OfflineAssortment.getValues().low_breadth')==65
            client.js("document.querySelector('#industry').click()")
            assert client.js('OfflineAssortment.getValues().high_breadth')==30
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            output=(approved if approved.exists() else root)/'getchells-offline-assortment.png'
            output.write_bytes(base64.b64decode(shot['data']))
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth<=innerWidth'),'Mobile overflow'
            assert hashlib.sha256(source.read_bytes()).hexdigest()==original_hash
            assert not client.errors,client.errors
            print(f'PASS: {len(cases)} four-input combinations match the Python backend (scores, stress ranges, finances, attribution).')
            print('PASS: file:// with network disabled, four-only controls, 12 fixed inputs, invalid guards, playable-copy reload, JSON export, reset/benchmarks and mobile layout.')
            print('Screenshot:',output)
        finally:
            if client:client.sock.close()
            process.terminate();process.wait(timeout=15)


if __name__=='__main__':main()
