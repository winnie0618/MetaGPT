from __future__ import annotations

from metagpt.ext.government_service.roles.service_coordinator import ServiceCoordinator
from metagpt.ext.government_service.schema import ServiceResponse


class GovServiceWorkflow:
    """Rule-based workflow for government service QA with traceability."""

    def __init__(
        self,
        raw_docs_dir: str | None = None,
        trace_dir: str | None = None,
        knowledge_backend: str = "rag",
        enable_process_planner: bool = True,
        enable_risk_auditor: bool = True,
        enable_trace_record: bool = True,
    ):
        self.raw_docs_dir = raw_docs_dir
        self.trace_dir = trace_dir
        self.knowledge_backend = knowledge_backend
        self.enable_process_planner = enable_process_planner
        self.enable_risk_auditor = enable_risk_auditor
        self.enable_trace_record = enable_trace_record
        self.coordinator = ServiceCoordinator(
            raw_docs_dir=raw_docs_dir,
            trace_dir=trace_dir,
            knowledge_backend=knowledge_backend,
            enable_process_planner=enable_process_planner,
            enable_risk_auditor=enable_risk_auditor,
            enable_trace_record=enable_trace_record,
        )

    async def run(self, query: str) -> ServiceResponse:
        return await self.coordinator.run(query)
