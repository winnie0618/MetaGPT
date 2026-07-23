from __future__ import annotations

from metagpt.ext.government_service.actions.policy_retrieve import PolicyRetrieveAction
from metagpt.ext.government_service.knowledge_base import RAGPolicyKnowledgeBase, SimplePolicyKnowledgeBase
from metagpt.ext.government_service.schema import PolicyEvidence


class PolicyExpert:
    def __init__(self, raw_docs_dir: str | None = None, knowledge_backend: str = "rag"):
        if knowledge_backend not in {"keyword", "rag"}:
            raise ValueError(f"Unsupported knowledge_backend: {knowledge_backend}")
        self.action = PolicyRetrieveAction(raw_docs_dir=raw_docs_dir)
        self.knowledge_backend = knowledge_backend
        if knowledge_backend == "keyword":
            self.knowledge_base = SimplePolicyKnowledgeBase(raw_docs_dir=raw_docs_dir)
        else:
            self.knowledge_base = RAGPolicyKnowledgeBase(raw_docs_dir=raw_docs_dir)
        self.last_status: dict = {}

    async def retrieve(self, query: str) -> list[PolicyEvidence]:
        evidences = self.knowledge_base.retrieve(query)
        self.last_status = self._status()
        if evidences:
            return evidences
        return await self.action.run(query)

    def _status(self) -> dict:
        if hasattr(self.knowledge_base, "status"):
            return self.knowledge_base.status()
        return {
            "backend": "keyword",
            "ready": True,
            "last_error": "",
            "raw_docs_dir": str(self.knowledge_base.raw_docs_dir),
            "persist_dir": "",
        }

