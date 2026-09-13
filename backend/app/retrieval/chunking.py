import re
import yaml
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("lenny.retrieval.chunking")


class TranscriptTurn(BaseModel):
    speaker: str
    timestamp_str: str
    timestamp_seconds: int
    text: str


class TranscriptChunk(BaseModel):
    chunk_id: str
    episode_slug: str
    title: str
    guest: Optional[str] = None
    speakers: List[str]
    primary_speaker: str
    timestamp_str: str
    timestamp_seconds: int
    youtube_url: Optional[str] = None
    youtube_timed_url: Optional[str] = None
    publish_date: Optional[str] = None
    keywords: List[str] = []
    text: str
    char_count: int


def parse_timestamp_to_seconds(ts_str: str) -> int:
    """Converts (HH:MM:SS) or (MM:SS) to integer seconds."""
    parts = ts_str.strip("()").split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 1:
        return int(parts[0])
    return 0


def parse_transcript_markdown(content: str, episode_slug: str) -> Dict[str, Any]:
    """
    Extracts YAML frontmatter and dialog turns from a Lenny Podcast transcript.
    """
    metadata: Dict[str, Any] = {}
    body = content

    # 1. Parse YAML frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1]) or {}
                body = parts[2]
            except Exception as e:
                logger.warning("Could not parse YAML frontmatter for %s: %s", episode_slug, e)

    # 2. Parse turns: "Speaker Name (HH:MM:SS):"
    turn_pattern = re.compile(
        r'^(?P<speaker>[A-Za-z0-9\s\.\'\-&]+?)\s*\((?P<timestamp>[\d]{1,2}:[\d]{2}(?::[\d]{2})?)\):\s*$',
        re.MULTILINE
    )

    turns: List[TranscriptTurn] = []
    lines = body.splitlines()
    current_speaker = None
    current_ts = "00:00:00"
    current_text_lines = []

    for line in lines:
        match = turn_pattern.match(line.strip())
        if match:
            # Commit previous turn if any
            if current_speaker and current_text_lines:
                full_turn_text = " ".join(current_text_lines).strip()
                if full_turn_text:
                    turns.append(TranscriptTurn(
                        speaker=current_speaker,
                        timestamp_str=current_ts,
                        timestamp_seconds=parse_timestamp_to_seconds(current_ts),
                        text=full_turn_text
                    ))
            current_speaker = match.group("speaker").strip()
            current_ts = match.group("timestamp").strip()
            current_text_lines = []
        else:
            stripped = line.strip()
            # Ignore markdown headings in body
            if stripped and not stripped.startswith("#"):
                current_text_lines.append(stripped)

    # Commit last turn
    if current_speaker and current_text_lines:
        full_turn_text = " ".join(current_text_lines).strip()
        if full_turn_text:
            turns.append(TranscriptTurn(
                speaker=current_speaker,
                timestamp_str=current_ts,
                timestamp_seconds=parse_timestamp_to_seconds(current_ts),
                text=full_turn_text
            ))

    return {
        "metadata": metadata,
        "turns": turns,
        "raw_body_fallback": body if not turns else None
    }


def chunk_transcript(
    episode_slug: str,
    parsed_data: Dict[str, Any],
    target_words: int = 350,
    overlap_turns: int = 1
) -> List[TranscriptChunk]:
    """
    Intelligently chunks dialogue turns using a sliding semantic window.
    Preserves speaker diarization, timestamps, and direct YouTube video links.
    """
    metadata = parsed_data.get("metadata", {})
    turns: List[TranscriptTurn] = parsed_data.get("turns", [])
    title = metadata.get("title", episode_slug.replace("-", " ").title())
    guest = metadata.get("guest", "")
    youtube_base = metadata.get("youtube_url", "")
    video_id = metadata.get("video_id", "")
    publish_date = str(metadata.get("publish_date", ""))
    keywords = metadata.get("keywords", []) or []

    chunks: List[TranscriptChunk] = []

    if not turns:
        # Fallback if transcript has no speaker timestamps: chunk by paragraphs
        fallback_text = parsed_data.get("raw_body_fallback", "")
        paragraphs = [p.strip() for p in fallback_text.split("\n\n") if p.strip()]
        cur_para_chunk = []
        cur_word_count = 0
        chunk_idx = 0
        for para in paragraphs:
            cur_para_chunk.append(para)
            cur_word_count += len(para.split())
            if cur_word_count >= target_words:
                text_block = "\n\n".join(cur_para_chunk)
                chunks.append(TranscriptChunk(
                    chunk_id=f"{episode_slug}#chunk-{chunk_idx}",
                    episode_slug=episode_slug,
                    title=title,
                    guest=guest,
                    speakers=[guest] if guest else ["Lenny"],
                    primary_speaker=guest or "Lenny",
                    timestamp_str="00:00:00",
                    timestamp_seconds=0,
                    youtube_url=youtube_base,
                    youtube_timed_url=youtube_base,
                    publish_date=publish_date,
                    keywords=keywords,
                    text=text_block,
                    char_count=len(text_block)
                ))
                chunk_idx += 1
                cur_para_chunk = []
                cur_word_count = 0
        return chunks

    i = 0
    chunk_index = 0
    total_turns = len(turns)

    while i < total_turns:
        window_turns: List[TranscriptTurn] = []
        accumulated_words = 0
        speakers_in_chunk = set()
        primary_speaker = turns[i].speaker
        start_ts_str = turns[i].timestamp_str
        start_ts_sec = turns[i].timestamp_seconds

        j = i
        while j < total_turns:
            turn = turns[j]
            window_turns.append(turn)
            speakers_in_chunk.add(turn.speaker)
            accumulated_words += len(turn.text.split())
            j += 1
            if accumulated_words >= target_words and len(window_turns) >= 2:
                break

        # Assemble chunk text with speaker headers
        formatted_turn_texts = [
            f"{t.speaker} ({t.timestamp_str}): {t.text}"
            for t in window_turns
        ]
        chunk_text = "\n".join(formatted_turn_texts)

        # Build timed YouTube URL
        timed_url = youtube_base
        if youtube_base and start_ts_sec > 0:
            sep = "&" if "?" in youtube_base else "?"
            timed_url = f"{youtube_base}{sep}t={start_ts_sec}s"

        chunk_obj = TranscriptChunk(
            chunk_id=f"{episode_slug}#chunk-{chunk_index}",
            episode_slug=episode_slug,
            title=title,
            guest=guest,
            speakers=list(speakers_in_chunk),
            primary_speaker=primary_speaker,
            timestamp_str=start_ts_str,
            timestamp_seconds=start_ts_sec,
            youtube_url=youtube_base,
            youtube_timed_url=timed_url,
            publish_date=publish_date,
            keywords=keywords,
            text=chunk_text,
            char_count=len(chunk_text)
        )
        chunks.append(chunk_obj)
        chunk_index += 1

        # Advance window with overlap
        step = max(1, len(window_turns) - overlap_turns)
        i += step

    logger.debug("Produced %d chunks for episode '%s'", len(chunks), episode_slug)
    return chunks
