import os
from typing import List, Literal, Optional

import numpy as np

Provider = Literal["local", "openai", "gemini"]


def get_provider() -> Provider:
    return (os.getenv("RAG_PROVIDER", "local").strip().lower() or "local")  # type: ignore


def _chunk(iterable, size: int):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def embed_texts_openai(texts: List[str], model: Optional[str] = None) -> np.ndarray:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    model = model or os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

    vectors: List[List[float]] = []
    # OpenAI embeddings API supports batches; keep conservative batch size
    for batch in _chunk(texts, 100):
        resp = client.embeddings.create(model=model, input=batch)
        # resp.data preserves input order
        vectors.extend([d.embedding for d in resp.data])
    return np.array(vectors, dtype=np.float32)


def embed_texts_gemini(texts: List[str], model: Optional[str] = None) -> np.ndarray:
    import google.generativeai as genai

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    genai.configure(api_key=api_key)
    model = model or os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")

    # Batch embed via embed_content (single) — do small batches
    vectors: List[List[float]] = []
    for batch in _chunk(texts, 32):
        for text in batch:
            res = genai.embed_content(model=model, content=text)
            vectors.append(res["embedding"])  # type: ignore[index]
    return np.array(vectors, dtype=np.float32)


def embed_texts(texts: List[str]) -> np.ndarray:
    provider = get_provider()
    if provider == "openai":
        return embed_texts_openai(texts)
    if provider == "gemini":
        return embed_texts_gemini(texts)
    raise RuntimeError("embed_texts called for provider 'local' — not applicable")
