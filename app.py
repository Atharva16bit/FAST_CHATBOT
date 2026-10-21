"""FAST_CHATBOT UI. Start: python -m streamlit run app.py"""
import os
import time
import base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from assistant import create_client, stream_answer, friendly_error
from retrieval import KnowledgeBase
from presentation import clean_answer, fee_answer
from connection import configured_key, connection_id, verify_connection, get_setting

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
st.set_page_config(page_title='FAST_CHATBOT | JLU',
    page_icon=str(ROOT / 'assets/jlu_icon.svg'), layout='centered')
st.markdown(f'<style>{(ROOT / "style.css").read_text()}</style>', unsafe_allow_html=True)


@st.cache_resource(show_spinner=False)
def load_knowledge(version):
    # File timestamps invalidate this cache after a local data update.
    return KnowledgeBase(ROOT / 'data')


try:
    version = tuple((ROOT / 'data' / name).stat().st_mtime_ns for name in
        ['knowledge.jsonl', 'intent_examples.jsonl', 'faculty_directory.jsonl'])
    kb = load_knowledge(version)
except (OSError, ValueError, KeyError):
    st.error('The knowledge files are missing or invalid. Restore the data folder from the project ZIP and restart.')
    st.stop()

for field, default in [('messages', []), ('programs', []), ('client', None), ('last_intent','')]:
    if field not in st.session_state:
        st.session_state[field] = default


@st.cache_data(show_spinner=False)
def asset_uri(name):
    return 'data:image/svg+xml;base64,' + base64.b64encode((ROOT/'assets'/name).read_bytes()).decode()


def session_client(key):
    if st.session_state.get('_client_key') != key or st.session_state.client is None:
        if st.session_state.client is not None:
            st.session_state.client.close()
        st.session_state.client = create_client(key)
        st.session_state._client_key = key
    return st.session_state.client


def save_turn(question, answer, result, elapsed, mode, warning=''):
    st.session_state.messages.extend([
        {'role':'user', 'content':question},
        {'role':'assistant', 'content':clean_answer(answer), 'sources':result.records,
         'seconds':elapsed, 'retrieval_ms':result.retrieval_ms, 'mode':mode,
         'warning':warning}])
    # Keep at most 30 completed exchanges per session.
    st.session_state.messages = st.session_state.messages[-60:]
    if result.programs:
        st.session_state.programs = result.programs
    elif result.intent not in {'thanks','greeting'}:
        st.session_state.programs = []
    st.session_state.last_intent = result.intent


with st.sidebar:
    st.image(str(ROOT / 'assets/jlu_wordmark.svg'), width='stretch')
    st.markdown('<div class="sidebar-label">FACULTY OF SCIENCE & TECHNOLOGY</div><p class="sidebar-intro">Your admission information desk.</p>', unsafe_allow_html=True)
    if st.button('＋ New conversation', use_container_width=True, type='primary'):
        st.session_state.messages = []
        st.session_state.programs = []
        st.session_state.last_intent = ''
        st.session_state.pop('retry_prompt', None)
        st.session_state.pop('show_fees', None)
        st.rerun()
    st.divider()
    show_settings = get_setting('SHOW_API_SETTINGS', 'true').lower() == 'true'
    server_key = get_setting('GEMINI_API_KEY', '')
    server_model = get_setting('GEMINI_MODEL', 'gemini-3.5-flash-lite')
    key_input, connect, model, use_ai, detailed = '', False, server_model, True, False
    if show_settings:
        st.markdown('**Gemini connection**')
        with st.expander('API settings', expanded=False):
            with st.form('api_connection'):
                key_input = st.text_input('Google AI Studio API key', type='password', key='api_key_input',
                    help='Keep your key here or in your local .env file. Never paste it into chat.')
                model = st.text_input('Model ID', value=server_model)
                connect = st.form_submit_button('Connect Gemini', use_container_width=True)
            st.caption('Connect sends a small test request to Google and may use API quota. The entered key stays in this session.')
            use_ai = st.toggle('Use Gemini for explanations', value=True)
            detailed = st.toggle('Detailed AI answers', value=False)
    key = configured_key(key_input, server_key)
    model = model.strip()
    if connect:
        if not key or not model:
            st.warning('Enter your API key and an accessible model ID first.')
        else:
            try:
                with st.spinner('Checking Gemini…'):
                    verify_connection(session_client(key), model)
                st.session_state.verified_connection = connection_id(key, model)
                st.success('Gemini connected successfully.')
            except Exception as error:
                st.session_state.pop('verified_connection', None)
                st.error(friendly_error(error))
    if show_settings:
        if key and st.session_state.get('verified_connection')==connection_id(key,model):
            st.caption('● Connected · API check passed')
        elif key:
            st.caption('○ Key configured · connection not tested')
        else:
            st.caption('○ Add your key in API settings')
        st.caption('Dataset answers are available with or without Gemini.')
    else:
        st.caption('AI explanations available' if key else 'Dataset information available')
    st.divider()
    if st.button('View course fees', use_container_width=True):
        st.session_state.show_fees = not st.session_state.get('show_fees', False)
    st.markdown('**Ask about FAST**')
    st.caption('Programs and duration\n\nFees and scholarships\n\nAdmissions and documents\n\nHostel and faculty')
    if st.session_state.messages:
        text = '\n\n'.join(f"{m['role'].upper()}: {m['content']}" +
            ('\nSources: ' + '; '.join(r['source_refs'] for r in m.get('sources', [])) if m.get('sources') else '')
            for m in st.session_state.messages)
        st.download_button('Download conversation', text, 'FAST_CHATBOT-chat.txt', 'text/plain', use_container_width=True)
    with st.expander('About this assistant'):
        st.caption('Student project using supplied 2026–27 information. Confirm current details with the university.')
        st.caption('No live seats or personal application access. With Gemini enabled, your question, up to two recent questions and selected records are sent to Google.')

