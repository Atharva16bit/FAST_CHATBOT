import os
os.environ['FAST_ENABLE_SEMANTIC'] = '0'
from pathlib import Path
from retrieval import KnowledgeBase
from presentation import display_answer

def kb():
    return KnowledgeBase(Path(__file__).resolve().parents[1] / 'data')

def test_fee_table_grounded():
    r = kb().retrieve('B.Tech CSE fee structure')
    text = display_answer(r.direct_answer or kb().format_answer(r.intent, r.records), r.intent, r.records)
    assert '₹35,000' in text and '₹1,50,000' in text
    assert 'Admission charges (separate)' in text
    assert 'Their payment frequency and refund conditions require confirmation' in text

def test_original_fee_data_not_changed():
    r = kb().retrieve('B.Tech CSE fee structure')
    assert 'INR 105,000' in r.records[0]['answer']

def test_unrelated_answer_not_reformatted():
    assert display_answer('Hello', 'greeting', []) == 'Hello'

def test_unknown_fee_format_not_fabricated():
    assert display_answer('Fee not available', 'program_fee', [{'answer':'Unknown','entity':'Example'}]) == 'Fee not available'
