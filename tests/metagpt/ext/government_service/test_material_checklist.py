import pytest

from metagpt.ext.government_service.actions.material_checklist import MaterialChecklistAction
from metagpt.ext.government_service.schema import PolicyEvidence
from metagpt.ext.government_service.workflow import GovServiceWorkflow


@pytest.mark.asyncio
async def test_material_checklist_uses_query_aliases():
    action = MaterialChecklistAction()
    materials = await action.run("上传身份证、毕业证和银行卡需要注意什么？", evidences=[])
    names = [item.name for item in materials]

    assert "身份证明" in names
    assert "毕业证书" in names
    assert "银行卡信息" in names


@pytest.mark.asyncio
async def test_material_checklist_normalizes_employment_and_startup_aliases():
    action = MaterialChecklistAction()
    materials = await action.run(
        "就业证明和营业执照可以作为材料吗？",
        evidences=[PolicyEvidence(doc_id="p1", title="材料说明", snippet="可提交劳动合同或营业执照。", score=1.0)],
    )
    names = [item.name for item in materials]

    assert "就业协议" in names
    assert "创业证明" in names


@pytest.mark.asyncio
async def test_workflow_builds_materials_for_policy_query_with_material_terms(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_1.txt").write_text("上传身份证和银行卡时应注意隐私保护。", encoding="utf-8")

    workflow = GovServiceWorkflow(raw_docs_dir=str(raw_dir), trace_dir=str(tmp_path / "traces"), knowledge_backend="keyword")
    response = await workflow.run("信息安全方面，上传身份证和银行卡需要注意什么？")
    names = [item.name for item in response.materials]

    assert "身份证明" in names
    assert "银行卡信息" in names
