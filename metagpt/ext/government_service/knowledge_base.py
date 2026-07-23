from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.ext.government_service.config import RAW_DOCS_DIR
from metagpt.ext.government_service.schema import PolicyEvidence


class SimplePolicyKnowledgeBase:
    """A lightweight policy retriever based on keyword matching."""

    def __init__(self, raw_docs_dir: str | Path | None = None):
        self.raw_docs_dir = Path(raw_docs_dir) if raw_docs_dir else RAW_DOCS_DIR
        self._chunks: list[dict] = []
        self._loaded = False

    def load(self) -> None:
        self._chunks = []
        if not self.raw_docs_dir.exists():
            self._loaded = True
            return

        for file_path in sorted(self.raw_docs_dir.glob("*.txt")):
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            self._chunks.extend(self._split_into_chunks(file_path, text))
        self._loaded = True

    def retrieve(self, query: str, top_k: int = 3) -> list[PolicyEvidence]:
        if not self._loaded:
            self.load()
        if not self._chunks:
            return []

        query_terms = self._tokenize(query)
        scored: list[tuple[float, dict]] = []

        for chunk in self._chunks:
            score = self._score(query_terms=query_terms, title=chunk["title"], content=chunk["snippet"])
            if score > 0:
                scored.append((score, chunk))

        if not scored:
            fallback = self._chunks[:top_k]
            return [
                PolicyEvidence(doc_id=item["doc_id"], title=item["title"], snippet=item["snippet"], score=0.0)
                for item in fallback
            ]

        scored.sort(key=lambda x: x[0], reverse=True)
        top_items = scored[:top_k]
        max_score = max(score for score, _ in top_items) or 1.0

        return [
            PolicyEvidence(
                doc_id=item["doc_id"],
                title=item["title"],
                snippet=item["snippet"],
                score=round(score / max_score, 4),
            )
            for score, item in top_items
        ]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        text = text.lower()
        raw_terms = re.findall(r"[\u4e00-\u9fff]+|[a-z0-9_]+", text)
        terms: list[str] = []
        for term in raw_terms:
            if re.fullmatch(r"[\u4e00-\u9fff]+", term):
                terms.append(term)
                terms.extend(term[i : i + 2] for i in range(len(term) - 1))
            else:
                terms.append(term)
        return list(dict.fromkeys(t for t in terms if len(t) >= 2))

    @staticmethod
    def _score(query_terms: list[str], title: str, content: str) -> float:
        title_lower = title.lower()
        content_lower = content.lower()
        score = 0.0
        for term in query_terms:
            weight = 2.0 if len(term) >= 4 else 1.0
            score += content_lower.count(term) * weight
            score += title_lower.count(term) * weight * 1.5
        return score

    @staticmethod
    def _split_into_chunks(file_path: Path, text: str) -> list[dict]:
        title = file_path.stem
        paragraphs = [seg.strip() for seg in re.split(r"\n{2,}", text) if seg.strip()]
        chunks: list[dict] = []
        if not paragraphs:
            return chunks

        for idx, para in enumerate(paragraphs, start=1):
            snippet = para[:400]
            chunks.append(
                {
                    "doc_id": f"{title}_{idx:03d}",
                    "title": title,
                    "snippet": snippet,
                }
            )
        return chunks


