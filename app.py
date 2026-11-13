
"""FAST_CHATBOT — JLU Faculty of Science & Technology assistant."""

import base64
import logging
import os
import re
from html import escape
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from assistant import create_client, friendly_error, stream_answer
from presentation import display_answer
from retrieval import KnowledgeBase, normalize


# ============================================================
# 1. CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

ICON = ROOT / "assets" / "jlu_icon.png"
WORDMARK = ROOT / "assets" / "jlu_wordmark_reference.png"
FAVICON = ROOT / "assets" / "favicon.ico"
VOICE_JS = ROOT / "voice_component" / "inline_mic.js"
CSS = ROOT / "style.css"

LOGGER = logging.getLogger(__name__)

st.set_page_config(
    page_title="FAST_CHATBOT | JLU",
    page_icon=str(FAVICON) if FAVICON.is_file() else "💬",
    layout="centered",
    initial_sidebar_state="expanded",
)

if CSS.is_file():
    st.markdown(
        f"<style>{CSS.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )


# ============================================================
# 2. KNOWLEDGE BASE
# ============================================================

def image_uri(path: Path) -> str:
    """Convert a local PNG file into a browser data URI."""

    if not path.is_file():
        return ""

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode("ascii")

    return f"data:image/png;base64,{encoded}"


@st.cache_resource(show_spinner="Loading FAST knowledge base…")
def load_knowledge_base(version):
    return KnowledgeBase(ROOT / "data")


try:
    dependency_files = [
        ROOT / "data" / "knowledge.jsonl",
        ROOT / "data" / "intent_examples.jsonl",
        ROOT / "data" / "faculty_directory.jsonl",
        ROOT / "retrieval.py",
        ROOT / "semantic_retrieval.py",
    ]

    version = tuple(
        file.stat().st_mtime_ns
        for file in dependency_files
    )

    kb = load_knowledge_base(version)

except (OSError, ValueError, KeyError) as error:
    st.error(f"Could not load FAST knowledge base: {error}")
    st.stop()


# ============================================================
# 3. SESSION STATE
# ============================================================

DEFAULT_STATE = {
    "messages": [],
    "programs": [],
    "last_intent": "",
    "pending_family": "",
    "queued_prompt": None,
    "voice_last_event": None,
}

for name, initial in DEFAULT_STATE.items():
    if name not in st.session_state:
        st.session_state[name] = (
            initial.copy()
            if isinstance(initial, list)
            else initial
        )


def reset_chat():
    """Reset messages, context and chat composer."""

    for name, initial in DEFAULT_STATE.items():
        st.session_state[name] = (
            initial.copy()
            if isinstance(initial, list)
            else initial
        )

    st.session_state["fast_chat_prompt"] = ""


def queue_prompt(text):
    """Receive a question from sidebar or quick-action button."""

    if (
        isinstance(text, str)
        and text.strip()
        and not st.session_state.queued_prompt
    ):
        st.session_state.queued_prompt = text.strip()


def validate_voice_event(payload):
    """Validate a transcript received from the JavaScript microphone."""

    if not isinstance(payload, dict):
        return None

    event_id = payload.get("id")
    transcript = payload.get("transcript")

    if not isinstance(event_id, str):
        return None

    if not 1 <= len(event_id) <= 100:
        return None

    if not isinstance(transcript, str):
        return None

    transcript = " ".join(transcript.split())

    if not 0 < len(transcript) <= 2000:
        return None

    return event_id, transcript


# ============================================================
# 4. GEMINI CONFIGURATION
# ============================================================

def app_setting(name, default=""):
    """Read local environment variables or Streamlit secrets."""

    from_env = os.getenv(name, "").strip()

    if from_env:
        return from_env

    try:
        return str(st.secrets.get(name, default)).strip()

    except (FileNotFoundError, KeyError):
        return default


GEMINI_KEY = app_setting("GEMINI_API_KEY")

GEMINI_MODEL = app_setting(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


# ============================================================
# 5. CHAT MESSAGE RENDERING
# ============================================================

def show_message(message):
    """
    Student: compact content-sized bubble on the RIGHT.
    Assistant: standard evidence-capable message on the LEFT.
    """

    role = message["role"]
    content = str(message["content"])

    if role == "user":

        # Escape HTML so users cannot inject markup or scripts.
        safe_text = escape(
            content,
            quote=True,
        ).replace("\n", "<br>")

        st.markdown(
            f"""
            <div class="fast-user-row">
                <div class="fast-user-bubble">
                    <span class="fast-user-text">{safe_text}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    # Assistant keeps native Streamlit chat formatting.
    with st.chat_message(
        "assistant",
        avatar=(
            str(ICON)
            if ICON.is_file()
            else "💬"
        ),
        width="stretch",
    ):

        st.markdown(content)

        if message.get("sources"):

            with st.expander("Evidence sources"):

                for source in message["sources"]:
                    st.caption(source)


# ============================================================
# 6. SIDEBAR
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
        ("Admissions", "How do I apply for admission?"),
        ("Programs", "Which programs are listed under FAST?"),
        ("Fees", "What are the annual fees for B.Tech CSE?"),
        ("Scholarships", "What academic scholarships are listed?"),
        ("Hostel", "What hostel room charges are listed?"),
        ("Faculty", "List the faculty directory."),
    ]

    for name, question in topics:

        st.button(
            name,
            key=f"topic_{name.lower()}",
            use_container_width=True,
            on_click=queue_prompt,
            args=(question,),
        )

    st.divider()

    # Always-visible voice language choice.
    voice_language = st.radio(
        "Voice recognition language",
        options=["en-IN", "hi-IN"],
        index=0,
        key="voice_language",
        horizontal=True,
        format_func=lambda code: {
            "en-IN": "English",
            "hi-IN": "Hindi",
        }[code],
    )

    st.caption(
        "Use the microphone to fill the chat bar. "
        "Correct the recognized text before sending."
    )

    # Optional Gemini.
    with st.expander(
        "Advanced settings",
        expanded=False,
    ):

        enable_ai = st.toggle(
            "Use Gemini for explanations",
            value=False,
            disabled=not bool(GEMINI_KEY),
            key="enable_gemini",
            help="Requires a configured Gemini API key.",
        )

        st.caption(
            "Semantic retrieval: "
            + (
                "available"
                if kb.semantic_records.ready
                else "BM25 fallback active"
            )
        )

    # Download conversation.
    if st.session_state.messages:

        conversation = "\n\n".join(
            f"{item['role'].upper()}: {item['content']}"
            for item in st.session_state.messages
        )

        st.download_button(
            "Download conversation",
            data=conversation,
            file_name="FAST_CHATBOT-conversation.txt",
            mime="text/plain",
            use_container_width=True,
            key="download_conversation",
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
# 7. HEADER
# ============================================================

icon_url = image_uri(ICON)

icon_html = (
    f'<img alt="JLU emblem" src="{icon_url}">'
    if icon_url
    else ""
)

st.markdown(
    '<header class="jlu-header">'
    + icon_html
    + '<div>'
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
# 8. WELCOME SCREEN
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
        ("Admission steps", "How do I apply for admission?"),
        ("Explore programs", "Which programs are listed under FAST?"),
        ("B.Tech CSE fees", "What are the fees for B.Tech CSE?"),
        ("Faculty directory", "List the faculty directory."),
    ]

    columns = st.columns(2)

    for index, (label, question) in enumerate(suggestions):

        columns[index % 2].button(
            label,
            key=f"quick_{index}",
            use_container_width=True,
            on_click=queue_prompt,
            args=(question,),
        )


# ============================================================
# 9. DISPLAY PREVIOUS CONVERSATION
# ============================================================

for message in st.session_state.messages:
    show_message(message)


# ============================================================
# 10. JAVASCRIPT MICROPHONE
# ============================================================

if VOICE_JS.is_file():

    js_code = VOICE_JS.read_text(encoding="utf-8")

    if not hasattr(st.components, "v2"):

        st.sidebar.warning(
            "Microphone requires Streamlit Components V2."
        )

    elif not re.search(r"\bexport\s+default\b", js_code):

        st.sidebar.warning(
            "Microphone JavaScript needs a default export."
        )

    else:

        microphone = st.components.v2.component(
            "fast_inline_microphone",
            js=js_code,
            isolate_styles=False,
        )

        voice_result = microphone(
            key="fast_mic",
            data={
                "language": voice_language,
            },
            on_voice_change=lambda: None,
        )

        event = validate_voice_event(
            getattr(voice_result, "voice", None)
        )

        if event is not None:

            event_id, recognized_text = event

            if event_id != st.session_state.voice_last_event:

                st.session_state.voice_last_event = event_id

                # Prefill the native chat bar.
                # Voice input does not auto-submit.
                st.session_state[
                    "fast_chat_prompt"
                ] = recognized_text

else:

    st.sidebar.caption(
        "Voice input unavailable; typing still works."
    )


# ============================================================
# 11. NATIVE CHAT INPUT
# ============================================================

prompt = st.chat_input(
    "Ask about admissions, fees, courses or hostel…",
    key="fast_chat_prompt",
    max_chars=2000,
)

question = st.session_state.queued_prompt or prompt


# ============================================================
# 12. PROCESS QUESTION
# ============================================================

if question:

    st.session_state.queued_prompt = None

    # Store user's question.
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    # Display compact user bubble on the RIGHT.
    show_message(
        {
            "role": "user",
            "content": question,
        }
    )

    shown = ""
    references = []

    # Display chatbot answer on the LEFT.
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

            try:

                query = question
                normalized = normalize(question)

                # --------------------------------------------
                # Conversational context
                # --------------------------------------------

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
                        normalized,
                    )
                ):

                    query = (
                        f"{st.session_state.pending_family} "
                        f"{question}"
                    )

                # --------------------------------------------
                # Retrieve relevant knowledge
                # --------------------------------------------

                result = kb.retrieve(
                    query,
                    st.session_state.programs,
                    previous_intent=(
                        st.session_state.last_intent
                    ),
                )

                family = re.search(
                    r"\b(btech|bca|mtech|mca)\b",
                    normalized,
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

                # --------------------------------------------
                # Evidence-based answer
                # --------------------------------------------

                answer = (
                    result.direct_answer
                    or kb.format_answer(
                        result.intent,
                        result.records,
                        query,
                    )
                )

                # --------------------------------------------
                # Optional Gemini explanation
                # --------------------------------------------

                if (
                    enable_ai
                    and GEMINI_KEY
                    and result.records
                    and not result.direct_answer
                ):

                    try:

                        previous_questions = [
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
                                previous_questions,
                            )
                        )

                        if generated.strip():
                            answer = generated

                    except Exception as error:

                        LOGGER.warning(
                            "Gemini explanation failed: %s",
                            error,
                        )

                        st.warning(
                            f"{friendly_error(error)} "
                            "Showing the dataset answer instead."
                        )

                # --------------------------------------------
                # Format response
                # --------------------------------------------

                shown = display_answer(
                    answer,
                    result.intent,
                    result.records,
                )

                references = [
                    (
                        f"{record.get('source_refs', 'Source unspecified')}"
                        f" · {record.get('academic_year', '')}"
                    )
                    for record in result.records
                ]

                st.markdown(shown)

                if references:

                    with st.expander("Evidence sources"):

                        for reference in references:
                            st.caption(reference)

                # --------------------------------------------
                # Update conversation memory
                # --------------------------------------------

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

                LOGGER.exception(
                    "FAST_CHATBOT response generation failed"
                )

                shown = (
                    "I could not retrieve the requested "
                    "information. Please try again or "
                    "consult the official JLU website."
                )

                st.error(shown)

    # Save assistant response for chat history.
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": shown,
            "sources": references,
        }
    )

    st.rerun()
