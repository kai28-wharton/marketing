"""Package the four-input lab and its data as one offline, interactive HTML file."""
import json
from datetime import datetime, timezone
from pathlib import Path
from assortment import analyze, import_team_plan

ROOT=Path(__file__).resolve().parent
FILENAME='getchells-assortment-lab-offline.html'


def script_json(value):
    # Prevent a workbook/source string from terminating the inert JSON script tag.
    return json.dumps(value,ensure_ascii=False,allow_nan=False).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e').replace('\u2028','\\u2028').replace('\u2029','\\u2029')


def build_offline_lab(payload,data,validate,evaluate):
    if payload is None:
        team=import_team_plan(data['factors'],validate)
        baseline=team['decisions'] if team['available'] else data['baseline']
        payload={'baseline':baseline,'changes':{k:baseline[k] for k in ('low_breadth','low_depth','high_breadth','high_depth')},
                 'assumptions':team['assumptions'] if team['available'] else data['assumptions'],
                 'source':team['source']+' · Column B' if team['available'] else 'Original screenshot reference (team workbook unavailable)'}
    source=payload.get('source','Locked plan exported from Assortment Lab')
    if not isinstance(source,str) or len(source)>300:
        raise ValueError('Offline lab source must be a string of at most 300 characters.')
    report=analyze(payload,data,validate,evaluate)
    base=report['baseline']
    snapshot={
        'format_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),
        'source':source,'model_version':base['model_version'],
        'baseline_fingerprint':report['baseline_fingerprint'],
        'baseline':base['decisions'],'initial_values':{k:report['candidate']['decisions'][k] for k in report['adjustable_keys']},
        'assumptions':base['assumptions'],'configuration':base['kahn']['configuration'],
        'weights':base['kahn']['weights'],'historical_evidence':base['kahn']['historical_evidence'],
        'observed_scores':{r['quadrant']:r['value'] for r in data['kahn'] if r['round']==0 and r['company']=="GETCHELL'S"},
        'income':{r['name']:r['value'] for r in data['income']},'budget':data['budget'],
        'factors':data['factors'],'sources':data['sources'],
        'limitations':report['limitations'],'readiness':report['readiness'],'baseline_warnings':base['warnings'],
        'marketing':data.get('marketing',{'available':False}),
        'verification':{'baseline_scores':base['scores'],'baseline_net_income':base['net_income'],
                        'initial_scores':report['candidate']['scores'],'initial_net_income':report['candidate']['net_income']},
    }
    template=(ROOT/'offline'/'assortment.html').read_text()
    # Replace the data last so user/source strings cannot act as template tokens.
    styles=(ROOT/'offline'/'assortment.css').read_text()+'\n'+(ROOT/'web'/'assortment_readiness.css').read_text()
    scripts=(ROOT/'web'/'assortment_readiness.js').read_text()+'\n'+(ROOT/'web'/'marketing.js').read_text()+'\n'+(ROOT/'offline'/'assortment.js').read_text()
    styles+='\n'+(ROOT/'web'/'marketing.css').read_text()
    styles+='\n'+(ROOT/'web'/'vivid.css').read_text()
    return template.replace('__INLINE_STYLE__',styles).replace('__INLINE_SCRIPT__',scripts).replace('__SNAPSHOT_JSON__',script_json(snapshot))


if __name__=='__main__':
    import app
    output=ROOT/'reports'/FILENAME
    output.parent.mkdir(exist_ok=True)
    output.write_text(build_offline_lab(None,app.load_data(),app.validate,app.evaluate),encoding='utf-8')
    print(output)
