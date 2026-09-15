# Objective

Build the Lenny Growth Assistant take-home application as a grounded, evaluator-friendly full-stack product. The goal was to provide transcript-based growth advice, local execution, generated artifacts, persistence, and security controls in a runnable repository.

# Agent Instruction

The coding agent was directed to implement the application around the existing product requirements and repository structure, keeping the work grounded in Lenny's Podcast transcripts and supporting a local-first demo path. The instruction covered the backend, frontend, RAG pipeline, agent tools, persistence, artifacts, security, and project documentation.

# Agent Outcome

The repository history records the full-stack implementation and a subsequent completion pass. The resulting system includes:

- A FastAPI backend with chat, health, session, and artifact APIs.
- A React/TypeScript/Vite frontend with chat, source display, diagnostics, and an artifact viewer.
- Transcript parsing, speaker/timestamp-preserving chunking, vector storage, embeddings, retrieval, and lexical boosting.
- A unified agent/tool architecture with transcript search, Ship 30 essay generation, and product artifact creation.
- Local Ollama execution plus optional cloud provider paths through the LLM abstraction.
- PostgreSQL-first persistence with Alembic migrations and a local SQLite fallback.
- Server-side HTML/CSS sanitization and a client-side opaque iframe sandbox for artifacts.
- README, PRD, architecture, design, Docker, and ingestion documentation.

The implementation was reviewed as a local-first system: an Anthropic key is optional when using the default Ollama path.

# Verification

The implementation commits contain the backend, frontend, tests, data/index artifacts, Docker configuration, and documentation. The test suite covers API flows, persistence, routing, retrieval, refusal behavior, skills, and security. Later verification confirmed the completed application with 40 passing backend tests and a successful frontend production build.

# Failure / Correction

The initial implementation required follow-up corrections during development rather than being treated as complete on first pass. Those corrections are documented separately in the retrieval and CSS sanitizer transcripts. Human review kept the changes focused on observed failures and checked that unrelated behavior was not changed.
