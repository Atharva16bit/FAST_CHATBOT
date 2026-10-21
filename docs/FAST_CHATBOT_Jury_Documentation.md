> UI revision: see ../UI_CHANGES.md for the current course-fee selector, removal of technical chat panels, and 38-test result. Earlier UI descriptions below reflect the previous release.

# FAST CHATBOT


Technical documentation and jury presentation guide


Faculty of Science and Technology
Jagran Lakecity University
Prepared for Atharva Patankar
21 October 2026


## Project in one paragraph


We built FAST_CHATBOT to help prospective students and parents find Faculty of Science and Technology information before applying. The application combines a curated local knowledge base, transparent retrieval rules and Google Gemini explanations. Exact facts such as listed fees and faculty contacts use direct data lookups. Descriptive requests can use Gemini with selected supporting records. The interface shows sources and handles missing information explicitly.


| Item | Implemented position |
| --- | --- |

| Interface | Streamlit with a navy sidebar, warm-white conversation area and original JLU branding |

| Knowledge | 136 permitted records and coverage notes; 14 faculty members |

| Routing examples | 161 development questions across 47 intents |

| Validation | 34 automated checks in the deployment-prepared build; 47-question routing regression set |

| Hosting | Prepared for Streamlit Community Cloud; no live deployment URL claimed |

## How to use this guide


Read sections 1 to 13 to understand the engineering. Sections 14 to 16 cover running, hosting and maintenance. Section 17 provides the demonstration sequence. Sections 18 and 19 contain viva answers. Section 20 lists the evidence and official deployment references.


This is a student assignment using supplied information. It does not establish that the university has approved the service or independently verified every underlying claim.


# 1 Problem audience and scope


## The problem we chose


A first-time applicant may need program options, duration, fee components, admission steps, documents and hostel information in one conversation. Parents often need clear costs and conditions. Existing students may ask about faculty or general support. We designed a narrow information assistant around these tasks instead of building a general-purpose study tutor.


| User | Typical task | Design consequence |
| --- | --- | --- |

| Prospective student | Compare listed degrees and understand application steps | Use familiar program names, starter questions and specialization clarification |

| Parent | Separate academic fees from hostel, deposits and other charges | Keep monetary units, academic year and components explicit |

| Current student | Find a faculty contact or general subject allocation | Use the final supplied directory; do not invent a live timetable |

## Functional requirements


- Answer supported questions about programs, fees, admissions, documents, scholarships, hostel, campus and faculty.

- Understand common aliases such as B.Tech CSE and btech computer science and engineering.

- Support a short follow-up such as What about its fees after discussing a named program.

- Show supporting records, provide a new conversation action, retry failed AI explanations and download the conversation.

## Boundaries


The app does not submit applications, process payments, access student accounts, read live seats or decide admission eligibility. Unverified placement outcomes, refund calculations and approved curriculum details remain restricted. General coding lessons and unrelated requests are redirected to FAST information.


# 2 System architecture


## Two deliberate answer paths


Path A returns an exact answer or a coverage limitation locally. A B.Tech CSE fee request should preserve the recorded annual amount and the separate admission and caution charges. A request for an unconnected timetable should state the limitation. Neither task needs a language model to create new facts.


Path B retrieves a small evidence set and asks Gemini to explain it. For example, How do I apply retrieves the supplied application-process records, sends them with the question and displays the streamed response. If that request fails, the application displays the retrieved text as a fallback.


## What runs where


The browser displays the interface. A Python process on the local machine or hosting server runs Streamlit, retrieval and session logic. Google hosts the model used by Gemini API requests. The browser never needs to hold the server-configured Gemini key. Source records remain local to the Python application unless selected for an API request.


Source expanders show the records retrieved by the application. They support transparency, but retrieval alone does not prove that every generated sentence is entailed by those records.


# 3 Technology choices and tradeoffs


| Choice | Why we used it | Tradeoff |
| --- | --- | --- |

| Python | One readable language for UI, retrieval, data processing and SDK calls | Less control over browser interactions than a custom frontend |

