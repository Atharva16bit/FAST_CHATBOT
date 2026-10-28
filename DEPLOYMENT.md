# FAST_CHATBOT — Deployment guide

## Recommended hosting: Streamlit Community Cloud

1. Create a clean GitHub repository and put the **contents of this folder** at the repository root. Confirm `app.py`, `data/` and `requirements.txt` are present.
2. Verify `.env`, `.venv`, `.git`, token files, local caches and `secrets.toml` are **not committed**. If a credential was previously published, revoke/rotate it.
3. Run locally with Python 3.12 and `python -m pip install -r requirements.txt` followed by `python -m streamlit run app.py`.
4. Run `python -m pip install -r requirements-dev.txt` and `python -m pytest -q`; then run `python smoke_test.py`.
5. Visit https://share.streamlit.io/ and select **Create app**, the GitHub repository/branch, and `app.py`.
6. In Advanced settings choose **Python 3.12**. In Secrets add `GEMINI_API_KEY = "..."` and optionally `GEMINI_MODEL = "gemini-2.5-flash"` if you want Gemini explanations. No key is necessary for dataset responses.
7. Deploy and test startup and interactions. The first semantic model download requires internet access and may be slow or fail on a restricted platform. Set `FAST_ENABLE_SEMANTIC=0` via environment configuration if memory/build constraints prevent model loading; BM25 remains available. Streamlit secrets can also provide `FAST_ENABLE_SEMANTIC` only if your code explicitly consumes it, so use an environment variable for this setting.

## Release gate
- Confirm all 3 JSONL datasets are present.
- Verify admission questions and paraphrases, B.Tech CSE fee, academic-year restrictions, out-of-scope questions, and multi-turn fee clarification.
- Check desktop/mobile layouts, logo, favicon and chat input focus state.
- Verify Gemini errors don't disrupt dataset-only responses.
- Verify that `.env` and secret keys are absent from GitHub and deployment logs.
- Check that the 2026–27 source data is still applicable; this is a student assignment, not an official JLU service.
- Configure privacy disclosures if hosting publicly: conversations are in Streamlit session memory; with Gemini on, selected evidence and recent questions are sent to Google.

## Operating notes
Community Cloud resource limits may affect model download/startup. Run an actual hosted deployment to validate resource consumption and cold-start behavior. No external monitoring, rate limiting or abuse mitigation is implemented here; these are needed for broader public exposure.
