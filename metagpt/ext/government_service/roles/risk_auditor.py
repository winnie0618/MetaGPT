from __future__ import annotations

from metagpt.ext.government_service.actions.risk_assess import RiskAssessAction
from metagpt.ext.government_service.schema import IntentType, RiskAssessment


class RiskAuditor:
    def __init__(self):
        self.action = RiskAssessAction()

    async def assess(self, query: str, intent: IntentType) -> RiskAssessment:
        return await self.action.run(query=query, intent=intent)
