"""Package the marketing review pages as offline, interactive HTML files.

The shared file reuses the same charts, segment selectors and source tables as
the live application, but embeds its own copy of the marketing data. It has no
external assets, no network calls and no dependency on the Python server.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FILENAME = 'getchells-marketing-intelligence.html'
PLACEHOLDERS = ('__INLINE_STYLE__', '__INLINE_SCRIPT__', '__MARKETING_JSON__')


def script_json(value):
    # Prevent a source string from terminating the inert JSON script tag.
    return (json.dumps(value, ensure_ascii=False, allow_nan=False)
            .replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def build_marketing_report(marketing, generated_at=None):
    if not isinstance(marketing, dict) or not marketing.get('available'):
        raise ValueError('Marketing data is unavailable; nothing to package.')
    for key in ('segments', 'attributes', 'companies', 'positions', 'raw_tables'):
        if not marketing.get(key):
            raise ValueError(f'Marketing data is missing required field: {key}')
    payload = {
        'format_version': 1,
        'generated_at': generated_at or datetime.now(timezone.utc).isoformat(),
        'marketing': marketing,
    }
    template = (ROOT / 'offline' / 'marketing.html').read_text(encoding='utf-8')
    for token in PLACEHOLDERS:
        assert token in template, f'offline/marketing.html is missing {token}'
    styles = '\n'.join((ROOT / 'web' / name).read_text(encoding='utf-8') for name in
                       ('style.css', 'marketing.css', 'marketing_charts.css', 'vivid.css', 'marketing_report.css'))
    scripts = '\n'.join((ROOT / 'web' / name).read_text(encoding='utf-8')
                        for name in ('marketing_charts.js', 'marketing.js')) + '\n' + (ROOT / 'offline' / 'marketing.js').read_text(encoding='utf-8')
    # Replace the data last so a source string cannot act as a template token.
    html = template.replace('__INLINE_STYLE__', styles).replace('__INLINE_SCRIPT__', scripts)
    assert '__INLINE_STYLE__' not in html and '__INLINE_SCRIPT__' not in html
    return html.replace('__MARKETING_JSON__', script_json(payload))


def build_current_report(data=None, page='marketing'):
    """Latest observed Marketing Intelligence, with no decision inputs exported."""
    from round_review import dataset
    current = data or dataset()
    if page not in ('marketing','segmentation','marketvalue','wacc','combined'):
        raise ValueError('Report page unavailable.')
    if page=='combined' and not all(current.get(k) for k in ('segment_decision','history_analysis','wacc_analysis','final_review')):
        raise ValueError('Combined report requires the final segmentation, market-value and WACC analyses.')
    payload = {key: current[key] for key in ('rounds', 'kahn', 'marketing', 'sources', 'model', 'simulation',
                                             'definitions', 'definitions_available')}
    payload['team'] = {key: current['team'][key] for key in ('source', 'column_label', 'sha256')}
    # Share targeting evidence, never the editable plan or conditional draft.
    payload['strategy'] = {key: current['strategy'][key] for key in ('policy','segments','boundary')}
    if current['current_round']>=2:
        payload['availability']=current['availability']
        payload['strategy'].update({key:current['strategy'][key] for key in ('objectives','focus_summary','criteria','required_evidence','sources','verdict','focus_group')})
        payload['segment_decision']=current['segment_decision']
        if current.get('history_analysis'):
            payload['history_analysis']=current['history_analysis']
            payload['strategy']['funding']=current['strategy']['funding']
            if current.get('wacc_analysis'):payload['wacc_analysis']=current['wacc_analysis']
            if current.get('final_review'):
                payload['final_review']=current['final_review']
                payload['simulation_complete']=True
    payload['generated_at'] = datetime.now(timezone.utc).isoformat()
    payload['report_page']=page
    payload.update({key:current[key] for key in ('current_round','previous_round','planning_round') if key in current})
    styles = '\n'.join((ROOT/'web'/name).read_text(encoding='utf-8') for name in ('style.css','vivid.css','review.css'))
    script = 'window.__deferReviewInit=true;\n'+'\n'.join((ROOT/'web'/name).read_text(encoding='utf-8') for name in ('review.js','current.js','segmentation_lab.js','history_analysis.js','final_analysis.js'))+'\ninit();'
    template = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'">
<title>Getchell’s · Round 1 Marketing Intelligence</title><style>__STYLE__</style></head>
<body class="report-only"><header class="report-banner"><strong>GETCHELL’S · MARKETING INTELLIGENCE · ROUND 1</strong><p id="report-generated"></p><button id="report-print">Print / save PDF</button></header><main><div id="content"></div></main>
<noscript>Enable JavaScript and open this file in a full browser to view the interactive charts and source tables.</noscript>
<footer>Share this HTML file itself. No server, installation or internet needed. Frozen Round 1 snapshot; regenerate to refresh source data. Intrinsic fair value and Round 1 segment CLV are unavailable.</footer>
<script type="application/json" id="review-data">__DATA__</script><script>__SCRIPT__</script></body></html>'''
    if current['current_round']>=2:
        c=current['current_round'];p=current['planning_round']
        template=template.replace('Round 1 Marketing Intelligence',f'Export {c} Marketing Intelligence')
        template=template.replace('MARKETING INTELLIGENCE · ROUND 1',f'MARKETING INTELLIGENCE · EXPORT {c} · ROUND {p} PLANNING')
        template=template.replace('<button id="report-print">', '<p><a href="#marketing">Marketing Intelligence</a> · <a href="#segmentation">Customer segmentation decision</a></p><button id="report-print">')
        template=template.replace('Frozen Round 1 snapshot; regenerate to refresh source data. Intrinsic fair value and Round 1 segment CLV are unavailable.',f'Frozen export {c} snapshot; regenerate to refresh. Current segment CLV is reported; financial statements are available through export {current["availability"]["financial_round"]}. Segment contribution and intrinsic equity value remain unquantified.')
    if page=='segmentation':
        template=template.replace(f'Export {current["current_round"]} Marketing Intelligence',f'Export {current["current_round"]} Customer segmentation decision')
        template=template.replace('MARKETING INTELLIGENCE · EXPORT','CUSTOMER SEGMENTATION DECISION · EXPORT')
    if current.get('history_analysis'):
        template=template.replace('Customer segmentation decision','Customer segmentation analysis').replace('CUSTOMER SEGMENTATION DECISION','CUSTOMER SEGMENTATION ANALYSIS')
        template=template.replace('<a href="#marketing">Marketing Intelligence</a>', '<a href="#overview">Executive overview</a> · <a href="#stp">STP decision</a> · <a href="#marketvalue">Market value analysis</a> · <a href="#marketing">Marketing Intelligence</a>')
    if page=='marketvalue':
        template=template.replace(f'Export {current["current_round"]} Marketing Intelligence',f'Export {current["current_round"]} Market value analysis').replace('MARKETING INTELLIGENCE · EXPORT','MARKET VALUE ANALYSIS · EXPORT')
    if current.get('wacc_analysis'):
        template=template.replace('<a href="#marketvalue">Market value analysis</a>','<a href="#marketvalue">Market value analysis</a> · <a href="#wacc">WACC impact analysis</a>')
    if page=='wacc':
        template=template.replace(f'Export {current["current_round"]} Marketing Intelligence',f'Export {current["current_round"]} WACC impact analysis').replace('MARKETING INTELLIGENCE · EXPORT','WACC IMPACT ANALYSIS · EXPORT')
    if current.get('simulation_complete'):
        template=template.replace(f'ROUND {current["planning_round"]} PLANNING','FINAL R1–R8 REVIEW')
    if page=='combined':
        nav='<p><a href="#overview">Executive overview</a> · <a href="#segmentation">Customer segmentation</a> · <a href="#marketvalue">Market value</a> · <a href="#wacc">WACC impact</a></p>'
        template=re.sub(r'<p><a href="#overview".*?</p>',nav,template,count=1,flags=re.S)
        template=template.replace(f'Export {current["current_round"]} Marketing Intelligence','Final R1–R8 Marketing & Finance Report')
        template=re.sub(r'<header class="report-banner">.*?</header>','',template,count=1,flags=re.S)
        template=re.sub(r'<footer>.*?</footer>','<footer>Five-section final review: overview, strategy, customer segmentation, market value and WACC. All sections use the same embedded R0–R8 evidence. No server or internet needed; print to PDF to share.</footer>',template,count=1,flags=re.S)
    return template.replace('__STYLE__',styles).replace('__SCRIPT__',script).replace('__DATA__',script_json(payload))


if __name__ == '__main__':
    import app
    from round_review import dataset
    current=dataset()
    output = ROOT / 'reports' / FILENAME
    output.parent.mkdir(exist_ok=True)
    output.write_text(build_current_report(current), encoding='utf-8')
    print(output)
    segmentation_output=ROOT/'reports/getchells-customer-segmentation-decision.html'
    segmentation_output.write_text(build_current_report(current,page='segmentation'),encoding='utf-8')
    print(segmentation_output)
    if current.get('history_analysis'):
        for page,name in [('segmentation','getchells-customer-segmentation-analysis.html'),('marketvalue','getchells-market-value-analysis.html'),('wacc','getchells-wacc-impact-analysis.html')]:
            path=ROOT/'reports'/name
            path.write_text(build_current_report(current,page=page),encoding='utf-8')
            print(path)
    if all(current.get(k) for k in ('segment_decision','history_analysis','wacc_analysis','final_review')):
        path=ROOT/'reports/getchells-final-report.html'
        path.write_text(build_current_report(current,page='combined'),encoding='utf-8')
        print(path)
