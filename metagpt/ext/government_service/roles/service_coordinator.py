from __future__ import annotations

from metagpt.ext.government_service.schema import ServiceResponse
from metagpt.ext.government_service.workflow import GovServiceWorkflow


class ServiceCoordinator:
    """Coordinate a complete government service response workflow."""

    def __init__(self, workflow: GovServiceWorkflow | None = None):
        self.workflow = workflow or GovServiceWorkflow()

    async def run(self, query: str) -> ServiceResponse:
        return await self.workflow.run(query)
