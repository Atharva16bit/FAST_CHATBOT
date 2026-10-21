# UI update: course fees and cleaner answers

This update supersedes descriptions of visible source/evidence and
response-timing panels in the earlier jury guide.

- Understand fees opens ten course buttons instead of assuming B.Tech CSE.
- View course fees in the sidebar reopens the selector during a conversation.
- A general fee question without program context also offers course buttons.
- Course selection uses existing deterministic retrieval without a Gemini call.
- Fees show stored annual tuition, resource and examination components,
  plus the annual total.
- Admission and caution charges remain separate.
- Hostel and mess remain excluded from the academic-fee total.
- No fee amounts were changed.
- Internal KB citations, source-record panels, response-detail panels and
  repeated generic verification text are removed from chat.
- Source records and timing remain in session metadata for debugging.
- Academic-year/project information remains on the welcome screen and in About.
- Specific factual limitations remain in answers.
- presentation.py contains the display helpers.
- The original evidence and retrieval rules are unchanged.
- 38 automated tests pass.
- Live Gemini output has not been tested with a real key in this environment.

Run:

    python -m streamlit run app.py

Keep your real key in .env locally or in hosting Secrets after deployment.

## Mobile message input

The native chat input renders inside an inline Streamlit container below
the title.

This avoids depending on the viewport-pinned bottom composer in narrow
or embedded previews.

Input font size is 16px. Existing keyboard and native send-arrow behavior
remain.

Physical mobile keyboard behavior still needs testing on the deployed app.

## Hosting diagnostics and Lighthouse

- browser.gatherUsageStats=false disables Streamlit app usage statistics.
- Community Cloud may inject independent hosting scripts.
- client.toolbarMode=minimal simplifies built-in menu options.
- Hosting-provided controls may remain.
- theme.font uses the documented sans-serif value.
- The mobile composer remains inline below the header.
- The project contains no calls to /api/v2/user/details, Heap scripts,
  or custom iframe sandbox/permission code.
- The supplied console trace suggests hosting or embedded framework UI
  generates those requests.
- A browser network trace is needed to conclusively attribute every request.
- Do not add a fake user-details route or suppress console errors.
- Do not disable browser security to hide warnings.
- App configuration does not guarantee elimination of hosting warnings.
- Lighthouse unused-framework-JavaScript findings cannot be resolved by
  minifying Python files.
- No new Lighthouse score has been measured.
- Recheck in an incognito window after deployment.
- Test on a physical phone.
- Collect expanded accessibility audit details for remaining failures;
  general score screenshots do not identify failing elements.
