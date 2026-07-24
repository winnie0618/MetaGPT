import pytest

from metagpt.ext.government_service.actions.trace_record import TraceRecordStore
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


@pytest.mark.asyncio
async def test_workflow_supports_keyword_backend(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("补贴申请需要身份证明和毕业证书。", encoding="utf-8")

    workflow = GovServiceWorkflow(raw_docs_dir=str(raw_dir), trace_dir=str(tmp_path / "traces"), knowledge_backend="keyword")
    response = await workflow.run("补贴申请需要什么材料？")

    assert response.policy_evidence
    assert workflow.coordinator.policy_expert.last_status["backend"] == "keyword"


@pytest.mark.asyncio
async def test_workflow_supports_tfidf_backend(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("补贴申请需要身份证明和毕业证书。", encoding="utf-8")

    workflow = GovServiceWorkflow(raw_docs_dir=str(raw_dir), trace_dir=str(tmp_path / "traces"), knowledge_backend="tfidf")
    response = await workflow.run("毕业生补贴申请材料")

    assert response.policy_evidence
    assert workflow.coordinator.policy_expert.last_status["backend"] in {"tfidf", "fallback"}


@pytest.mark.asyncio
async def test_workflow_supports_embedding_backend(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("补贴申请需要身份证明和毕业证书。", encoding="utf-8")

    workflow = GovServiceWorkflow(
        raw_docs_dir=str(raw_dir),
        trace_dir=str(tmp_path / "traces"),
        knowledge_backend="embedding",
    )
    response = await workflow.run("毕业生补贴申请材料")

    assert response.policy_evidence
    assert workflow.coordinator.policy_expert.last_status["backend"] in {"embedding", "fallback"}


@pytest.mark.asyncio
async def test_workflow_records_answer_mode_in_trace_metadata(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    trace_dir = tmp_path / "traces"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("补贴申请需要身份证明。", encoding="utf-8")

    workflow = GovServiceWorkflow(
        raw_docs_dir=str(raw_dir),
        trace_dir=str(trace_dir),
        knowledge_backend="keyword",
        answer_mode="template",
    )
    response = await workflow.run("补贴申请需要什么材料？")
    record = TraceRecordStore(trace_dir=trace_dir).find_by_trace_id(response.trace_id)

    assert record is not None
    assert record["metadata"]["answer_mode"] == "template"


@pytest.mark.asyncio
async def test_workflow_ablation_can_disable_risk_auditor(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("创业补贴申请需要按政策审核。", encoding="utf-8")

    workflow = GovServiceWorkflow(
        raw_docs_dir=str(raw_dir),
        trace_dir=str(tmp_path / "traces"),
        knowledge_backend="keyword",
        enable_risk_auditor=False,
    )
    response = await workflow.run("我能不能确定拿到创业补贴，金额是多少？")

    assert response.risk_assessment.risk_level == "low"
    assert response.risk_assessment.human_review_required is False


@pytest.mark.asyncio
async def test_workflow_ablation_can_disable_process_planner(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("补贴申请需要身份证明、毕业证书，并提交申请。", encoding="utf-8")

    workflow = GovServiceWorkflow(
        raw_docs_dir=str(raw_dir),
        trace_dir=str(tmp_path / "traces"),
        knowledge_backend="keyword",
        enable_process_planner=False,
    )
    response = await workflow.run("补贴申请需要哪些材料，流程是什么？")

    assert response.materials == []
    assert response.process_steps == []


@pytest.mark.asyncio
async def test_workflow_ablation_can_disable_trace_record(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    trace_dir = tmp_path / "traces"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("补贴申请需要身份证明。", encoding="utf-8")

    workflow = GovServiceWorkflow(
        raw_docs_dir=str(raw_dir),
        trace_dir=str(trace_dir),
        knowledge_backend="keyword",
        enable_trace_record=False,
    )
    response = await workflow.run("补贴申请需要什么材料？")

    assert response.trace_id
    assert TraceRecordStore(trace_dir=trace_dir).find_by_trace_id(response.trace_id) is None
