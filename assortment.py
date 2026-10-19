"""Four-input assortment experiments around an explicitly locked full plan."""
import hashlib
import json
import math
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, BadZipFile
from assortment_evidence import LIMITATIONS, build_readiness
from marketing import assortment_alignment

KEYS = ('low_breadth', 'low_depth', 'high_breadth', 'high_depth')
TEAM_FILE = Path(__file__).resolve().parent / 'decision_making' / 'round_1' / 'decision_making_team11_round1.xlsx'
NS = {'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def _import_team_plan(factors, validate, path=None):
    """Read the known workbook without packages; never evaluate Excel formulas."""
    file=Path(path) if path is not None else TEAM_FILE
    if not file.exists():
        return {'available':False, 'source':'decision_making/decision_making_team11_0.xlsx',
                'message':'Team workbook not found. Lock a current or saved studio plan instead.'}
    labels = {f['label']:f for f in factors}
    with ZipFile(file) as archive:
        strings = []
        if 'xl/sharedStrings.xml' in archive.namelist():
            strings = [''.join(t.text or '' for t in node.findall('.//m:t',NS))
                       for node in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        styles = ET.fromstring(archive.read('xl/styles.xml'))
        custom = {int(n.get('numFmtId')):n.get('formatCode','') for n in styles.findall('m:numFmts/m:numFmt',NS)}
        percentage_styles = set()
        for i,style in enumerate(styles.findall('m:cellXfs/m:xf',NS)):
            fmt = int(style.get('numFmtId','0'))
            if fmt in (9,10) or '%' in custom.get(fmt,''):
                percentage_styles.add(i)
        root = ET.fromstring(archive.read('xl/worksheets/sheet1.xml'))

        def text(cell):
            value = cell.find('m:v',NS)
            raw = value.text if value is not None else ''
            if cell.get('t') == 's':
                return strings[int(raw)]
            if cell.get('t') == 'inlineStr':
                return ''.join(n.text or '' for n in cell.findall('.//m:t',NS))
            return raw

        plan, provenance, header = {}, {}, ''
        for row in root.findall('m:sheetData/m:row',NS):
            cells = {c.get('r'):c for c in row.findall('m:c',NS)}
            row_id = row.get('r')
            if row_id == '1':
                header = text(cells['B1']) if 'B1' in cells else 'Column B'
            label_cell = cells.get('A'+row_id)
            if label_cell is None:
                continue
            label = text(label_cell).strip()
            if label not in labels:
                continue
            f = labels[label]
            if f['key'] in plan:
                raise ValueError('Duplicate decision in team workbook: '+label)
            value_cell = cells.get('B'+row_id)
            if value_cell is None or value_cell.find('m:f',NS) is not None:
                raise ValueError('Team workbook needs an explicit, non-formula value for '+label)
            value = float(text(value_cell))
            if f['unit'] == '%':
                if int(value_cell.get('s','0')) not in percentage_styles:
                    raise ValueError('Percentage format is required in team workbook for '+label)
                value *= 100
            plan[f['key']] = value
            provenance[f['key']] = 'Sheet1!B'+row_id
    clean, assumptions = validate(plan)
    return {'available':True, 'source':str(file.relative_to(Path(__file__).resolve().parent)) if file.is_relative_to(Path(__file__).resolve().parent) else str(file),
            'column_label':header, 'decisions':clean, 'assumptions':assumptions, 'cells':provenance,
             'note':'Read submitted values from Column B. The workbook header and source path retain the user’s decision-period naming. Outcome linkage is recorded by the dashboard timeline, not inferred from old filenames. Percentage-formatted cells become percentage points; breadth/depth remain indices.'}


def import_team_plan(factors, validate, path=None):
    try:
        return _import_team_plan(factors,validate,path)
    except (BadZipFile,ET.ParseError,KeyError,IndexError,TypeError) as exc:
        raise ValueError('The team workbook is unreadable or does not have the expected Sheet1 / Column B layout.') from exc


def analyze(payload, data, validate, evaluate):
    baseline, assumptions = validate(payload.get('baseline'),payload.get('assumptions'))
    changes = payload.get('changes')
    if not isinstance(changes,dict) or set(changes) != set(KEYS):
        raise ValueError('Only the four breadth/depth fields may be changed; supply all four.')
    candidate, _ = validate(dict(baseline,**changes),assumptions)
    locked = [f['key'] for f in data['factors'] if f['key'] not in KEYS]
    # Rebuilding from the baseline guarantees that the other 12 values cannot drift.
    base = evaluate(baseline,assumptions,data)
    trial = evaluate(candidate,assumptions,data)

    def metrics(result):
        gross = result['gross_profit']
        return {'revenue':result['revenue'], 'cogs':result['cogs'],
                'gross_profit':gross, 'net_income':result['net_income'],
                'gross_margin':result['gross_margin'], 'explicit_spend':result['spent'],
                'remaining':result['remaining']}

    bm, cm = metrics(base), metrics(trial)
    deltas = {key:cm[key]-bm[key] for key in bm}
    # Exact four-factor Shapley values include score-bound and financial interactions.
    cache = {}
    for mask in range(16):
        plan = dict(baseline)
        for i,key in enumerate(KEYS):
            if mask & (1<<i):
                plan[key] = candidate[key]
        result = evaluate(plan,assumptions,data,detailed=False)
        cache[mask] = {'scores':result['scores'],'financial':metrics(result)}
    attribution = []
    for i,key in enumerate(KEYS):
        row = {'key':key,'scores':{q:0. for q in base['scores']},'financial':{m:0. for m in bm}}
        for mask in range(16):
            if mask & (1<<i):
                continue
            weight = 1/(4*math.comb(3,bin(mask).count('1')))
            for group in ('scores','financial'):
                for metric in row[group]:
                    row[group][metric] += weight*(cache[mask|(1<<i)][group][metric]-cache[mask][group][metric])
        attribution.append(row)
    probes = []
    for key in KEYS:
        row = {'key':key,'step':10}
        for label,step in [('increase',10),('decrease',-10)]:
            if not 1 <= candidate[key]+step <= 100:
                row[label] = None
                continue
            plan = dict(candidate,**{key:candidate[key]+step})
            result = evaluate(plan,assumptions,data,detailed=False)
            m = metrics(result)
            row[label] = {'scores':{q:result['scores'][q]-trial['scores'][q] for q in trial['scores']},
                          'revenue':m['revenue']-cm['revenue'],'net_income':m['net_income']-cm['net_income']}
        probes.append(row)
    outside = [f['label'] for f in data['factors'] if f['key'] in KEYS and
               not f['industry']['minimum']<=candidate[f['key']]<=f['industry']['maximum']]
    readiness=build_readiness(data)
    return {'baseline':base, 'candidate':trial, 'baseline_financial':bm,'candidate_financial':cm,
            'financial_changes':deltas,'score_changes':{q:trial['scores'][q]-base['scores'][q] for q in base['scores']},
            'segments':{'baseline':base['segments'],'candidate':trial['segments']},
            'locked_keys':locked,'adjustable_keys':list(KEYS),
            'baseline_fingerprint':hashlib.sha256(json.dumps({'plan':baseline,'assumptions':assumptions},sort_keys=True).encode()).hexdigest()[:12],
            'attribution':attribution,'sensitivities':probes,'outside_industry_range':outside,
            'incremental_cost_allowance':max(0,deltas['net_income']),
            'limitations':readiness['limitations'],'readiness':readiness,
            'segment_alignment':assortment_alignment(data.get('marketing'),baseline,candidate)}
