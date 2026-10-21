import os,sys,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connection import configured_key,connection_id,verify_connection
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
class ConnectionTests(unittest.TestCase):
 def test_placeholder_not_used(self):
  self.assertEqual(configured_key('', 'your_google_ai_studio_api_key_here'),'')
  self.assertEqual(configured_key('manual-key','environment-key'),'manual-key')
 def test_fingerprint_changes(self):
  self.assertNotEqual(connection_id('k1','m1'),connection_id('k1','m2'))
  self.assertNotEqual(connection_id('k1','m1'),connection_id('k2','m1'))
 def test_explicit_check(self):
  c=Mock();c.models.generate_content.return_value=Mock(text='Ready')
  self.assertTrue(verify_connection(c,'model'));c.models.generate_content.assert_called_once()
 @patch.dict(os.environ,{'GEMINI_API_KEY':''})
 def test_connect_button(self):
  with patch('assistant.create_client',return_value=Mock()),patch('connection.verify_connection',return_value=True) as verify:
   a=AppTest.from_file(str(ROOT/'app.py')).run();self.assertFalse(a.exception)
   verify.assert_not_called()
   a.sidebar.text_input[0].set_value('test-only')
   next(b for b in a.sidebar.button if b.label=='Connect Gemini').click().run()
   self.assertFalse(a.exception);verify.assert_called_once()
   self.assertTrue(a.session_state.verified_connection);self.assertEqual(a.session_state.messages,[])
 def test_svg_favicon(self):
  from streamlit.commands.page_config import _get_favicon_string
  self.assertTrue(_get_favicon_string(str(ROOT/'assets/jlu_icon.svg')).startswith('data:image/svg+xml;base64,'))
  svg=(ROOT/'assets/jlu_icon.svg').read_text()
  self.assertIn('clip-path="url(#circle)"',svg);self.assertIn('data:image/png;base64,',svg)
class CloudConfigurationTests(unittest.TestCase):
 @patch.dict(os.environ,{'GEMINI_API_KEY':'','SHOW_API_SETTINGS':''})
 def test_public_mode_hides_api_controls(self):
  a=AppTest.from_file(str(ROOT/'app.py'))
  a.secrets['GEMINI_API_KEY']='cloud-test-key'
  a.secrets['SHOW_API_SETTINGS']='false'
  a.secrets['GEMINI_MODEL']='test-model'
  a.run()
  self.assertFalse(a.exception)
  self.assertFalse(any(x.label=='Google AI Studio API key' for x in a.sidebar.text_input))
  a.chat_input[0].set_value('B.Tech CSE fees').run()
  self.assertIn('150,000',a.session_state.messages[-1]['content'])
  self.assertNotIn('cloud-test-key',a.session_state.messages[-1]['content'])
 @patch.dict(os.environ,{'FAST_TEST_SETTING':'environment-value'})
 def test_environment_precedence(self):
  from connection import get_setting
  self.assertEqual(get_setting('FAST_TEST_SETTING'),'environment-value')
 @patch.dict(os.environ,{'GEMINI_API_KEY':''})
 def test_cloud_secret_read(self):
  from connection import get_setting
  with patch('connection.st.secrets',{'GEMINI_API_KEY':'test-cloud-value'}):
   self.assertEqual(get_setting('GEMINI_API_KEY'),'test-cloud-value')

if __name__=='__main__':unittest.main()
