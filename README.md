# FAST_CHATBOT — RAG edition
Faculty of Science & Technology, Jagran Lakecity University

An admission information assistant for prospective students and parents, with
limited current-student information. The original supplied JLU logos and
circular favicon are preserved. This is a student assignment, not an official
university service.

## 1. Start in VS Code on Windows
Extract the ZIP manually. Open the FAST_CHATBOT folder containing app.py and
requirements.txt. Open Terminal → New Terminal → PowerShell.
Python 3.11 or newer is recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open http://localhost:8501. Dataset answers work immediately without a key.
For Gemini explanations, expand API settings and enter your Google AI Studio API
key, then click Connect Gemini to test it. The key is not bundled in this project. Press Ctrl+C to stop the server.
On later starts, run only the third command from the same folder.

Optional persistent local configuration:

```powershell
Copy-Item .env.example .env
```
Edit .env with your own key and model ID, save it, then restart the app.
Do not commit or share .env. If moving a key from the earlier project, copy only
your own .env into this new folder. Do not copy an old .venv.
If Google reports model unavailability, enter a model ID accessible to your
account in API settings. Do not assume that any particular model is free or that
access is guaranteed.

## 2. What changed from the original
- General academic tutoring is replaced with FAST admission/university information.
- 136 permitted evidence/coverage records and 161 development intent examples
  are connected. 47 evaluation questions are stored separately and are never
  loaded by the application search index.
- Program aliases and bounded program context support follow-ups such as
  B.Tech CSE → What about its fees? Explicitly named new programs override old ones.
- Missing specializations prompt clarification. BCA does not silently mean BCA General.
- Exact monetary data, faculty contacts, scholarship bands and historical dates
  use direct lookup replies. Descriptive questions can use one Gemini call
  supplied with only selected evidence and up to two recent user questions.
- Sources are generated from retrieved records by the app, not invented by the model.
- No-key dataset mode, retry, transcript download and useful API-failure fallback
  are included. Incomplete AI prose is discarded before a fallback is saved.
- Session history is limited to 30 completed exchanges. New conversation clears
  the conversation, active program and last intent.

## 3. Architecture you can explain
Question → normalize words and aliases → identify intent → resolve program
and filters → retrieve relevant records → exact reply OR one grounded Gemini
request → display reply and supporting sources.

- app.py: Streamlit widgets, session state, cached data loading and source display.
- retrieval.py: transparent routing rules, entity filters, BM25 word ranking,
  missing-data handling and exact answers. Standard Python library only.
- assistant.py: Gemini client, evidence-only prompt, streaming and safe errors.
- style.css / .streamlit/config.toml: original teal design and responsive spacing.
- data/knowledge.jsonl: the factual/coverage corpus used at runtime.
- data/intent_examples.jsonl: development questions for routing fallback only.
- data/faculty_directory.jsonl: final user-supplied faculty names and email status.
- evaluation/questions.jsonl: starter regression questions, excluded from runtime.
- evaluate.py: reproducible local routing and retrieval timing report.
- tests/test_app.py: retrieval, interface and mocked SDK behavior checks.
- docs/: architecture explanation and validation report.

RAG means retrieving outside evidence before asking the language model to answer.
This version uses lexical BM25 retrieval, not neural embedding/vector retrieval.
Exact structured questions bypass generation deliberately. No LangChain, FAISS,
Chroma, embedding API, database service or model download is required. For this
small dataset that keeps startup, installation and the explanation simple.

## 4. Speed choices
The JSON and search index are cached once per file version using cache_resource.
The current file's modification timestamp invalidates the cache after updates.
Social replies and missing-information replies do not call Google. Exact facts
also avoid model latency. Each ordinary descriptive request uses up to six
records; complete directory/program overview lists and simple multi-topic direct
answers can show more records without an LLM call. Gemini uses a per-session
reused client and one HTTP attempt with a 30-second timeout. Streaming improves
perceived waiting time, not the model's total generation time.

Actual end-to-end latency depends on the model, quota, network, prompt and
answer length. See docs/validation.json for this machine's local measurements.
Those timings exclude Google, Streamlit rendering and concurrent-user load.

## 5. Data boundaries
83 records are reported from the supplied workbook and are not independently
verified, 38 faculty/allocation records are user_confirmed, 2 are historical
dates, and 13 are project-authored coverage limitations. 161 blocked records
from preparation are not included in the runtime knowledge file.
The faculty table supplies general subject allocations, not a live timetable.

