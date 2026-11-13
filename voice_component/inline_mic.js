export default function (component) {
  const { data, parentElement, setTriggerValue } = component;

  const SpeechRecognition =
    window.SpeechRecognition || window.webkitSpeechRecognition;

  const language = data?.language || "en-IN";

  let recognition = null;
  let state = "idle";
  let transcript = "";
  let disposed = false;
  let scheduled = false;
  let observer = null;
  let activeSession = false;

  // Streamlit component root
  const root = document.createElement("div");
  root.style.display = "none";
  parentElement.appendChild(root);

  // ==========================================================
  // MICROPHONE BUTTON
  // ==========================================================

  const button = document.createElement("button");

  button.type = "button";
  button.className = "fast-mic-button";
  button.dataset.state = "idle";
  button.title = "Speak your question";
  button.setAttribute("aria-label", "Start voice input");

  button.innerHTML = `
    <svg
      class="fast-mic-icon"
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

    <span
      class="fast-mic-spinner"
      aria-hidden="true"
    ></span>
  `;

  // ==========================================================
  // COMPONENT STYLES
  // ==========================================================

  const style = document.createElement("style");

  style.textContent = `
    .fast-mic-button {
      flex: 0 0 36px;
      width: 36px;
      height: 36px;
      padding: 0;
      margin-right: 4px;

      display: inline-flex;
      justify-content: center;
      align-items: center;

      background: transparent;
      border: none;
      border-radius: 10px;

      color: #38556a;
      cursor: pointer;

      transition:
        background-color 0.18s ease,
        color 0.18s ease,
        transform 0.12s ease;
    }

    .fast-mic-button:hover:not(:disabled) {
      background: #d8edf3;
      color: #075f73;
    }

    .fast-mic-button:active:not(:disabled) {
      background: #b8dfe8;
      transform: scale(0.94);
    }

    .fast-mic-button:focus:not(:focus-visible) {
      outline: none;
    }

    .fast-mic-button:focus-visible {
      outline: 2px solid #08788e;
      outline-offset: 2px;
    }

    .fast-mic-button[data-state="listening"] {
      background: #fee2e2;
      color: #dc2626;
    }

    .fast-mic-button[data-state="processing"] {
      background: #e5f4f7;
      color: #08788e;
      cursor: progress;
    }

    .fast-mic-button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }

    .fast-mic-spinner {
      display: none;
      width: 18px;
      height: 18px;

      border: 2px solid #bddde5;
      border-top-color: #08788e;
      border-radius: 50%;

      animation: fast-mic-spin 0.7s linear infinite;
    }

    .fast-mic-button[data-state="processing"]
    .fast-mic-icon {
      display: none;
    }

    .fast-mic-button[data-state="processing"]
    .fast-mic-spinner {
      display: block;
    }

    @keyframes fast-mic-spin {
      to { transform: rotate(360deg); }
    }

    @media (prefers-reduced-motion: reduce) {
      .fast-mic-spinner {
        animation: none;
      }
    }
  `;

  document.head.appendChild(style);

  // ==========================================================
  // MICROPHONE STATE
  // ==========================================================

  function setState(nextState) {
    state = nextState;
    button.dataset.state = nextState;

    button.disabled = nextState === "processing" || !SpeechRecognition;

    button.setAttribute(
      "aria-busy",
      nextState === "processing" ? "true" : "false",
    );

    const labels = {
      idle: "Start voice input",
      listening: "Stop voice input",
      processing: "Processing speech",
    };

    button.setAttribute("aria-label", labels[nextState] || labels.idle);

    button.title = labels[nextState] || labels.idle;
  }

  // ==========================================================
  // POSITION MICROPHONE BEFORE SEND ARROW
  // ==========================================================

  function positionMic() {
    if (disposed) return;

    const sendContainer = document.querySelector(
      '[data-testid="stChatInputSubmitButton"]',
    );

    if (!sendContainer?.parentElement) return;

    const actionRow = sendContainer.parentElement;

    if (
      button.parentElement !== actionRow ||
      button.nextElementSibling !== sendContainer
    ) {
      actionRow.insertBefore(button, sendContainer);
    }
  }

  observer = new MutationObserver(() => {
    if (disposed || scheduled) return;

    scheduled = true;

    requestAnimationFrame(() => {
      scheduled = false;
      positionMic();
    });
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true,
  });

  positionMic();

  // ==========================================================
  // SPEECH RECOGNITION
  // ==========================================================

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();

    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      if (disposed) return;

      activeSession = true;
      transcript = "";
      setState("listening");
    };

    recognition.onresult = (event) => {
      if (disposed) return;

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];

        if (result.isFinal && result[0]?.transcript) {
          transcript += result[0].transcript + " ";
        }
      }

      setState("processing");
    };

    recognition.onerror = (event) => {
      if (disposed) return;

      console.warn("[FAST_CHATBOT microphone]", event.error);

      activeSession = false;
      transcript = "";
      setState("idle");

      button.title = `Speech recognition error: ${event.error}`;
    };

    recognition.onend = () => {
      if (disposed) return;

      activeSession = false;

      const finalText = transcript.replace(/\s+/g, " ").trim();

      transcript = "";
      setState("idle");

      if (!finalText || finalText.length > 2000) return;

      // Prefills the native Streamlit chat input in app.py.
      // It does not submit the question automatically.
      setTriggerValue("voice", {
        id:
          typeof crypto.randomUUID === "function"
            ? crypto.randomUUID()
            : `${Date.now()}-${Math.random()}`,
        transcript: finalText,
      });
    };
  } else {
    setState("idle");
    button.title = "Speech recognition unsupported";
  }

  // ==========================================================
  // CLICK HANDLER
  // ==========================================================

  function handleClick(event) {
    event.preventDefault();
    event.stopPropagation();

    if (!recognition || disposed) return;

    if (activeSession) {
      setState("processing");
      recognition.stop();
      return;
    }

    if (state === "processing") return;

    try {
      transcript = "";
      recognition.start();
    } catch (error) {
      console.error("[FAST_CHATBOT microphone]", error);
      setState("idle");
    }
  }

  button.addEventListener("click", handleClick);

  // ==========================================================
  // CLEANUP
  // ==========================================================

  return () => {
    disposed = true;

    if (observer) observer.disconnect();

    button.removeEventListener("click", handleClick);

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

    button.remove();
    style.remove();
    root.remove();
  };
}