| Streamlit | Native chat widgets, forms, session state and rapid development | Rerun model and CSS overrides require care; not a full frontend framework |

| Google Gen AI SDK | Direct Gemini access with typed request configuration and streaming | Network, quota and model access remain external dependencies |

| JSONL | One complete record per line; easy to inspect and load | No database transactions, concurrent editing or automatic schema migration |

| Local BM25 ranking | Fast lexical retrieval with explainable weights and no embedding request | Can miss unfamiliar paraphrases, spelling errors and semantic matches |

| Explicit intent rules | Easy to explain and debug for a small, fixed scope | Rules overlap and require evaluation as the vocabulary grows |

| python-dotenv | Loads local configuration from .env | Local file must remain private; .env.example is only a template |

| CSS and SVG wrappers | Improve layout while preserving original university artwork | Streamlit DOM changes can require CSS maintenance |

| tzdata | Supports the Asia/Kolkata date used in model payloads across platforms | Adds a small environment dependency |

## What we deliberately did not add


React, a separate REST backend, a vector database and an orchestration framework would increase deployment and explanation effort for 136 records. This version does not use LangChain, FAISS, Chroma, neural embeddings or an independently trained intent classifier. Those choices should be added only if measured requirements justify them. Pillow is pinned as part of the tested imaging environment used by Streamlit; the final icon display uses SVG wrappers.


# 4 File structure and responsibilities


| File or folder | Responsibility |
| --- | --- |

| app.py | Renders the interface; loads cached knowledge; manages chat state; chooses local or AI response; displays sources |

| retrieval.py | Normalizes text, identifies intent, resolves programs, filters records, ranks matches and formats exact answers |

| assistant.py | Creates the Gemini client, builds a bounded evidence payload, streams output and returns readable errors |

| connection.py | Handles key configuration, connection fingerprints, explicit API checks and cloud settings |

| style.css | Defines spacing, colours, focus treatment, avatar presentation and composer styles |

| .streamlit/config.toml | Defines native light theme and dark sidebar settings |

| data/knowledge.jsonl | The permitted factual records and project coverage limitations used at runtime |

| data/intent_examples.jsonl | Development utterances for the routing fallback; not answer facts |

| data/faculty_directory.jsonl | Names, IDs, designations, subjects and usable email values for 14 faculty members |

| evaluation/questions.jsonl | 47 routing regression questions; excluded from the application index |

| tests and evaluate.py | Automated behavior checks and the reproducible local routing/timing report |

| assets | Original supplied logos plus SVG display wrappers for the icon and wordmark |

## Important UI helpers


load_knowledge caches the KnowledgeBase by the modification times of the three runtime data files. session_client keeps the Gemini client inside one user session and replaces it if the key changes. save_turn stores a completed exchange, trims the session to 30 exchanges and updates the active program. show_sources renders supporting record metadata. asset_uri embeds the header SVG without changing the source artwork.


# 5 Streamlit lifecycle and conversation state


Streamlit reruns the script after widget interactions. Without explicit state, a conversation would disappear during a rerun. We use st.session_state for data that belongs to one visitor, and Streamlit caches for reusable knowledge and static assets.


| State | Purpose | Lifetime |
| --- | --- | --- |

| messages | Completed user and assistant turns, sources, mode and timing | Current session; capped at 60 messages |

| programs | Named program context for a relevant follow-up | Updated or cleared after completed turns |

| last_intent | Helps interpret short requests such as And MCA | Current session |

| client and _client_key | Reuse a connection for the configured key | Per session, replaced when the key changes |

| verified_connection | Hash identifying a successfully checked key and model pair | Invalidated by a configuration change |

| retry_prompt | Question whose AI explanation fell back to local text | Cleared by a new request or conversation reset |

## Request sequence


- Render controls and the completed conversation.

- Accept a starter question, typed question or retry action.

- Retrieve evidence and determine whether an exact reply is available.

- Use one Gemini call only when an explanation is appropriate and a key is configured.

- Save the completed answer and rerun to present the updated conversation.

