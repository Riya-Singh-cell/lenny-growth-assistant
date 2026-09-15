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

---

## 3. Key Features

- 🎙️ **Transcript-Grounded Q&A**: Answers complex growth queries using authentic Lenny's Podcast dialogue turns.
- 🛑 **Deterministic RAG Refusal**: Hard programmatic check before LLM generation. When evidence is insufficient, immediately returns refusal with zero LLM calls.
- 🔗 **Timed YouTube Citations**: Every quote provides a link directly to the video timestamp (`&t=Xs`).
- ✍️ **Ship 30 for 30 Essay Skill**: Dedicated multi-stage pipeline producing ~1,250-word publication-ready essays.
- 🎨 **In-App Artifact Viewer**: Split-screen preview for interactive HTML/CSS frameworks and Markdown documents.
- 🛡️ **Opaque HTML Security & Sandboxing**: Server-side Bleach + TinyCSS2 sanitization + client-side sandboxed `<iframe>` (`sandbox=""`), defanging `<script>`, event handlers, SVG attacks, and CSS expression vectors.
- 🔄 **Hot-Swappable LLM Providers**: Toggle between local Ollama (`myphi3:latest`, `llama3.2`) and Cloud Claude/OpenAI on the fly.
- 💾 **PostgreSQL First with SQLite Fallback**: Canonical database with Alembic schema migrations; automatically falls back to local SQLite with structured logging.
- 📱 **Responsive Mobile/Tablet UX**: Collapsible artifact panel and mobile tab switcher preserving full usability on screens under 1024px.
- 🩺 **Startup Diagnostics**: Real-time observability over model reachability, database engine, and vector index chunk counts.

---

## 4. Tech Stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Lucide React, React-Markdown, Remark-GFM.
- **Backend**: Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (Async), Alembic, Bleach, TinyCSS2, BeautifulSoup4.
- **Database**: PostgreSQL 16 with pgvector (Docker) / SQLite with aiosqlite (local zero-config fallback).
- **AI & RAG**: Claude Agent SDK (`claude-agent-sdk`), Ollama local provider (`qwen2.5:0.5b` recommended), SentenceTransformers / hashed embeddings, Numpy cosine similarity.
- **Testing**: Pytest, Pytest-Asyncio, HTTPX TestClient (**38 automated tests passing**).
- **Deployment**: Docker, Docker Compose, Nginx.

---

## 5. Prerequisites

- **Python**: 3.10 or higher.
- **Node.js**: v18 or higher (v20+ recommended).
- **Ollama** (for local offline demo): [https://ollama.com](https://ollama.com)
- *(Optional)* **Docker & Docker Compose** (for PostgreSQL and containerized execution).

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

Run the comprehensive 38-test test suite:
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

## 12. License
MIT License. Transcripts and guest insights courtesy of [Lenny's Podcast](https://www.lennyspodcast.com/).