st.markdown(f'<div class="product-header"><img src="{asset_uri("jlu_icon.svg")}" alt="Jagran Lakecity University icon"><div><h1>FAST_CHATBOT</h1><p>Faculty of Science &amp; Technology · Jagran Lakecity University</p></div></div>', unsafe_allow_html=True)

prompt = None
if not st.session_state.messages:
    st.markdown('<section class="welcome"><div class="eyebrow">A clearer start to your next chapter</div><h2>Your questions.<br>Your next step.</h2><p>Explore programs, understand fees, and find the information you need before applying to FAST.</p></section>', unsafe_allow_html=True)
    options = [('Explore programs','Which programs are listed under FAST?'),
               ('Understand fees',None),
               ('Admission steps','What application steps does the supplied FAQ describe?'),
               ('Faculty directory','List the faculty directory.')]
    cols = st.columns(2)
    for i,(label,question) in enumerate(options):
        if cols[i % 2].button(label, use_container_width=True):
            if question is None:
                st.session_state.show_fees = True
            else:
                prompt = question
    st.markdown('<div class="scope-note">Student project · Based on supplied 2026–27 information.<br>Confirm current fees, dates and availability with the university.</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message['role'], avatar=str(ROOT / 'assets/jlu_icon.svg') if message['role']=='assistant' else None):
        st.markdown(clean_answer(message['content']))
        if message['role']=='assistant':
            if message.get('warning'):
                st.warning(message['warning'])

# Course choices also appear when a typed fee question needs a program.
needs_course = (st.session_state.last_intent in {'program_fee', 'fee_breakdown'}
                and not st.session_state.programs)
if st.session_state.get('show_fees', False) or needs_course:
    st.markdown('### Choose a course')
    st.caption('Academic fees · 2026–27')
    courses = list(dict.fromkeys(r['entity'] for r in kb.by_topic['program_fee']))
    course_columns = st.columns(2)
    for index, course in enumerate(courses):
        if course_columns[index % 2].button(course, key=f'fee_course_{index}',
                                             use_container_width=True):
            prompt = f'What is the annual fee breakdown for {course} for 2026-27?'
            st.session_state.show_fees = False


if st.session_state.get('retry_prompt'):
    if st.button('Retry last AI explanation', disabled=not key or not model):
        prompt = st.session_state.retry_prompt
        # Replace the fallback exchange, rather than duplicating it.
        if len(st.session_state.messages)>=2 and st.session_state.messages[-2]['content']==prompt:
            st.session_state.messages = st.session_state.messages[:-2]

entered = st.chat_input('Ask FAST a question…', max_chars=4000)
if entered:
    prompt = entered
if prompt:
    st.session_state.pop('retry_prompt', None)
    with st.chat_message('user'):
        st.markdown(prompt)
    started = time.perf_counter()
    result = kb.retrieve(prompt, st.session_state.programs, previous_intent=st.session_state.last_intent)
    warning = ''
    with st.chat_message('assistant', avatar=str(ROOT / 'assets/jlu_icon.svg')):
        if result.direct_answer:
            answer = fee_answer(result) or clean_answer(result.direct_answer)
            mode = 'Dataset answer' if result.records else 'FAST guidance'
            st.markdown(answer)
        elif key and model and use_ai:
            placeholder = st.empty()
            answer = ''
            try:
                client = session_client(key)
                recent = [m['content'] for m in st.session_state.messages if m['role']=='user'][-2:]
                with st.spinner('Preparing an answer from the retrieved records…'):
                    for piece in stream_answer(client, model, prompt, result.records, recent, detailed):
                        answer += piece
                        placeholder.markdown(clean_answer(answer) + ' ▌')
                if not answer.strip():
                    raise ValueError('No text response')
                answer = clean_answer(answer)
                placeholder.markdown(answer)
                st.session_state.verified_connection = connection_id(key, model)
                mode = 'Gemini · retrieved evidence'
            except Exception as error:
                # Discard incomplete AI prose; preserve a useful factual fallback.
                answer = fee_answer(result) or clean_answer(kb.format_answer(result.intent, result.records, prompt))
                placeholder.markdown(answer)
                warning = friendly_error(error)
                st.session_state.retry_prompt = prompt
                mode = 'Dataset fallback'
        else:
            answer = fee_answer(result) or clean_answer(kb.format_answer(result.intent, result.records, prompt))
            mode = 'Dataset answer'
            st.markdown(answer)
        save_turn(prompt, answer, result, time.perf_counter()-started, mode, warning)
        st.rerun()
