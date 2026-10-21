# UI update: course fees and cleaner answers

This update supersedes descriptions of visible source/evidence and response-timing panels in the earlier jury guide.

- Understand fees opens ten course buttons instead of assuming B.Tech CSE.
- View course fees in the sidebar reopens the selector during a conversation.
- A general fee question without program context also offers course buttons.
- Course selection uses existing deterministic retrieval, without a Gemini call.
- Fees show stored annual tuition/resource/examination components and total, with admission/caution separate. Hostel/mess remain excluded. No amounts changed.
- Internal KB citations, source-record panels, response-detail panels and repeated generic verification text are removed from chat. Source records and timing remain in session metadata for explanation/debugging.
- Academic-year/project information remains on the welcome screen and in About. Specific factual limitations remain in answers.
- presentation.py contains the small display helpers. The original evidence and retrieval rules are unchanged.
- 38 automated tests pass, including all ten course selections, the vague-fee flow, fee exclusions and existing API fallback checks. Live Gemini output has not been tested with a real key in this environment.

Run: python -m streamlit run app.py
Keep your real key in .env locally, or in hosting Secrets after deployment. It is not included in this ZIP.
