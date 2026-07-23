from __future__ import annotations

import re
from pathlib import Path

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
    """RAG / FAISS knowledge base with fallback to SimplePolicyKnowledgeBase."""

    def __init__(self, raw_docs_dir: str | Path | None = None, persist_dir: str | Path | None = None):
        self.raw_docs_dir = Path(raw_docs_dir) if raw_docs_dir else RAW_DOCS_DIR
        self.persist_dir = Path(persist_dir) if persist_dir else (DEFAULT_WORKSPACE_ROOT / "government_service" / "rag")
        self._engine = None
        self._fallback = SimplePolicyKnowledgeBase(self.raw_docs_dir)
        self._ready = False

    def build_index(self) -> None:
        try:
            from metagpt.rag.engines import SimpleEngine
            from metagpt.rag.schema import FAISSIndexConfig, FAISSRetrieverConfig

            files = sorted(self.raw_docs_dir.glob("*.txt")) + sorted(self.raw_docs_dir.glob("*.md"))
            if not files:
                self._engine = None
                self._ready = True
                return

            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._engine = SimpleEngine.from_docs(input_files=[str(f) for f in files], retriever_configs=[FAISSRetrieverConfig()])
            self._engine.persist(self.persist_dir)
            self._ready = True
        except Exception:
            self._engine = None
            self._ready = True

    def _ensure_engine(self):
        if self._ready:
            return
        index_path = self.persist_dir
        try:
            from metagpt.rag.engines import SimpleEngine
            from metagpt.rag.schema import FAISSIndexConfig, FAISSRetrieverConfig

            if index_path.exists() and any(index_path.iterdir()):
                self._engine = SimpleEngine.from_index(
                    index_config=FAISSIndexConfig(persist_path=index_path), retriever_configs=[FAISSRetrieverConfig()]
                )
            else:
                self.build_index()
        except Exception:
            self._engine = None
            self._ready = True

    def retrieve(self, query: str, top_k: int = 3) -> list[PolicyEvidence]:
        try:
            self._ensure_engine()
            if self._engine:
                nodes = self._engine.retrieve(query)
                evidences: list[PolicyEvidence] = []
                for node in nodes[:top_k]:
                    source = node.node
                    metadata = getattr(source, "metadata", {}) or {}
                    doc_id = metadata.get("file_name") or metadata.get("file_path") or metadata.get("doc_id") or "rag_doc"
                    title = metadata.get("file_name") or Path(str(metadata.get("file_path", doc_id))).stem or doc_id
                    snippet = getattr(source, "text", "")[:400]
                    evidences.append(
                        PolicyEvidence(doc_id=str(doc_id), title=str(title), snippet=snippet, score=float(node.score or 0.0))
                    )
                if evidences:
                    return evidences
        except Exception:
            pass
        return self._fallback.retrieve(query=query, top_k=top_k)
