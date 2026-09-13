import logging
import numpy as np
from typing import List, Union
import httpx
from app.config import settings

logger = logging.getLogger("lenny.retrieval.embeddings")

_st_model = None


def get_sentence_transformer_model():
    global _st_model
    if _st_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = settings.EMBEDDING_MODEL
            logger.info("Loading SentenceTransformer embedding model: %s", model_name)
            _st_model = SentenceTransformer(model_name)
        except Exception as e:
            logger.warning("Could not load SentenceTransformer (%s). Falling back to hash embeddings: %s", settings.EMBEDDING_MODEL, e)
            _st_model = None
    return _st_model


class EmbeddingService:
    def __init__(self):
        self.provider = settings.EMBEDDING_PROVIDER.lower().strip()
        self.model_name = settings.EMBEDDING_MODEL
        self.ollama_base_url = settings.OLLAMA_BASE_URL

    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embeds a list of strings into normalized float32 numpy arrays.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        if self.provider == "ollama":
            return await self._embed_ollama(texts)
        else:
            return self._embed_local(texts)

    async def embed_query(self, query: str) -> np.ndarray:
        """
        Embeds a single query string.
        """
        res = await self.embed_texts([query])
        return res[0]

    def _embed_local(self, texts: List[str]) -> np.ndarray:
        st_model = get_sentence_transformer_model()
        if st_model is not None:
            embeddings = st_model.encode(
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            return np.array(embeddings, dtype=np.float32)
        else:
            return self._embed_fallback(texts)

    async def _embed_ollama(self, texts: List[str]) -> np.ndarray:
        embeddings = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                try:
                    res = await client.post(
                        f"{self.ollama_base_url}/api/embeddings",
                        json={"model": self.model_name, "prompt": text}
                    )
                    if res.status_code == 200:
                        vec = res.json().get("embedding", [])
                        embeddings.append(vec)
                    else:
                        embeddings.append(self._hash_vector(text))
                except Exception:
                    embeddings.append(self._hash_vector(text))

        arr = np.array(embeddings, dtype=np.float32)
        # Normalize
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        return arr / norms

    def _embed_fallback(self, texts: List[str]) -> np.ndarray:
        """Fast deterministic hashed feature vector for zero-dependency test/offline execution."""
        arr = np.array([self._hash_vector(t) for t in texts], dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        return arr / norms

    def _hash_vector(self, text: str, dim: int = 384) -> np.ndarray:
        import hashlib
        vec = np.zeros(dim, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
