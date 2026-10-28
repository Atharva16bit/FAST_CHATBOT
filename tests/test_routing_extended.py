"""Manual independent regression prompts; not included in runtime intent_examples.jsonl."""
import os
from pathlib import Path
import pytest
os.environ['FAST_ENABLE_SEMANTIC'] = '0'
from retrieval import KnowledgeBase

@pytest.fixture(scope='module')
def kb():
    return KnowledgeBase(Path(__file__).resolve().parents[1] / 'data')

@pytest.mark.parametrize('question,intent', [
    ('How can I join FAST?', 'application_process'),
    ('Can you explain the steps for joining?', 'application_process'),
    ('I want to enroll at JLU', 'application_process'),
    ('What is the application procedure?', 'application_process'),
    ('How do admissions work?', 'application_process'),
    ('what is the admissions procedure', 'application_process'),
    ('Tell me about lecturers', 'faculty'),
    ('What are the class timings?', 'timetable'),
    ('How can I register for a course?', 'student_support'),
    ('What is the hostel fee?', 'hostel_fee'),
    ('Can I enter without maths?', 'eligibility'),
    ('Who teaches DBMS?', 'faculty_assignment'),
    ('Is admission still open?', 'live_admission'),
    ('What is the refund policy?', 'refund'),
    ('How much does B.Tech CSE cost?', 'program_fee'),
    ('Tell me about scholarships', 'scholarship'),
    ('Show me the latest cricket score', 'out_of_scope'),
    ('What is the deadline for admission?', 'admission_dates'),
    ('Do you provide hostel laundry?', 'hostel_facilities'),
    ('Can I see my grades?', 'personal_records'),
    ('Can I change my program?', 'program_transfer'),
    ('List all faculty members', 'faculty'),
    ('What is the duration of BCA?', 'program_duration'),
    ('Does the university offer transport?', 'transport'),
])
def test_varied_intents(kb,question,intent):
    assert kb.retrieve(question).intent == intent


def test_no_unsupported_future_facts(kb):
    r=kb.retrieve('How much are B.Tech CSE fees in 2029?')
    assert not r.records
    assert 'cannot confirm' in r.direct_answer.lower()


def test_admission_has_grounded_records(kb):
    r=kb.retrieve('How can I join FAST?')
    assert r.records and all(item['topic']=='application_process' for item in r.records)


def test_datasets_unmodified(kb):
    assert len(kb.records) >= 100
    assert all(r.get('record_id') and r.get('source_refs') for r in kb.records)


@pytest.mark.parametrize('question', [
    'fess for btech ai',
    'feees for b.tech ai',
    'fees for btech ai',
])
def test_fee_typo_with_specialization(kb, question):
    result = kb.retrieve(question)
    assert result.intent == 'program_fee'
    assert result.records and all(row['topic'] == 'program_fee' for row in result.records)


def test_fee_followup_preserves_program(kb):
    first = kb.retrieve('fees for btech ai')
    second = kb.retrieve('fees?', first.programs, previous_intent=first.intent)
    assert second.intent == 'program_fee'
    assert second.records and second.records[0]['entity'] == first.records[0]['entity']
