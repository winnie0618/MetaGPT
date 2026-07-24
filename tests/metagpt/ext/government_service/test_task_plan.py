import pytest

from metagpt.ext.government_service.actions.task_plan import TaskPlanAction
from metagpt.ext.government_service.schema import PolicyEvidence
from metagpt.ext.government_service.workflow import GovServiceWorkflow


@pytest.mark.asyncio
async def test_task_plan_uses_query_process_synonyms():
    action = TaskPlanAction()
    steps = await action.run("线上提交后多久能知道审核结果？", evidences=[])
    titles = [step.title for step in steps]

    assert "提交申请" in titles
    assert "受理" in titles
    assert "审核" in titles


@pytest.mark.asyncio
async def test_task_plan_extracts_correction_and_review_steps():
    action = TaskPlanAction()
    steps = await action.run(
        "材料被退回后怎么申诉复核？",
        evidences=[PolicyEvidence(doc_id="p1", title="补正说明", snippet="材料不完整时按通知补正材料。", score=1.0)],
    )
    titles = [step.title for step in steps]

    assert "补正材料" in titles
    assert "提交申请" in titles
    assert "审核" in titles
    assert "人工复核" in titles


@pytest.mark.asyncio
async def test_workflow_builds_steps_for_high_risk_process_query(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("审核通过后可进入公示，公示无异议后按规定发放。", encoding="utf-8")

    workflow = GovServiceWorkflow(raw_docs_dir=str(raw_dir), trace_dir=str(tmp_path / "traces"), knowledge_backend="keyword")
    response = await workflow.run("是否可以保证我进入公示名单并发放补贴？")
    titles = [step.title for step in response.process_steps]

    assert response.risk_assessment.risk_level == "high"
    assert "公示" in titles
    assert "发放" in titles
