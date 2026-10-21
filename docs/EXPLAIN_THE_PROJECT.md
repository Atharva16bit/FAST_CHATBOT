# Explain the project in your viva

## What does it do?
It helps students and parents explore Faculty of Science & Technology admission
information: listed programs, fees, process, documents, scholarships, hostel and
faculty. Current students can get limited general information. It does not
access personal records or make admission decisions.

## What is RAG here?
Retrieval-Augmented Generation means the model receives relevant knowledge
selected from our dataset before answering. An LLM alone may invent a college
fee; retrieval supplies the recorded amount and its source. Exact fees and
contacts use a direct response because there is no benefit in asking the model
to rewrite a number or address.

## How does retrieval work?
1. Normalize B.Tech / B Tech / btech and subject aliases to shared forms.
2. Determine the question's intent with readable rules. Development examples
   provide a keyword-based fallback for some paraphrases.
3. Resolve the program and required specialization. Carry the previous program
   only where a follow-up makes sense, and respect explicitly named changes.
4. Filter by topic and entity. For example, B.Tech CSE must not return MCA fees.
5. BM25 ranks word matches. Words appearing in fewer records receive more weight.
6. Select a small evidence set. Handle missing data locally or send the selected
   records to Gemini for a short explanation.
7. Display the retrieved source references independently of the generated prose.

## Why not train a model on the intent spreadsheet?
These few question examples are useful for routing and testing. A separate
classifier would add training, dependencies and maintenance before demonstrating
any improvement. The dataset is the evidence corpus; example questions are not
new university facts. Future evaluation may justify semantic retrieval or a
classifier if keyword coverage proves inadequate.

## How is it optimized?
The local index is small and created once per data version. Repeated Streamlit
reruns reuse it. There is no embedding network request. Greetings, exact facts
and missing-data responses need no Gemini call. Descriptive answers need at most
one. Context and output length are bounded, and chunks display progressively.
No cross-user chat-answer cache is used.

## Complexity and limitations
Building the BM25 index is linear in the total token count of the dataset.
Each ranked search scans the small collection of documents and query words.
This is appropriate for hundreds of records, not millions. Large collections
would need an inverted/vector index, relevance evaluation and more robust
entity resolution. Rules and lexical matching can miss unfamiliar paraphrases,
misspellings or unsupported languages. We include English and Roman-script
Hinglish examples, not a guarantee of comprehensive multilingual retrieval.

## UX principles used
- Visibility: knowledge status, generation spinner, streaming, sources and timing.
- Familiar language: programs, fees, admission steps and faculty labels.
- Control: new conversation, retry, download and AI-answer settings.
- Consistency: original teal branding, repeated spacing and native controls.
- Error prevention: specialization clarification and evidence-status filters.
- Recognition: four useful starter prompts, persistent conversation and sources.
- Efficiency: local exact answers, cached index and optional detailed AI replies.
- Minimalism: chat is the main task; configuration stays in the sidebar.
- Recovery: readable API errors and a factual fallback instead of a broken chat.
- Help: setup guide, source explanations and explicit limits.
Native labelled widgets, visible focus and reduced-motion styling help
accessibility. They are not a substitute for manual mobile/keyboard/screen-reader
verification or a formal accessibility audit.

## What still needs improvement?
Obtain authoritative source documents; maintain the corrected faculty contacts; clarify
refund boundaries; validate curricula and dated placement outcomes. Add new
unseen real parent/student questions and evaluate answer correctness, not just
routing. Measure real Google API latency and concurrency before making speed or
scale claims. Add semantic retrieval only if evaluation demonstrates a need.

## UI and API update
connection.py owns key placeholder handling, a per-key/per-model status fingerprint
and the explicit Gemini test. The session client is reused. The university
artwork remains original inside SVG cropping/clipping viewports. The dark sidebar
and light chat surface are defined by the Streamlit theme; style.css controls
spacing, focus, avatar clipping and composer treatment. Sources and response
diagnostics remain secondary expandable content.
