"""Explicit adapters; references and relevance labels never become retrieval inputs."""
import hashlib
import json
from pathlib import Path

SOURCES = {'lamp', 'longlamp', 'longmemeval', 'prism', 'coauthor', 'synthetic'}

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def load(path):
    text = Path(path).read_text()
    return json.loads(text) if text.lstrip().startswith(('[', '{')) and Path(path).suffix != '.jsonl' else [json.loads(x) for x in text.splitlines() if x.strip()]

def manifest(path):
    m = load(path)
    for key in ('source', 'version', 'url', 'license', 'allowed_uses'):
        if not m.get(key):
            raise ValueError(f'Manifest requires {key}')
    if m['source'] not in SOURCES or 'research_evaluation' not in m['allowed_uses']:
        raise ValueError('Unsupported source or evaluation permission missing')
    return m

def adapt(rows, m):
    """LaMP/LongLaMP question arrays and LongMemEval official JSON supported.

    PRISM conversations and CoAuthor raw events are preserved as observations,
    not automatically transformed into binary preferences.
    """
    if not isinstance(rows, list):
        raise ValueError('Expected a JSON array or JSONL records')
    out = []
    for row in rows:
        source = m['source']
        if source == 'longmemeval':
            ids, sessions, dates = row['haystack_session_ids'], row['haystack_sessions'], row['haystack_dates']
            if not len(ids) == len(sessions) == len(dates):
                raise ValueError('Misaligned LongMemEval sessions')
            docs = [{'id': str(i), 'text': '\n'.join(f"{t['role']}: {t['content']}" for t in turns), 'date': date}
                    for i, turns, date in zip(ids, sessions, dates)]
            unique = {}
            duplicate_count = 0
            for document in docs:
                previous = unique.get(document['id'])
                if previous is not None:
                    if previous['text'] != document['text']:
                        raise ValueError('Conflicting content for one session id')
                    previous.setdefault('alternate_dates', []).append(document['date'])
                    duplicate_count += 1
                    continue
                unique[document['id']] = document
            docs = list(unique.values())
            item = dict(id=str(row['question_id']), user_id=str(row['question_id']), task='memory_qa',
                        query=row['question'], reference=row['answer'], documents=docs,
                        relevant_ids=[str(x) for x in row['answer_session_ids']],
                        metadata={'question_type': row['question_type'], 'question_date': row['question_date'], 'duplicate_sessions_collapsed': duplicate_count})
        elif source in ('lamp', 'longlamp'):
            docs = []
            for p in row['profile']:
                # Explicit whitelist: do not silently ingest labels or arbitrary metadata.
                text = '\n'.join(str(p[k]) for k in ('title', 'text', 'abstract', 'description', 'review', 'summary') if p.get(k))
                if not text:
                    raise ValueError('Unsupported profile shape; add an explicit field mapping')
                docs.append({'id': str(p['id']), 'text': text, 'date': p.get('date', '')})
            item = dict(id=str(row['id']), user_id=str(row.get('user_id', row['id'])), task='personalized_generation',
                        query=row['input'], reference=row.get('output'), documents=docs, relevant_ids=None,
                        metadata={'identity': 'query-scoped unless upstream supplies user_id'})
        elif source == 'prism':
            item = dict(id=str(row['conversation_id']), user_id=str(row['user_id']), task='interaction_observation',
                        query=row['opening_prompt'], documents=[], relevant_ids=None,
                        metadata={'conversation_history': row['conversation_history'],
                                  'open_feedback': row.get('open_feedback'),
                                  'warning': 'No automatic pairwise labels; inspect documented rating fields first'})
        elif source == 'coauthor':
            # Caller supplies a session envelope; raw event payload is preserved losslessly.
            for k in ('session_id', 'writer_id', 'events'):
                if k not in row:
                    raise ValueError('CoAuthor envelope needs session_id, writer_id, events')
            item = dict(id=str(row['session_id']), user_id=str(row['writer_id']), task='interaction_observation',
                        query='', documents=[], relevant_ids=None, metadata={'events': row['events'],
                        'warning': 'Raw observations only; no keystroke replay or inferred rejection labels'})
        else:
            item = dict(row)
        item['source'] = source
        item['source_version'] = m['version']
        item['manifest_sha256'] = digest(m)
        item['tenant_id'] = m.get('tenant_id', 'public-research')
        if len({d['id'] for d in item['documents']}) != len(item['documents']):
            raise ValueError('Duplicate document ids')
        if any(not isinstance(d['text'], str) for d in item['documents']):
            raise ValueError('Document text must be a string')
        out.append(item)
    if len({x['id'] for x in out}) != len(out):
        raise ValueError('Duplicate example ids')
    return out

def user_split(source, user_id, seed=17):
    """Stable user-level split; not a temporal split or an upstream official split."""
    n = int(digest([seed, source, user_id])[:8], 16) % 100
    return 'train' if n < 70 else 'validation' if n < 85 else 'test'

def audit(rows):
    """Flag exact normalized duplicates spanning users/splits; no silent dropping."""
    seen, overlaps = {}, []
    for row in rows:
        split = user_split(row['source'], row['user_id'])
        for d in row['documents']:
            key = digest(' '.join(d['text'].lower().split()))
            group = (row['source'], row['user_id'], split)
            if key in seen and seen[key] != group:
                overlaps.append({'content_sha256': key, 'first': seen[key], 'second': group})
            else:
                seen[key] = group
    return {'examples': len(rows), 'unique_users': len({(r['source'], r['user_id']) for r in rows}),
            'duplicate_cross_group_documents': overlaps,
            'near_duplicate_detection': 'not implemented; review before training'}
