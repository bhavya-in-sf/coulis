"""Retrieval diagnostics only. No claims about generation or personal taste."""
import hashlib
import json
import platform
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from .data import adapt, audit, digest, load, manifest
from coulis_core.retrieval import retrieve

def evaluate(rows, method='bm25', k=3):
    outcomes, users = [], defaultdict(list)
    for row in rows:
        if row['task'] == 'interaction_observation':
            continue
        start = time.perf_counter()
        selected = retrieve(row['query'], row['documents'], k, method)
        ids = [x['id'] for x in selected]
        relevant = row.get('relevant_ids')
        result = {'id':row['id'], 'user_id':row['user_id'], 'retrieved_ids':ids,
                  'latency_ms':(time.perf_counter()-start)*1000, 'recall_at_k':None, 'reciprocal_rank':None}
        if relevant:
            gold = set(relevant)
            result['recall_at_k'] = len(gold.intersection(ids))/len(gold)
            result['reciprocal_rank'] = next((1/(i+1) for i,x in enumerate(ids) if x in gold),0)
            users[(row['source'],row['user_id'])].append(result['recall_at_k'])
        outcomes.append(result)
    measured = [r for r in outcomes if r['recall_at_k'] is not None]
    mean = lambda xs: sum(xs)/len(xs) if xs else None
    return {'method':method, 'k':k, 'queries':len(outcomes), 'scored_queries':len(measured),
            'unscored_queries':len(outcomes)-len(measured),
            'mean_recall_at_k':mean([r['recall_at_k'] for r in measured]),
            'macro_user_recall_at_k':mean([mean(v) for v in users.values()]),
            'mean_reciprocal_rank':mean([r['reciprocal_rank'] for r in measured]),
            'outcomes':outcomes}

def run(input_path, manifest_path, output, k=3):
    m = manifest(manifest_path)
    raw = Path(input_path).read_bytes()
    rows = adapt(load(input_path), m)
    try:
        revision = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
        dirty = bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        revision, dirty = None, None
    root = Path(__file__).resolve().parents[1]
    code_hash = digest({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for folder in ('coulis_research','coulis_core') for p in sorted((root/folder).glob('*.py'))})
    report = {'schema':'coulis.research/report-v1', 'dataset':m, 'input_sha256':hashlib.sha256(raw).hexdigest(),
              'manifest_sha256':digest(m), 'code_sha256':code_hash, 'git_revision':revision,'git_dirty':dirty,
              'python':platform.python_version(), 'audit':audit(rows),
              'scope':'Retrieval diagnostics only. Not an official benchmark score, generation quality, or evidence of personal taste.',
              'conditions':[evaluate(rows,method,k) for method in ('none','bm25','tfidf')]}
    out = Path(output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+'\n')
    return report
