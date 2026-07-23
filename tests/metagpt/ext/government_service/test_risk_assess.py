import pytest

from metagpt.ext.government_service.actions.risk_assess import RiskAssessAction


@pytest.mark.asyncio
async def test_risk_assess_high():
    action = RiskAssessAction()
    result = await action.run("这个补贴最终能批多少钱？", intent="high_risk_decision")
    assert result.risk_level == "high"
    assert result.human_review_required is True


@pytest.mark.asyncio
async def test_risk_assess_medium():
    action = RiskAssessAction()
    result = await action.run("我这个条件是否符合申请资格？", intent="qualification_check")
    assert result.risk_level == "medium"
    assert result.human_review_required is False


@pytest.mark.asyncio
async def test_risk_assess_low():
    action = RiskAssessAction()
    result = await action.run("办理地点和材料清单是什么？", intent="material_checklist")
    assert result.risk_level == "low"
