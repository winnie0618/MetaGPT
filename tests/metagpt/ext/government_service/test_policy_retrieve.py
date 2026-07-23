import pytest

from metagpt.ext.government_service.actions.policy_retrieve import PolicyRetrieveAction


@pytest.mark.asyncio
async def test_policy_retrieve_return_related_chunks(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_a.txt").write_text(
        "高校毕业生补贴申请可提交身份证明与毕业证书，办理时限一般为20个工作日。", encoding="utf-8"
    )
    (raw_dir / "policy_b.txt").write_text("创业扶持政策面向首次创业人员，需提供营业执照。", encoding="utf-8")

    action = PolicyRetrieveAction(raw_docs_dir=str(raw_dir), top_k=2)
    result = await action.run("毕业生补贴要提交哪些材料？")

    assert len(result) >= 1
    assert any("毕业" in item.snippet or "补贴" in item.snippet for item in result)
