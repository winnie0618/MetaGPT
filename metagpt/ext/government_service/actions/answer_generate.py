from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence, ProcessStep, RiskAssessment


class AnswerGenerateAction(Action):
    name: str = "AnswerGenerateAction"
    use_llm: bool = False

    async def run(
        self,
        query: str,
        intent: str,
        evidences: list[PolicyEvidence],
        materials: list[MaterialItem],
        process_steps: list[ProcessStep],
        risk_assessment: RiskAssessment,
        human_review_message: str = "",
    ) -> str:
        if not self.use_llm:
            return self._build_template_answer(query, evidences, materials, process_steps, risk_assessment, human_review_message)

        prompt = self._build_prompt(query, intent, evidences, materials, process_steps, risk_assessment, human_review_message)
        return await self._aask(prompt)

    @staticmethod
    def _build_template_answer(
        query: str,
        evidences: list[PolicyEvidence],
        materials: list[MaterialItem],
        process_steps: list[ProcessStep],
        risk_assessment: RiskAssessment,
        human_review_message: str,
    ) -> str:
        _ = query
        lines = ["办理建议：请结合当地办事指南和已检索政策材料办理。"]
        if evidences:
            lines.append("政策依据：")
            for item in evidences:
                lines.append(f"- [{item.title}] {item.snippet}")
        if materials:
            lines.append("材料清单：")
            for item in materials:
                required = "必需" if item.required else "可选"
                lines.append(f"- {item.name}（{required}）：{item.note}")
        if process_steps:
            lines.append("办理步骤：")
            for step in process_steps:
                lines.append(f"{step.step_no}. {step.title}：{step.detail}")
        lines.append(f"风险提示：{risk_assessment.reason}")
        if human_review_message:
            lines.append(f"人工复核：{human_review_message}")
        return "\n".join(lines)

    @staticmethod
    def _build_prompt(
        query: str,
        intent: str,
        evidences: list[PolicyEvidence],
        materials: list[MaterialItem],
        process_steps: list[ProcessStep],
        risk_assessment: RiskAssessment,
        human_review_message: str,
    ) -> str:
        evidence_text = "\n".join(f"- [{e.title}] {e.snippet}" for e in evidences) or "无"
        material_text = "\n".join(f"- {m.name}: {m.note}" for m in materials) or "无"
        step_text = "\n".join(f"- {s.step_no}. {s.title}: {s.detail}" for s in process_steps) or "无"
        return (
            "你是政务服务助手。只能基于给定政策依据回答，不得承诺审批结果，不得编造补贴金额。\n"
            f"问题：{query}\n"
            f"意图：{intent}\n"
            f"政策依据：\n{evidence_text}\n"
            f"材料清单：\n{material_text}\n"
            f"办理步骤：\n{step_text}\n"
            f"风险等级：{risk_assessment.risk_level}\n"
            f"人工复核提示：{human_review_message or '无'}\n"
            "请输出中文结构化回答，包含办理建议、政策依据、材料清单、办理步骤和风险提示。"
        )