## Recovery behavior


An API failure does not erase the question or leave incomplete model text as a completed answer. The app replaces partial output with retrieved text, saves the warning and offers a retry. Retrying replaces the previous fallback exchange. New conversation clears messages and program context, but it does not delete the configured local or hosting secret.


# 6 Retrieval and BM25 explained


## From text to candidate records


normalize converts equivalent forms such as B.Tech, B Tech and btech to a shared token. It also handles selected names and subjects. tokens removes common words that contribute little to matching. Ordered regular-expression rules detect common intents. When no clear rule matches, development question examples supply a BM25-based routing fallback with minimum overlap and score requirements.


The retrieval stage selects a topic and applies program, faculty, applicant-type, scholarship or room-type filters where appropriate. It ranks permitted candidates, rather than searching blocked material and hoping the model ignores it. Ordinary descriptive requests take at most six records. Complete directory/program lists and simple multi-area local replies may contain more.


## What BM25 is doing


A word that occurs in fewer documents receives more importance. Repeated occurrences help a match, but the contribution saturates instead of growing without bound. Document length is normalized so longer records do not win simply by containing more words. The implementation uses k1 = 1.2 and b = 0.75.


```
idf(t) = log(1 + (N - df(t) + 0.5) / (df(t) + 0.5))
contribution = idf(t) * tf(t,d) * 2.2 /
    (tf(t,d) + 1.2 * (0.25 + 0.75 * length(d)/average_length))
score = sum(contribution for each matching query word)
```


This is executable-style pseudocode for the calculation in SearchIndex.rank. N is document count, df is the number of documents containing a word, and tf is its count in one record. For equally sized records, a word found in 2 of 100 documents has a larger IDF than a word found in 80 of 100. That makes a specific subject or surname more useful than a generic term.


This is lexical retrieval. We have not implemented an embedding model, semantic reranker or confidence-calibrated answer score.


# 7 Program context and difficult questions


| Request | Expected handling | Reason |
| --- | --- | --- |

| B.Tech CSE fees | Return only the matching program fee record | Avoid substituting fees from another degree |

| BCA fees | Ask for the specialization | BCA General and specialized BCA listings differ |

| What about its fees | Use a recently resolved program when the follow-up permits it | Reduce repetition without inventing a program |

| And MCA after CSE fees | Use MCA instead of the previous CSE program | Explicit new entity takes precedence |

| BCA AI fees | State that current program availability/fees are not confirmed | Do not borrow B.Tech AI or BCA General fees |

| Fees for 2027 to 2028 | State the missing-year limitation | The connected amounts are supplied for 2026 to 2027 |

| Fees and hostel details | Handle simple independently requested areas together | Avoid silently dropping one recognized area |

| Who teaches DBMS | Show the general supplied subject allocation | Do not claim a current-semester teaching schedule |

## Faculty directory ordering


The display follows the project owner's requested sequence: Dr. Dileep Kumar Singh, Dr. Vandana Rathore, Dr. Ravi Kumar Jadhav, Dr. Shweta Singh, Vishali Sharma, Anjali Nighoskar, Rudresh Sharma, Ashish Kumar Singh, Rahul Khajuria, Shivangee Nagar and Divya Jain, followed by Anjali Thakur, Reshma Chavan and Sukanta Kundu. IDs remain unchanged. This display sequence is not a new claim about formal seniority.


## Current limits


The rules handle selected English and Roman-script Hinglish forms. They are not a general language-understanding engine. Unfamiliar paraphrases and complex mixed requests can still be misrouted. Multiple missing details may require additional turns. Evaluation should include real questions from parents and students, not only prepared examples.


# 8 Dataset preparation and evidence


The supplied workbooks combined admission information, FAQs, faculty data, course allocations and overlapping question banks. We separated answer evidence from example questions, assigned stable record IDs, corrected mismatched FAQs, labelled missing information and preserved source references. The original question sheets contained 348 and 250 rows; they were consolidated rather than treated as 598 independent facts.


| Evidence state | Runtime records | Meaning |
| --- | --- | --- |

