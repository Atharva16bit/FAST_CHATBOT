"""Explicit local key configuration and a small user-triggered connection test."""
import hashlib
import os
import streamlit as st
from google.genai import types


def get_setting(name, default=''):
    """Environment/.env locally, then managed Streamlit secrets in the cloud."""
    value = os.getenv(name)
    if value is not None and value.strip():
        return value
    try:
        return str(st.secrets.get(name, default))
    except (FileNotFoundError, KeyError, st.errors.StreamlitSecretNotFoundError):
        return default


def configured_key(entered, environment):
    key = (entered or environment or '').strip()
    if key.lower() in {'your_google_ai_studio_api_key_here', 'your_api_key_here', 'replace_me'}:
        return ''
    return key


def connection_id(key, model):
    return hashlib.sha256((key + '\0' + model).encode()).hexdigest()


def verify_connection(client, model):
    # Triggered by the Connect Gemini button, never on page load.
    # This is one small API request and is subject to Google's quota/billing.
    response = client.models.generate_content(
        model=model, contents='Reply with the single word Ready.',
        config=types.GenerateContentConfig(max_output_tokens=128, temperature=0))
    if not response.text or not response.text.strip():
        raise ValueError('Google returned no readable text for the connection check.')
    return True
