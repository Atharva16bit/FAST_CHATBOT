"""Topic regression cases include common short phrases, aliases and boundaries."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from streamlit.testing.v1 import AppTest
from retrieval import KnowledgeBase
ROOT = Path(__file__).resolve().parents[1]

class TopicAuditTests(unittest.TestCase):
    def test_curated_topic_matrix(self):
        kb = KnowledgeBase(ROOT/'data')
        cases = json.loads((ROOT/'evaluation/topic_regression.json').read_text())
        for case in cases:
            with self.subTest(question=case['question']):
                result = kb.retrieve(case['question'])
                self.assertEqual(result.intent, case['intent'])
                if 'records' in case:
                    self.assertEqual(len(result.records), case['records'])
                if 'contains' in case:
                    answer = result.direct_answer or kb.format_answer(result.intent, result.records, case['question'])
                    self.assertIn(case['contains'], answer)
    def test_document_and_program_followups(self):
        kb = KnowledgeBase(ROOT/'data')
        for reply in ['UG','PG']:
            result = kb.retrieve(reply, previous_intent='documents')
            self.assertEqual(result.intent, 'documents')
            self.assertTrue(result.records)
        result = kb.retrieve('And MCA?', ['B.Tech (Computer Science and Engineering)'], previous_intent='program_fee')
        self.assertEqual(result.intent, 'program_fee')
        self.assertEqual(result.records[0]['entity'], 'MCA')
    def test_substrings_and_compound_questions_keep_correct_topic(self):
        kb = KnowledgeBase(ROOT/'data')
        cases = {
            'Mere BCA batch ka approved syllabus connected hai?': 'curriculum',
            'Is the latest B.Tech CSE section A schedule connected?': 'timetable',
            'How do I submit an online application for a FAST program?': 'application_process',
            'What is the role of original document verification?': 'admission_confirmation',
            'Help us compare B.Tech CSE and BCA for admission.': 'program_comparison',
            'Break down the B.Tech AI fee into tuition, resource and exam charges.': 'fee_breakdown',
            'Is B.Tech Robotics and Automation currently offered?': 'program_status',
            'Which school and duration are listed for MCA?': 'program_info',
            'Does the workbook say the application fee is refundable?': 'application_fee',
            'Thank you for explaining the fee components.': 'thanks',
            'Are there football scholarships?': 'scholarship',
        }
        for question, intent in cases.items():
            with self.subTest(question=question):
                self.assertEqual(kb.retrieve(question).intent, intent)
    def test_unknown_subject_does_not_return_random_allocations(self):
        result = KnowledgeBase(ROOT/'data').retrieve('Who teaches quantum mechanics?')
        self.assertEqual(result.intent, 'faculty_assignment')
        self.assertFalse(result.records)
        self.assertIn('couldn’t find', result.direct_answer)
    def test_natural_program_followup_keeps_fee_task(self):
        kb = KnowledgeBase(ROOT/'data')
        for question in ['What about MCA?', 'How about MCA?', 'And MCA?']:
            result = kb.retrieve(question, ['B.Tech (Computer Science and Engineering)'], previous_intent='program_fee')
            self.assertEqual(result.intent, 'program_fee')
            self.assertEqual(result.records[0]['entity'], 'MCA')
    @patch.dict(os.environ, {'GEMINI_API_KEY':''})
    def test_thanks_preserves_program_followup_context(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        for question in ['B.Tech CSE fees', 'Thanks', 'What about MCA?']:
            app.chat_input[0].set_value(question).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state.messages[-1]['intent'], 'program_fee')
        self.assertIn('100,000', app.session_state.messages[-1]['content'])
    @patch.dict(os.environ, {'GEMINI_API_KEY':''})
    def test_multiple_turns_have_no_duplicate_or_stuck_pending_state(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        for question in ['faculty', 'admission', 'programs', 'MCA', 'my scores', 'xyzabc']:
            before = len(app.session_state.messages)
            app.chat_input[0].set_value(question).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.session_state.messages), before + 2)
            self.assertIsNone(app.session_state.pending_prompt)
            self.assertFalse(app.chat_input[0].disabled)
        self.assertEqual(app.session_state.turn_sequence, 6)
    @patch.dict(os.environ, {'GEMINI_API_KEY':''})
    def test_scholarship_and_document_choices_answer_the_topic(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        app.chat_input[0].set_value('scholarships').run()
        next(b for b in app.button if b.label == 'Academic scholarships').click().run()
        self.assertEqual(len(app.session_state.messages[-1]['sources']), 3)
        app.chat_input[0].set_value('documents').run()
        next(b for b in app.button if b.label == 'Undergraduate (UG)').click().run()
        self.assertEqual(app.session_state.messages[-1]['intent'], 'documents')
        self.assertTrue(app.session_state.messages[-1]['sources'])
    @patch.dict(os.environ, {'GEMINI_API_KEY':'test-only'})
    def test_retry_replaces_failed_exchange(self):
        with patch('assistant.create_client', return_value=Mock()), patch('assistant.stream_answer', side_effect=RuntimeError('test failure')):
            app = AppTest.from_file(str(ROOT/'app.py')).run()
            app.chat_input[0].set_value('How do I apply?').run()
        self.assertEqual(len(app.session_state.messages), 2)
        with patch('assistant.create_client', return_value=Mock()), patch('assistant.stream_answer', return_value=iter(['Apply online.'])):
            next(b for b in app.button if b.label == 'Retry last AI explanation').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state.messages), 2)
        self.assertEqual(app.session_state.messages[-1]['mode'], 'Gemini · retrieved evidence')
        self.assertIsNone(app.session_state.pending_prompt)

if __name__ == '__main__':
    unittest.main()