All 14 faculty email addresses are supplied. The three corrected contacts are:
- F010 Shivangee Nagar: shivangee.nagar@jlu.edu.in
- F011 Divya Jain: divya.jain@jlu.edu.in
- F013 Reshma Chavan: reshma.chavan@jlu.edu.in
They are user-confirmed contacts; delivery has not been tested.
Directory order follows the project owner's requested sequence: HOD, Vandana,
Ravi, Shweta, Vishali, Anjali Nighoskar, Rudresh, Ashish, Rahul, Shivangee, Divya,
followed by Anjali Thakur, Reshma Chavan and Sukanta Kundu.
Vishali Sharma and vaishali.sharma@jlu.edu.in are preserved exactly as supplied.
Sukanta Kundu's Yahoo address is retained as explicitly supplied.

The supplied 31 August 2026 deadline is historical. The app does not infer
current admission status or live seat availability. Academic fees and hostel
charges retain their year and payment units. Admission and caution charges
remain separate from the listed academic annual total. No official full-degree,
first-year payable or refund calculation is offered. Refund boundary issues,
approved course credits/semester allocations, official placement outcomes,
mess fees and other unconnected information receive explicit limitations.

Source labels reference the supplied workbook and final user table. The app did
not inspect the named PDFs/screenshots, browse the university, access accounts,
or independently verify those claims. Prompt safeguards cannot guarantee that
all generated text is correct. Check official sources before relying on it.

## 6. Test and demo

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluate.py
```
34 automated checks cover aliases, fee components, ambiguous BCA, follow-ups,
new program/year boundaries, emails, refund/live-data limitations, room units,
scholarship filtering, multi-topic replies, dataset filtering, evaluation
separation, SDK payloads, errors, interface flow and mocked streaming/fallback.

The 47-question file was used to debug this implementation. Its routing match
count is a regression check, NOT an unbiased held-out accuracy estimate.
It does not measure generated-answer factual accuracy. Add new unseen questions
before claiming general accuracy. Model access, quota, actual Google streaming,
first-token time and answer quality need a live test with your key.
The Streamlit server health check and AppTest flow checks passed. A full
browser screenshot/mobile/screen-reader audit could not be run in this build
environment because a browser executable was unavailable.

Try these demo prompts:
1. Which programs are listed under FAST?
2. What is the duration of B.Tech CSE?
3. What about its fees?
4. And MCA?
5. Which documents are listed for UG applicants?
6. How do I apply? (uses Gemini if a key is configured)
7. Who teaches DBMS?
8. Shivangee Nagar email
9. Double occupancy AC hostel charge
10. Are admissions open now?
11. Calculate my refund exactly 15 days before the deadline.
12. Write a Python sorting program. (redirects to FAST information)

## 7. Editing the dataset later
Runtime reads the files in data/. Edit the corresponding JSONL records when
updating information. Earlier spreadsheet source copies are not bundled in this
runtime package; they are not loaded by the app.
Keep record_id stable and evidence states accurate. If changing
a faculty contact, update both its knowledge.jsonl answer and the corresponding
faculty_directory.jsonl entry. Never copy unreviewed records into runtime simply
to make the bot answer more questions. Restart or let the file-version cache
reload after an update. Re-run tests and the evaluator.

This is a single-server assignment app: no login, persistent chat database,
private student information, live university integration or account actions.


## UI update
The application now uses a navy sidebar, warm-white conversation area and teal
controls. The university wordmark uses an SVG viewport around the unchanged
supplied PNG, removing exterior padding and the detached tagline. The favicon,
header icon and chat avatar use an SVG circular clip around the unchanged
supplied icon; transparent corners replace the previous white corners.
The message composer has a defined border, focus ring and integrated send
control. Response timings are under Response details, rather than always visible.
Sources remain available separately. Mobile spacing is handled in style.css.

### Connect your Google AI Studio key
1. Open API settings in the sidebar.
2. Enter your own API key and an accessible model ID.
3. Click Connect Gemini. This sends one small test request to Google and may
   consume quota. No check runs automatically on page load.
4. Wait for Connected / API check passed, then ask How do I apply?
The manually entered key remains in the current server session. For your own
persistent local setup, use .env. A placeholder in .env.example is not treated
as a configured key. Changing the key or model invalidates the connection badge.
Exact fact lookups remain local, even when Gemini is connected.

API checks are mocked in the automated suite. A real key was not supplied in
this build and no live connection is claimed. Visual browser screenshots could
not be obtained because a browser executable could not be installed in this
environment. The updated Streamlit controls and SVG paths passed AppTest checks.

## Hosting preparation
Read DEPLOYMENT.md for the browser-based Community Cloud setup. This build adds
managed st.secrets fallback and SHOW_API_SETTINGS=false visitor mode. A repository
and a successful hosting/account setup are still required; no live URL is claimed.