| reported_unverified | 83 | Claim recorded in the supplied workbook; not newly verified against the underlying document |

| user_confirmed | 38 | 14 faculty records and 24 general subject allocations confirmed by the project owner |

| historical | 2 | Recorded application dates; not current admissions status |

| policy | 13 | Project-authored coverage limitations; not official university policy |

| Total permitted | 136 | Only these records enter the factual/coverage corpus |

| Blocked in preparation | 161 | Excluded from runtime pending evidence or clarification |

## Record schema


Each knowledge row includes record_id, topic, entity, question, answer, audience, academic_year, evidence_status, response_rule, source_refs and keywords. Additional source/status/date fields preserve provenance. Faculty rows distinguish supplied_email from usable_email. Correction of an address is user confirmation, not proof of email delivery.


## Why JSONL instead of runtime Excel


One JSON object per line is easy to inspect and load without spreadsheet parsing. The app builds the index once per file version. Excel was used for reviewing and editing the source information; the runtime reads JSONL. Editing a spreadsheet alone does not update the deployed app. Changes must be exported to the runtime files and checked before release.


Duplicate or outdated facts can harm an informational bot even if retrieval is fast. We therefore retain year, payment units, source status and explicit response restrictions instead of simply embedding all supplied rows.


# 9 Prompt engineering and Gemini integration


## Prompt structure


The system instruction defines the assistant role, primary audience, domain, response length, evidence-only rule and uncertainty behavior. It explains the meaning of evidence states, limits unsupported university claims, disallows invented citations and treats question/document text as untrusted data. These are prompt-engineering controls, not model training.


```
Role: FAST informational assistant for students and parents.
Evidence: use only the selected records for university facts.
Uncertainty: state what is missing; do not invent an answer.
Style: direct, normally under 180 words; match the user language.
Sources: cite only record IDs supplied in the request.
Boundary: no live seats, account access or unsupported guarantees.
```


## Request payload


The API request contains the current India date, current question, up to two recent user questions and selected evidence. Evidence includes the record ID, entity, answer, academic year, state, response rule and source reference. The entire knowledge base and complete conversation are not transmitted. Previous assistant prose is not used as authoritative evidence.


| Parameter | Configured behavior |
| --- | --- |

| Model | GEMINI_MODEL setting; default gemini-3.5-flash-lite, subject to account access |

| Temperature | 0.2 for normal explanation requests |

| Output limit | 800 tokens normally, 1400 for detailed AI answers |

| Connection policy | Reused per-session client; one HTTP attempt; 30000 ms timeout |

| Streaming | Append returned text chunks to a placeholder |

Unknown bracketed KB citation IDs are stripped from the final model text. Sources shown by the UI come from retrieved records. These controls reduce some failures, but they do not prove that every generated claim is correct. No claim of zero hallucinations or measured generated-answer accuracy is made.


# 10 API keys privacy and hosted mode


## Local configuration


The running local app can accept a key in API settings. Alternatively, copy .env.example to .env beside app.py and replace the placeholder. load_dotenv loads that private file. The example file is a template and is not loaded as the actual secret file. A real key is never bundled with the project.


## Connection testing


Connect Gemini sends one small request asking for Ready. A successful readable response sets a connection fingerprint. The SHA-256 fingerprint identifies a key/model pair; it does not encrypt the stored key, authenticate a user or provide access control. A key/model change invalidates the matching status. A successful chat request also confirms that configuration.


## Cloud configuration added for deployment


get_setting reads environment/.env values first and managed st.secrets values second. In Community Cloud the owner enters the key in Advanced settings under Secrets. SHOW_API_SETTINGS set to false hides the visitor key/model controls and uses the server configuration. Local defaults retain the settings form for development.


```
GEMINI_API_KEY = "YOUR_REAL_KEY_IN_HOSTING_SECRETS_ONLY"
GEMINI_MODEL = "gemini-3.5-flash-lite"
SHOW_API_SETTINGS = "false"
```


## Data handling and limits


