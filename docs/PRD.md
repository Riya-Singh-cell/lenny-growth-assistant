# Product Requirements Document (PRD)
# The Lenny Growth Assistant

**Status**: Implemented; local runtime and PostgreSQL deployment remain environment-dependent verification items.  
**Author**: Forward Deployed AI Engineer  
**Knowledge Base**: [Lenny's Podcast Transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts) (300+ Episodes)

---

## 1. Discovery Brief

### 1.1 The User & Persona
- **Primary Persona**: Product Managers, Heads of Growth, Startup Founders, and Executive Leaders seeking tactical, field-tested playbooks on product-market fit, activation, retention, pricing, and org design.
- **Secondary Persona**: Content creators, venture associates, and growth practitioners who want to transform podcast insights into structured frameworks and publishable essays.

### 1.2 The Problem
Product managers and founders face an ocean of high-signal knowledge embedded inside hundreds of hours of Lenny’s Podcast episodes (over 300 deep-dive interviews with practitioners like Adam Fishman, Elena Verna, Brian Balfour, Julie Zhuo, Casey Winters, etc.). However:
1. **Search friction**: Finding what specific leaders recommended on onboarding or experimentation requires wading through hours of video or full transcripts.
2. **Hallucination risk**: Generic LLMs hallucinate growth frameworks, cite non-existent case studies, or generalize without practitioner nuance.
3. **Synthesis bottleneck**: Converting raw interview transcripts into executive decision artifacts or publication-grade essays (~1,250 words) requires hours of manual drafting.

### 1.3 Job-to-be-Done (JTBD)
> *"When I need to make an urgent strategic growth decision or write an executive brief on a product initiative, I want to query Lenny’s Podcast knowledge base directly, receive an authoritative answer grounded strictly in what real guests shared, verify the exact transcript sources with YouTube timestamp playback, and generate standalone executive frameworks and Ship 30-style essays without leaving my workspace."*

### 1.4 Pain Removed
- Eliminates 95% of manual audio/transcript skimming time.
- Guarantees zero hallucinations through strict grounding and transparent refusal when evidence is missing.
- Bridges the gap between messy spoken dialog and polished, structured deliverables (visual HTML framework artifacts and atomic essays).

### 1.5 Success Metrics
- **Grounding Accuracy**: 100% of factual growth claims are attributable to specific guest quotes/excerpts.
- **Source Transparency**: 100% of answers display verified episode title, guest name, active speaker, timestamp, and timed YouTube link.
- **Evaluator Time-to-Value**: An evaluator can clone the repository, run the demo locally with Ollama or Cloud LLMs, and inspect sources in < 5 minutes.
- **Essay Fidelity**: Ship 30 for 30 skill reliably outputs ~1,250-word essays adhering to visual architecture rules (1-3-1 cadence, bold lead-ins, actionable checklists).

### 1.6 Assumptions
- The user has Docker or a local Python 3.10+ and Node.js environment.
- Ollama is available for offline local evaluation; Cloud APIs (Anthropic Claude / OpenAI) are supported for cloud evaluation.
- SQLite is acceptable as an automatic local zero-config fallback when PostgreSQL is not running.

### 1.7 Scope Included
- Real transcript ingestion pipeline from `ChatPRD/lennys-podcast-transcripts`.
- Diarized sliding-window chunker with timestamp preservation (`HH:MM:SS`) and YouTube timestamp link generation (`&t=Xs`).
- Pluggable vector retriever with cosine similarity search and keyword boost.
- Strict Grounded Growth Assistant with transparent refusal.
- Dedicated Ship 30 for 30 Content Skill (~1,250 words).
- Dedicated Artifact Generation Skill producing Markdown or styled HTML/CSS.
- Sandboxed in-app Artifact Viewer (`<iframe>` with an opaque `sandbox=""`).
- Multi-session persistence with session isolation in PostgreSQL/SQLite.
- Hot-swappable LLM Provider abstraction (Ollama, Anthropic Claude, OpenAI).
- Comprehensive automated test suite (`pytest`) and diagnostics panel.

### 1.8 Scope Excluded (v1)
- Live YouTube audio transcription at runtime (knowledge base is ingested from curated transcript repository).
- Audio speech synthesis / voice cloning of Lenny.
- Direct multi-tenant enterprise RBAC / user billing.

### 1.9 Risks & Mitigations
| Risk | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| LLM Hallucination | High | Strict system prompt directive + evidence injection + explicit refusal instruction when similarity score is below threshold. |
| Ollama offline / not started | Medium | Non-crashing healthcheck, UI readiness badge, and diagnostic step-by-step instructions (`ollama serve`). |
| Malicious HTML Injection in Artifacts | High | Server-side sanitizer (`bleach` + `BeautifulSoup`) stripping `<script>`, inline handlers, and protocols + sandboxed `<iframe>` isolation. |
| Database unavailable | Medium | Resilient DB engine with automatic fallback from PostgreSQL to SQLite. |

---

## 2. Product Requirements

### 2.1 Grounded Growth Assistant
- **FR-1.1**: The system must accept free-form product and growth queries.
- **FR-1.2**: Answers must be derived strictly from retrieved transcript context.
- **FR-1.3**: The assistant must decline to fabricate when context is missing, stating: *"Based on the available Lenny's Podcast transcript material, there is insufficient evidence to provide a fully grounded answer to this specific question."*
- **FR-1.4**: Every response must include structured source metadata: Episode Title, Guest Name, Speaker Name, Timestamp, and direct YouTube timed link.

### 2.2 Conversational Sessions & Isolation
- **FR-2.1**: Users can create, list, view, and delete chat sessions.
- **FR-2.2**: Each session maintains independent conversational memory (up to last 10 messages).
- **FR-2.3**: Session isolation: Session A must never expose or leak message or artifact context to Session B.

### 2.3 Ship 30 for 30 Skill
- **FR-3.1**: Triggered automatically when user requests an essay, Ship 30 format, or ~1,250 words.
- **FR-3.2**: Follows explicit Ship 30 digital writing architecture:
  - Strong hook with 1-3-1 cadence.
  - Numbered core pillars with bold sentence anchors.
  - Bulleted breakdowns of frameworks.
  - "The Monday Morning Execution Checklist".
  - Grounded podcast source citations at the conclusion.
- **FR-3.3**: Generates approximately 1,250 words without generic filler.

### 2.4 Artifact Generation & Viewer
- **FR-4.1**: Generates either Markdown or complete HTML/CSS frameworks.
- **FR-4.2**: Untrusted HTML is sanitized on the server before database storage.
- **FR-4.3**: Artifact Viewer renders beside the chat conversation in a split-screen layout.
- **FR-4.4**: Viewer features: "Preview" mode (sandboxed `<iframe>`), "Source" mode, "Copy to Clipboard", and "Download".

### 2.5 Model & Provider Switching
- **FR-5.1**: Evaluators can toggle between `ollama`, `anthropic`, and `openai` via UI or configuration without changing application code.
- **FR-5.2**: System health and model availability are visible in the header and diagnostics modal.

---

## 3. User Flows

```
[User Query]
    │
    ▼
[Intent Router]
    ├── Grounded Q&A  ──► [Retriever] ──► [Growth Assistant] ──► [Answer + Citations]
    ├── Ship 30 Essay ──► [Retriever] ──► [Ship 30 Skill]    ──► [~1,250w Essay + Citations]
    └── Artifact Gen  ──► [Retriever] ──► [Artifact Skill]   ──► [Sanitizer] ──► [Artifact Viewer]
```

---

## 4. Measurable Acceptance Criteria

1. **AC-1 (API Health)**: `GET /health` returns HTTP 200 with `status: ok`; `GET /ready` reports LLM, DB, and chunk counts.
2. **AC-2 (Grounded Retrieval)**: Asking about Adam Fishman's onboarding advice retrieves Adam Fishman's transcript chunks with relevance score and YouTube timestamp links.
3. **AC-3 (Ship 30 Length)**: Requesting a Ship 30 essay produces structured output between 1,000 and 1,500 words with explicit bold anchors and checklist.
4. **AC-4 (Artifact Isolation)**: Generating an HTML artifact renders inside an `<iframe>` with opaque `sandbox=""`; embedded `<script>` tags are scrubbed.
5. **AC-5 (Session Isolation)**: Messages saved in Session 1 cannot be fetched via Session 2 endpoints.
