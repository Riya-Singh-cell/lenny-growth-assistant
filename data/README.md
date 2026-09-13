# Data Directory - Lenny's Podcast Transcripts

This directory houses the knowledge base for **The Lenny Growth Assistant**.

## Knowledge Base Source

The canonical source of transcripts is:
- **Repository**: [https://github.com/ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts)
- **Episodes**: Over 300 deep-dive interviews with world-class product leaders, growth practitioners, founders, and executives (e.g., Adam Fishman, Elena Verna, Brian Balfour, Sean Ellis, Casey Winters, Julie Zhuo, etc.).

## Directory Layout

- `data/transcripts/`: Raw transcript markdown files downloaded from the repository. Each file contains YAML frontmatter (`guest`, `title`, `youtube_url`, `publish_date`, `keywords`) and speaker-diarized text turns.
- `data/vector_store/`: Persistent indexed embeddings, chunk metadata, and lexical index for fast RAG retrieval.

## Ingestion

To ingest or update the transcripts:

```bash
# Ingest top episodes or all episodes:
python scripts/ingest_transcripts.py --limit 30

# Ingest all available episodes:
python scripts/ingest_transcripts.py --all
```

Metadata preserved for each chunk includes:
- `episode`: Episode identifier/slug
- `title`: Full title of the episode
- `guest`: Name of the featured guest
- `speaker`: Active speaker for that snippet
- `timestamp`: Video timestamp (HH:MM:SS)
- `youtube_url`: Direct link to YouTube with timestamp parameter `&t=Xs`
- `chunk_id`: Unique chunk identifier
- `text`: Diarized content
