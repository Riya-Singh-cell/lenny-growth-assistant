import os
import glob
import logging
import subprocess
from typing import List, Optional, Tuple
from app.config import settings
from app.retrieval.chunking import parse_transcript_markdown, chunk_transcript, TranscriptChunk
from app.retrieval.retriever import get_retriever

logger = logging.getLogger("lenny.retrieval.ingestion")

REPO_URL = "https://github.com/ChatPRD/lennys-podcast-transcripts.git"


def ensure_transcripts_cloned(target_raw_dir: str = "data/transcripts_raw") -> bool:
    """
    Ensures a local shallow clone of the ChatPRD repository exists.
    Eliminates unauthenticated GitHub API rate limits (60 reqs/hr).
    """
    if os.path.exists(os.path.join(target_raw_dir, "episodes")):
        return True

    logger.info("Shallow cloning ChatPRD/lennys-podcast-transcripts into %s...", target_raw_dir)
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", REPO_URL, target_raw_dir],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Successfully cloned transcript repository.")
        return True
    except Exception as e:
        logger.warning("Git clone failed (%s). Continuing with existing local files.", e)
        return False


def load_local_transcript_files(data_dir: str) -> List[Tuple[str, str]]:
    """Loads all transcript.md files from a given root directory."""
    results = []
    pattern = os.path.join(data_dir, "**", "*.md")
    for file_path in glob.glob(pattern, recursive=True):
        if "README" in file_path or "CLAUDE" in file_path:
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                slug = os.path.basename(os.path.dirname(file_path))
                if slug in ("transcripts", "data", "", "transcripts_raw"):
                    slug = os.path.splitext(os.path.basename(file_path))[0]
                results.append((slug, content))
        except Exception as e:
            logger.warning("Error reading transcript file %s: %s", file_path, e)
    return results


async def ingest_transcripts(
    limit: Optional[int] = 15,
    local_dir: Optional[str] = None,
    force_reindex: bool = False
) -> int:
    """
    Ingests and indexes Lenny's Podcast transcripts into the vector store.
    1. Reads from curated data/transcripts/ directory.
    2. If additional episodes are requested, pulls from data/transcripts_raw/ without API rate limits.
    3. Prevents duplicate chunking and duplicate indexing.
    4. Reports progress cleanly.
    """
    retriever = get_retriever()
    existing_slugs = set(c.episode_slug for c in retriever.chunks) if not force_reindex else set()

    episodes_to_process: List[Tuple[str, str]] = []

    # 1. Load curated local files
    curated_path = local_dir or settings.TRANSCRIPTS_DATA_PATH
    if os.path.exists(curated_path):
        curated_episodes = load_local_transcript_files(curated_path)
        for slug, content in curated_episodes:
            if slug not in existing_slugs and slug not in [s for s, _ in episodes_to_process]:
                episodes_to_process.append((slug, content))

    # 2. If more episodes requested, check raw clone directory
    max_target = limit if limit is not None else 9999
    if len(episodes_to_process) < max_target:
        raw_dir = "data/transcripts_raw/episodes"
        if not os.path.exists(raw_dir):
            ensure_transcripts_cloned("data/transcripts_raw")

        if os.path.exists(raw_dir):
            for entry in os.listdir(raw_dir):
                if entry in existing_slugs or entry in [s for s, _ in episodes_to_process]:
                    continue
                file_path = os.path.join(raw_dir, entry, "transcript.md")
                if os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            episodes_to_process.append((entry, f.read()))
                    except Exception as e:
                        logger.warning("Error reading %s: %s", file_path, e)
                if len(episodes_to_process) >= max_target:
                    break

    if not episodes_to_process:
        logger.info("All requested episodes are already indexed. Current vector store count: %d chunks.", retriever.total_chunks)
        return retriever.total_chunks

    logger.info("Ingesting %d new episodes into vector store...", len(episodes_to_process))
    all_new_chunks: List[TranscriptChunk] = []

    for idx, (slug, content) in enumerate(episodes_to_process, 1):
        parsed = parse_transcript_markdown(content, slug)
        chunks = chunk_transcript(slug, parsed)
        all_new_chunks.extend(chunks)
        logger.info("[%d/%d] Ingested '%s': generated %d chunks", idx, len(episodes_to_process), slug, len(chunks))

    logger.info("Computing embeddings and indexing %d total chunks...", len(all_new_chunks))
    await retriever.add_chunks(all_new_chunks)
    logger.info("Ingestion complete. Total indexed chunks in knowledge base: %d", retriever.total_chunks)
    return retriever.total_chunks
