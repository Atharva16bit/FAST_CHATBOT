# FAST_CHATBOT

An informational chatbot for prospective students, parents and limited current-student enquiries about the Faculty of Science & Technology at Jagran Lakecity University.

**Start with [START_HERE.md](START_HERE.md)** for installing this complete build, updating the existing Git repository and deploying it.

## Stack and design

- Python and Streamlit for the application and chat interface.
- CSS for the responsive presentation; original JLU branding assets included.
- JSONL knowledge records prepared from the supplied spreadsheets and final faculty information.
- Rule-based topic routing, program aliases and a small custom BM25 index.
- Direct dataset answers for exact facts such as fees and faculty emails.
- Optional Google Gemini explanations using selected records, through the official Google GenAI SDK.
- GitHub for source control and Streamlit Community Cloud for hosting.

No model is trained or fine-tuned here. There is no embedding service, vector database, live seat database or student ERP account integration.

## Main files

| File | Responsibility |
| --- | --- |
| `app.py` | UI, question queue, conversation state and response orchestration |
| `retrieval.py` | Knowledge loading, aliases, topic rules, BM25 retrieval and factual answers |
| `assistant.py` | Gemini request, streaming and readable API failure messages |
| `connection.py` | Environment/secrets configuration and explicit API connection checks |
| `presentation.py` | Answer cleanup and fee breakdown display |
| `guidance.py` | Topic suggestions and external-link validation |
| `ui_feedback.py` | Loading acknowledgement and trusted scroll-helper integration |
| `static/chat_scroll.js` | Follow the latest turn, with manual-scroll cancellation |
| `style.css` | Layout, native widget styling and mobile-safe composer |
| `tests/` | Automated local regressions; AI calls are mocked |
| `evaluation/` | Additional routing regression cases |
| `tools/verify_browser.py` | Optional Playwright checks for desktop and mobile viewports |

## Run locally

Use Python 3.12. In PowerShell inside this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Copy `.env.example` only for a fresh installation. Preserve an existing `.env` containing your key. Edit the placeholder privately; never commit a real key. A key is optional for direct dataset answers.

## Behaviour

- General topics recognise common short phrases and useful aliases.
- Program lists include the complete connected listings; general faculty requests include all 14 supplied faculty entries in the requested order.
- Fees show annual components and total, with separate admission/caution charges and hostel/mess exclusions.
- Documents and scholarships offer relevant follow-up choices.
- Ambiguous course or score questions ask for clarification.
- Missing personal marks, results, CGPA and attendance are directed to the student ERP.
- Missing/unrelated questions offer supported topics and external university links.
- Loading dots appear before processing; very fast replies use a short 350 ms acknowledgement window.
- Recent messages render by default; earlier retained messages can be expanded.
- API failures preserve a factual dataset fallback; Retry replaces the fallback exchange.

## Validation

```powershell
python -m unittest discover -s tests -q
python evaluate.py
```

The final audit includes 60 automated tests, a 100-phrase topic matrix within those tests, the original 47-question regression set and real headless Chromium checks at desktop and mobile viewport sizes. See [docs/FINAL_AUDIT.md](docs/FINAL_AUDIT.md).

Optional browser checks require development tools separately:

```powershell
python -m pip install playwright
python -m playwright install chromium
python tools/verify_browser.py --start-server
```

Playwright is not a runtime dependency of the deployed app.

## Data and scope

The supplied information is for 2026–27. Runtime records retain evidence status and source references. Faculty entries and general subject allocations reflect the project owner's final supplied table. Other supplied claims have not all been independently verified. General subject allocations are not a live timetable.

The chatbot cannot access personal applications, results, attendance, current seat availability or student accounts. Historical admission dates do not establish current admission availability. Refund and other incomplete policies retain explicit limitations. Do not describe the project as an official university service or claim zero hallucinations.

The website and ERP buttons open external sites; they do not perform a live website search or read private records. Browser tests use local data without a real Gemini key; generated-answer accuracy and production performance are not certified by passing regression tests.
