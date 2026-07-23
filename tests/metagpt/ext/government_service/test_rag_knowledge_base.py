from metagpt.ext.government_service.knowledge_base import RAGPolicyKnowledgeBase


def test_rag_knowledge_base_retrieve_with_status(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy.txt").write_text("高校毕业生创业补贴需要身份证明和毕业证书。", encoding="utf-8")

    kb = RAGPolicyKnowledgeBase(raw_docs_dir=str(raw_dir), persist_dir=str(tmp_path / "rag"))
    evidences = kb.retrieve("毕业生补贴材料")
    assert evidences
    assert any("毕业证书" in item.snippet for item in evidences)
    assert kb.status()["backend"] in {"rag", "fallback"}
