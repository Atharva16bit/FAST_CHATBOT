from pathlib import Path
import os
os.environ['FAST_ENABLE_SEMANTIC']='0'
from retrieval import KnowledgeBase
kb = KnowledgeBase(Path(__file__).resolve().parents[1] / 'data')

def test_admission_paraphrases():
    for q in ['what is the admissions procedure', 'How do I apply for admission?', 'tell me admission process']:
        result = kb.retrieve(q)
        assert result.intent == 'application_process'
        assert result.records

def test_personal_status_no_leak():
    r = kb.retrieve('what is my application status')
    assert 'cannot access' in r.direct_answer.lower()

def test_future_fees_no_fabrication():
    r = kb.retrieve('What is the B.Tech CSE fee for 2029?')
    assert not r.records
    assert 'cannot confirm' in r.direct_answer.lower()

def test_out_of_scope():
    assert kb.retrieve('tell me a cricket score').intent == 'out_of_scope'
