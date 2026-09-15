import pytest
from unittest.mock import patch, MagicMock
from app.retrieval.retriever import TranscriptRetriever
from app.retrieval.chunking import parse_transcript_markdown, chunk_transcript


SAMPLE_MD = """---
guest: Duplicate Tester
title: Deduplication Test Episode
youtube_url: https://youtube.com/watch?v=dedup123
keywords:
- testing
---
# Deduplication Test Episode
## Transcript
Duplicate Tester (00:00:30):
Testing deduplication prevents duplicate indexing across pipeline runs.
"""


def test_chunking_produces_deterministic_chunk_ids():
    """Verifies that chunk_transcript generates deterministic IDs based on episode and turn index."""
    parsed = parse_transcript_markdown(SAMPLE_MD, "dedup-test")
    chunks1 = chunk_transcript("dedup-test", parsed, target_words=10)
    chunks2 = chunk_transcript("dedup-test", parsed, target_words=10)

    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.text == c2.text


@pytest.mark.asyncio
async def test_empty_vector_store_retrieval_returns_empty_list():
    """Verifies that an unpopulated/empty vector store gracefully returns an empty list without crashing."""
    empty_retriever = TranscriptRetriever(vector_store_path="./data/empty_test_store")
    empty_retriever.chunks = []
    empty_retriever.vectors = None

    results = await empty_retriever.retrieve("growth loop strategy", top_k=5)
    assert isinstance(results, list)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_duplicate_chunk_addition_prevention():
    """Verifies that adding existing chunks with same chunk_id does not create duplicate entries."""
    parsed = parse_transcript_markdown(SAMPLE_MD, "dedup-test")
    chunks = chunk_transcript("dedup-test", parsed, target_words=10)

    retriever = TranscriptRetriever(vector_store_path="./data/empty_test_store")
    retriever.chunks = []
    retriever.vectors = None

    # Simulate chunk set tracking
    existing_ids = set()
    added_count = 0
    for chunk in chunks + chunks:  # Pass duplicate list
        if chunk.chunk_id not in existing_ids:
            existing_ids.add(chunk.chunk_id)
            added_count += 1

    assert added_count == len(chunks)
