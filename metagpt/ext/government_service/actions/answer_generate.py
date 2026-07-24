from __future__ import annotations

import json
import os
from typing import Literal
from urllib import error, request

from metagpt.actions import Action
from metagpt.ext.government_service.config import (
    DEFAULT_ANSWER_MODE,
    DEFAULT_LLM_BASE_URL,
    DEFAULT_LLM_MODEL,
    DEFAULT_LLM_PROVIDER,
)
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence, ProcessStep, RiskAssessment

AnswerMode = Literal["template", "llm", "rag_llm"]


class AnswerGenerateAction(Action):
    name: str = "AnswerGenerateAction"
    use_llm: bool = False
    answer_mode: AnswerMode = DEFAULT_ANSWER_MODE  # template keeps the system fully offline.
    llm_provider: str = DEFAULT_LLM_PROVIDER
    llm_model: str = DEFAULT_LLM_MODEL
    llm_base_url: str = DEFAULT_LLM_BASE_URL

    async def run(
        self,
        query: str,
        intent: str,
        evidences: list[PolicyEvidence],
        materials: list[MaterialItem],
        process_steps: list[ProcessStep],
        risk_assessment: RiskAssessment,
        human_review_message: str = "",
        knowledge_base_backend: str | None = None,
        knowledge_base_status: dict | None = None,
    ) -> str:
        answer_mode = self._effective_answer_mode()
        if answer_mode == "template":
            return self._build_template_answer(
                query,
                evidences,
                materials,
                process_steps,
                risk_assessment,
                human_review_message,
                knowledge_base_backend,
                knowledge_base_status,
            )

        prompt = self._build_prompt(
            query,
            intent,
            evidences,
            materials,
            process_steps,
            risk_assessment,
            human_review_message,
        )
        try:
            if self.llm_provider == "metagpt":
                return await self._aask(prompt)
            return self._call_openai_compatible(prompt)
        except Exception as exc:
            fallback = self._build_template_answer(
                query,
                evidences,
                materials,
                process_steps,
                risk_assessment,
                human_review_message,
                knowledge_base_backend,
                knowledge_base_status,
            )
            return (
                f"{fallback}\n"
                f"模型生成状态：{answer_mode} 模式调用失败，已回退模板回答；"
                f"原因：{type(exc).__name__}: {exc}"
            )

    def _effective_answer_mode(self) -> AnswerMode:
        if self.answer_mode not in {"template", "llm", "rag_llm"}:
            raise ValueError(f"Unsupported answer_mode: {self.answer_mode}")
        if self.use_llm and self.answer_mode == "template":
            return "rag_llm"
        return self.answer_mode

    @staticmethod
    def _build_template_answer(
        query: str,
        evidences: list[PolicyEvidence],
        materials: list[MaterialItem],
        process_steps: list[ProcessStep],
        risk_assessment: RiskAssessment,
        human_review_message: str,
        knowledge_base_backend: str | None = None,
        knowledge_base_status: dict | None = None,
    ) -> str:
        _ = query
        lines = ["办理建议：请结合当地办事指南和已检索政策材料办理。"]
        if knowledge_base_backend:
            lines.append(f"知识库后端：{knowledge_base_backend}")
        if knowledge_base_status:
            lines.append(f"知识库状态：{knowledge_base_status.get('backend', 'fallback')} | ready={knowledge_base_status.get('ready', False)}")
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
            "你是政务服务助手。请严格基于给定政策依据回答，不得承诺审批结果，不得编造补贴金额、办理时限或资格结论。\n"
            "如果政策依据不足，请明确说明需要咨询经办机构或进入人工复核。\n"
            f"问题：{query}\n"
            f"意图：{intent}\n"
            f"政策依据：\n{evidence_text}\n"
            f"材料清单：\n{material_text}\n"
            f"办理步骤：\n{step_text}\n"
            f"风险等级：{risk_assessment.risk_level}\n"
            f"人工复核提示：{human_review_message or '无'}\n"
            "请输出中文结构化回答，包含办理建议、政策依据、材料清单、办理步骤、风险提示和可追溯说明。"
        )

    def _call_openai_compatible(self, prompt: str) -> str:
        base_url = os.getenv("GOVTRACE_LLM_BASE_URL", self.llm_base_url).rstrip("/")
        api_key = os.getenv("GOVTRACE_LLM_API_KEY", "ollama")
        model = os.getenv("GOVTRACE_LLM_MODEL", self.llm_model)
        timeout = float(os.getenv("GOVTRACE_LLM_TIMEOUT", "30"))
        payload = {
            "model": model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": "你是严谨的政务服务流程助手，回答必须可追溯、可复核、避免越权承诺。",
                },
                {"role": "user", "content": prompt},
            ],
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        http_request = request.Request(
            f"{base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=timeout) as response:
                raw = response.read().decode("utf-8")
        except error.URLError as exc:
            raise RuntimeError(f"LLM service unavailable at {base_url}: {exc}") from exc

        data = json.loads(raw)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response has no choices")
        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        if not content:
            raise RuntimeError("LLM response content is empty")
        return content
