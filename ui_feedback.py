"""Small, trusted UI helpers for loading feedback and reply scrolling."""
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
# A short visible acknowledgement, not a simulated multi-second search.
MIN_LOADING_SECONDS = 0.35
LOADING_HTML = '''<div class="answer-loading" role="status" aria-live="polite">
<span class="loading-dots" aria-hidden="true"><i></i><i></i><i></i></span>
<span>Finding your answer…</span></div>'''


def scroll_to_latest(sequence, live=False):
    """Follow a new turn; wheel/touch input immediately stops following."""
    phase = 'loading' if live else 'complete'
    # Sequence is internally generated; neither question nor AI output enters JS.
    event = f'{int(sequence)}-{phase}'
    script = (ROOT/'static/chat_scroll.js').read_text(encoding='utf-8')
    st.html(
        f'<div class="chat-end" data-fast-scroll="{event}" data-live="{str(live).lower()}"></div>'
        f'<script>{script}</script>',
        unsafe_allow_javascript=True,
    )