Session messages live in server memory and may disappear after session loss or restart. The app does not maintain a chat database. Gemini requests transmit the current question, selected records and up to two recent questions to Google. Download creates a transcript for the visitor. A hidden configuration form does not prevent others from consuming a public app's API quota: authentication, rate limiting and stronger abuse controls are future requirements.


# 11 UX principles tied to implementation


| Principle | Where it appears | What it helps |
| --- | --- | --- |

| Visibility of status | Spinner, streamed text, connection states, source/details expanders | Explain waiting, evidence and API readiness |

| Match to real language | Programs, fees, admission steps and faculty labels | Support first-time students and parents |

| User control | New conversation, retry, transcript download | Recover or leave with useful information |

| Consistency | One accent family, repeated spacing and native widgets | Reduce visual and interaction variation |

| Error prevention | Specialization clarification, exact monetary replies, evidence filters | Avoid unsupported substitutions and guessed details |

| Recognition over recall | Four starter prompts and visible conversation history | Reduce the need to know exact query wording |

| Efficiency | Cached retrieval and short answers by default | Avoid unnecessary API requests and repeated input |

| Minimalism | Chat is primary; settings, sources and diagnostics are secondary | Keep the admission task visible |

| Error recovery | Readable API errors, local fallback and retry | Keep the app useful when generation fails |

| Help and guidance | Scope notes, knowledge limits and setup documentation | Explain what the service can answer |

## What we can and cannot claim


We mapped the design to common usability heuristics and implemented the controls. We did not run a formal usability study, timed user-task experiment or accessibility certification. The selected patterns are engineering decisions to evaluate with users, not evidence that all UX principles are fully satisfied.


A useful next study would ask a student and a parent to find a program, separate academic and hostel charges, locate a faculty contact and recover from an ambiguous question. Record completion, errors and confusion before deciding which UI changes improve the experience.


# 12 Visual design and accessibility


## Branding and layout


The navy sidebar separates navigation and configuration from a warm-white conversation area. Teal connects interactive controls to the university branding. The main header identifies the faculty and institution. The welcome screen supplies four relevant starting tasks rather than a dashboard of unrelated statistics.


The original university artwork is retained. The icon uses an SVG circular clip so its previous white corner area is transparent. The wordmark uses an SVG viewport around the supplied PNG to remove exterior padding. The app uses the icon as favicon, header mark and assistant avatar. SVG display changes do not create a newly designed university logo.


## Input and message treatment


The composer has a visible boundary, focus treatment and send control. Native Streamlit widgets keep their labels and keyboard behavior. Chat messages use readable spacing and wrapped content. Sources and technical timing remain available without dominating every response. A two-column starter layout and smaller spacing are defined for narrow screens.


## Accessibility decisions


- Labelled native inputs and buttons support discoverable controls.

- Visible focus outlines help keyboard users identify the active control.

- Reduced-motion CSS disables decorative transitions where requested.

- Text wrapping and mobile spacing reduce avoidable overflow.

- The header icon has alternate text, while textual labels communicate the app identity.

## Checks still required


A real browser audit must verify mobile overflow, the collapsed-sidebar control, focus order, 200 percent zoom, contrast and screen-reader output. CSS styling depends on Streamlit DOM selectors and can change after an upgrade. The build environment could not complete a graphical browser audit, so automated widget tests must not be described as visual certification.


# 13 Testing results and performance


## Automated behavior checks


The deployment-prepared build passes 34 automated checks: 31 existing behavior checks plus three cloud-setting checks. Tests use real local records for retrieval and mocked Gemini calls for generation/connection behavior. They do not require or include a real API key.


| Area | Representative evidence |
| --- | --- |

| Entity and data boundaries | CSE aliases, ambiguous BCA, explicit MCA changes, unconfirmed programs and unsupported academic years |

| Factual output | Exact fee components, semester hostel units, scholarship filtering, corrected faculty emails and fixed directory order |

| Recovery and UI | No-key dataset mode, follow-ups, new conversation, streamed mock reply and API failure fallback |

