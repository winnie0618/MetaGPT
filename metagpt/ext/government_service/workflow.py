from __future__ import annotations

from metagpt.ext.government_service.roles.service_coordinator import ServiceCoordinator
from metagpt.ext.government_service.schema import ServiceResponse


class GovServiceWorkflow:
    """Rule-based workflow for government service QA with traceability."""

    def __init__(self, raw_docs_dir: str | None = None, trace_dir: str | None = None):
        self.raw_docs_dir = raw_docs_dir
        self.trace_dir = trace_dir
        self.coordinator = ServiceCoordinator(raw_docs_dir=raw_docs_dir, trace_dir=trace_dir)

    async def run(self, query: str) -> ServiceResponse:
        return await self.coordinator.run(query)
