
"""FAST_CHATBOT: Streamlit university assistant with browser voice input."""

import base64
import logging
import os
import re
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from assistant import create_client, friendly_error, stream_answer
from presentation import display_answer
from retrieval import KnowledgeBase, normalize

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

ICON = ROOT / "assets/jlu_icon.png"
WORDMARK = ROOT / "assets/jlu_wordmark_reference.png"
FAVICON = ROOT / "assets/favicon.ico"
VOICE_JS = ROOT / "voice_component/inline_mic.js"

st.set_page_config(
    page_title="FAST_CHATBOT | JLU",
    page_icon=str(FAVICON) if FAVICON.is_file() else "💬",
    layout="centered",
    initial_sidebar_state="expanded",
)

css_path = ROOT / "style.css"

if css_path.is_file():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# ============================================================
# UTILITIES
# ============================================================

def image_uri(path: Path) -> str:
    if not path.is_file():
        return ""

    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


@st.cache_resource(show_spinner="Loading FAST knowledge base…")
def load_kb(version):
    return KnowledgeBase(ROOT / "data")


try:
    dependencies = [
        ROOT / "data/knowledge.jsonl",
        ROOT / "data/intent_examples.jsonl",
        ROOT / "data/faculty_directory.jsonl",
        ROOT / "retrieval.py",
        ROOT / "semantic_retrieval.py",
    ]

    kb = load_kb(
        tuple(path.stat().st_mtime_ns for path in dependencies)
    )

except (OSError, ValueError, KeyError) as error:
    st.error(f"Cannot load FAST knowledge base: {error}")
    st.stop()


# ============================================================
# SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "messages": [],
    "programs": [],
    "last_intent": "",
    "pending_family": "",
    "queued_prompt": None,
    "voice_last_event": None,
}

for name, value in DEFAULT_STATE.items():
    if name not in st.session_state:
        st.session_state[name] = (
            value.copy()
            if isinstance(value, list)
            else value
        )


def reset_chat():
    for name, value in DEFAULT_STATE.items():
        st.session_state[name] = (
            value.copy()
            if isinstance(value, list)
            else value
        )


def queue_prompt(text):
    if (
        isinstance(text, str)
        and text.strip()
        and not st.session_state.queued_prompt
    ):
        st.session_state.queued_prompt = text.strip()


def valid_voice_event(payload):
    if not isinstance(payload, dict):
        return None

    event_id = payload.get("id")
    text = payload.get("transcript")

    if not isinstance(event_id, str):
        return None

    if not 1 <= len(event_id) <= 100:
        return None

    if not isinstance(text, str):
        return None

    text = " ".join(text.split())

    if not 0 < len(text) <= 2000:
        return None

    return event_id, text


# ============================================================
# ENVIRONMENT / GEMINI
# ============================================================

def setting(name, default=""):
    from_env = os.getenv(name, "").strip()

    if from_env:
        return from_env

    try:
        return str(st.secrets.get(name, default)).strip()

    except (FileNotFoundError, KeyError):
        return default


