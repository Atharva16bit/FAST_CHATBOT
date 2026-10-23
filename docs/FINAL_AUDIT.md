# Final chatbot audit

Build: **2026.10.23-audited**. This document and `START_HERE.md` supersede earlier release notes about the chat input, loader and response flow.

## Findings corrected

| Area | Previous problem | Current behaviour |
| --- | --- | --- |
| General faculty | Some ordinary phrases fell into unknown-question fallback | Faculty, teachers, teaching staff and natural faculty enquiries return the full directory |
| General programs | Broad requests could stop at six listings | All ten connected listings are shown |
| Admissions | Admission/admissions alone could be treated as unknown | Application information is retrieved |
| Degree names | MCA/BTech alone could be unrecognised | Resolve program or degree-family information |
| Program aliases | Short Cloud/Full Stack/DS labels could lose specialization | Recognised aliases resolve the supplied program |
| Contacts | Admissions email could route to faculty; faculty contact could route to admissions | Contact scope is preserved; missing faculty phone numbers are explained |
| Subjects | A teacher's keyword list could return their unrelated subjects | Filter actual subject allocation text before ranking |
| Substrings | Bus matched the end of syllabus | Match bus as a whole word |
| Compound questions | Splitting every “and” could break program names or fee components | Keep comparisons, fee breakdowns and related single-topic phrases together |
| Follow-ups | UG/PG and “What about MCA?” could lose the previous task | Retain relevant document/program task context, including after Thanks |
| Personal scores | Could be confused with admissions information | Explain that personal account records are not connected; offer ERP |
| Loading | Fast local lookup completed before the old spinner appeared | Render loading dots before processing, with a 350 ms minimum acknowledgement window |
| Submission lifecycle | Rendering, answering and rerunning could leave awkward transient states | One queued question, disabled input while pending, one saved exchange, pending cleared on completion |
| Retry | Risk of duplicating the fallback exchange | Replace the last fallback exchange |
| Scrolling | No explicit latest-response scroll operation | Trusted local JS follows a new turn; manual upward scrolling cancels following for that turn |
| Mobile | Older main-container selectors no longer matched current Streamlit markup | Correct selectors, safe-area padding, wrapping and horizontal table scrolling |
| Deployment cache | Routing edits could retain an old cached knowledge object | Include retrieval source timestamp in the knowledge cache version |

## Verification performed

- **60 Python automated tests passed**, including Streamlit AppTest interaction tests and mocked Gemini success/failure/retry cases.
- **100 curated topic phrases passed** within the test suite. These check route, selected-record counts and important answer fragments.
- **47/47 original regression questions matched their expected intents.** Local retrieval timing is recorded separately in `validation.json`; it does not measure page loading or Google API latency.
- **160/161 development examples matched their stored intent label.** The remaining example, “Tell me the fees,” is labelled ask_clarification in the source examples but intentionally routes to program_fee and asks for the course. Its visible behaviour is the required clarification rather than a guessed fee.
- **Real local Chromium browser checks passed** at 1280×800 and touch-enabled 390×844 viewports. The checks cover typed submission, visible loader, disabled pending composer, all 14 faculty in order, subsequent fees and unclear questions, recovery buttons, external-link targets, latest-answer visibility above the composer, manual upward scrolling and absence of horizontal page overflow.
- Loading indicators were observed in all eight browser-tested submissions (four per viewport). See `browser_validation.json` for observed samples.
- No JavaScript page exceptions were observed in those local browser runs. This does not certify Community Cloud's independently injected scripts.
- Browser screenshots of the loading state and completed desktop/mobile layouts were visually inspected during development; they are not included in the release archive.

## Limits and tradeoffs

The tests are curated development regressions, not independent answer-accuracy measurements. No system can be certified correct for every possible natural-language question by this finite test set.

No real Gemini key was available for live generation tests. Unit/UI tests mock success, incomplete/error handling and fallback behaviour. The current supplied dataset retains its own evidence limits; the chatbot does not invent live seats, personal marks or official refund calculations.

The mobile test emulates a mobile viewport and touch support. A physical Android/iPhone keyboard, the deployed Cloud wrapper and the user's browser extensions were not tested. Do one physical-phone check after deployment.

The 350 ms minimum loading acknowledgement deliberately adds a small visible feedback interval to otherwise near-instant local replies. No multi-second fake search is used. The label does not claim to search the JLU website.

The scroll helper contains only trusted application code. Questions, retrieved records and generated answers are not interpolated into executable JavaScript. It follows a new submission/response, then stops; wheel, touch or upward navigation can cancel it. The input remains Streamlit's native bottom composer.

Streamlit's required frontend bundles and Community Cloud's independent scripts remain. This release does not claim a new Lighthouse score, a smaller framework bundle or production load-test results.

## Repeat the checks

```powershell
python -m unittest discover -s tests -q
python evaluate.py
```

Optional local browser verification:

```powershell
python -m pip install playwright
python -m playwright install chromium
python tools/verify_browser.py --start-server
```

The optional tool starts a local server with no Gemini key, checks both viewport sizes and stops the server afterwards. It is not used by the deployed chatbot.
