import json

import pytest

from metagpt.ext.government_service.actions.answer_generate import AnswerGenerateAction
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence, ProcessStep, RiskAssessment


def test_answer_generate_template_mode():
    action = AnswerGenerateAction(use_llm=False)
    resp = action._build_template_answer(
        query="毕业生创业补贴需要哪些材料？",
        evidences=[PolicyEvidence(doc_id="p1", title="政策一", snippet="申请材料包括身份证明", score=1.0)],
        materials=[MaterialItem(name="身份证明", required=True, note="用于核验身份")],
        process_steps=[ProcessStep(step_no=1, title="确认条件", detail="先核验资格")],
        risk_assessment=RiskAssessment(risk_level="low", human_review_required=False, reason="政策解释"),
        human_review_message="",
    )
    assert "办理建议" in resp
    assert "身份证明" in resp
    assert "风险提示" in resp


def test_answer_generate_openai_compatible_client(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "模型生成回答"}}]}).encode("utf-8")

    def fake_urlopen(req, timeout):
        assert req.full_url == "http://127.0.0.1:11434/v1/chat/completions"
        assert timeout == 30
        return FakeResponse()

    monkeypatch.setattr("metagpt.ext.government_service.actions.answer_generate.request.urlopen", fake_urlopen)

    action = AnswerGenerateAction(answer_mode="rag_llm")
    assert action._call_openai_compatible("测试提示词") == "模型生成回答"


@pytest.mark.asyncio
async def test_answer_generate_llm_fallback_when_service_unavailable(monkeypatch):
    def fake_urlopen(req, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr("metagpt.ext.government_service.actions.answer_generate.request.urlopen", fake_urlopen)

    action = AnswerGenerateAction(answer_mode="rag_llm")
    resp = await action.run(
        query="毕业生创业补贴需要哪些材料？",
        intent="material_checklist",
        evidences=[PolicyEvidence(doc_id="p1", title="政策一", snippet="申请材料包括身份证明", score=1.0)],
        materials=[MaterialItem(name="身份证明", required=True, note="用于核验身份")],
        process_steps=[],
        risk_assessment=RiskAssessment(risk_level="low", human_review_required=False, reason="政策解释"),
    )

    assert "办理建议" in resp
    assert "模型生成状态" in resp
