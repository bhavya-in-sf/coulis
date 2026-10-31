import argparse
import json
from pathlib import Path
from .data import adapt, audit, load, manifest, user_split
from .evaluate import run

def main():
    parser = argparse.ArgumentParser(description='Coulis research: local data import and retrieval evaluation')
    sub = parser.add_subparsers(dest='command',required=True)
    for name in ('import','evaluate'):
        p = sub.add_parser(name)
        p.add_argument('--input',required=True)
        p.add_argument('--manifest',required=True)
        p.add_argument('--output',required=True)
        if name == 'evaluate':
            p.add_argument('--k',type=int,default=3)
    args = parser.parse_args()
    if args.command == 'evaluate':
        report = run(args.input,args.manifest,args.output,args.k)
        print(json.dumps([{k:v for k,v in c.items() if k != 'outcomes'} for c in report['conditions']],indent=2))
    else:
        rows = adapt(load(args.input),manifest(args.manifest))
        for row in rows:
            row['research_user_split'] = user_split(row['source'],row['user_id'])
        p = Path(args.output); p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        print(json.dumps(audit(rows),indent=2))

if __name__ == '__main__':
    main()
