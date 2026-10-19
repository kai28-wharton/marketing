"""Archived pre-Round-1 workflow plus reusable dependency-free CDP client.

Run separately: python3 tests/browser_smoke.py
Does not require Node, Playwright, or browser packages. Uses a disposable profile.
"""
import base64
import hashlib
import json
import os
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
BASE_URL = ''


class CDP:
    def __init__(self, url):
        parsed = urlparse(url)
        self.sock = socket.create_connection((parsed.hostname, parsed.port), timeout=15)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f'GET {parsed.path} HTTP/1.1\r\nHost: {parsed.netloc}\r\n'
                           f'Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n'
                           'Sec-WebSocket-Version: 13\r\n\r\n').encode())
        reply = b''
        while not reply.endswith(b'\r\n\r\n'):
            reply += self.sock.recv(1)
        assert reply.startswith(b'HTTP/1.1 101 '), reply
        accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest())
        assert accept in reply
        self.sequence = 0
        self.errors = []

    def read(self, count):
        out = b''
        while len(out) < count:
            chunk = self.sock.recv(count-len(out))
            if not chunk:
                raise EOFError('Browser closed its debugging socket')
            out += chunk
        return out

    def receive(self):
        _, length = self.read(2)
        assert length & 128 == 0
        length &= 127
        if length == 126:
            length = struct.unpack('!H', self.read(2))[0]
        elif length == 127:
            length = struct.unpack('!Q', self.read(8))[0]
        return json.loads(self.read(length))

    def call(self, method, params=None):
        self.sequence += 1
        payload = json.dumps({'id': self.sequence, 'method': method, 'params': params or {}}).encode()
        mask = os.urandom(4)
        header = b'\x81'
        if len(payload) < 126:
            header += bytes([128 | len(payload)])
        elif len(payload) < 65536:
            header += b'\xfe' + struct.pack('!H', len(payload))
        else:
            header += b'\xff' + struct.pack('!Q', len(payload))
        self.sock.sendall(header + mask + bytes(v ^ mask[i % 4] for i, v in enumerate(payload)))
        while True:
            message = self.receive()
            if message.get('method') == 'Runtime.exceptionThrown':
                self.errors.append(message)
            if message.get('id') == self.sequence:
                assert 'error' not in message, message
                return message.get('result', {})

    def js(self, expression):
        result = self.call('Runtime.evaluate', {'expression': expression, 'awaitPromise': True, 'returnByValue': True})
        assert 'exceptionDetails' not in result, result
        return result.get('result', {}).get('value')

    def wait(self, expression):
        for _ in range(100):
            if self.js(expression):
                return
            time.sleep(.05)
        raise AssertionError(f'Browser condition timed out: {expression}')


