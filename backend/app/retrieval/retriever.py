import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.config import settings
from app.retrieval.chunking import TranscriptChunk
from app.retrieval.embeddings import EmbeddingService

logger = logging.getLogger("lenny.retrieval.retriever")


class RetrievedChunk(BaseModel):
    chunk_id: str
    episode_slug: str
    title: str
    guest: Optional[str] = None
    speaker: str
    timestamp_str: str
    youtube_url: Optional[str] = None
    youtube_timed_url: Optional[str] = None
    text: str
    score: float


class TranscriptRetriever:
    """
    Modular vector & lexical retriever for Lenny's Podcast transcripts.
    Supports persistent disk storage, cosine vector similarity, and keyword boosting.
    """
    def __init__(self, vector_store_path: Optional[str] = None):
        self.store_dir = vector_store_path or settings.VECTOR_STORE_PATH
        self.embedding_service = EmbeddingService()
        self.chunks: List[TranscriptChunk] = []
        self.vectors: Optional[np.ndarray] = None
        self._load_from_disk()

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)

    def _load_from_disk(self):
        """Loads chunks and pre-computed vectors from store directory if present."""
        meta_file = os.path.join(self.store_dir, "chunks_metadata.json")
        vec_file = os.path.join(self.store_dir, "vectors.npy")

        if os.path.exists(meta_file) and os.path.exists(vec_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    raw_chunks = json.load(f)
                    self.chunks = [TranscriptChunk(**c) for c in raw_chunks]
                self.vectors = np.load(vec_file)
                logger.info("Loaded %d transcript chunks and vectors from %s", len(self.chunks), self.store_dir)
            except Exception as e:
                logger.error("Failed to load vector store from %s: %s", self.store_dir, e)
                self.chunks = []
                self.vectors = None
        else:
            logger.info("No existing vector store found at %s", self.store_dir)

    def save_to_disk(self):
        """Saves current chunks and embeddings to disk."""
        os.makedirs(self.store_dir, exist_ok=True)
        meta_file = os.path.join(self.store_dir, "chunks_metadata.json")
        vec_file = os.path.join(self.store_dir, "vectors.npy")

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump([c.dict() for c in self.chunks], f, indent=2)

        if self.vectors is not None:
            np.save(vec_file, self.vectors)

        logger.info("Successfully persisted %d chunks to %s", len(self.chunks), self.store_dir)

    async def add_chunks(self, new_chunks: List[TranscriptChunk]):
        """Embeds and indexes a list of transcript chunks."""
        if not new_chunks:
            return

        texts = [f"Episode: {c.title}. Guest: {c.guest or 'Lenny'}. Speaker: {c.primary_speaker}.\n{c.text}" for c in new_chunks]
        new_vecs = await self.embedding_service.embed_texts(texts)

        if self.vectors is None or len(self.chunks) == 0:
            self.chunks = new_chunks
            self.vectors = new_vecs
        else:
            self.chunks.extend(new_chunks)
            self.vectors = np.vstack([self.vectors, new_vecs])

        self.save_to_disk()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.10
    ) -> List[RetrievedChunk]:
        """
        Performs semantic vector search + keyword re-ranking.
        Returns top relevant chunks with source metadata.
        """
        if not query or not query.strip():
            return []

        if self.vectors is None or len(self.chunks) == 0:
            logger.warning("Retriever called with empty index.")
            return []

        # 1. Embed query
        query_vec = await self.embedding_service.embed_query(query)

        # 2. Cosine similarity
        scores = np.dot(self.vectors, query_vec)

        # 3. Keyword re-ranking / boosting
        query_words = set(query.lower().split())
        for idx, chunk in enumerate(self.chunks):
            boost = 0.0
            # Guest name match
            if chunk.guest and any(part.lower() in query_words for part in chunk.guest.split()):
                boost += 0.15
            # Title word match
            title_words = set(chunk.title.lower().split())
            common_title_words = query_words.intersection(title_words)
            if common_title_words:
                boost += 0.05 * min(3, len(common_title_words))
            # Keywords match
            for kw in chunk.keywords:
                if kw.lower() in query.lower():
                    boost += 0.08
            scores[idx] += boost

        # 4. Top-K indices
        top_indices = np.argsort(scores)[::-1][:top_k]

        results: List[RetrievedChunk] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score >= min_score:
                c = self.chunks[idx]
                results.append(RetrievedChunk(
                    chunk_id=c.chunk_id,
                    episode_slug=c.episode_slug,
                    title=c.title,
                    guest=c.guest,
                    speaker=c.primary_speaker,
                    timestamp_str=c.timestamp_str,
                    youtube_url=c.youtube_url,
                    youtube_timed_url=c.youtube_timed_url,
                    text=c.text,
                    score=round(score, 4)
                ))

        logger.info("Retrieved %d relevant chunks for query '%s' (top score=%.3f)", len(results), query[:40], results[0].score if results else 0.0)
        return results


# Global singleton instance
_global_retriever: Optional[TranscriptRetriever] = None


def get_retriever() -> TranscriptRetriever:
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = TranscriptRetriever()
    return _global_retriever
