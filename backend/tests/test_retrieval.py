import pytest
from app.retrieval.chunking import parse_transcript_markdown, chunk_transcript
from app.retrieval.retriever import get_retriever


SAMPLE_TRANSCRIPT_MD = """---
guest: Test Guest
title: Mastering Product Loops
youtube_url: https://www.youtube.com/watch?v=TEST12345
keywords:
- growth
- retention
---
# Mastering Product Loops
## Transcript
Test Guest (00:01:30):
Product loops are compounding mechanisms where user action generates new users or more usage.
Lenny (00:02:00):
How do you separate virality from true retention loops?
Test Guest (00:02:15):
Virality brings top of funnel, but retention loops are what keep active cohorts returning every week.
"""


def test_parse_transcript_frontmatter_and_turns():
    parsed = parse_transcript_markdown(SAMPLE_TRANSCRIPT_MD, "mastering-product-loops")
    meta = parsed["metadata"]
    turns = parsed["turns"]

    assert meta["guest"] == "Test Guest"
    assert meta["youtube_url"] == "https://www.youtube.com/watch?v=TEST12345"
    assert len(turns) == 3
    assert turns[0].speaker == "Test Guest"
    assert turns[0].timestamp_str == "00:01:30"
    assert turns[0].timestamp_seconds == 90
    assert "compounding mechanisms" in turns[0].text


def test_chunking_preserves_timed_youtube_url():
    parsed = parse_transcript_markdown(SAMPLE_TRANSCRIPT_MD, "mastering-product-loops")
    chunks = chunk_transcript("mastering-product-loops", parsed, target_words=10)

    assert len(chunks) >= 1
    first = chunks[0]
    assert first.title == "Mastering Product Loops"
    assert first.guest == "Test Guest"
    assert first.youtube_timed_url == "https://www.youtube.com/watch?v=TEST12345&t=90s"
    assert "Test Guest (00:01:30)" in first.text


@pytest.mark.asyncio
async def test_retriever_query_and_sources():
    retriever = get_retriever()
    assert retriever.total_chunks > 0

    results = await retriever.retrieve("onboarding experience at Lyft", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert top.title is not None
    assert top.score > 0
    assert top.speaker is not None


@pytest.mark.asyncio
async def test_retriever_empty_query():
    retriever = get_retriever()
    results = await retriever.retrieve("", top_k=3)
    # Empty query should return empty or low confidence results gracefully
    assert isinstance(results, list)