| Scope and privacy | Prompt-override handling, unrelated requests, error redaction and evaluation-file exclusion |

| Cloud preparation | Environment precedence, managed secret retrieval and hidden visitor API controls |

## Routing regression report


The 47 prepared evaluation questions currently match the expected intent labels. Those questions were used during debugging. This is a regression result, not an unbiased held-out accuracy estimate, and it does not measure answer completeness or model factual accuracy.


## Recorded local timing


The stored report contains 470 retrieval runs over the 47-question set: median 1.640 ms and 95th percentile 94.396 ms; index construction 106.957 ms on that run. Timing varies with host load. These measurements exclude Google generation, first-token delay, browser rendering and concurrent-user load. Earlier faster samples must not be presented as guaranteed end-to-end speed.


For a real performance claim, measure cold start, warm retrieval, first displayed model text, complete answer time, error rate and concurrency using the actual chosen model and account.


# 14 Local setup and troubleshooting


## Run in VS Code on Windows


Extract the complete project and open the folder containing app.py and requirements.txt. Python 3.11 or newer is recommended; the prepared hosting instructions select Python 3.12. Open a PowerShell terminal in that folder.


```
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```


Open http://localhost:8501. For later starts, only the final command is required. Stop the server with Ctrl+C. The app must run on a machine or hosted server; a localhost link is not a public deployment.


| Problem | Action |
| --- | --- |

| No module named connection | Confirm connection.py exists beside app.py; do not pip-install a package called connection |

| Key not configured | Use API settings or .env, not .env.example; restart after a local environment change |

| Model unavailable | Use an accessible model ID for the actual Google account |

| Quota or rate error | Check account usage; use local exact answers while generation is unavailable |

| Missing logos or data | Keep assets and data folders with their exact filenames and relative paths |

| Old reply still shown | Restart if needed and use New conversation; completed old messages are not rewritten automatically |

| Unsupported fact | Obtain the authoritative source; do not remove a guard merely to force an answer |

## Reproduce checks


```
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe evaluate.py
```


# 15 Free browser deployment


Recommended platform: Streamlit Community Cloud. It hosts the Python process and provides a shareable streamlit.app URL, so visitors do not need VS Code or a running laptop. Official documentation describes free hosting, GitHub integration and managed secrets [1-3]. Gemini usage remains subject to the selected model/account limits [5-6].


## Upload the prepared source


- Create a dedicated GitHub repository such as fast-chatbot. Choose repository visibility after reviewing whether the supplied data may be shared.

- Upload the extracted project CONTENTS so app.py and requirements.txt are at the repository root. Include data, assets, tests and .streamlit/config.toml. The deployment ZIP stores hidden configuration inside the FAST_CHATBOT folder.

- Exclude .env, .venv, __pycache__, actual secrets.toml files and credentials. A .gitignore does not protect a file uploaded manually through a browser; inspect the selection.

- Sign in at https://share.streamlit.io and connect the relevant GitHub account. Select Create app and choose repository, branch main and file app.py.

## Configure and launch


In Advanced settings select Python 3.12. Paste the three settings below into Secrets, replacing the key placeholder only in that private hosting field. Select an accessible Gemini model. Save and deploy, then inspect the build logs if startup fails [2-3].


```
GEMINI_API_KEY = "YOUR_REAL_KEY"
GEMINI_MODEL = "gemini-3.5-flash-lite"
SHOW_API_SETTINGS = "false"
```


Open the actual URL assigned by the platform, test a local fee answer and an AI application-process explanation, and verify the hidden settings mode. Record the working URL only after testing; no URL or successful live deployment is invented in this document.


Community Cloud currently sleeps apps after 12 hours without traffic. Open the app before the jury session and allow a sleeping instance to wake [4].


# 16 Maintenance operating limits and roadmap


## Maintain facts before tuning the model


Update source evidence, then update the relevant JSONL records while preserving their IDs. A faculty email change must update both faculty_directory.jsonl and the corresponding knowledge answer. Recheck year, program, amounts, fee units and source references. The fixed faculty display order is controlled by stable IDs in retrieval.py. Re-run behavior tests and inspect a real answer before releasing changes.


