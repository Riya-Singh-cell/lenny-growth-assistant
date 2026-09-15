# The Lenny Growth Assistant

> **An enterprise-grade, evaluator-friendly AI product advisor strictly grounded in Lenny's Podcast transcripts.**

Built for product leaders, growth practitioners, and hiring evaluators. Features semantic sliding-window transcript retrieval with direct YouTube timestamp citations, dedicated Ship 30 for 30 essay generation (~1,250 words), and an isolated in-app Artifact Viewer for interactive HTML and Markdown frameworks.

---

## 1. Project Overview
"The Lenny Growth Assistant" ingests authentic deep-dive podcast interviews from [Lenny's Podcast Transcript Knowledge Base](https://github.com/ChatPRD/lennys-podcast-transcripts) (Brian Balfour, Elena Verna, Adam Fishman, Julie Zhuo, Casey Winters, Shreyas Doshi, Sean Ellis, Gibson Biddle, Naomi Gleit, Madhavan Ramanujam, Gustaf Alstromer, etc.). It delivers:

- **Strict Grounding & Deterministic Refusal**: Zero hallucinated claims. The assistant enforces a hard programmatic guard BEFORE LLM invocation. If retrieval yields no chunks or the best similarity score falls below `RAG_CONFIDENCE_THRESHOLD`, it immediately returns a deterministic refusal without consuming LLM tokens.
- **Source Transparency**: Every grounded claim cites the episode title, guest name, active speaker, timestamp (`HH:MM:SS`), and a direct playback link to YouTube (`&t=Xs`).
- **Claude Agent SDK & Local Ollama Execution**:
  - **Cloud Mode**: Uses the official Python Claude Agent SDK (`claude-agent-sdk`) with in-process MCP tools (`search_lenny_transcripts`, `generate_ship30_essay`, `create_product_artifact`).
  - **Local Mode**: Uses an Ollama-compatible execution loop invoking the **exact same underlying tools** with zero cloud API dependencies.
- **Ship 30 for 30 Content Skill**: Generates high-impact ~1,250-word atomic essays structured with 1-3-1 hook rhythms, numbered framework pillars, bold sentence anchors, and actionable Monday execution checklists.
- **Sandboxed Artifact Viewer**: Split-screen preview for interactive HTML/CSS frameworks and Markdown documents, protected by server-side Bleach/CSS sanitization and an opaque client-side iframe sandbox (`sandbox=""`).
- **PostgreSQL-First Architecture**: Canonical persistence in PostgreSQL with Alembic migrations (`alembic/versions/001_initial_schema.py`) and automatic SQLite fallback logging `[FALLBACK] PostgreSQL unreachable. Operating in local SQLite compatibility mode.`
- **Responsive UX**: Desktop side-by-side split screen with a seamless collapsible artifact viewer and tab switcher for screens below 1024px.

---

## 2. Architecture & Execution Paths

```
CLOUD MODE:
Claude Agent SDK (`claude-agent-sdk`, in-process MCP tools)
        ↓
Canonical Tools:
  - search_lenny_transcripts
  - generate_ship30_essay
  - create_product_artifact
        ↓
Retrieval Engine (2,186 Chunks) / Ship30 Skill / Artifact Skill

LOCAL MODE (Mandatory Demo):
Ollama-compatible local tool execution path
        ↓
The SAME Canonical Tools:
  - search_lenny_transcripts
  - generate_ship30_essay
  - create_product_artifact
        ↓
Retrieval Engine (2,186 Chunks) / Ship30 Skill / Artifact Skill
```

### Backend API Surface

The FastAPI application is assembled in `backend/app/main.py` and exposes interactive API documentation at `/docs` when the backend is running.

- `GET /health`: lightweight HTTP 200 application health response.
- `GET /ready`: readiness details for the active LLM provider, database connection, and vector-store population.
- `POST /api/chat`: accepts `{ "session_id": "...", "message": "...", "provider": "...", "model": "..." }`. Provider and model are optional overrides. The response includes the assistant content, intent, sources, provider/model, tool calls, evidence status, and an optional artifact.
- `POST/GET/DELETE /api/sessions` and `GET /api/sessions/{session_id}`: create, list, inspect, and delete sessions with their messages and artifacts.
- `POST /api/artifacts`: stores Markdown or HTML artifacts; HTML is sanitized before the sanitized representation is persisted. `GET /api/artifacts/{artifact_id}` and `GET /api/artifacts/session/{session_id}` retrieve artifacts.

Messages and artifacts are persisted through SQLAlchemy repositories. PostgreSQL is the canonical database architecture; when PostgreSQL is unreachable, the application uses the local SQLite compatibility path and reports that mode in diagnostics/readiness.

---

## 3. Key Features

- 🎙️ **Transcript-Grounded Q&A**: Answers complex growth queries using authentic Lenny's Podcast dialogue turns.
- 🛑 **Deterministic RAG Refusal**: Hard programmatic check before LLM generation. When evidence is insufficient, immediately returns refusal with zero LLM calls.
- 🔗 **Timed YouTube Citations**: Every quote provides a link directly to the video timestamp (`&t=Xs`).
- ✍️ **Ship 30 for 30 Essay Skill**: Dedicated multi-stage pipeline producing ~1,250-word publication-ready essays.
- 🎨 **In-App Artifact Viewer**: Split-screen preview for interactive HTML/CSS frameworks and Markdown documents.
- 🛡️ **Opaque HTML Security & Sandboxing**: Server-side Bleach + TinyCSS2 sanitization + client-side sandboxed `<iframe>` (`sandbox=""`), defanging `<script>`, event handlers, SVG attacks, and CSS expression vectors.
- 🔄 **Hot-Swappable LLM Providers**: Toggle between local Ollama (`qwen2.5:0.5b` recommended) and Cloud Claude/OpenAI on the fly.
- 💾 **PostgreSQL First with SQLite Fallback**: Canonical database with Alembic schema migrations; automatically falls back to local SQLite with structured logging.
- 📱 **Responsive Mobile/Tablet UX**: Collapsible artifact panel and mobile tab switcher preserving full usability on screens under 1024px.
- 🩺 **Startup Diagnostics**: Real-time observability over model reachability, database engine, and vector index chunk counts.

---

## 4. Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, React-Markdown, Remark-GFM.
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Bleach, TinyCSS2, BeautifulSoup4.
- **Database**: PostgreSQL 16 with pgvector (Docker) / SQLite with aiosqlite (local zero-config fallback).
- **AI & RAG**: Claude Agent SDK (`claude-agent-sdk`), Ollama local provider (`qwen2.5:0.5b` recommended), SentenceTransformers / hashed embeddings, Numpy cosine similarity.
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient (**40 automated tests passing**).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 5. Prerequisites

- **Python**: 3.10 or higher.
- **Node.js**: v18 or higher (v20+ recommended).
- **Ollama** (for local offline demo): [https://ollama.com](https://ollama.com)
- *(Optional)* **Docker & Docker Compose** (for PostgreSQL and containerized execution).

### Environment Variables

Copy `.env.example` to `.env` and adjust only the values needed for the chosen run mode. The main settings are:

| Variable | Purpose | Local default / guidance |
| :--- | :--- | :--- |
| `LLM_PROVIDER` | Selects `ollama`, `anthropic`, or `openai`. | `ollama` |
| `OLLAMA_BASE_URL` | Ollama server address. | `http://localhost:11434` |
| `OLLAMA_MODEL` | Local generation model. | `qwen2.5:0.5b` |
| `OLLAMA_TIMEOUT_SECONDS` / `OLLAMA_MAX_TOKENS` | Local request timeout and output cap. | `180.0` / `512` |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Optional Anthropic cloud configuration. | Key omitted for local demo |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Optional OpenAI cloud configuration. | Key omitted for local demo |
| `DATABASE_URL` | PostgreSQL URL or explicit SQLite URL. | PostgreSQL default; SQLite fallback |
| `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` | Embedding backend and model. | `sentence_transformers` / `all-MiniLM-L6-v2` |
| `RAG_CONFIDENCE_THRESHOLD` | Minimum score used by the programmatic grounding guard. | `0.22` |
| `CORS_ORIGINS` | Comma-separated frontend origins. | Local Vite origins |

API keys are optional for the mandatory local Ollama demo. Never commit `.env` or secret values.

---

## 6. Quickstart: Local Ollama Demo

### Step 1: Start Ollama
Ensure Ollama is running on your machine:
```bash
ollama serve
```
Verify installed models (recommended lightweight model: `qwen2.5:0.5b`):
```bash
ollama list
```
If you need to pull a lightweight model:
```bash
ollama pull qwen2.5:0.5b
```

### Step 2: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Adjust `OLLAMA_MODEL` if desired (defaults to `qwen2.5:0.5b`).

### Step 3: Run Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
On startup, the backend automatically initializes tables (PostgreSQL or SQLite fallback) and displays the **Startup Diagnostics Banner**:
```
=================================================================
  THE LENNY GROWTH ASSISTANT - STARTUP DIAGNOSTICS
=================================================================
  - Active LLM Provider : ollama
  - Configured Model    : qwen2.5:0.5b
  - Provider Reachable  : YES
  - Database Backend    : SQLite (fallback mode; PostgreSQL runtime is environment-dependent)
  - Knowledge Base Chunks: 2186 indexed
  - RAG Refusal Guard   : threshold = 0.22
=================================================================
```

### Step 4: Run Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

### Cloud Model Setup

Cloud providers are optional alternatives to the verified local demo. Set `LLM_PROVIDER=anthropic` and provide `ANTHROPIC_API_KEY`, or set `LLM_PROVIDER=openai` and provide `OPENAI_API_KEY`; choose the corresponding model with `ANTHROPIC_MODEL` or `OPENAI_MODEL`. The application uses the cloud provider implementation and Claude Agent SDK path for Anthropic mode. A missing cloud key is reported as unavailable and generation instructs the operator to switch back to Ollama or configure the key.

### Provider and Model Switching

The configured provider/model is selected by the factory in `backend/app/llm/factory.py`. The `/api/chat` request can also supply optional `provider` and `model` overrides for a single request. An unrecognized provider falls back to the configured Ollama provider. The local Ollama path and cloud path expose the same canonical tools; only the execution driver changes.

---

## 7. Docker Deployment & Host Networking

To run the complete stack with PostgreSQL via Docker Compose:

```bash
docker compose up --build
```

### Host Networking for Ollama in Docker
When the backend runs inside Docker and needs to connect to Ollama running on your host machine:
- The `docker-compose.yml` configures `OLLAMA_BASE_URL=http://host.docker.internal:11434` and includes `extra_hosts: ["host.docker.internal:host-gateway"]`.
- On Linux hosts, set `OLLAMA_HOST=0.0.0.0:11434` when starting Ollama on the host to allow container connections.

---

## 8. Database Migrations (Alembic)

PostgreSQL is the canonical database. Migrations are managed via Alembic:

```bash
# Check SQL generated by initial migration
alembic -c backend/alembic.ini upgrade head --sql

# Apply migrations to live database
alembic -c backend/alembic.ini upgrade head
```

If PostgreSQL is unreachable, the system logs:
```
[FALLBACK] PostgreSQL unreachable. Operating in local SQLite compatibility mode.
```
and operates seamlessly using `./lenny_growth.db`.

---

## 9. Knowledge Base & Ingestion

The knowledge base contains **2,186 authentic indexed chunks** across **47 real episodes** from `ChatPRD/lennys-podcast-transcripts`.

To ingest additional episodes reproducibly without GitHub API rate limits:
```bash
# Ingest next 15 episodes from shallow clone
python scripts/ingest_transcripts.py --limit 15

# Ingest all available episodes
python scripts/ingest_transcripts.py --all

# Force re-indexing of existing episodes
python scripts/ingest_transcripts.py --force
```

---

## 10. Automated Testing

Run the comprehensive 40-test test suite:
```bash
pytest backend/tests -v
```

Test coverage includes:
1. End-to-end `/api/chat` flow with session persistence and source citations.
2. Deterministic zero-retrieval refusal (bypassing LLM).
3. Below-threshold retrieval refusal (bypassing LLM).
4. Grounded response generation with YouTube timestamp links.
5. Ship 30 for 30 essay word count (~1,250 words) and visual digital architecture.
6. ArtifactSkill generation and HTML sanitization.
7. Artifact database persistence and query via `/api/artifacts/{id}`.
8. Duplicate ingestion prevention and deterministic chunk IDs.
9. Empty vector store graceful handling.
10. Full attack vector security suite (`<script>`, `onclick`, `onload`, `javascript:`, `data:text/html`, SVG handlers, entity encoding, CSS vectors).
11. Provider routing and factory fallback.
12. Agent tool invocation.

### Manual UI Test Plan

With Ollama running and both services started:

1. Open the frontend and confirm the startup/model status is visible.
2. Submit a grounded growth question and confirm an answer includes transcript source cards, speaker/timestamp metadata, and a timed playback link.
3. Submit an unsupported question and confirm the deterministic insufficient-evidence refusal appears without fabricated sources.
4. Request a Ship 30 essay and confirm the essay intent, structured headings, checklist, and source citations.
5. Request an HTML artifact, confirm the split-screen viewer opens, then inspect Preview and Source modes and the download/copy controls.
6. Confirm the responsive chat/artifact tabs work below the desktop breakpoint.

The automated result verified in the current local environment is **40 passed, 0 failed, 26 warnings**. The local run used the SQLite fallback because PostgreSQL was not reachable/authenticated; PostgreSQL runtime success was not claimed.

---

## 11. Security Model

Artifacts generated by LLMs are untrusted HTML/CSS. The system implements strict defense-in-depth:
1. **Server-Side Sanitization** (`backend/app/security/sanitizer.py`):
   - Bleach HTML tag and attribute whitelisting.
   - Beautiful Soup pre-processing stripping `<script>`, `<iframe>`, `<object>`, `<embed>`, `<animate>`, `<set>`.
   - Stripping of all inline `on*` event handlers and entity-encoded protocols (`javascript:`, `data:text/html`).
   - CSS expression, `@import`, and behavioral binding neutralization.
2. **Client-Side Opaque Sandbox** (`frontend/src/components/ArtifactViewer.tsx`):
   - Rendered in an isolated `<iframe>` with `sandbox=""`.
   - Scripts are completely disabled.
   - Origin is treated as an opaque `null` origin, preventing same-origin access to parent window DOM, localStorage, cookies, or authorization tokens.

---

## 12. Troubleshooting

- **Ollama is unavailable:** run `ollama serve`, confirm `ollama list`, and check `OLLAMA_BASE_URL`. `/ready` and the startup diagnostics report the provider error.
- **The configured Ollama model is missing:** run `ollama pull qwen2.5:0.5b` or change `OLLAMA_MODEL` to an installed model. The health check can report available models; generation errors identify the missing model.
- **Ollama generation times out:** the request may still be loading the model or generating. Increase `OLLAMA_TIMEOUT_SECONDS` or use a smaller installed model.
- **Cloud provider is unavailable:** confirm the matching API key is configured, or set `LLM_PROVIDER=ollama` for the local demo. No cloud key is required for local mode.
- **Readiness is degraded:** inspect `/ready` for LLM, database, and vector-store details. An empty vector store can trigger initial ingestion on startup; otherwise run the ingestion command below.
- **PostgreSQL is unreachable:** local startup uses SQLite compatibility mode and logs `[FALLBACK] PostgreSQL unreachable. Operating in local SQLite compatibility mode.` This is the verified local behavior; PostgreSQL remains the canonical deployment architecture.
- **Retrieval returns no evidence:** confirm `data/vector_store/` contains the indexed metadata and vectors, then check the query against the indexed transcript topics. The programmatic guard returns a deterministic refusal for empty or below-threshold retrieval.
- **Frontend cannot reach the backend:** start the backend on port 8000, confirm the frontend origin is included in `CORS_ORIGINS`, and inspect the browser network panel for `/api` errors.

## 13. Extending the System

- **LLM providers:** add or update provider implementations under `backend/app/llm/`, then register selection behavior in `backend/app/llm/factory.py`.
- **Retrieval and ingestion:** inspect `backend/app/retrieval/chunking.py`, `embeddings.py`, `retriever.py`, and `ingestion.py`; refresh the corpus with `scripts/ingest_transcripts.py`.
- **Agent tools and skills:** add canonical tool dispatch or schemas in `backend/app/agents/core.py`; implement focused skills under `backend/app/agents/skills/` and route intents through the existing agent flow.
- **Artifact security:** modify the narrow allowlists and sanitization behavior in `backend/app/security/sanitizer.py`; preserve server sanitization and the client iframe sandbox together.
- **API and frontend behavior:** update the relevant router under `backend/app/api/`, then the matching frontend service/component under `frontend/src/`; extend `backend/tests/` for changed contracts.

## 14. Project Deliverables

- [Product requirements](docs/PRD.md)
- [Design specification](docs/design.md)
- [Architecture documentation](docs/architecture.md)
- [AI-assisted development transcripts](agent-transcripts/)
- [Backend test suite](backend/tests/)
- [This README](README.md)

## 15. Fresh Evaluator Checklist

1. Clone the repository.
2. Create `.env` from `.env.example`.
3. Install backend dependencies: `cd backend` then `pip install -r requirements.txt`.
4. Start Ollama and pull the recommended model: `ollama serve`, then `ollama pull qwen2.5:0.5b`.
5. Start the backend: `python -m uvicorn app.main:app --reload --port 8000`.
6. Install frontend dependencies: `cd frontend` then `npm install`.
7. Start the frontend: `npm run dev`.
8. Open `http://localhost:5173`.
9. Run the tests: from the repository root use `pytest backend/tests -q`, or from `backend` use `python -m pytest -q`.

---

## 16. License
MIT License. Transcripts and guest insights courtesy of [Lenny's Podcast](https://www.lennyspodcast.com/).
