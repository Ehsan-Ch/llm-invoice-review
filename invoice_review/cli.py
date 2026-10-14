import argparse,json,sys
from pathlib import Path
from .core import extract,rules_extract,validate,repair_from_evidence
from .model import LocalModel
from .ledger import Ledger

def main():
    p=argparse.ArgumentParser(description='Extract invoice fields locally and record human review decisions. No payments.')
    p.add_argument('--endpoint',default='http://127.0.0.1:8095');p.add_argument('--model',default='invoice-qwen')
    p.add_argument('--db',default='runtime/review.sqlite')
    sub=p.add_subparsers(dest='command',required=True)
    for name in ('extract','ingest'):
        s=sub.add_parser(name);s.add_argument('file',type=Path);s.add_argument('--backend',choices=['llm','rules'],default='llm');s.add_argument('--repair-evidence',action='store_true')
    sub.add_parser('list')
    a=sub.add_parser('audit');a.add_argument('id')
    r=sub.add_parser('review');r.add_argument('id');r.add_argument('action',choices=['approve','reject','reopen']);r.add_argument('--version',type=int,required=True);r.add_argument('--actor',required=True);r.add_argument('--reason',required=True)
    e=sub.add_parser('evaluate');e.add_argument('--out',default='reports/evaluation')
    h=sub.add_parser('render');h.add_argument('--input',default='reports/evaluation/evaluation.json');h.add_argument('--out',default='reports/evaluation/report.html')
    args=p.parse_args();ledger=None
    try:
        if args.command in ('extract','ingest'):
            text=args.file.read_text(encoding='utf-8')
            if args.backend=='rules':
                obj=rules_extract(text);result={**validate(text,obj),'extracted':obj,'backend':'rules'}
            else:result={**extract(text,LocalModel(args.endpoint,args.model)),'backend':'llm'}
            if args.repair_evidence:result=repair_from_evidence(text,result)
            if args.command=='ingest':
                ledger=Ledger(args.db);print(json.dumps({**ledger.add(text,result),'result':result},indent=2))
            else:print(json.dumps(result,indent=2))
            return 2 if result['status']=='NEEDS_REVIEW' else 0
        if args.command in ('list','audit','review'):
            ledger=Ledger(args.db)
            result=ledger.list() if args.command=='list' else ledger.audit(args.id) if args.command=='audit' else ledger.review(args.id,args.action,args.version,args.actor,args.reason)
            print(json.dumps(result,indent=2));return 0
        from .evaluate import run,render
        if args.command=='evaluate':
            result=run(LocalModel(args.endpoint,args.model),args.out);render(result,Path(args.out)/'report.html')
            return 1 if result['summary']['llm']['errors'] else 0
        render(json.loads(Path(args.input).read_text(encoding='utf-8')),args.out);return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        print(f'Unable to complete: {exc}',file=sys.stderr);return 1
    finally:
        if ledger:ledger.close()

if __name__=='__main__':sys.exit(main())