## Operate a hosted app


Keep the API key in managed secrets and rotate it there if required. Read cloud logs for dependency or startup errors. Code and data updates are committed to GitHub; the hosting platform rebuilds or refreshes the application. Existing sessions can lose state during restart. Transcript download is the only current user-controlled export; there is no permanent conversation store.


## Important limits


- No authenticated student access, transactional database or live ERP/admission integration.

- Rules and word matching can misroute unfamiliar questions. Generated prose still needs factual evaluation.

- The server-configured key is shared in quota across visitors; hiding settings is not authentication or abuse prevention.

- No guarantee of continuous free hosting availability, unlimited API requests or current university facts.

- No formal load test, browser accessibility certification or official institutional endorsement.

## Prioritized improvements


First obtain authoritative program, eligibility, fee, scholarship, hostel and refund sources. Next collect unseen real-user questions and evaluate retrieval and answer correctness. Then measure live latency and common errors. Add semantic retrieval or reranking only if the measured failures justify it. For a public service, add authentication where needed, rate controls, source/version administration, monitoring and a defined data-review process.


# 17 Jury demonstration plan


| Time | Demonstration | Explain the engineering |
| --- | --- | --- |

| 0 to 40 s | Introduce the audience and problem | An admissions information assistant for students and parents; not a general tutor |

| 40 to 90 s | Explore programs, then ask B.Tech CSE duration | Curated records, aliases and visible sources |

| 90 to 140 s | Ask What about its fees | Program context, exact fee values and separate admission/caution components |

| 140 to 190 s | Show faculty directory and Reshma Chavan email | Requested HOD-first order and corrected user-supplied contacts |

| 190 to 245 s | Ask How do I apply | Show one grounded Gemini explanation and supporting records if the live key works |

| 245 to 285 s | Ask for a current seat count or exact refund | State a missing-data or unresolved-policy limitation rather than fabricating |

| 285 to 300 s | Show the test summary and close | Explain what was measured and the next improvements |

## Opening explanation


We built FAST_CHATBOT for people enquiring about the Faculty of Science and Technology. We use a curated dataset because university-specific facts should come from evidence. Our retrieval layer selects the relevant records. Exact facts use direct replies; Gemini explains selected descriptive records. This reduces unnecessary model calls and keeps source references visible.


## If the live API fails


Show the fallback instead of repeatedly clicking Connect. Explain that retrieval and exact answers run locally while generation depends on Google access, quota and network. Demonstrate a fee answer, faculty contact, ambiguous BCA clarification and a missing-data response. Do not describe a dataset fallback as a successful live Gemini response.


## Before the presentation


Open the hosted page, test one AI request, check the faculty order and correct fees, and keep this guide available. Never project the Secrets field or a real key. Confirm whether the audience may view supplied data before making an app or repository public.


# 18 Viva questions on the implementation


## 1 What makes this an AI chatbot
Gemini generates selected explanations from retrieved evidence. Some paths are intentionally deterministic; the presence of direct fact replies does not mean every request uses a model.


## 2 What is RAG
Retrieval-Augmented Generation supplies relevant external records to a model before it answers. Our implementation retrieves local JSONL records and gives selected evidence to Gemini.


## 3 Is this vector RAG
No. The implemented retriever uses topic/entity filters and BM25 lexical matching. No embedding model or vector database is present.


## 4 Did you train or fine tune Gemini
No. We use a pretrained model through its API. We prepare data, write prompts and implement retrieval/routing; we do not modify model weights.


## 5 Why does a fee answer not call Gemini
The amount already exists in the record. A direct answer avoids a model rewriting a number, reduces quota usage and removes generation delay for that task.


## 6 What is an intent
An intent describes the user task, such as program_fee or application_process. It guides routing and filtering; it is not itself an answer fact.


## 7 Why keep questions separate from knowledge
Example questions help routing and evaluation. University facts must come from evidence records. Mixing them can create duplicates and confuse what is actually supported.


