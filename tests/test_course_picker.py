import os
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from retrieval import KnowledgeBase
from presentation import clean_answer, fee_answer
ROOT = Path(__file__).resolve().parents[1]

@patch.dict(os.environ, {'GEMINI_API_KEY': ''})
class CoursePickerTests(unittest.TestCase):
    def test_home_picker_and_exact_fees(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        next(b for b in app.button if b.label == 'Understand fees').click().run()
        self.assertEqual(len([b for b in app.button if str(b.key).startswith('fee_course_')]), 10)
        next(b for b in app.button if b.label == 'BCA (Data Science)').click().run()
        self.assertFalse(app.exception)
        reply = app.session_state.messages[-1]['content']
        for value in ['90,000', '55,000', '25,000', '10,000', '30,000', 'separate']:
            self.assertIn(value, reply)
        self.assertFalse(any('Sources and evidence' in e.label or e.label == 'Response details' for e in app.expander))
    def test_vague_fee_question_offers_courses(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        app.chat_input[0].set_value('fees').run()
        self.assertTrue(any(b.label == 'MCA' for b in app.button))
    def test_every_course_keeps_stored_amounts(self):
        kb = KnowledgeBase(ROOT/'data')
        for record in kb.by_topic['program_fee']:
            result = kb.retrieve(f"Annual fee breakdown for {record['entity']} for 2026-27?")
            answer = fee_answer(result)
            self.assertIn(record['entity'], answer)
            self.assertIn('Annual academic fee', answer)
            self.assertIn('Hostel and mess', answer)
    def test_display_cleanup_preserves_specific_limits(self):
        self.assertEqual(clean_answer('Apply online [KB0277, KB0031].'), 'Apply online.')
        self.assertIn('deadline has passed', clean_answer('The recorded deadline has passed.'))

if __name__ == '__main__':
    unittest.main()
