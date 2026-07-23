from __future__ import annotations

from pathlib import Path

from metagpt.actions import Action
from metagpt.ext.government_service.config import DEFAULT_TOP_K
from metagpt.ext.government_service.knowledge_base import SimplePolicyKnowledgeBase
from metagpt.ext.government_service.schema import PolicyEvidence


class PolicyRetrieveAction(Action):
    name: str = "PolicyRetrieveAction"
    top_k: int = DEFAULT_TOP_K
    raw_docs_dir: str | None = None

    def _build_kb(self) -> SimplePolicyKnowledgeBase:
        return SimplePolicyKnowledgeBase(Path(self.raw_docs_dir) if self.raw_docs_dir else None)

    async def run(self, query: str, top_k: int | None = None) -> list[PolicyEvidence]:
        kb = self._build_kb()
        return kb.retrieve(query=query, top_k=top_k or self.top_k)
