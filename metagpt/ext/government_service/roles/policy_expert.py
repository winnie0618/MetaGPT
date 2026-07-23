from __future__ import annotations

from metagpt.ext.government_service.actions.policy_retrieve import PolicyRetrieveAction
from metagpt.ext.government_service.knowledge_base import RAGPolicyKnowledgeBase
from metagpt.ext.government_service.schema import PolicyEvidence


class PolicyExpert:
    def __init__(self, raw_docs_dir: str | None = None):
        self.action = PolicyRetrieveAction(raw_docs_dir=raw_docs_dir)
        self.knowledge_base = RAGPolicyKnowledgeBase(raw_docs_dir=raw_docs_dir)
        self.last_status: dict = {}

    async def retrieve(self, query: str) -> list[PolicyEvidence]:
        evidences = self.knowledge_base.retrieve(query)
        self.last_status = self.knowledge_base.status()
        if evidences:
            return evidences
        return await self.action.run(query)

