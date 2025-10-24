import os
import json
from typing import List, Dict, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class RagService:
    """
    Lightweight RAG service using TF-IDF + cosine similarity.
    - Indexes plain-text knowledge from data/knowledge_base (txt, md, json)
    - Provides search(query, k) returning top-k relevant passages
    - Supports ingest_text to append new content and rebuild index
    """

    def __init__(self, corpus_dir: Optional[str] = None):
        self.corpus_dir = corpus_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_base"))
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.doc_term = None
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
        """Load documents from corpus_dir and build TF-IDF index."""
        self.documents = self._read_corpus()
        texts = [d["content"] for d in self.documents]

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
            # Fit on a dummy document to keep pipeline consistent
            self.doc_term = self.vectorizer.fit_transform([""])

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

        q_vec = self.vectorizer.transform([query]) if self.vectorizer else None
        if q_vec is None or self.doc_term is None or self.doc_term.shape[0] == 0:
            return []

        sims = cosine_similarity(q_vec, self.doc_term).ravel()
        if sims.size == 0:
            return []

        top_idx = sims.argsort()[::-1][:k]
        results: List[Dict] = []
        for i in top_idx:
            # Guard for dummy vector
            if i >= len(self.documents):
                continue
            doc = self.documents[i]
            results.append({
                "score": float(sims[i]),
                "content": doc["content"][:800],  # return snippet
                "source": doc["source"],
                "id": doc["id"],
            })
        return results


# Singleton instance
rag_service = RagService()
