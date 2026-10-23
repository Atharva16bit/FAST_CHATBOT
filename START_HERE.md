# FAST_CHATBOT final audited build

This folder is the complete project, not a patch. It includes the corrected routing, visible loading dots, response scrolling, official website and student ERP links.

## Update your existing project

1. Keep your existing project folder, `.git` folder, local `.env` and any real `.streamlit/secrets.toml`.
2. Extract this ZIP somewhere else. Open its inner `FAST_CHATBOT` folder.
3. Copy **all its contents**, including `.streamlit`, `static`, `tools`, `guidance.py` and `ui_feedback.py`, into your existing project. Replace matching files. Do not copy only `app.py`.
4. Open PowerShell in the existing project folder and run:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

5. After checking locally, publish the changes:

```powershell
git add .
git diff --cached --name-only
git commit -m "Audit chatbot routing and fix loading and reply scrolling"
git push origin main
```

The staged file list must not include `.env` or `.streamlit/secrets.toml`. Their `.example` versions contain placeholders and are safe to commit.

## Hosting

Repository: `Atharva16bit/FAST_CHATBOT`; branch: `main`; entry point: `app.py`; Python: `3.12`.

Keep your existing real API key and working model in Streamlit hosting Secrets. The public student ERP address defaults to `https://erp.jlu.edu.in/Login.aspx`; `JLU_ERP_URL` can override it. The official website is `https://www.jlu.edu.in/`. These links open the sites; they do not access accounts or search the website.

Wait for deployment to finish. Reboot the app once after this larger update and open a fresh browser tab. The clean public URL is:

https://fastchatbot-16.streamlit.app/?embed=true

## Quick checks after deployment

- Type `faculty`: all 14 faculty, with HOD first.
- Type `admission`: application information, rather than unknown-question fallback.
- Type `programs`: all ten supplied program listings.
- Type `MCA fees`: ₹100,000 annual academic total, with admission/caution separate.
- Type `documents`, then select Undergraduate or Postgraduate.
- Type `scholarships`, then select Academic or Sports.
- Type `DBMS teacher`: Vishali Sharma's subject allocation.
- Type `my marks`: no invented result; offer the official ERP.
- Type an unrelated question: supported-topic choices and website link.
- Check that loading dots appear after sending, the composer is disabled while pending, and the latest answer is brought into view.

## What changed in the chat lifecycle

A callback queues one question. The next run displays the user message and loading dots before processing. The composer is disabled until the answer completes. The loading acknowledgement has a 350 ms minimum display window for very fast local lookups. Gemini text redraws at most approximately every 150 ms, plus a final render. One completed exchange is saved and the pending state is cleared.

A small trusted local JavaScript helper moves the view to the latest turn. It stops following when the user scrolls upward; a new question starts a new follow operation. Older messages are available through Show earlier messages, and transcript download includes the retained history.

See `docs/FINAL_AUDIT.md` for what was tested and the remaining limits. The optional browser test tool is not needed to run the chatbot.
