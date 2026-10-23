import os
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from streamlit.testing.v1 import AppTest
from retrieval import KnowledgeBase
from guidance import erp_link
ROOT = Path(__file__).resolve().parents[1]

class GuidanceTests(unittest.TestCase):
    def test_personal_scores_are_not_admission_answers(self):
        kb = KnowledgeBase(ROOT/'data')
        for question in ['atharva score', 'What are my scores in BTech first year?', 'my CGPA', 'my attendance']:
            result = kb.retrieve(question)
            self.assertEqual(result.intent, 'personal_records')
            self.assertFalse(result.records)
            self.assertIn('database', result.direct_answer)
            self.assertIn('ERP', result.direct_answer)
    def test_user_provided_marks_can_still_ask_scholarship(self):
        result = KnowledgeBase(ROOT/'data').retrieve('My marks are 85 percent, what scholarship is listed?')
        self.assertEqual(result.intent, 'scholarship')
    def test_bare_score_asks_for_score_type(self):
        result = KnowledgeBase(ROOT/'data').retrieve('score')
        self.assertEqual(result.intent, 'score_clarification')
        self.assertIn('scholarships', result.direct_answer)
    @patch.dict(os.environ, {'GEMINI_API_KEY':'test-only', 'SHOW_API_SETTINGS':'false', 'JLU_ERP_URL':''})
    def test_missing_answer_has_choices_and_no_ai_call(self):
        with patch('assistant.create_client', return_value=Mock()) as create:
            app = AppTest.from_file(str(ROOT/'app.py')).run()
            app.chat_input[0].set_value('atharva score').run()
            self.assertFalse(app.exception)
            self.assertIn('database', app.session_state.messages[-1]['content'])
            self.assertTrue(any(b.label == 'Programs' for b in app.button))
            self.assertTrue(any(b.label == 'Fees' for b in app.button))
            create.assert_not_called()
            next(b for b in app.button if b.label == 'Fees').click().run()
            self.assertTrue(any(b.label == 'MCA' for b in app.button))
    @patch.dict(os.environ, {'GEMINI_API_KEY':'', 'JLU_ERP_URL':''})
    def test_score_buttons_route_to_personal_result_guidance(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        app.chat_input[0].set_value('score').run()
        next(b for b in app.button if b.label == 'My semester results').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state.messages[-1]['intent'], 'personal_records')
    @patch.dict(os.environ, {'GEMINI_API_KEY':''})
    def test_recent_history_can_expand_without_losing_messages(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        for _ in range(7):
            app.chat_input[0].set_value('B.Tech CSE fees').run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state.messages), 14)
        self.assertEqual(len(app.chat_message), 12)
        next(t for t in app.toggle if t.label == 'Show earlier messages').set_value(True).run()
        self.assertEqual(len(app.chat_message), 14)
        self.assertEqual(len(app.session_state.messages), 14)
    def test_erp_link_requires_configured_https(self):
        for value in ['', 'javascript:alert(1)', 'http://example.com', 'https://user:secret@example.com']:
            self.assertEqual(erp_link(value), '')
        self.assertEqual(erp_link('https://example.edu/student'), 'https://example.edu/student')

class FacultyRegressionTests(unittest.TestCase):
    def test_generic_faculty_phrases_return_complete_directory(self):
        kb = KnowledgeBase(ROOT/'data')
        for question in ['faculty', 'TELL ME ABOUT FACULTY', 'faculty details', 'teaching staff', 'teachers']:
            result = kb.retrieve(question)
            self.assertEqual(result.intent, 'faculty', question)
            self.assertEqual(len(result.records), 14, question)
            self.assertEqual(result.records[0]['entity'], 'Dr. Dileep Kumar Singh')
            self.assertIn('reshma.chavan@jlu.edu.in', result.direct_answer)
    def test_specific_faculty_and_brand_name_do_not_get_hijacked(self):
        kb = KnowledgeBase(ROOT/'data')
        self.assertEqual(len(kb.retrieve('Shivangee Nagar email').records), 1)
        self.assertEqual(kb.retrieve('Faculty of Science and Technology B.Tech CSE fees').intent, 'program_fee')
        self.assertEqual(kb.retrieve('faculty subjects').intent, 'faculty_assignment')
    @patch.dict(os.environ, {'GEMINI_API_KEY':''})
    def test_exact_reported_question_in_ui(self):
        app = AppTest.from_file(str(ROOT/'app.py')).run()
        app.chat_input[0].set_value('TELL ME ABOUT FACULTY').run()
        self.assertFalse(app.exception)
        reply = app.session_state.messages[-1]
        self.assertEqual(reply['intent'], 'faculty')
        self.assertEqual(len(reply['sources']), 14)
        self.assertNotIn('couldn’t find', reply['content'])
        self.assertTrue(any(c.value == '✓ Answer ready' for c in app.caption))

if __name__ == '__main__':
    unittest.main()
