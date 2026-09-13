# System Architecture Document
# The Lenny Growth Assistant

## 1. System Architecture Overview

The Lenny Growth Assistant is an enterprise-grade AI system designed to ingest, index, and query over 300 deep-dive podcast transcripts from Lenny's Podcast. It enforces strict context grounding, provides direct YouTube video timestamp citations, generates ~1,250-word Ship 30 essays, and renders isolated HTML/Markdown artifacts.

```mermaid
flowchart TD
    subgraph Client [Frontend Layer]
        Browser[React 19 + TypeScript + Vite UI]
        ChatArea[Chat Thread & Composer]
        Viewer[Sandboxed Artifact Viewer Iframe]
        Browser --> ChatArea
        Browser --> Viewer
    end

    subgraph API [FastAPI Backend]
        RouterEndpoint["/api/chat"]
        SessionEndpoint["/api/sessions"]
        ArtifactEndpoint["/api/artifacts"]
        HealthEndpoint["/ready, /health"]
    end

    subgraph AgentLayer [Agent & Skills Engine]
        IntentRouter[Intent Router]
        GrowthAgent[Grounded Growth Assistant]
        Ship30Skill[Ship 30 for 30 Skill ~1,250w]
        ArtifactSkill[Artifact Generation Skill]
        
        IntentRouter -->|GROUNDED_QA| GrowthAgent
        IntentRouter -->|SHIP30_ESSAY| Ship30Skill
        IntentRouter -->|ARTIFACT_GEN| ArtifactSkill
    end

    subgraph RAG [RAG Engine]
        Retriever[Transcript Retriever]
        EmbeddingService[Embedding Service: MiniLM / Ollama]
        VectorStore[(Persistent Vector Store)]
        Retriever --> EmbeddingService
        Retriever --> VectorStore
    end

    subgraph LLM [LLM Provider Abstraction]
        LLMFactory[LLM Factory]
        OllamaProv[Ollama Local Provider]
        CloudProv[Anthropic Claude / OpenAI Provider]
        LLMFactory --> OllamaProv
        LLMFactory --> CloudProv
    end

    subgraph Security [Security Layer]
        Sanitizer[HTML/CSS Sanitizer: Bleach + TinyCSS2]
    end

    subgraph DB [Persistence Layer]
        SqlAlchemy[SQLAlchemy 2.0 Async]
        Postgres[(PostgreSQL / SQLite Fallback)]
        SqlAlchemy --> Postgres
    end

    ChatArea -->|HTTP POST| RouterEndpoint
    RouterEndpoint --> IntentRouter
    
    GrowthAgent --> Retriever
    Ship30Skill --> Retriever
    ArtifactSkill --> Retriever
    
    GrowthAgent --> LLMFactory
    Ship30Skill --> LLMFactory
    ArtifactSkill --> LLMFactory
    
    ArtifactSkill --> Sanitizer
    Sanitizer --> Viewer
    
    RouterEndpoint --> SqlAlchemy
    SessionEndpoint --> SqlAlchemy
```

---

## 2. Component Boundaries & Responsibilities

| Component | Path | Responsibility |
| :--- | :--- | :--- |
| **FastAPI App** | `backend/app/main.py` | Request dispatching, CORS, structured logging, error handling, startup seeding. |
| **API Endpoints** | `backend/app/api/` | REST controllers for sessions, messages, artifacts, health diagnostics. |
| **Intent Router** | `backend/app/agents/router.py` | Classifies incoming intent (`GROUNDED_QA`, `SHIP30_ESSAY`, `ARTIFACT_GEN`). |
| **Growth Agent** | `backend/app/agents/growth_assistant.py` | Enforces transcript grounding, checks confidence threshold, attributes citations. |
| **Ship 30 Skill** | `backend/app/agents/skills/ship30.py` | 3-stage transformation to ~1,250 word essay with 1-3-1 hook and execution checklist. |
| **Artifact Skill** | `backend/app/agents/skills/artifact_gen.py` | Generates standalone HTML/CSS cards and Markdown frameworks. |
| **HTML Sanitizer** | `backend/app/security/sanitizer.py` | Defangs untrusted HTML, strips `<script>` tags, inline handlers, and bad protocols. |
| **LLM Abstraction**| `backend/app/llm/` | Unified provider interface for local Ollama and Cloud Claude/GPT-4o. |
| **RAG Ingestion** | `backend/app/retrieval/` | Parses YAML frontmatter, speaker diarization, chunking, and vector indexing. |
| **Data Models** | `backend/app/db/` | SQLAlchemy models and session-isolated query repositories. |

