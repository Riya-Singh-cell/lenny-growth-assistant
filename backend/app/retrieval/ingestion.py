import os
import glob
import logging
import asyncio
from typing import List, Optional
import httpx
from app.config import settings
from app.retrieval.chunking import parse_transcript_markdown, chunk_transcript, TranscriptChunk
from app.retrieval.retriever import get_retriever

logger = logging.getLogger("lenny.retrieval.ingestion")

GITHUB_REPO_RAW_BASE = "https://raw.githubusercontent.com/ChatPRD/lennys-podcast-transcripts/main"
GITHUB_API_EPISODES = "https://api.github.com/repos/ChatPRD/lennys-podcast-transcripts/contents/episodes"


async def fetch_episode_list_from_github(limit: Optional[int] = None) -> List[str]:
    """Fetches episode directory slugs from ChatPRD GitHub repository."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(GITHUB_API_EPISODES)
        if res.status_code == 200:
            files = res.json()
            slugs = [f["name"] for f in files if f.get("type") == "dir"]
            if limit:
                slugs = slugs[:limit]
            return slugs
        else:
            logger.error("Failed to query GitHub API: HTTP %d", res.status_code)
            return []


async def fetch_transcript_from_github(episode_slug: str) -> Optional[str]:
    """Downloads transcript.md for an episode directly from GitHub raw content."""
    url = f"{GITHUB_REPO_RAW_BASE}/episodes/{episode_slug}/transcript.md"
    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.get(url)
        if res.status_code == 200:
            return res.text
        logger.warning("Could not fetch transcript for %s (HTTP %d)", episode_slug, res.status_code)
        return None


def load_local_transcript_files(data_dir: str) -> List[tuple[str, str]]:
    """Loads markdown files from local directory if present."""
    results = []
    pattern = os.path.join(data_dir, "**", "*.md")
    for file_path in glob.glob(pattern, recursive=True):
        if "README" in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Use parent folder or file stem as episode slug
                slug = os.path.basename(os.path.dirname(file_path))
                if slug in ("transcripts", "data", ""):
                    slug = os.path.splitext(os.path.basename(file_path))[0]
                results.append((slug, content))
        except Exception as e:
            logger.warning("Error reading file %s: %s", file_path, e)
    return results


async def ingest_transcripts(
    limit: Optional[int] = 15,
    local_dir: Optional[str] = None,
    force_reindex: bool = False
) -> int:
    """
    Ingests and indexes Lenny's Podcast transcripts.
    1. Checks local cache first; if empty, fetches directly from ChatPRD GitHub repository.
    2. Parses frontmatter & speaker-diarized dialogue turns.
    3. Generates chunks with full metadata & YouTube timestamp links.
    4. Computes embeddings and saves to persistent vector store.
    """
    retriever = get_retriever()
    existing_slugs = set(c.episode_slug for c in retriever.chunks) if not force_reindex else set()

    episodes_to_process: List[tuple[str, str]] = []

    # Check local files first
    local_path = local_dir or settings.TRANSCRIPTS_DATA_PATH
    if os.path.exists(local_path):
        local_episodes = load_local_transcript_files(local_path)
        for slug, content in local_episodes:
            if slug not in existing_slugs:
                episodes_to_process.append((slug, content))

    # If we still need more episodes or local is empty, fetch from GitHub
    if len(episodes_to_process) < (limit or 15):
        needed = (limit or 15) - len(episodes_to_process)
        logger.info("Fetching episode catalog from GitHub (up to %d episodes)...", needed)
        try:
            slugs = await fetch_episode_list_from_github(limit=(needed + len(existing_slugs) + 5))
            for slug in slugs:
                if slug in existing_slugs:
                    continue
                content = await fetch_transcript_from_github(slug)
                if content:
                    episodes_to_process.append((slug, content))
                    # Also cache locally for fast reuse
                    os.makedirs(os.path.join(local_path, slug), exist_ok=True)
                    with open(os.path.join(local_path, slug, "transcript.md"), "w", encoding="utf-8") as f:
                        f.write(content)
                if len(episodes_to_process) >= (limit or 15):
                    break
        except Exception as e:
            logger.error("Failed downloading from GitHub: %s", e)

    if not episodes_to_process:
        logger.info("No new episodes to ingest. Vector store has %d chunks.", retriever.total_chunks)
        return retriever.total_chunks

    logger.info("Processing %d episodes into chunks...", len(episodes_to_process))
    all_new_chunks: List[TranscriptChunk] = []

    for slug, content in episodes_to_process:
        parsed = parse_transcript_markdown(content, slug)
        chunks = chunk_transcript(slug, parsed)
        all_new_chunks.extend(chunks)
        logger.info("Episode '%s': generated %d chunks", slug, len(chunks))

    logger.info("Embedding and indexing %d total chunks...", len(all_new_chunks))
    await retriever.add_chunks(all_new_chunks)
    logger.info("Ingestion complete. Total indexed chunks: %d", retriever.total_chunks)
    return retriever.total_chunks
