import hashlib,json,statistics
from importlib.resources import files
from pathlib import Path
from datetime import datetime,timezone
from .core import FIELDS,PROMPT,extract,rules_extract,validate,repair_from_evidence

def fixtures():return json.loads(files('invoice_review').joinpath('data/cases.json').read_text(encoding='utf-8'))

def measure(case,result):
    obj=result['extracted']
    matches={f:isinstance(obj,dict) and isinstance(obj.get(f),dict) and obj[f].get('value')==case['gold'][f] for f in FIELDS}
    return {'field_matches':matches,'exact_record':all(matches.values()),
            'routing_correct':(result['status']=='CHECKS_PASSED')==case['expected_checks_passed']}

def run(model,out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[]
    for case in fixtures():
        if case['split']!='evaluation':continue
        obj=rules_extract(case['text']);baseline={**validate(case['text'],obj),'extracted':obj}
        try:result=extract(case['text'],model)
        except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
            result=dict(status='ERROR',issues=[str(exc)],extracted={},normalized={},checked={},balance_delta=None,raw='',latency_seconds=0,usage={})
        rows.append({**case,'llm':result,'rules':baseline,'llm_metrics':measure(case,result),'rules_metrics':measure(case,baseline)})
        print(case['id'],result['status'],rows[-1]['llm_metrics']['exact_record'],flush=True)
        (out/'progress.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    summary={}
    for method in ('llm','rules'):
        summary[method]={'exact_records':sum(r[method+'_metrics']['exact_record'] for r in rows),
          'field_matches':sum(sum(r[method+'_metrics']['field_matches'].values()) for r in rows),
          'routing_correct':sum(r[method+'_metrics']['routing_correct'] and r[method]['status']!='ERROR' for r in rows),
          'checks_passed':sum(r[method]['status']=='CHECKS_PASSED' for r in rows),
          'unsafe_passes':sum(r[method]['status']=='CHECKS_PASSED' and not r['expected_checks_passed'] for r in rows),
          'errors':sum(r[method]['status']=='ERROR' for r in rows)}
    summary.update(records=len(rows),fields=len(rows)*len(FIELDS),median_latency_seconds=statistics.median(r['llm']['latency_seconds'] for r in rows),
        prompt_tokens=sum(r['llm']['usage'].get('prompt_tokens',0) for r in rows),completion_tokens=sum(r['llm']['usage'].get('completion_tokens',0) for r in rows))
    payload={'created_utc':datetime.now(timezone.utc).isoformat(),'model':model.model,'summary':summary,'rows':rows,
        'protocol':{'development':4,'evaluation':16,'temperature':0,'seed':41,'max_tokens':900,'thinking':False,
          'prompt_sha256':hashlib.sha256(PROMPT.encode()).hexdigest(),'fixture_sha256':hashlib.sha256(json.dumps(fixtures(),sort_keys=True).encode()).hexdigest()}}
    payload=add_repair_results(payload)
    (out/'evaluation.json').write_text(json.dumps(payload,indent=2),encoding='utf-8');(out/'progress.json').unlink(missing_ok=True)
    print(json.dumps(summary,indent=2));return payload

def add_repair_results(payload):
    rows=payload['rows']
    for r in rows:
        r['repaired']=repair_from_evidence(r['text'],r['llm'])
        r['repaired_metrics']=measure(r,r['repaired'])
    payload['summary']['repaired']={
      'exact_records':sum(r['repaired_metrics']['exact_record'] for r in rows),
      'field_matches':sum(sum(r['repaired_metrics']['field_matches'].values()) for r in rows),
      'routing_correct':sum(r['repaired_metrics']['routing_correct'] and r['repaired']['status']!='ERROR' for r in rows),
      'checks_passed':sum(r['repaired']['status']=='CHECKS_PASSED' for r in rows),
      'unsafe_passes':sum(r['repaired']['status']=='CHECKS_PASSED' and not r['expected_checks_passed'] for r in rows),
      'errors':sum(r['repaired']['status']=='ERROR' for r in rows),
      'corrected_fields':sum(len(r['repaired'].get('corrections',[])) for r in rows)}
    payload['protocol']['repair_note']='The optional source-line repair was developed after inspecting raw-run identifier errors. Its scores are a diagnostic replay on seen examples, not independent validation.'
    return payload

def render(payload,path):
    template=files('invoice_review').joinpath('template.html').read_text(encoding='utf-8')
    Path(path).write_text(template.replace('__DATA__',json.dumps(payload,allow_nan=False).replace('<','\\u003c')),encoding='utf-8')
