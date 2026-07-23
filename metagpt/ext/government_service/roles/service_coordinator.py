from __future__ import annotations

import uuid
from datetime import datetime

from metagpt.ext.government_service.actions.answer_generate import AnswerGenerateAction
from metagpt.ext.government_service.actions.human_review import HumanReviewAction
from metagpt.ext.government_service.actions.intent_recognize import IntentRecognizeAction
from metagpt.ext.government_service.actions.trace_record import TraceRecordAction
from metagpt.ext.government_service.roles.policy_expert import PolicyExpert
from metagpt.ext.government_service.roles.process_planner import ProcessPlanner
from metagpt.ext.government_service.roles.risk_auditor import RiskAuditor
from metagpt.ext.government_service.schema import ServiceResponse, TraceRecord


class ServiceCoordinator:
    """Coordinate the government service assistant via role chain."""

    def __init__(
        self,
        raw_docs_dir: str | None = None,
        trace_dir: str | None = None,
        knowledge_backend: str = "rag",
    ):
        self.intent_action = IntentRecognizeAction()
        self.policy_expert = PolicyExpert(raw_docs_dir=raw_docs_dir, knowledge_backend=knowledge_backend)
        self.process_planner = ProcessPlanner()
        self.risk_auditor = RiskAuditor()
        self.answer_action = AnswerGenerateAction(use_llm=False)
        self.human_review_action = HumanReviewAction()
        self.trace_action = TraceRecordAction(trace_dir=trace_dir)

    async def run(self, query: str) -> ServiceResponse:
        intent = await self.intent_action.run(query)
        evidences = await self.policy_expert.retrieve(query)
        kb_status = self.policy_expert.last_status

        process_steps = []
        materials = []
        if intent.intent in {"process_plan", "mixed", "qualification_check"}:
            process_steps = await self.process_planner.build_steps(query, evidences)
        if intent.intent in {"material_checklist", "mixed", "qualification_check"}:
            materials = await self.process_planner.build_materials(query, evidences)

        risk_assessment = await self.risk_auditor.assess(query, intent.intent)
        human_review_message = await self.human_review_action.run() if risk_assessment.human_review_required else ""

        direct_answer = await self.answer_action.run(
            query=query,
            intent=intent.intent,
            evidences=evidences,
            materials=materials,
            process_steps=process_steps,
            risk_assessment=risk_assessment,
            human_review_message=human_review_message,
            knowledge_base_backend=kb_status.get("backend", "fallback"),
            knowledge_base_status=kb_status,
        )

        trace_id = self._new_trace_id()
        trace_record = TraceRecord(
            trace_id=trace_id,
            query=query,
            intent=intent.intent,
            retrieved_docs=[e.doc_id for e in evidences],
            actions=[
                self.intent_action.name,
                self.policy_expert.action.name,
                self.process_planner.task_plan_action.name if process_steps else "",
                self.process_planner.material_action.name if materials else "",
                self.risk_auditor.action.name,
                self.answer_action.name,
                self.human_review_action.name if human_review_message else "",
            ],
            risk_level=risk_assessment.risk_level,
            human_review_required=risk_assessment.human_review_required,
            answer=direct_answer,
            timestamp=datetime.now(),
            metadata={
                "backend": kb_status.get("backend", "fallback"),
                "intent_confidence": intent.confidence,
                "knowledge_base_status": kb_status,
            },
        )
        trace_record.actions = [a for a in trace_record.actions if a]
        await self.trace_action.run(trace_record)

        return ServiceResponse(
            direct_answer=direct_answer,
            policy_evidence=evidences,
            process_steps=process_steps,
            materials=materials,
            risk_assessment=risk_assessment,
            human_review_message=human_review_message,
            trace_id=trace_id,
        )

    @staticmethod
    def _new_trace_id() -> str:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"{ts}-{uuid.uuid4().hex[:6]}"

