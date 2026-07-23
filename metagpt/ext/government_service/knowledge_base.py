from __future__ import annotations

import re
from pathlib import Path

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
        return re.findall(r"[\u4e00-\u9fff]{2,}|[a-z0-9_]+", text)

    @staticmethod
    def _score(query_terms: list[str], title: str, content: str) -> float:
        title_lower = title.lower()
        content_lower = content.lower()
        score = 0.0
        for term in query_terms:
            score += content_lower.count(term)
            score += title_lower.count(term) * 1.5
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
