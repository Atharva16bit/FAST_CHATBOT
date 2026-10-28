# FAST_CHATBOT — Phase 2 clean project

Student-built informational chatbot for FAST, Jagran Lakecity University. **Not an official university service.** Knowledge records are supplied 2026–27 data and require confirmation with the university.

## Folder layout

- `app.py`: Streamlit entry point
- `style.css`, `assets/`: UI and branding (logo images are screenshot-derived references)
- `assistant.py`: optional Gemini explanations and guarded prompts
- `retrieval.py`, `semantic_retrieval.py`: intent matching and hybrid BM25/embedding retrieval
- `presentation.py`: structured fee and response formatting
- `data/`: runtime knowledge, faculty and development routing examples
- `tests/`: development regression tests, not required to serve the app
- `requirements.txt`: runtime dependencies
- `requirements-dev.txt`: runtime + test dependencies

## Local setup

Python 3.11 or 3.12 recommended.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
streamlit run app.py
```

Set `GEMINI_API_KEY` only if Gemini explanations are required. Never commit `.env`. The chatbot can use dataset responses without Gemini. The sentence embedding model downloads on first use; if unavailable, the index falls back to BM25. To force offline BM25 mode, set `FAST_ENABLE_SEMANTIC=0`.

## Regression tests

```powershell
$env:FAST_ENABLE_SEMANTIC='0'
python -m pytest -q
```

## Phase 2 cleanup decisions

Removed from this distribution: `__pycache__`, `.pytest_cache`, redundant intermediate favicon assets and `app_original_requires_assets.py`. These are not loaded by the current `app.py`. Original files were not deleted from your machine. The root project shown in screenshots contains additional `connection.py`, `guidance.py`, `ui_feedback.py`, `evaluation/`, `docs/`, `tools/`, `static/`, and deployment configuration not supplied in this package; **do not delete them from your local project until their imports and references are audited**.

## Production limitations

- The supplied logo is reconstructed from a screenshot; replace with an authorized original SVG/PNG before publishing.
- Offline regression tests validate behavior with semantic retrieval disabled, not live sentence-transformer inference.
- Streamlit browser, mobile-device, Gemini API and deployment testing are not yet completed.
- Current university facts and dates are not independently verified.
- The dependency versions are retained from the working source; reproducible deployment requires environment-specific installation verification.


## Production deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) and run `python smoke_test.py` before deploying. Keep `.env` and Streamlit secrets out of Git.
