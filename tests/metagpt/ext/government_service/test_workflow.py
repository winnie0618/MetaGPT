import pytest

from metagpt.ext.government_service.workflow import GovServiceWorkflow


@pytest.mark.asyncio
async def test_workflow_returns_service_response(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text(
        "毕业生创业补贴可在线申请，需身份证明、毕业证书、创业证明。", encoding="utf-8"
    )

    trace_dir = tmp_path / "traces"
    workflow = GovServiceWorkflow(raw_docs_dir=str(raw_dir), trace_dir=str(trace_dir))

    response = await workflow.run("毕业生创业补贴需要哪些材料，流程是什么？")

    assert response.trace_id
    assert response.risk_assessment.risk_level in {"low", "medium", "high"}
    assert len(response.policy_evidence) >= 1
    assert len(response.materials) >= 1
    assert len(response.process_steps) >= 1