---

## 3. Database Schema

The persistence layer uses PostgreSQL (with pgvector support in Docker) and automatically falls back to SQLite for zero-friction local execution.

```mermaid
erDiagram
    SESSIONS ||--o{ MESSAGES : "has many"
    SESSIONS ||--o{ ARTIFACTS : "has many"

    SESSIONS {
        string id PK "UUID"
        string title "Conversation Title"
        datetime created_at "Creation timestamp"
        datetime updated_at "Last activity timestamp"
        json user_metadata "Optional client metadata"
    }

    MESSAGES {
        string id PK "UUID"
        string session_id FK "References SESSIONS(id)"
        string role "user | assistant | system"
        text content "Message body"
        json sources "Array of transcript citations"
        string intent "GROUNDED_QA | SHIP30_ESSAY | ARTIFACT_GEN"
        datetime created_at "Creation timestamp"
    }

    ARTIFACTS {
        string id PK "UUID"
        string session_id FK "References SESSIONS(id)"
        string title "Artifact Name"
        string type "markdown | html"
        text content "Raw generated content"
        text sanitized_content "Sanitized safe content"
        datetime created_at "Creation timestamp"
    }
```

### Strict Session Isolation
All database reads and writes in `app/db/repositories.py` explicitly filter queries by `session_id`. Messages and artifacts from Session A are strictly segregated from Session B at the database layer.

---

## 4. Ingestion & Retrieval Flow

```mermaid
sequenceDiagram
    participant CLI as Ingest CLI / Startup Lifespan
    participant GitHub as ChatPRD Transcript Repo
    participant Chunker as Sliding Window Chunker
    participant Embed as Embedding Service
    participant Store as Vector Store

    CLI->>GitHub: Fetch episodes & transcript.md
    GitHub-->>CLI: YAML frontmatter + diarized dialogue turns
    CLI->>Chunker: Parse turns & sliding window (350 words, 1 turn overlap)
    Chunker-->>CLI: Chunks with speaker, timestamp, & YouTube timed link
    CLI->>Embed: Compute 384-dim dense vectors (MiniLM / Ollama)
    Embed-->>CLI: Normalized numpy embeddings
    CLI->>Store: Persist chunks_metadata.json & vectors.npy
```

---

## 5. Security Architecture & Threat Model

Generated HTML from LLMs must be treated as untrusted user input:

```
LLM Output (Raw HTML)
    │
    ▼
[Server-Side Sanitizer]
    ├── Strips <script>, <object>, <embed>, <iframe>
    ├── Strips all on* attributes (onclick, onload, onerror)
    ├── Validates URL schemes (blocks javascript:, data:text/html, vbscript:)
    └── Sanitizes CSS styles via Bleach CSSSanitizer (TinyCSS2)
    │
    ▼
[Database Persistence] (Saved as sanitized_content)
    │
    ▼
[Frontend Sandbox Isolation]
    └── Rendered in <iframe sandbox="allow-same-origin" srcDoc={sanitized_content} />
        (Prevents access to parent window, localStorage, or cookies)
```

---

## 6. Observability & Failure Handling

The application logs every major transaction with request IDs, response durations, and error details:

- **LLM Offline Handling**: When Ollama or Cloud API is unreachable, the system does not crash or throw unhandled 500s. It returns a structured error to the client with exact setup instructions (`ollama serve`).
- **Low Confidence Retrieval Handling**: If cosine similarity is below 0.22, the assistant explicitly reports that evidence is insufficient rather than hallucinating answers.
- **Database Fallback**: If PostgreSQL connection is refused, the database engine transparently spins up local SQLite storage (`lenny_growth.db`).
