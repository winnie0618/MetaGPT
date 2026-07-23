from __future__ import annotations

import uuid
from datetime import datetime

from metagpt.ext.government_service.actions import (
    HumanReviewAction,
    IntentRecognizeAction,
    MaterialChecklistAction,
    PolicyRetrieveAction,
    RiskAssessAction,
    TaskPlanAction,
    TraceRecordAction,
)
from metagpt.ext.government_service.schema import ServiceResponse, TraceRecord


class GovServiceWorkflow:
    """Rule-based workflow for government service QA with traceability."""

    def __init__(self, raw_docs_dir: str | None = None, trace_dir: str | None = None):
        self.intent_action = IntentRecognizeAction()
        self.policy_action = PolicyRetrieveAction(raw_docs_dir=raw_docs_dir)
        self.task_plan_action = TaskPlanAction()
        self.material_action = MaterialChecklistAction()
        self.risk_action = RiskAssessAction()
        self.human_review_action = HumanReviewAction()
        self.trace_action = TraceRecordAction(trace_dir=trace_dir)

    async def run(self, query: str) -> ServiceResponse:
        intent_result = await self.intent_action.run(query)
        evidences = await self.policy_action.run(query)

        process_steps = []
        materials = []
        if intent_result.intent in {"process_plan", "mixed", "qualification_check"}:
            process_steps = await self.task_plan_action.run(query, evidences)
        if intent_result.intent in {"material_checklist", "mixed", "qualification_check"}:
            materials = await self.material_action.run(query, evidences)

        risk_assessment = await self.risk_action.run(query=query, intent=intent_result.intent)
        human_review_message = ""
        if risk_assessment.human_review_required:
            human_review_message = await self.human_review_action.run()

        direct_answer = self._build_answer(
            query=query,
            evidences=evidences,
            materials=materials,
            process_steps=process_steps,
            human_review_message=human_review_message,
        )

        trace_id = self._new_trace_id()
        trace_record = TraceRecord(
            trace_id=trace_id,
            query=query,
            intent=intent_result.intent,
            retrieved_docs=[e.doc_id for e in evidences],
            actions=[
                self.intent_action.name,
                self.policy_action.name,
                self.task_plan_action.name if process_steps else "",
                self.material_action.name if materials else "",
                self.risk_action.name,
                self.human_review_action.name if human_review_message else "",
            ],
            risk_level=risk_assessment.risk_level,
            human_review_required=risk_assessment.human_review_required,
            answer=direct_answer,
            timestamp=datetime.now(),
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

    @staticmethod
    def _build_answer(query: str, evidences, materials, process_steps, human_review_message: str) -> str:
        _ = query
        lines = ["以下是基于现有政策材料给出的办理建议："]
        if evidences:
            lines.append(f"- 已检索到 {len(evidences)} 条政策依据。")
        if materials:
            lines.append("- 可先准备身份证明、毕业证书和就业/创业相关证明。")
        if process_steps:
            lines.append("- 建议按‘条件核验→材料准备→提交申请→等待审核’流程办理。")
        if not (materials or process_steps):
            lines.append("- 当前问题以政策解释为主，建议结合当地办事指南进一步核验。")
        if human_review_message:
            lines.append(f"- {human_review_message}")
        return "\n".join(lines)
