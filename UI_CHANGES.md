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

## Database fallback and suggested topics

- Missing/unclear questions explicitly state that matching information was not found in the chatbot database.
- The latest recovery reply offers Programs, Fees, Admissions, Scholarships, Hostel and Faculty buttons. Fees opens the course selector.
- A bare score/marks question offers entrance, eligibility, scholarship and personal-result clarification choices.
- Personal marks, CGPA, results and attendance requests explain that student accounts are not connected and point users to their ERP. These answers do not call Gemini.
- The official website button uses https://www.jlu.edu.in/ (checked 23 October 2026). This is a link, not a live website search.
- The optional ERP button appears only when JLU_ERP_URL is configured with a confirmed HTTPS address. No ERP URL has been guessed or configured in this release. The button opens the external portal; it does not read student records.
- Use the bottom composer and loading indicator from the preceding release.

Validation: 47 automated tests pass, including personal records, score clarification, user-provided scholarship marks, topic buttons and URL configuration. Mobile device behaviour still requires a deployed phone check.

## Rendering performance update

- Streamed Gemini output repaints at most approximately once per 150ms, plus a final complete render, rather than reparsing the whole answer for every SDK chunk. No artificial sleep is used.
- Show only the most recent six exchanges by default once history exceeds twelve messages. A Show earlier messages toggle restores the rest of the retained conversation. Transcript download still includes all retained messages.
- Use an opaque header background and remove the decorative composer shadow. No overflow locks, scroll hijacking, global height overrides or console suppression are introduced.
- This does not remove Streamlit frontend bundles or independent Community Cloud scripts.
- Browser-extension scripts in the supplied report must be excluded by measuring with extensions disabled.
- Compare cold and warm loads separately, and record a browser Performance trace during scrolling. No revised Lighthouse score or measured FPS improvement is claimed.

Rendering validation: 48 automated tests pass, including showing earlier messages without losing retained history. Real scrolling performance still needs measurement in the deployed browser.