GEMINI_KEY = setting("GEMINI_API_KEY")
GEMINI_MODEL = setting(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# ============================================================
# CHAT DISPLAY — USER RIGHT / ASSISTANT LEFT
# ============================================================

def show_message(message):
    is_user = message["role"] == "user"

    alignment = "right" if is_user else "left"

    avatar = (
        "👤"
        if is_user or not ICON.is_file()
        else str(ICON)
    )

    with st.container(horizontal_alignment=alignment):
        with st.chat_message(
            "user" if is_user else "assistant",
            avatar=avatar,
            width="content" if is_user else "stretch",
        ):
            st.markdown(message["content"])

            if not is_user and message.get("sources"):
                with st.expander("Evidence sources"):
                    for source in message["sources"]:
                        st.caption(source)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    if WORDMARK.is_file():
        st.image(
            str(WORDMARK),
            use_container_width=True,
        )

    st.markdown(
        '<div class="jlu-sidebar-label">'
        'FACULTY OF SCIENCE & TECHNOLOGY'
        '</div>'
        '<div class="jlu-sidebar-desc">'
        'Your admission information desk.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.button(
        "＋ New conversation",
        key="sidebar_new_conversation",
        type="primary",
        use_container_width=True,
        on_click=reset_chat,
    )

    st.divider()
    st.markdown("**Explore topics**")

    topics = [
        (
            "Admissions",
            "How do I apply for admission?",
        ),
        (
            "Programs",
            "Which programs are listed under FAST?",
        ),
        (
            "Fees",
            "What are the annual fees for B.Tech CSE?",
        ),
        (
            "Scholarships",
            "What academic scholarships are listed?",
        ),
        (
            "Hostel",
            "What hostel room charges are listed?",
        ),
        (
            "Faculty",
            "List the faculty directory.",
        ),
    ]

    for name, question in topics:
        st.button(
            name,
            key=f"topic_{name}",
            use_container_width=True,
            on_click=queue_prompt,
            args=(question,),
        )

    st.divider()

    voice_language = st.selectbox(
        "Voice recognition language",
        ["en-IN", "hi-IN"],
        key="voice_language",
        format_func=lambda lang: (
            "English (India)"
            if lang == "en-IN"
            else "Hindi (India)"
        ),
    )

    st.caption(
        "Review and edit recognized speech before sending it."
    )

    with st.expander("Advanced settings"):

        enable_ai = st.toggle(
            "Use Gemini for explanations",
            disabled=not bool(GEMINI_KEY),
            help="Requires GEMINI_API_KEY",
        )

        st.caption(
            "Semantic retrieval: "
            + (
                "available"
                if kb.semantic_records.ready
                else "BM25 fallback active"
            )
        )

    if st.session_state.messages:

        conversation = "\n\n".join(
            f"{message['role'].upper()}: "
            f"{message['content']}"
            for message in st.session_state.messages
        )

        st.download_button(
            "Download conversation",
            conversation,
            file_name="FAST_CHATBOT-conversation.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.caption(
        "Student project · Not an official JLU service"
    )

    st.link_button(
        "Official university website",
        "https://www.jlu.edu.in/",
        use_container_width=True,
    )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    f'<header class="jlu-header">'
    f'<img alt="JLU emblem" src="{image_uri(ICON)}">'
    '<div>'
    '<h1>FAST_CHATBOT</h1>'
    '<p>Faculty of Science & Technology'
    ' · Jagran Lakecity University</p>'
    '</div>'
    '</header>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="jlu-notice">'
    'Based on supplied 2026–27 university records. '
    'Confirm current fees, admission dates and '
    'availability with JLU. No live seats or '
    'personal accounts are connected.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# WELCOME SCREEN
# ============================================================

if not st.session_state.messages:

    st.markdown(
        '<section class="jlu-hero">'
        '<h2>How can I help you today?</h2>'
        '<p>Explore programs, listed fees, admission '
        'steps, or faculty information.</p>'
        '</section>',
        unsafe_allow_html=True,
    )

    suggestions = [
        (
            "Admission steps",
            "How do I apply for admission?",
        ),
        (
            "Explore programs",
            "Which programs are listed under FAST?",
        ),
        (
            "B.Tech CSE fees",
            "What are the fees for B.Tech CSE?",
        ),
        (
            "Faculty directory",
            "List the faculty directory.",
        ),
    ]

    cols = st.columns(2)

    for index, (name, question) in enumerate(suggestions):
        cols[index % 2].button(
            name,
            key=f"quick_{index}",
            use_container_width=True,
            on_click=queue_prompt,
            args=(question,),
        )


# ============================================================
# EXISTING CHAT HISTORY
# ============================================================

for message in st.session_state.messages:
    show_message(message)


# ============================================================
# JAVASCRIPT MICROPHONE
# ============================================================

if VOICE_JS.is_file():

    js_code = VOICE_JS.read_text(encoding="utf-8")

    if (
        re.search(r"\bexport\s+default\b", js_code)
        and hasattr(st.components, "v2")
    ):

        voice_component = st.components.v2.component(
            "fast_inline_microphone",
            js=js_code,
            isolate_styles=False,
        )

        voice_result = voice_component(
            key="fast_mic",
            data={"language": voice_language},
            on_voice_change=lambda: None,
        )

        voice_event = valid_voice_event(
            getattr(voice_result, "voice", None)
        )

        if voice_event is not None:

            event_id, transcript = voice_event

            if (
                event_id
                != st.session_state.voice_last_event
            ):

                st.session_state.voice_last_event = event_id

                queue_prompt(transcript)

    else:
        st.sidebar.warning(
            "Voice JavaScript must use Streamlit Components V2."
        )

else:
    st.sidebar.info(
        "Voice component not installed; typed chat is available."
    )


# ============================================================
# CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask about admissions, fees, courses or hostel…",
    max_chars=2000,
)

