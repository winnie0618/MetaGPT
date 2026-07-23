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
