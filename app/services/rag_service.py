import os
import json
from typing import List, Dict, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .rag_providers import get_provider, embed_texts


class RagService:
    """
    Lightweight RAG service using TF-IDF + cosine similarity.
    - Indexes plain-text knowledge from data/knowledge_base (txt, md, json)
    - Provides search(query, k) returning top-k relevant passages
    - Supports ingest_text to append new content and rebuild index
    """

    def __init__(self, corpus_dir: Optional[str] = None):
        self.corpus_dir = corpus_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_base"))
        # Local TF-IDF
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_term = None
        # Remote embeddings via provider (openai/gemini)
        self.provider = get_provider()
        self.embeddings: Optional[np.ndarray] = None  # shape: (N, D)
        self.embedding_cache = os.path.join(self.corpus_dir, ".embeddings.json")
        self.documents: List[Dict] = []  # {id, content, source}
        self._is_built = False

    def _read_corpus(self) -> List[Dict]:
        docs: List[Dict] = []
        if not os.path.isdir(self.corpus_dir):
            return docs

        for root, _, files in os.walk(self.corpus_dir):
            for fname in files:
                path = os.path.join(root, fname)
                ext = os.path.splitext(fname)[1].lower()
                try:
                    if ext in [".txt", ".md"]:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    elif ext == ".json":
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            data = json.load(f)
                        # Try common keys, fallback to str
                        content = data.get("content") or data.get("text") or json.dumps(data, ensure_ascii=False)
                    else:
                        continue

                    content = (content or "").strip()
                    if not content:
                        continue
                    docs.append({
                        "id": path,
                        "content": content,
                        "source": path.replace(self.corpus_dir + os.sep, "")
                    })
                except Exception:
                    # Skip problematic files silently
                    continue
        return docs

    def build_index(self) -> int:
        """Load documents and build retrieval index (TF-IDF or embeddings)."""
        self.documents = self._read_corpus()
        texts = [d["content"] for d in self.documents]

        if self.provider == "local":
            # If no docs, still initialize empty vectorizer to avoid crashes
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                ngram_range=(1, 2),
                max_df=0.9,
                min_df=1,
            )
            if texts:
                self.doc_term = self.vectorizer.fit_transform(texts)
            else:
                self.doc_term = self.vectorizer.fit_transform([""])
            self.embeddings = None
        else:
            # Provider mode: compute and cache embeddings
            if not texts:
                self.embeddings = np.zeros((0, 0), dtype=np.float32)
            else:
                # Try to reuse cache by file id (path)
                cache = self._load_embedding_cache()
                missing_indices = []
                vecs: List[np.ndarray] = []
                for i, doc in enumerate(self.documents):
                    key = doc["id"]
                    cached = cache.get(key)
                    if cached and isinstance(cached, list):
                        vecs.append(np.array(cached, dtype=np.float32))
                    else:
                        vecs.append(None)  # type: ignore
                        missing_indices.append(i)

                # Compute missing via provider
                if missing_indices:
                    to_embed = [self.documents[i]["content"] for i in missing_indices]
                    embedded = embed_texts(to_embed)
                    for j, i in enumerate(missing_indices):
                        vec = embedded[j]
                        vecs[i] = vec  # type: ignore
                        cache[self.documents[i]["id"]] = vec.tolist()
                    self._save_embedding_cache(cache)

                # Stack all
                self.embeddings = np.stack(vecs, axis=0) if vecs else np.zeros((0, 0), dtype=np.float32)
            # Clear TF-IDF references in provider mode
            self.vectorizer = None
            self.doc_term = None

        self._is_built = True
        return len(self.documents)

    def ensure_index(self):
        if not self._is_built:
            self.build_index()

    def ingest_text(self, content: str, source: Optional[str] = None) -> int:
        """Append a new document and rebuild index. Returns new corpus size."""
        content = (content or "").strip()
        if not content:
            return len(self.documents)

        # Persist to disk for durability (optional)
        try:
            os.makedirs(self.corpus_dir, exist_ok=True)
            file_idx = len(self.documents) + 1
            filename = f"ingested_{file_idx:04d}.txt"
            path = os.path.join(self.corpus_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            # Fallback: in-memory only
            pass

        # Rebuild index from disk to keep consistency
        return self.build_index()

    def search(self, query: str, k: int = 3) -> List[Dict]:
        self.ensure_index()
        query = (query or "").strip()
        if not query:
            return []

        results: List[Dict] = []
        if self.provider == "local":
            q_vec = self.vectorizer.transform([query]) if self.vectorizer else None
            if q_vec is None or self.doc_term is None or self.doc_term.shape[0] == 0:
                return []
            sims = cosine_similarity(q_vec, self.doc_term).ravel()
            top_idx = sims.argsort()[::-1][:k]
        else:
            # Provider mode: embed query and cosine with doc embeddings
            if self.embeddings is None or self.embeddings.shape[0] == 0:
                return []
            q_emb = embed_texts([query])[0]
            # Normalize for cosine
            A = self.embeddings
            denom = (np.linalg.norm(A, axis=1) * np.linalg.norm(q_emb) + 1e-12)
            sims = (A @ q_emb) / denom
            top_idx = sims.argsort()[::-1][:k]

        for i in top_idx:
            if i >= len(self.documents):
                continue
            doc = self.documents[i]
            results.append({
                "score": float(sims[i]),
                "content": doc["content"][:800],
                "source": doc["source"],
                "id": doc["id"],
            })
        return results

    # ---- Cache helpers ----
    def _load_embedding_cache(self) -> Dict[str, List[float]]:
        try:
            if os.path.isfile(self.embedding_cache):
                with open(self.embedding_cache, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_embedding_cache(self, data: Dict[str, List[float]]):
        try:
            os.makedirs(self.corpus_dir, exist_ok=True)
            with open(self.embedding_cache, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass


# Singleton instance
rag_service = RagService()
