# Final audited UI and routing update

Build **2026.10.23-audited** consolidates the previous changes. Follow `START_HERE.md` when updating the project.

- Native message composer stays at the bottom on desktop and mobile.
- A question callback queues one pending turn before rendering the loading acknowledgement.
- Loading dots appear before dataset processing and remain for a minimum 350 ms acknowledgement window.
- Duplicate submission is disabled while an answer is pending.
- AI output redraws in batches instead of on every small SDK chunk.
- The latest response is brought into view using a small trusted local scroll helper. Manual upward scrolling stops following for the current turn.
- The latest six exchanges render by default; earlier retained messages and the full retained transcript remain available.
- Broad program and faculty enquiries display complete connected lists.
- Common admissions, contact, degree, subject and follow-up phrases have explicit regression coverage.
- Course fee buttons display stored amounts without using Gemini.
- Scholarship and document questions offer relevant category/applicant choices.
- Personal records and missing-information replies provide scope guidance and the official website/ERP links.
- User and assistant text never enters the executable scroll helper.
- Source records and existing fee components are preserved.

Validation: **60 automated tests**, a **100-phrase topic matrix**, **47/47 original routing regressions**, and local real-browser checks at desktop/mobile viewport sizes. See `docs/FINAL_AUDIT.md` and the JSON reports for scope and remaining limitations.

This archive contains no real API key, `.env`, `.git`, virtual environment or real hosting Secrets file. Copy all included files, including `static`, `ui_feedback.py` and `guidance.py`, when updating the existing project.