def main():
    approved = Path('/private/var/folders/86/w9c93qb93hg8f5yyjtkgjmpw0000gn/T/opencode')
    parent = str(approved) if approved.exists() else None
    with tempfile.TemporaryDirectory(prefix='getchells-browser-', dir=parent) as profile:
        process = subprocess.Popen([CHROME, '--headless', '--disable-gpu', '--no-first-run',
                                    '--no-default-browser-check', '--remote-debugging-port=0',
                                    '--remote-allow-origins=*', '--user-data-dir='+profile, 'about:blank'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        client = None
        try:
            port_file = Path(profile) / 'DevToolsActivePort'
            for _ in range(100):
                if port_file.exists():
                    break
                time.sleep(.1)
            port = int(port_file.read_text().splitlines()[0])
            with urlopen(f'http://127.0.0.1:{port}/json/list') as response:
                target = next(t for t in json.load(response) if t['type'] == 'page')
            client = CDP(target['webSocketDebuggerUrl'])
            client.call('Page.enable')
            client.call('Runtime.enable')
            client.call('Emulation.setDeviceMetricsOverride', {'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            client.call('Page.navigate', {'url':BASE_URL})
            client.wait("document.querySelector('h1')?.textContent.includes('Better decisions')")
            assert client.js("document.body.innerText.includes('$372.80M')")
            assert client.js("getComputedStyle(document.querySelector('.sidebar')).backgroundImage.includes('linear-gradient')"), 'Vivid navigation theme missing'
            assert client.js("getComputedStyle(document.documentElement).getPropertyValue('--green').trim()")=='#087f5b'
            assert client.js("getComputedStyle(document.documentElement).getPropertyValue('--red').trim()")=='#cc2948'
            assert client.js("!!document.querySelector('#marketing-context')"), 'Overview marketing context missing'
            client.js("location.hash='marketing'")
            client.wait("document.querySelector('h1')?.textContent==='Marketing Intelligence'")
            assert client.js("document.querySelectorAll('.marketing-source-tables details').length")==9
            assert client.js("document.body.innerText.includes('100.200%')"), 'Rounding audit missing'
            assert client.js("document.querySelectorAll('#marketing-analysis svg').length")==5
            assert client.js("document.querySelectorAll('#marketing-analysis svg title[id]').length")==5
            assert client.js("marketingDecisionData(data.marketing,'SEGMENT 2','revenue').rankings[0].id")=='SEGMENT 5'
            assert client.js("marketingDecisionData(data.marketing,'SEGMENT 2','clv').rankings[0].id")=='SEGMENT 2'
            assert client.js("marketingDecisionData(data.marketing,'SEGMENT 2','size').rankings[0].id")=='SEGMENT 1'
            assert client.js("marketingDecisionData(data.marketing,'SEGMENT 2','SHOPPING EXPERIENCE').rankings[0].id")=='SEGMENT 3'
            assert client.js("marketingDecisionData(data.marketing,'SEGMENT 2').trend[0].revenue") == 100
            marketing_plan_before=client.js('JSON.stringify(decisions)')
            client.js("document.querySelector('#marketing-decision-lens').value='clv';document.querySelector('#marketing-decision-lens').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#marketing-decision-lens').value")=='clv'
            assert client.js("document.querySelector('#segment-ranking-desc').textContent.includes('not the forecast')")
            client.js("document.querySelector('.marketing-segment-chip[data-chart-segment=\"SEGMENT 1\"]').click()")
            assert client.js("document.querySelector('#marketing-analysis-segment').value")=='SEGMENT 1'
            assert client.js("document.querySelector('#marketing-segment').value")=='SEGMENT 1'
            assert client.js("document.querySelector('#marketing-decision-brief').innerText.includes('SEGMENT 1')")
            assert client.js("!!document.querySelector('.marketing-brief-narrative summary')")
            assert client.js("document.querySelector('.marketing-execution-evidence').innerText.includes('Compare this customer need')")
            assert client.js("marketingPropositionEvidence(data.marketing,'SHOPPING EXPERIENCE').includes('2.4')")
            client.js("document.querySelector('svg [data-chart-segment=\"SEGMENT 6\"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true}))")
            assert client.js('marketingSegment')=='SEGMENT 6'
            assert client.js("document.querySelector('#segment-trend-title').textContent.includes('SEGMENT 6')")
            assert client.js('JSON.stringify(decisions)')==marketing_plan_before,'Charts mutated the working plan'
            assert client.js("![...document.querySelectorAll('#marketing-analysis svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))"),'Invalid SVG coordinates'
            client.js("document.querySelector('#marketing-segment').value='SEGMENT 5';document.querySelector('#marketing-segment').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#marketing-segment').value")=='SEGMENT 5'
            assert client.js("document.querySelector('#marketing-analysis-segment').value")=='SEGMENT 5'
            assert client.js("document.body.innerText.includes('SEGMENT 5: raw preference profile')")
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth<=innerWidth'),'Marketing page mobile overflow'
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            marketing_shot_dir=approved if approved.exists() else Path(tempfile.gettempdir())
            (marketing_shot_dir/'getchells-marketing.png').write_bytes(base64.b64decode(shot['data']))
            client.js("document.querySelector('.marketing-chart-grid').scrollIntoView({block:'start'})")
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            (marketing_shot_dir/'getchells-marketing-charts.png').write_bytes(base64.b64decode(shot['data']))
            client.js('window.scrollTo(0,0)')
            client.js("location.hash='overview'")
            client.wait("document.querySelector('h1')?.textContent.includes('Better decisions')")
            shot = client.call('Page.captureScreenshot', {'format':'png'})
            shot_dir = approved if approved.exists() else Path(tempfile.gettempdir())
            (shot_dir / 'getchells-overview.png').write_bytes(base64.b64decode(shot['data']))
            studio_before=client.js('JSON.stringify(decisions)')
            client.js("location.hash='assortment'")
            client.wait("!!assortmentReport && !assortmentStale")
            assert client.js("!!(document.querySelector('#assortment-recommendation').compareDocumentPosition(document.querySelector('.assortment-layout')) & Node.DOCUMENT_POSITION_FOLLOWING)"), 'Recommendation must precede sensitivity controls'
            assert client.js("!!(document.querySelector('.assortment-layout').compareDocumentPosition(document.querySelector('#assortment-readiness')) & Node.DOCUMENT_POSITION_FOLLOWING)"), 'Limitations and data gaps must follow sensitivity analysis'
            assert client.js("['75.9%','39.8%','35.1%','90.9%'].every(v=>document.querySelector('#assortment-recommendation').innerText.includes(v))")
            assert client.js("document.querySelectorAll('#assortment-readiness .readiness-limitations li').length===assortmentReport.limitations.length")
            assert client.js("document.querySelectorAll('#assortment-readiness .readiness-status.missing').length>=3")
            assert client.js("document.querySelector('#assortment-readiness').innerText.includes('$58,651,343')")
            assert client.js("document.querySelectorAll('input[type=number][data-assortment-key]').length")==4
            assert client.js('assortmentBaseline.online')==9_000_000
            assert client.js('assortmentChanges.low_breadth')==65
            assert client.js('assortmentChanges.low_depth')==30
            assert client.js('assortmentReport.locked_keys.length')==12
            assert client.js("!!document.querySelector('#segment-alignment')"), 'Assortment segment diagnostic missing'
            assert client.js("document.querySelector('#assortment-recommendation').innerText.includes('investigate breadth gaps')")
            assert client.js('Object.isFrozen(assortmentBaseline)')
            client.js("(()=>{const f=document.querySelector('#a4-low_breadth');f.value=75;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            assert client.js("document.querySelector('[data-assortment-action=export]').disabled")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_breadth===75")
            assert client.js("assortmentReport.segment_alignment.rows.find(r=>r.segment==='SEGMENT 2').alignment_change_pp>assortmentReport.segment_alignment.rows.find(r=>r.segment==='SEGMENT 6').alignment_change_pp")
            assert client.js("assortmentReport.score_changes.BRAND>0 && assortmentReport.financial_changes.explicit_spend===0")
            assert client.js("(()=>{const section=[...document.querySelectorAll('#assortment-results section')].find(s=>s.querySelector('h2')?.textContent.startsWith('Financial impact'));const change=section.querySelector('tbody tr td:last-child span');const kahn=document.querySelector('#assortment-results td.positive');return change.classList.contains('positive')&&getComputedStyle(change).color===getComputedStyle(kahn).color;})()"), 'Positive financial changes should use the Kahn green'
            client.js("(()=>{const f=document.querySelector('#a4-low_breadth');f.value=55;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_breadth===55")
            assert client.js("(()=>{const section=[...document.querySelectorAll('#assortment-results section')].find(s=>s.querySelector('h2')?.textContent.startsWith('Financial impact'));const change=section.querySelector('tbody tr td:last-child span');const kahn=document.querySelector('#assortment-results td.negative');return change.classList.contains('negative')&&getComputedStyle(change).color===getComputedStyle(kahn).color;})()"), 'Negative financial changes should use the Kahn red'
            client.js("(()=>{const f=document.querySelector('#a4-low_breadth');f.value=75;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_breadth===75")
            client.js("(()=>{const f=document.querySelector('input[type=range][data-assortment-key=low_depth]');f.value=45;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_depth===45")
            assert client.js('assortmentReport.score_changes.FRICTIONLESS>0')
            assert client.js('assortmentReport.locked_keys.every(k=>assortmentReport.candidate.decisions[k]===assortmentBaseline[k])')
            client.js("(()=>{const f=document.querySelector('#a4-low_breadth');f.value=0;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            assert client.js('assortmentStale && assortmentInvalid.size===1')
            assert client.js("document.querySelector('[data-assortment-action=save]').disabled")
            client.js("(()=>{const f=document.querySelector('#a4-low_breadth');f.value=70;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_breadth===70")
            client.js("location.hash='financials'")
            client.wait("document.querySelector('h1')?.textContent==='Financial health'")
            client.js("location.hash='assortment'")
            client.wait("!!document.querySelector('#a4-low_breadth')")
            assert client.js("document.querySelector('#a4-low_breadth').value")=='70'
            client.js("document.querySelector('[data-assortment-action=reset]').click()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_breadth===65")
            assert client.js('Object.values(assortmentReport.score_changes).every(v=>v===0)')
            client.js("document.querySelector('[data-assortment-action=industry]').click()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.low_breadth===43")
            client.js("document.querySelector('[data-assortment-action=choose]').click();document.querySelector('#assortment-source').value='studio';document.querySelector('[data-assortment-action=lock]').click()")
            client.wait("!assortmentStale && assortmentBaseline.online===2000000")
            client.js("document.querySelector('[data-assortment-action=choose]').click();document.querySelector('#assortment-source').value='team';document.querySelector('[data-assortment-action=lock]').click()")
            client.wait("!assortmentStale && assortmentBaseline.online===9000000")
            client.js("window.prompt=()=> 'Assortment smoke alternative';document.querySelector('[data-assortment-action=save]').click()")
            client.wait("scenarios.some(s=>s.name==='Assortment smoke alternative')")
            assert client.js('JSON.stringify(decisions)')==studio_before, 'Assortment lab changed the studio plan'
            assert client.js("document.querySelector('#assortment-readiness').innerText.includes('same per-index')")
            assert client.js("assortmentReport.candidate.warnings.every(w=>document.querySelector('#assortment-readiness').innerText.includes(w))")
            assert client.js("![...document.querySelectorAll('#assortment-results h2')].some(h=>h.textContent.includes('What this engine can'))"), 'Old bottom disclosure should be relocated'
            shot=client.call('Page.captureScreenshot',{'format':'png'})
            (shot_dir/'getchells-assortment.png').write_bytes(base64.b64decode(shot['data']))
            client.call('Emulation.setDeviceMetricsOverride',{'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth <= innerWidth'), 'Assortment mobile overflow'
            client.call('Emulation.setDeviceMetricsOverride',{'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            for route, title in [('positioning','Compete where it matters.'), ('financials','Financial health'),
                                 ('model','Model, assumptions & sources'), ('decisions','Decision studio')]:
                client.js(f"location.hash={json.dumps(route)}")
                client.wait(f"document.querySelector('h1')?.textContent==={json.dumps(title)}")
            assert client.js("document.querySelectorAll('[data-factor]').length") == 16
            assert client.js("document.querySelector('#kahn-details').innerText.includes('kahn-2.0')")
            assert client.js("document.querySelector('#kahn-details').innerText.includes('structural') || document.querySelector('#kahn-details').innerText.includes('Structural')")
            client.js("(()=>{const f=document.querySelector('[data-factor=online]');f.value=10000000;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("document.querySelector('#budget-panel').innerText.includes('OVER BUDGET')")
            client.js("(()=>{const f=document.querySelector('[data-factor=online]');f.value=3000000;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("document.querySelector('#budget-panel').innerText.includes('$68.00M')")
            assert client.js("document.querySelector('#kahn-details').innerText.includes('+0.')")
            client.js("location.hash='scenarios'")
            client.wait("!!document.querySelector('#scenario-name')")
            client.js("document.querySelector('[data-action=optimize]').click()")
            client.wait("!!document.querySelector('[data-action=adopt]')")
            client.js("document.querySelector('[data-action=adopt]').click()")
            client.wait("!document.querySelector('[data-action=adopt]')")
            # Save to the running smoke-test server's disposable DB, not user scenarios.
            client.js("document.querySelector('#scenario-name').value='Browser smoke scenario';document.querySelector('#save-form').requestSubmit()")
            client.wait("!!document.querySelector('[data-load]')")
            client.js("document.querySelector('[data-load]').click()")
            client.wait("document.querySelector('h1')?.textContent==='Decision studio'")
            client.js("location.hash='model'")
            client.wait("!!document.querySelector('#a-score_response')")
            client.js("document.querySelector('#a-score_response').value=0;document.querySelector('#assumptions-form').requestSubmit()")
            client.wait("document.querySelector('#notice').textContent==='Working-plan assumptions updated.'")
            assert client.js("document.querySelector('#a-score_response').value") == '0'
            client.js("location.hash='decisions'")
            client.wait("document.querySelector('h1')?.textContent==='Decision studio'")
            screenshot = client.call('Page.captureScreenshot', {'format':'png'})
            output = (approved if approved.exists() else Path(tempfile.gettempdir())) / 'getchells-decision-studio.png'
            output.write_bytes(base64.b64decode(screenshot['data']))
            client.call('Emulation.setDeviceMetricsOverride', {'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth <= innerWidth'), 'Mobile page has horizontal overflow'
            client.js("location.hash='overview'")
            client.wait("document.querySelector('h1')?.textContent.includes('Better decisions')")
            assert client.js('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overview has horizontal overflow'
            before_chat = client.js('JSON.stringify(decisions)')
            client.js("location.hash='chat'")
            client.wait("!!document.querySelector('#chat-question')")
            assert client.js('document.documentElement.scrollWidth <= innerWidth'), 'Mobile chat has horizontal overflow'
            client.js("document.querySelector('[data-chat-prompt=\"0\"]').click()")
            client.wait("document.querySelectorAll('.assistant-message').length===1 && !document.querySelector('#chat-question').disabled")
            assert client.js("document.querySelector('#chat-transcript').innerText.includes('A practical tour')")
            assert client.js("document.querySelectorAll('.chat-sources').length") > 0
            client.js("document.querySelector('#chat-question').value='What if online investment were $5M?';document.querySelector('#chat-form').requestSubmit()")
            client.wait("document.querySelectorAll('.assistant-message').length===2 && !document.querySelector('#chat-question').disabled")
            assert client.js("document.querySelector('#chat-transcript').innerText.includes('working plan unchanged')")
            assert client.js('JSON.stringify(decisions)') == before_chat, 'Chat mutated the working plan'
            client.js("document.querySelector('#chat-question').value='<img src=x onerror=alert(1)> What is the weather?';document.querySelector('#chat-form').requestSubmit()")
            client.wait("document.querySelectorAll('.assistant-message').length===3 && !document.querySelector('#chat-question').disabled")
            assert not client.js("!!document.querySelector('#chat-transcript img')"), 'Chat rendered user content as HTML'
            assert client.js("document.querySelector('#chat-transcript').innerText.includes('reliable answer')")
            client.call('Page.reload')
            client.wait("document.querySelectorAll('.assistant-message').length===3")
            client.call('Emulation.setDeviceMetricsOverride', {'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            screenshot = client.call('Page.captureScreenshot', {'format':'png'})
            (shot_dir / 'getchells-chat.png').write_bytes(base64.b64decode(screenshot['data']))
            client.js("document.querySelector('[data-action=clear-chat]').click()")
            client.wait("!document.querySelector('.chat-message')")
            assert client.js("sessionStorage.getItem('getchells-chat')") == '[]'
            before_projection = client.js('JSON.stringify(decisions)')
            client.js("location.hash='whatif'")
            client.wait("!!document.querySelector('#projection-results table') && !projectionBusy")
            assert client.js("document.querySelectorAll('[data-projection-factor]').length") == 16
            assert client.js("projectionOutput.working.periods[2].explicit_spend") == 68_000_000
            assert client.js("projectionOutput.working.periods[2].net_income === projectionOutput.working.periods[1].net_income")
            assert client.js('JSON.stringify(decisions)') == before_projection, 'What-if page mutated the studio plan'
            client.js("(()=>{const f=document.querySelector('#p-market_growth');f.value=3;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            assert client.js("document.querySelector('[data-projection-action=export]').disabled")
            client.js("location.hash='overview'")
            client.wait("document.querySelector('h1')?.textContent.includes('Better decisions')")
            client.js("location.hash='whatif'")
            client.wait("!!document.querySelector('#p-market_growth')")
            assert client.js("document.querySelector('#p-market_growth').value") == '3', 'Draft settings lost on navigation'
            client.js("document.querySelector('#p-year1_realization').value=50;document.querySelector('#projection-form').requestSubmit()")
            client.wait("!projectionBusy && !projectionStale && projectionOutput.working.planning.market_growth===0.03")
            assert client.js("projectionOutput.working.periods[2].realization") == .75
            client.js("document.querySelector('#projection-preset').value='brand';document.querySelector('#projection-preset').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('#projection-form').requestSubmit()")
            client.wait("!projectionBusy && !projectionStale && projectionOutput.working.decisions.national_quality===6")
            assert client.js("projectionOutput.working.unpriced_changes.includes('National Brand Quality')")
            assert client.js("document.querySelector('#projection-results').innerText.includes('UNKNOWN COSTS')")
            client.call('Emulation.setDeviceMetricsOverride', {'width':390,'height':844,'deviceScaleFactor':1,'mobile':True})
            assert client.js('document.documentElement.scrollWidth <= innerWidth'), 'Year-2 page has mobile horizontal overflow'
            client.call('Emulation.setDeviceMetricsOverride', {'width':1440,'height':1100,'deviceScaleFactor':1,'mobile':False})
            screenshot = client.call('Page.captureScreenshot', {'format':'png'})
            (shot_dir / 'getchells-year2.png').write_bytes(base64.b64decode(screenshot['data']))
            downloads=Path(profile)/'projection-exports'
            downloads.mkdir()
            client.call('Browser.setDownloadBehavior',{'behavior':'allow','downloadPath':str(downloads)})
            client.js("document.querySelector('[data-projection-action=export]').click()")
            exported=downloads/'getchells-year2-projection.json'
            for _ in range(100):
                if exported.exists():
                    break
                time.sleep(.05)
            brief=json.loads(exported.read_text())
            assert brief['working']['decisions']['national_quality']==6
            assert brief['working']['planning']['market_growth']==.03
            assert len(brief['comparisons'])==3
            client.js("document.querySelector('[data-projection-action=html]').click()")
            html_export=downloads/'getchells-marketing-decision-report.html'
            for _ in range(100):
                if html_export.exists():
                    break
                time.sleep(.05)
            report_html=html_export.read_text()
            assert report_html.startswith('<!doctype html>')
            assert 'Submitted page draft' in report_html
            assert 'cannot establish a defensible global optimum' in report_html
            assert '3.0%' in report_html
            client.js("document.querySelector('[data-projection-action=adopt]').click()")
            client.wait("document.querySelector('h1')?.textContent==='Decision studio'")
            assert client.js('decisions.national_quality') == 6
            client.js("location.hash='whatif'")
            client.wait("!!document.querySelector('#projection-form')")
            client.call('Page.reload')
            client.wait("!!document.querySelector('#projection-results table') && !projectionBusy")
            assert client.js('projectionOutput.working.decisions.national_quality')==5
            assert client.js('projectionOutput.working.planning.market_growth')==0
            client.js("location.hash='assortment'")
            client.wait("!!assortmentReport && !assortmentStale")
            client.js("(()=>{const f=document.querySelector('#a4-high_depth');f.value=50;f.dispatchEvent(new Event('input',{bubbles:true}));})()")
            client.wait("!assortmentStale && assortmentReport.candidate.decisions.high_depth===50")
            client.js("document.querySelector('[data-assortment-action=export]').click()")
            assortment_export=downloads/'getchells-assortment-comparison.json'
            for _ in range(100):
                if assortment_export.exists():
                    break
                time.sleep(.05)
            assortment_brief=json.loads(assortment_export.read_text())
            assert len(assortment_brief['locked_keys'])==12
            assert assortment_brief['candidate']['decisions']['high_depth']==50
            assert assortment_brief['candidate']['decisions']['online']==9_000_000
            assert assortment_brief['financial_changes']['explicit_spend']==0
            client.js("document.querySelector('[data-assortment-action=offline]').click()")
            offline_export=downloads/'getchells-assortment-lab-offline.html'
            for _ in range(100):
                if offline_export.exists():break
                time.sleep(.05)
            assert 'function scorePoint' in offline_export.read_text()
            client.js("location.hash='marketing'")
            client.wait("document.querySelectorAll('#marketing-analysis svg').length===5")
            client.js("document.querySelector('#marketing-analysis-segment').value='SEGMENT 5';document.querySelector('#marketing-analysis-segment').dispatchEvent(new Event('change',{bubbles:true}))")
            client.js("document.querySelector('#marketing-decision-lens').value='clv';document.querySelector('#marketing-decision-lens').dispatchEvent(new Event('change',{bubbles:true}));document.querySelector('[data-marketing-export]').click()")
            marketing_export=downloads/'getchells-marketing-intelligence.json'
            for _ in range(100):
                if marketing_export.exists():break
                time.sleep(.05)
            marketing_brief=json.loads(marketing_export.read_text())
            assert marketing_brief['decision_view']['selected_segment']=='SEGMENT 5'
            assert marketing_brief['decision_view']['lens']=='clv'
            assert marketing_brief['decision_view']['rankings'][0]['id']=='SEGMENT 2'
            assert len(marketing_brief['raw_tables'])==9
            assert client.js("!!document.querySelector('[data-marketing-share]')"), 'Marketing share-HTML link missing'
            from marketing_report import build_marketing_report
            import app as app_module
            standalone_marketing=downloads/'getchells-marketing-intelligence.html'
            standalone_marketing.write_text(build_marketing_report(app_module.load_data()['marketing']),encoding='utf-8')
            client.call('Page.navigate',{'url':standalone_marketing.as_uri()})
            client.wait("document.querySelector('h1')?.textContent==='Marketing Intelligence'")
            assert client.js("document.querySelectorAll('#marketing-analysis svg').length")==5
            assert client.js("document.querySelectorAll('.marketing-segment-chip').length")==6
            assert client.js("document.querySelectorAll('.marketing-source-tables details').length")==9
            assert client.js("!!document.querySelector('#marketing-print')")
            assert not client.js("!!document.querySelector('#marketing-share-link')"), 'Server-only share link should be removed offline'
            assert not client.js("!!document.querySelector('script[src],link[rel=stylesheet],img,iframe')"), 'Standalone report pulled an external asset'
            assert client.js("[...performance.getEntriesByType('resource')].every(e=>e.name.startsWith('file:'))"), 'Standalone report made a network request'
            assert client.js("getComputedStyle(document.querySelector('.marketing-standalone-bar')).backgroundImage.includes('linear-gradient')")
            client.js("document.querySelector('.marketing-segment-chip[data-chart-segment=\"SEGMENT 3\"]').click()")
            assert client.js("document.querySelector('#marketing-analysis-segment').value")=='SEGMENT 3'
            assert client.js("document.querySelector('#marketing-segment').value")=='SEGMENT 3'
            assert client.js("document.querySelector('#marketing-decision-brief').innerText.includes('SEGMENT 3')")
            client.js("document.querySelector('#marketing-decision-lens').value='size';document.querySelector('#marketing-decision-lens').dispatchEvent(new Event('change',{bubbles:true}))")
            assert client.js("document.querySelector('#marketing-decision-lens').value")=='size'
            assert client.js("marketingDecisionData(data.marketing,'SEGMENT 3','size').rankings[0].id")=='SEGMENT 1'
            assert client.js("![...document.querySelectorAll('#marketing-analysis svg *')].some(n=>[...n.attributes].some(a=>/NaN|Infinity/.test(a.value)))")
            assert not client.errors, client.errors
            screenshot=client.call('Page.captureScreenshot',{'format':'png'})
            (shot_dir/'getchells-marketing-standalone.png').write_bytes(base64.b64decode(screenshot['data']))
            client.call('Page.navigate',{'url':html_export.as_uri()})
            client.wait("document.querySelector('h1')?.textContent.includes('Brand, customer service')")
            assert client.js("document.body.innerText.includes('$4,314,000')")
            assert not client.js("!!document.querySelector('script,link[rel=stylesheet],iframe')")
            screenshot=client.call('Page.captureScreenshot',{'format':'png'})
            (shot_dir/'getchells-team-report.png').write_bytes(base64.b64decode(screenshot['data']))
            client.call('Page.navigate',{'url':offline_export.as_uri()})
            client.wait('!!window.OfflineAssortment')
            assert client.js('OfflineAssortment.getValues().high_depth')==50
            assert client.js('OfflineAssortment.getReport().candidate.decisions.online')==9_000_000
            assert not client.errors, client.errors
            print('PASS: all 10 pages, 16 fields, live budget and overspend, assumptions, optimization, scenarios, and mobile layout.')
            print('PASS: Marketing Intelligence raw tables, scope audit, segment selection, mobile layout, overview context, and assortment segmentation diagnostic.')
            print('PASS: five segmentation charts, accessible SVG titles, decision-lens rankings, synced click/keyboard selections, indexed trends, valid coordinates, and no plan mutation.')
            print('PASS: Assortment Lab workbook import, four-only edits, live effects, frozen 12 inputs, invalid guards, navigation, reset/benchmarks, baseline replacement, isolated scenario saving, and comparison download.')
            print('PASS: chat guidance, citations, what-if without mutation, unsupported questions, HTML escaping, session history, and clear chat.')
            print('PASS: Year-2 defaults, no repeated uplift, draft isolation/preservation, stale-result guards, delayed benefits, growth, unpriced presets, JSON export, explicit studio adoption, and direct page reload.')
            print('PASS: shareable HTML download and standalone file:// report opening, with no app scripts or external stylesheets.')
            print('PASS: web-app offline-lab export opens as a playable standalone file with the submitted four settings preserved.')
            print('PASS: Marketing Intelligence standalone HTML opens offline with embedded charts, no external assets, no network requests and synced segment controls.')
            print('Screenshot:', output)
        finally:
            if client:
                client.sock.close()
            process.terminate()
            process.wait(timeout=15)


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import app
    with tempfile.TemporaryDirectory(prefix='getchells-test-db-') as directory:
        app.DB = Path(directory) / 'scenarios.sqlite3'
        server = ThreadingHTTPServer(('127.0.0.1', 0), app.Handler)
        BASE_URL = f'http://127.0.0.1:{server.server_port}'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            main()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