class RAGPolicyKnowledgeBase:
    """Local FAISS retriever with explicit fallback reporting."""

    dimensions: int = 384

    def __init__(self, raw_docs_dir: str | Path | None = None, persist_dir: str | Path | None = None):
        self.raw_docs_dir = Path(raw_docs_dir) if raw_docs_dir else RAW_DOCS_DIR
        self.persist_dir = Path(persist_dir) if persist_dir else (DEFAULT_WORKSPACE_ROOT / "government_service" / "rag")
        self._engine: Any = None
        self._metadata: list[dict] = []
        self._fallback = SimplePolicyKnowledgeBase(self.raw_docs_dir)
        self._ready = False
        self.backend = "fallback"
        self.last_error = ""

    def build_index(self) -> None:
        self.last_error = ""
        self._engine = None
        self._metadata = []
        self._ready = False
        try:
            import faiss

            chunks = self._load_chunks()
            if not chunks:
                self._engine = None
                self._ready = False
                self.backend = "fallback"
                self.last_error = "未发现可用于构建 RAG 索引的文档。"
                return

            self.persist_dir.mkdir(parents=True, exist_ok=True)
            vectors = np.vstack(
                [self._embed_text(f"{chunk['title']}\n{chunk['snippet']}") for chunk in chunks]
            ).astype("float32")
            index = faiss.IndexFlatIP(self.dimensions)
            index.add(vectors)
            faiss.write_index(index, str(self._index_path))
            payload = {"fingerprint": self._docs_fingerprint(), "chunks": chunks}
            self._metadata_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            self._engine = index
            self._metadata = chunks
            self._ready = True
            self.backend = "rag"
            self.last_error = ""
        except Exception as exc:
            self._engine = None
            self._metadata = []
            self._ready = False
            self.backend = "fallback"
            self.last_error = f"RAG 初始化失败: {exc}"

    def _ensure_engine(self) -> None:
        if self._ready and self.backend == "rag" and self._engine is not None:
            return

        self.last_error = ""
        try:
            import faiss

            if self._index_path.exists() and self._metadata_path.exists():
                metadata_payload = json.loads(self._metadata_path.read_text(encoding="utf-8"))
                metadata_fingerprint = ""
                metadata_chunks = metadata_payload
                if isinstance(metadata_payload, dict):
                    metadata_fingerprint = str(metadata_payload.get("fingerprint", ""))
                    metadata_chunks = metadata_payload.get("chunks", [])
                if metadata_fingerprint != self._docs_fingerprint():
                    self.build_index()
                    return
                self._engine = faiss.read_index(str(self._index_path))
                self._metadata = metadata_chunks
                self._ready = True
                self.backend = "rag"
                return

            self.build_index()
        except Exception as exc:
            self._engine = None
            self._metadata = []
            self._ready = False
            self.backend = "fallback"
            self.last_error = f"RAG 初始化失败: {exc}"

    def retrieve(self, query: str, top_k: int = 3) -> list[PolicyEvidence]:
        try:
            self._ensure_engine()
            if self._engine is not None and self.backend == "rag" and self._metadata:
                query_vector = self._embed_text(query).reshape(1, -1).astype("float32")
                scores, indices = self._engine.search(query_vector, min(top_k, len(self._metadata)))
                evidences: list[PolicyEvidence] = []
                for score, index in zip(scores[0], indices[0]):
                    if index < 0:
                        continue
                    item = self._metadata[int(index)]
                    evidences.append(
                        PolicyEvidence(
                            doc_id=item["doc_id"],
                            title=item["title"],
                            snippet=item["snippet"],
                            score=round(float(score), 4),
                        )
                    )
                if evidences:
                    self.last_error = ""
                    return evidences
        except Exception as exc:
            self._engine = None
            self._metadata = []
            self._ready = False
            self.backend = "fallback"
            self.last_error = f"RAG 检索失败: {exc}"

        fallback_evidences = self._fallback.retrieve(query=query, top_k=top_k)
        self.backend = "fallback"
        if not self.last_error:
            self.last_error = "RAG 未启用，使用关键词 fallback 检索。"
        return fallback_evidences

    def status(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "ready": self.backend == "rag" and self._ready,
            "last_error": self.last_error,
            "raw_docs_dir": str(self.raw_docs_dir),
            "persist_dir": str(self.persist_dir),
        }

    @property
    def _index_path(self) -> Path:
        return self.persist_dir / "policy.faiss"

    @property
    def _metadata_path(self) -> Path:
        return self.persist_dir / "policy_metadata.json"

    def _load_chunks(self) -> list[dict]:
        kb = SimplePolicyKnowledgeBase(self.raw_docs_dir)
        kb.load()
        return kb._chunks

    def _docs_fingerprint(self) -> str:
        digest = hashlib.sha256()
        if not self.raw_docs_dir.exists():
            return ""
        for file_path in sorted(self.raw_docs_dir.glob("*.txt")):
            digest.update(file_path.name.encode("utf-8"))
            digest.update(file_path.read_bytes())
        return digest.hexdigest()

    def _embed_text(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype="float32")
        for token in SimplePolicyKnowledgeBase._tokenize(text):
            for feature in self._features(token):
                digest = hashlib.md5(feature.encode("utf-8")).hexdigest()
                vector[int(digest[:8], 16) % self.dimensions] += 1.0
        norm = float(np.linalg.norm(vector))
        if norm > 0:
            vector /= norm
        return vector

    @staticmethod
    def _features(token: str) -> list[str]:
        features = [token]
        if re.fullmatch(r"[\u4e00-\u9fff]+", token) and len(token) > 2:
            features.extend(token[i : i + 2] for i in range(len(token) - 1))
        return features
