# Deploy FAST_CHATBOT to Streamlit Community Cloud

## Current status
The source package is ready and passes 34 automated checks. It is not yet a
live deployment. The actual hosting URL exists only after the deployment succeeds.

## One-time setup
1. Sign in to GitHub and create a repository named fast-chatbot. Choose public
   or private visibility after reviewing the supplied faculty/institution data.
2. Extract the deployment ZIP. Upload the CONTENTS of its FAST_CHATBOT folder
   to your repository, so app.py and requirements.txt are at the root.
3. Include .streamlit/config.toml, assets, data, connection.py, assistant.py,
   retrieval.py and style.css. Preserve folder names and file capitalization.
4. Never upload .env, .venv, __pycache__ or a real .streamlit/secrets.toml.
   .gitignore does not filter files manually selected in the GitHub upload UI.
5. Open https://share.streamlit.io, sign in/connect GitHub, and select Create app.
6. Select the repository, main branch and app.py as the entrypoint.
7. In Advanced settings, choose Python 3.12 and enter Secrets:

```toml
GEMINI_API_KEY = "YOUR_REAL_GOOGLE_AI_STUDIO_KEY"
GEMINI_MODEL = "gemini-3.5-flash-lite"
SHOW_API_SETTINGS = "false"
```

8. Save and deploy. Inspect logs if dependency installation or startup fails.
9. Open the assigned streamlit.app URL. Check a fee answer, the HOD-first
   directory and an AI question such as How do I apply. Ensure the API settings
   form is hidden. Do not publish a guessed URL as if it were live.
10. Bookmark the real URL. The local machine and VS Code need not remain open.

## Accounts and cost
Community Cloud is currently free hosting. Gemini quotas, free-tier eligibility
and any API billing are separate and depend on the account/model. The app does
not force billing activation. Check Google AI Studio before relying on a free
quota. Community Cloud currently sleeps an app after 12 hours without traffic;
open it before the jury demonstration so it can wake if needed.

## Source layout if uploaded as a nested folder
The recommended layout puts app.py at the repository root. If you intentionally
keep a FAST_CHATBOT subfolder, the entrypoint is FAST_CHATBOT/app.py and
Streamlit must find the right dependency/config files. Use the root layout
above to avoid that ambiguity.

## Secrets and visitor mode
This build reads non-empty environment/.env values first, then st.secrets.
SHOW_API_SETTINGS defaults to true locally, preserving the development form.
Set it to false in hosted Secrets so visitors do not see API-key/model controls.
A hidden settings form is not authentication or rate limiting. All visitors
using the server key share the owner's API quota. Do not upload private data.

## Verify a release
Run python -m unittest discover -s tests -v locally before uploading.
After deployment, test actual Gemini access and an independent mobile/browser
session. The automated SDK tests use mocks and cannot prove live API access.
Changing data or code in GitHub updates the hosted app; changes may reset sessions.

## Official references checked 21 October 2026
https://docs.streamlit.io/deploy/streamlit-community-cloud
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app
https://ai.google.dev/gemini-api/docs/rate-limits