question = st.session_state.queued_prompt or prompt


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    st.session_state.queued_prompt = None

    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Student message goes RIGHT
    show_message(
        {
            "role": "user",
            "content": question,
        }
    )

    # FAST_CHATBOT answer goes LEFT
    with st.container(horizontal_alignment="left"):

        with st.chat_message(
            "assistant",
            avatar=(
                str(ICON)
                if ICON.is_file()
                else "💬"
            ),
            width="stretch",
        ):

            with st.spinner(
                "Checking the FAST knowledge base…"
            ):

                shown = ""
                refs = []

                try:
                    query = question
                    norm = normalize(question)

                    # Handle short contextual follow-ups
                    if (
                        st.session_state.pending_family
                        and st.session_state.last_intent
                        in {
                            "program_fee",
                            "fee_breakdown",
                            "program_duration",
                        }
                        and re.fullmatch(
                            r"(?:cse|ai|datascience|data science|"
                            r"general|fullstack|cloud)",
                            norm,
                        )
                    ):

                        query = (
                            f"{st.session_state.pending_family} "
                            f"{question}"
                        )

                    result = kb.retrieve(
                        query,
                        st.session_state.programs,
                        previous_intent=(
                            st.session_state.last_intent
                        ),
                    )

                    family = re.search(
                        r"\b(btech|bca|mtech|mca)\b",
                        norm,
                    )

                    st.session_state.pending_family = (
                        family.group(1)
                        if (
                            family
                            and result.intent
                            in {
                                "program_fee",
                                "fee_breakdown",
                                "program_duration",
                            }
                            and not result.records
                        )
                        else ""
                    )

                    answer = (
                        result.direct_answer
                        or kb.format_answer(
                            result.intent,
                            result.records,
                            query,
                        )
                    )

                    # Optional Gemini explanation
                    if (
                        enable_ai
                        and GEMINI_KEY
                        and result.records
                        and not result.direct_answer
                    ):

                        try:

                            previous = [
                                item["content"]
                                for item
                                in st.session_state.messages
                                if item["role"] == "user"
                            ][-3:-1]

                            generated = "".join(
                                stream_answer(
                                    create_client(GEMINI_KEY),
                                    GEMINI_MODEL,
                                    question,
                                    result.records,
                                    previous,
                                )
                            )

                            if generated.strip():
                                answer = generated

                        except Exception as error:

                            st.warning(
                                f"{friendly_error(error)} "
                                "Showing the dataset answer instead."
                            )

                    shown = display_answer(
                        answer,
                        result.intent,
                        result.records,
                    )

                    refs = [
                        f"{record.get('source_refs', 'Source unspecified')}"
                        f" · {record.get('academic_year', '')}"
                        for record in result.records
                    ]

                    st.markdown(shown)

                    if refs:
                        with st.expander("Evidence sources"):
                            for source in refs:
                                st.caption(source)

                    if result.programs:
                        st.session_state.programs = result.programs

                    if result.intent not in (
                        "greeting",
                        "thanks",
                    ):
                        st.session_state.last_intent = (
                            result.intent
                        )

                except Exception:

                    logging.getLogger(__name__).exception(
                        "FAST_CHATBOT response failed"
                    )

                    shown = (
                        "I could not retrieve the requested "
                        "information. Please try again or "
                        "consult the official JLU website."
                    )

                    st.error(shown)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": shown,
            "sources": refs,
        }
    )

    st.rerun()
