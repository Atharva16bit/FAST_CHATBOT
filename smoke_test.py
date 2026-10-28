"""Run fast, offline deployment diagnostics without starting Streamlit."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent
required = ('app.py', 'assistant.py', 'retrieval.py', 'semantic_retrieval.py',
            'presentation.py', 'style.css', 'assets/jlu_icon.png',
            'assets/jlu_wordmark_reference.png', 'assets/favicon.ico',
            'data/knowledge.jsonl', 'data/intent_examples.jsonl', 'data/faculty_directory.jsonl')
missing = [name for name in required if not (ROOT / name).is_file()]
assert not missing, f'Missing deployment files: {missing}'
for name in ('knowledge', 'intent_examples', 'faculty_directory'):
    p = ROOT / 'data' / (name + '.jsonl')
    rows = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
    assert rows, f'Empty data source: {p}'
    print(f'{name}: {len(rows)} records')
# Test retrieval without optional embedding model or remote APIs.
os.environ['FAST_ENABLE_SEMANTIC'] = '0'
from retrieval import KnowledgeBase
kb = KnowledgeBase(ROOT / 'data')
queries = ['What is the admissions procedure?', 'How do I apply for admission?',
           'What are the fees for B.Tech CSE?', 'What are the fees for 2029?']
for q in queries:
    result = kb.retrieve(q)
    print(q, '=>', result.intent, len(result.records))
    assert result.records or result.direct_answer, f'No retrieval answer for: {q}'
print('Offline smoke checks passed.')