## 8 How are follow ups handled
The session stores the resolved program and last intent. A relevant short follow-up may reuse them; an explicitly named new program takes priority.


## 9 Why use Streamlit
It gives Python-native chat widgets, forms, caching and session state, allowing a small application to be built and explained with fewer components.


## 10 Why not use a database
The runtime corpus is small and read-mostly. JSONL keeps the assignment simple. Concurrent administration, authenticated records and large data would justify a database.


## 11 What does BM25 improve
It gives more weight to distinctive matching words and normalizes document length. It helps lexical ranking but does not infer general semantic similarity.


## 12 Why do you ask for BCA specialization
The dataset contains different BCA fee records. Guessing General for an unspecified BCA request could give a wrong cost.


# 19 Viva questions on quality and deployment


## 13 Can the bot hallucinate
Yes. Evidence prompts, exact replies and source display reduce some risks; they do not guarantee that generated prose is always correct.


## 14 What does 47 out of 47 mean
All prepared routing regression questions match their expected intent labels. Those examples were used in debugging, so this is not an independent accuracy estimate.


## 15 What do the automated tests cover
They check specific retrieval, data-boundary, UI, mocked API and cloud-configuration behaviors. They do not establish real-user usability or live generated-answer accuracy.


## 16 Does streaming make the model faster
It lets users read text before the complete response is finished. It improves perceived waiting but does not necessarily reduce total generation time.


## 17 What happens when the API is unavailable
The app discards incomplete model prose, shows retrieved text with a warning and offers a retry. Exact local answers can still work.


## 18 Where is the key kept
Locally in .env or session input; on the host in managed secrets. It is excluded from repository uploads and is not included in the project archive.


## 19 Is the connection fingerprint encryption
No. It identifies whether the key/model configuration changed. The client still needs the actual key; the hash is not an access-control mechanism.


## 20 Is hosted use completely unlimited and free
Hosting is currently free on the selected Community Cloud service. API limits, model eligibility, billing and app sleep/resource limits are separate considerations.


## 21 Can parents use it without VS Code
After successful hosting they open the assigned app URL. The Python server runs on the host rather than their device.


## 22 What is the biggest remaining quality risk
The reliability and currency of source information. A fast retriever cannot make an outdated or unsupported fee, policy or placement claim correct.


## 23 How would you improve scale
Measure workload first. Consider an inverted/vector index, managed data storage, authentication, rate limits, monitoring and stronger content administration as requirements grow.


## 24 Is the directory order formal seniority
No. It is the exact presentation sequence supplied by the project owner. It does not change faculty IDs, designations or the meaning of the supplied subject allocations.


# 20 Evidence references and presentation claims


## Implementation evidence


The guide was checked against the consolidated project files: app.py, retrieval.py, assistant.py, connection.py, the three runtime JSONL files, theme/CSS assets, tests and docs/validation.json. Runtime counts were read from the actual files. The deployment build adds managed-secret loading and a visitor mode; it was tested with mocked cloud settings.


## Official references checked on 21 October 2026


[1] Streamlit Community Cloud overview
https://docs.streamlit.io/deploy/streamlit-community-cloud


[2] Deploy your app on Community Cloud
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy


[3] Secrets management for your Community Cloud app
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management


[4] Manage your app including app hibernation
https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app


[5] Gemini API rate limits
https://ai.google.dev/gemini-api/docs/rate-limits


[6] Gemini API billing and pricing
https://ai.google.dev/gemini-api/docs/billing
https://ai.google.dev/gemini-api/docs/pricing


## Claims to avoid in the jury presentation


- We trained Gemini on our Excel file.

- We use neural embeddings or a vector database in this version.

- The chatbot is 100 percent accurate or cannot hallucinate.

- The app has live admission status, guaranteed placements or official refund calculations.

- All university facts have been independently verified.

- A passing mocked API test proves that the live key or hosted service works.

Deployment status at document creation: source package prepared and local automated checks passed. A repository, hosting-account setup, private key configuration and post-deployment checks are still required before a working public link can be claimed.
