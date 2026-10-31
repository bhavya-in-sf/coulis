#!/usr/bin/env python3
"""Reproducible rule diagnostic, NOT voice accuracy or eight-axis critique validation."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from coulis_core import check, profile_from_folder


def score(text, prof, surface='linkedin'):
    # Remove claim identifiers and exclude factual/banned-phrase issues from this diagnostic.
    # This is a deliberately weak rule baseline, not a personal voice metric.
    masked = re.sub(r'\b\d[\d,.]*[kKmM%]*\b', '[NUMBER]', text)
    result = check(masked, prof, surface or 'linkedin')
    relevant = [i for i in result['issues'] if i['check'] in {'em_dash', 'filler', 'slang'}]
    return max(0, 100 - sum(15 if i['level'] == 'Hold' else 5 for i in relevant))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(a):
    source = Path(a.heldout if a.cmd == 'voice' else a.picks)
    rows = [json.loads(l) for l in source.read_text().splitlines() if l.strip()]
    paths = a.personas if a.cmd == 'voice' else [a.persona]
    if len({Path(p).name for p in paths}) != len(paths):
        raise ValueError('Persona folder names must be unique')
    profiles = {Path(p).name: profile_from_folder(p) for p in paths}
    if a.cmd == 'voice' and len(profiles) < 2:
        raise ValueError('At least two profiles are required')
    details, pairs, wins, ties = [], 0, 0, 0
    for index, row in enumerate(rows):
        surface = row.get('surface', 'linkedin')
        if a.cmd == 'voice':
            if row['author'] not in profiles:
                raise ValueError('Unknown author: ' + row['author'])
            if any(row['text'].strip() == sample.strip() for sample in profiles[row['author']].samples):
                raise ValueError('Held-out text duplicates a profile sample')
            preferred = score(row['text'], profiles[row['author']], surface)
            others = [score(row['text'], p, surface) for name, p in profiles.items() if name != row['author']]
        else:
            preferred = score(row['picked'], next(iter(profiles.values())), surface)
            others = [score(t, next(iter(profiles.values())), surface) for t in row['rejected']]
            if not others:
                raise ValueError('Each pick needs a rejected alternative')
        w, t = sum(preferred > x for x in others), sum(preferred == x for x in others)
        details.append({'row': index, 'comparisons': len(others), 'wins': w, 'ties': t,
                        'strict_win_against_all': bool(others) and w == len(others)})
        pairs += len(others); wins += w; ties += t
    try:
        commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip())
    except (OSError, subprocess.CalledProcessError):
        commit = 'unknown'
        dirty = None
    inputs = {str(source): digest(source)}
    for folder in paths:
        for filename in ('TASTE.md', 'claims.md', 'claims.json', 'preferences.json'):
            file = Path(folder) / filename
            if file.exists():
                inputs[str(file)] = digest(file)
    code = {str(p): digest(p) for root in ('coulis_core', 'scripts') for p in sorted(Path(root).glob('*.py'))}
    code['evals/benchmark.py'] = digest(__file__)
    return {'schema': 'coulis.rule-diagnostic/v1', 'task': a.cmd,
            'not_validated': ['eight-axis critique', 'voice quality', 'time saved', 'unseen-topic improvement'],
            'dataset_version': a.dataset_version, 'split_description': a.split_description,
            'public_inputs': a.public_inputs, 'command': [sys.executable] + sys.argv,
            'git_commit': commit, 'working_tree_dirty': dirty, 'input_sha256': inputs, 'code_sha256': code,
            'rows': len(rows), 'profiles': len(profiles), 'comparisons': pairs,
            'wins': wins, 'ties': ties, 'losses': pairs-wins-ties,
            'strict_winning_rows': sum(r['strict_win_against_all'] for r in details), 'details': details,
            'caution': 'Comparisons sharing authors/posts are dependent. No accuracy or confidence interval is inferred.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    subs = ap.add_subparsers(dest='cmd', required=True)
    for name in ('voice', 'picks'):
        sub = subs.add_parser(name)
        if name == 'voice':
            sub.add_argument('--personas', nargs='+', required=True); sub.add_argument('--heldout', required=True)
        else:
            sub.add_argument('--persona', required=True); sub.add_argument('--picks', required=True)
        sub.add_argument('--dataset-version', required=True)
        sub.add_argument('--split-description', required=True)
        sub.add_argument('--public-inputs', action='store_true')
        sub.add_argument('--output', required=True)
    args = ap.parse_args()
    report = run(args)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
