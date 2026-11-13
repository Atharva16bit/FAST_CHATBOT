/**
 * FAST_CHATBOT Microphone
 * Streamlit Components V2
 *
 * Features:
 * - Browser speech recognition
 * - Microphone beside send arrow
 * - Red listening state
 * - Processing spinner
 * - Editable transcript preview
 * - Send / Cancel
 */

export default function (component) {
  const { data, parentElement, setTriggerValue } = component;

  const Recognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  const language = data?.language === "hi-IN" ? "hi-IN" : "en-IN";

  let recognition = null;
  let listening = false;
  let disposed = false;
  let transcript = "";
  let observer = null;
  let scheduled = false;
  let state = "idle";

  // Component root
  const root = document.createElement("div");
  root.className = "fast-voice-root";

  parentElement.appendChild(root);

  // ==========================================================
  // MICROPHONE STYLES
  // ==========================================================

  const style = document.createElement("style");

  style.textContent = `
    .fast-voice-control {
      display: flex;
      align-items: center;
      position: relative;
      flex: 0 0 auto;
    }

    .fast-mic-button {
      width: 36px;
      height: 36px;
      border: 0;
      border-radius: 10px;

      display: inline-flex;
      justify-content: center;
      align-items: center;

      background: transparent;
      color: #38556a;
      cursor: pointer;

      transition:
        background-color 0.15s ease,
        color 0.15s ease,
        transform 0.12s ease;
    }

    .fast-mic-button:hover:not(:disabled) {
      background: #d8edf3;
      color: #075f73;
    }

    .fast-mic-button:active:not(:disabled) {
      transform: scale(0.95);
      background: #b8dfe8;
    }

    .fast-mic-button:focus:not(:focus-visible) {
      outline: none;
    }

    .fast-mic-button:focus-visible {
      outline: 2px solid #0788a3;
      outline-offset: 2px;
    }

    .fast-mic-button[data-state="listening"] {
      background: #fee2e2;
      color: #dc2626;
    }

    .fast-mic-button[data-state="processing"] {
      background: #e5f4f7;
      color: #08788e;
    }

    .fast-mic-button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }

    /* Animated speech processing loader */

    .fast-mic-spinner {
      display: none;

      width: 18px;
      height: 18px;

      border: 2px solid #b3dbe5;
      border-top-color: #08788e;
      border-radius: 50%;

      animation: fast-voice-spin 0.7s linear infinite;
    }

    .fast-mic-button[data-state="processing"]
    .fast-mic-spinner {
      display: block;
    }

    .fast-mic-button[data-state="processing"]
    .fast-mic-svg {
      display: none;
    }

    @keyframes fast-voice-spin {
      to {
        transform: rotate(360deg);
      }
    }

    /* Transcript review popup */

    .fast-voice-review {
      position: absolute;
      bottom: calc(100% + 12px);
      right: -45px;

      width: min(340px, calc(100vw - 32px));
      padding: 12px;

      border: 1px solid #cbdde5;
      background: #ffffff;
      border-radius: 14px;

      box-shadow: 0 8px 28px #10354b22;
      z-index: 99999;

      display: none;
      color: #183346;
    }

    .fast-voice-review.open {
      display: block;
    }

    .fast-voice-review label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 7px;
    }

    .fast-voice-review input {
      width: 100%;
      min-width: 0;

      border: 1px solid #a4bac7;
      border-radius: 8px;

      padding: 9px;
      font: inherit;
      font-size: 14px;

      color: #183346;
      background: #ffffff;
    }

    .fast-voice-review input:focus {
      outline: 2px solid #08788e;
      outline-offset: 1px;
    }

    .fast-voice-actions {
      display: flex;
      justify-content: flex-end;
      gap: 7px;
      margin-top: 9px;
    }

    .fast-voice-actions button {
      border-radius: 8px;
      padding: 7px 12px;
      cursor: pointer;

      font: inherit;
      font-size: 12px;

      border: 1px solid #cbdde5;
      background: #ffffff;
      color: #183346;
    }

    .fast-voice-actions button:hover {
      background: #e5f4f7;
    }

    .fast-voice-actions .fast-voice-send {
      background: #08788e;
      border-color: #08788e;
      color: #ffffff;
    }

    .fast-voice-actions .fast-voice-send:hover {
      background: #075f73;
      color: #ffffff;
    }

    .fast-voice-status {
      font-size: 11px;
      margin-top: 7px;
      color: #647888;
    }

    @media (prefers-reduced-motion: reduce) {
      .fast-mic-spinner {
        animation: none;
      }
    }
  `;

  document.head.appendChild(style);

  // ==========================================================
  // MICROPHONE BUTTON AND TRANSCRIPT REVIEW
  // ==========================================================

  const control = document.createElement("div");

  control.className = "fast-voice-control";

  control.innerHTML = `
    <button
      type="button"
      class="fast-mic-button"
      aria-label="Start voice input"
      title="Speak your question"
      data-state="idle"
    >
      <svg
        class="fast-mic-svg"
        width="19"
        height="19"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        aria-hidden="true"
      >
        <rect x="9" y="2" width="6" height="12" rx="3"/>
        <path d="M5 10a7 7 0 0 0 14 0"/>
        <path d="M12 17v5"/>
        <path d="M8 22h8"/>
      </svg>

      <span class="fast-mic-spinner" aria-hidden="true"></span>
    </button>

    <div
      class="fast-voice-review"
      role="group"
      aria-label="Review voice transcript"
    >
      <label for="fast-voice-transcript">
        Check your question before sending
      </label>

      <input
        id="fast-voice-transcript"
        maxlength="2000"
        autocomplete="off"
      />

      <div class="fast-voice-status">
        Correct any recognition mistakes, then send.
      </div>

      <div class="fast-voice-actions">
        <button type="button" class="fast-voice-cancel">
          Cancel
        </button>

        <button type="button" class="fast-voice-send">
          Send
        </button>
      </div>
    </div>
  `;

  root.appendChild(control);

  const button = control.querySelector(".fast-mic-button");
  const review = control.querySelector(".fast-voice-review");
  const input = control.querySelector(".fast-voice-review input");
  const cancel = control.querySelector(".fast-voice-cancel");
  const send = control.querySelector(".fast-voice-send");

  // ==========================================================
  // BUTTON STATES
  // ==========================================================

  function setState(next) {
    state = next;

    button.dataset.state = next;

    button.setAttribute("aria-busy", next === "processing" ? "true" : "false");

    button.setAttribute(
      "aria-label",
      next === "listening"
        ? "Stop voice input"
        : next === "processing"
          ? "Processing speech"
          : "Start voice input",
    );

    button.title =
      next === "listening"
        ? "Stop listening"
        : next === "processing"
          ? "Processing speech..."
          : "Speak your question";

    button.disabled = next === "processing" || !Recognition;
  }

  // ==========================================================
  // POSITION BESIDE STREAMLIT SEND ARROW
  // ==========================================================

  function placeMic() {
    if (disposed) return;

    const submit = document.querySelector(
      '[data-testid="stChatInputSubmitButton"]',
    );

    if (!submit?.parentElement) return;

    if (
      control.parentElement !== submit.parentElement ||
      control.nextElementSibling !== submit
    ) {
      submit.parentElement.insertBefore(control, submit);
    }
  }

  // Reattach the mic when Streamlit rerenders its composer.

  observer = new MutationObserver(() => {
    if (scheduled || disposed) return;

    scheduled = true;

    requestAnimationFrame(() => {
      scheduled = false;
      placeMic();
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  placeMic();

  // ==========================================================
  // TRANSCRIPT REVIEW
  // ==========================================================

  function closeReview() {
    review.classList.remove("open");
    input.value = "";
    setState("idle");
  }

  function showReview(text) {
    const cleaned = text.replace(/\s+/g, " ").trim();

    if (!cleaned) {
      setState("idle");
      return;
    }

    input.value = cleaned;

    review.classList.add("open");
    setState("idle");

    input.focus();
    input.select();
  }

  function submitText() {
    const text = input.value.replace(/\s+/g, " ").trim();

    if (!text || text.length > 2000) return;

    closeReview();

    // Send the corrected transcript into app.py.
    setTriggerValue("voice", {
      id:
        typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random()}`,
      transcript: text,
    });
  }

  // ==========================================================
  // SPEECH RECOGNITION
  // ==========================================================

  if (Recognition) {
    recognition = new Recognition();

    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      if (disposed) return;

      listening = true;
      transcript = "";

      setState("listening");
    };

    recognition.onresult = (event) => {
      if (disposed) return;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal && event.results[i][0]?.transcript) {
          transcript += event.results[i][0].transcript + " ";
        }
      }

      setState("processing");
    };

    recognition.onerror = (event) => {
      if (disposed) return;

      listening = false;
      transcript = "";

      setState("idle");

      console.warn("FAST voice recognition:", event.error);

      button.title = `Speech error: ${event.error}`;
    };

    recognition.onend = () => {
      if (disposed) return;

      listening = false;

      const final = transcript;
      transcript = "";

      showReview(final);
    };
  } else {
    button.title = "Speech recognition is unsupported in this browser";

    setState("idle");
  }

  // ==========================================================
  // EVENT HANDLERS
  // ==========================================================

  function handleMicClick(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!recognition || disposed) return;

    if (listening) {
      setState("processing");
      recognition.stop();
      return;
    }

    if (state === "processing") return;

    closeReview();

    try {
      recognition.start();
    } catch (error) {
      setState("idle");
      console.error("Microphone start failed", error);
    }
  }

  function handleCancel(event) {
    event.preventDefault();
    closeReview();
  }

  function handleSend(event) {
    event.preventDefault();
    submitText();
  }

  function handleKey(event) {
    if (event.key === "Enter") {
      event.preventDefault();
      submitText();
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeReview();
    }
  }

  button.addEventListener("click", handleMicClick);
  cancel.addEventListener("click", handleCancel);
  send.addEventListener("click", handleSend);
  input.addEventListener("keydown", handleKey);

  // ==========================================================
  // COMPONENT CLEANUP
  // ==========================================================

  return () => {
    disposed = true;

    observer.disconnect();

    button.removeEventListener("click", handleMicClick);
    cancel.removeEventListener("click", handleCancel);
    send.removeEventListener("click", handleSend);
    input.removeEventListener("keydown", handleKey);

    if (recognition) {
      recognition.onstart = null;
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;

      try {
        recognition.abort();
      } catch (_) {
        // Ignore shutdown errors.
      }
    }

    control.remove();
    root.remove();
    style.remove();
  };
}
