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

## Mobile message input

The native chat input now renders inside an inline Streamlit container below the title. This avoids depending on the viewport-pinned bottom composer in narrow or embedded previews. Input font size is 16px. Existing keyboard and native send-arrow behavior remain. Physical mobile keyboard behavior still needs testing on the deployed app.

## Hosting diagnostics and Lighthouse

- Disable Streamlit app usage statistics with browser.gatherUsageStats=false. Community Cloud may inject its own independent scripts.
- Set client.toolbarMode=minimal to simplify built-in menu options. Hosting-provided controls may remain.
- Correct theme.font to the documented sans-serif value.
- Keep the mobile composer inline below the header and 16px input text.
- The project contains no calls to /api/v2/user/details, Heap scripts, or custom iframe sandbox/permission code. The supplied console trace suggests these originate in hosting or embedded framework UI; a browser network trace is needed to conclusively attribute every request.
- Do not add a fake user-details route, suppress console errors, disable browser security, or claim these warnings are fixed by app configuration.
- Generic Lighthouse findings about unused framework JavaScript cannot be resolved by minifying the Python files. No new Lighthouse score has been measured.
- Recheck in an incognito window after deployment; test on a physical phone and collect expanded audit details for any remaining accessibility findings. General score screenshots do not identify the failing elements.

## Review update: bottom composer, loading state and scope guidance

This section supersedes earlier notes about putting the composer below the title.

- The native Streamlit chat input is now at the bottom of the page on mobile and desktop.
- The bottom container includes safe-area padding for mobile devices.
- The composer has one focus highlight, avoiding a second rectangle around its textarea.
- A spinner covers dataset retrieval and AI response processing. Very fast local answers may finish before the spinner becomes visible; no artificial delay is added.
- Unclear questions ask the user to rephrase and list supported FAST topics.
- Other/another/ather school, college or university requests return a scope explanation instead of FAST fee records, including when an earlier course is remembered.
- Other unrelated topics use the same scope explanation. Topic-specific missing-information replies retain their specific limitations.
- Fee amount formatting no longer includes trailing sentence commas.
- 41 automated tests pass. Physical phone keyboard/viewport behaviour still needs verification after deployment.
