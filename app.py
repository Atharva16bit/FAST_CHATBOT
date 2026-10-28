"""FAST_CHATBOT branded Streamlit interface. Run: streamlit run app.py."""
import base64
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from assistant import create_client, friendly_error, stream_answer
from presentation import display_answer
from retrieval import KnowledgeBase, normalize

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
ICON = ROOT / 'assets' / 'jlu_icon.png'
WORDMARK = ROOT / 'assets' / 'jlu_wordmark_reference.png'

st.set_page_config(page_title='FAST_CHATBOT | JLU', page_icon=str(ROOT / 'assets' / 'favicon.ico'), layout='centered', initial_sidebar_state='expanded')
st.markdown('<style>' + (ROOT / 'style.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)


def image_uri(path):
    return 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode('ascii')


@st.cache_resource(show_spinner='Loading FAST knowledge base…')
def load_kb(version):
    return KnowledgeBase(ROOT / 'data')


try:
    files = [ROOT/'data'/n for n in ('knowledge.jsonl', 'intent_examples.jsonl', 'faculty_directory.jsonl')]
    files.extend((ROOT/'retrieval.py', ROOT/'semantic_retrieval.py'))
    kb = load_kb(tuple(f.stat().st_mtime_ns for f in files))
except (OSError, ValueError, KeyError) as exc:
    st.error(f'Knowledge base could not load: {exc}')
    st.stop()

for k, initial in {'messages': [], 'programs': [], 'last_intent': '', 'pending_family': '', 'queued_prompt': None}.items():
    if k not in st.session_state:
        st.session_state[k] = initial


def reset_chat():
    for k, value in {'messages': [], 'programs': [], 'last_intent': '', 'pending_family': '', 'queued_prompt': None}.items():
        st.session_state[k] = value


def queue_prompt(value):
    if not st.session_state.queued_prompt:
        st.session_state.queued_prompt = value


def app_setting(name, default=''):
    """Read environment first, then Streamlit Cloud secrets; never expose values."""
    value = os.getenv(name, '').strip()
    if value:
        return value
    try:
        return str(st.secrets.get(name, default)).strip()
    except (FileNotFoundError, KeyError):
        return default


KEY = app_setting('GEMINI_API_KEY')
MODEL = app_setting('GEMINI_MODEL', 'gemini-2.5-flash')

with st.sidebar:
    st.image(str(WORDMARK), use_container_width=True)
    st.markdown('<div class="jlu-sidebar-label">FACULTY OF SCIENCE & TECHNOLOGY</div><div class="jlu-sidebar-desc">Your admission information desk.</div>', unsafe_allow_html=True)
    st.button('＋ New conversation', type='primary', use_container_width=True, on_click=reset_chat)
    st.divider()
    st.markdown('**Explore topics**')
    sidebar_topics = [
        ('Admissions', 'How do I apply for admission?'),
        ('Programs', 'Which programs are listed under FAST?'),
        ('Fees', 'What are the annual fees for B.Tech CSE?'),
        ('Scholarships', 'What academic scholarships are listed?'),
        ('Hostel', 'What hostel room charges are listed?'),
        ('Faculty', 'List the faculty directory.'),
    ]
    for name, question in sidebar_topics:
        st.button(name, key='topic_'+name, use_container_width=True, on_click=queue_prompt, args=(question,))
    st.divider()
    with st.expander('Advanced settings', expanded=False):
        enable_ai = st.toggle('Use Gemini for explanations', value=False, disabled=not bool(KEY), help='Requires GEMINI_API_KEY in .env or deployment secrets.')
        st.caption('Semantic retrieval: ' + ('available' if kb.semantic_records.ready else 'BM25 fallback active'))
        if not kb.semantic_records.ready:
            st.caption('Embedding model was not available in this environment.')
        st.caption('Gemini requires a configured API key. Never paste credentials into chat.')
    if st.session_state.messages:
        transcript = '\n\n'.join(f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages)
        st.download_button('Download conversation', transcript, file_name='FAST_CHATBOT-conversation.txt', mime='text/plain', use_container_width=True)
    st.caption('Student project · Not an official JLU service')
    st.link_button('Official university website', 'https://www.jlu.edu.in/', use_container_width=True)

st.markdown(f'<header class="jlu-header"><img alt="JLU emblem" src="{image_uri(ICON)}"><div><h1>FAST_CHATBOT</h1><p>Faculty of Science & Technology · Jagran Lakecity University</p></div></header>', unsafe_allow_html=True)
st.markdown('<div class="jlu-notice">Based on supplied 2026–27 university records. Confirm current fees, admission dates and availability with JLU. No live seats or personal accounts are connected.</div>', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown('<section class="jlu-hero"><h2>How can I help you today?</h2><p>Explore programs, check listed fees, understand admission steps, or find faculty information.</p></section>', unsafe_allow_html=True)
    options = [('Admission steps', 'How do I apply for admission?'), ('Explore programs', 'Which programs are listed under FAST?'), ('B.Tech CSE fees', 'What are the fees for B.Tech CSE?'), ('Faculty directory', 'List the faculty directory.')]
    cols = st.columns(2)
    for i,(name,q) in enumerate(options):
        cols[i%2].button(name, key='quick_'+str(i), on_click=queue_prompt, args=(q,), use_container_width=True)

for i,message in enumerate(st.session_state.messages):
    avatar = str(ICON) if message['role'] == 'assistant' else '👤'
    with st.chat_message(message['role'], avatar=avatar):
        st.markdown(message['content'])
        if message['role']=='assistant' and message.get('sources'):
            with st.expander('Evidence sources'):
                for ref in message['sources']:
                    st.caption(ref)

prompt = st.chat_input('Ask about admissions, fees, courses or hostel…', max_chars=2000)
question = st.session_state.queued_prompt or prompt
if question:
    st.session_state.queued_prompt = None
    st.session_state.messages.append({'role':'user','content':question})
    with st.chat_message('user', avatar='👤'):
        st.markdown(question)
    with st.chat_message('assistant', avatar=str(ICON)):
        with st.spinner('Checking the FAST knowledge base…'):
            query = question
            norm = normalize(question)
            if (st.session_state.pending_family and st.session_state.last_intent in {'program_fee','fee_breakdown','program_duration'}
                    and re.fullmatch(r'(?:cse|ai|datascience|data science|general|fullstack|cloud)', norm)):
                query = st.session_state.pending_family + ' ' + question
            try:
                result = kb.retrieve(query, st.session_state.programs, previous_intent=st.session_state.last_intent)
                family = re.search(r'\b(btech|bca|mtech|mca)\b', norm)
                st.session_state.pending_family = (family.group(1) if family and result.intent in {'program_fee','fee_breakdown','program_duration'} and not result.records else '')
                answer = result.direct_answer or kb.format_answer(result.intent, result.records, query)
                if enable_ai and KEY and result.records and not result.direct_answer:
                    try:
                        previous = [m['content'] for m in st.session_state.messages if m['role']=='user'][-3:-1]
                        generated = ''.join(stream_answer(create_client(KEY), MODEL, question, result.records, previous))
                        if generated.strip():
                            answer = generated
                    except Exception as error:
                        st.warning(friendly_error(error) + ' Showing the dataset answer instead.')
                shown = display_answer(answer, result.intent, result.records)
                refs = []
                for record in result.records:
                    refs.append(f"{record.get('source_refs','Source unspecified')} · {record.get('academic_year','')}")
                st.markdown(shown)
                if refs:
                    with st.expander('Evidence sources'):
                        for ref in refs:
                            st.caption(ref)
                if result.programs:
                    st.session_state.programs = result.programs
                if result.intent not in ('greeting','thanks'):
                    st.session_state.last_intent = result.intent
            except Exception:
                shown = 'I could not retrieve the requested information. Please try again or consult the official JLU website.'
                refs = []
                st.error(shown)
    st.session_state.messages.append({'role':'assistant','content':shown,'sources':refs})
    st.rerun()
