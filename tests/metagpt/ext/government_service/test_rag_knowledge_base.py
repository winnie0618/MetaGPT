import numpy as np

from metagpt.ext.government_service.knowledge_base import (
    RAGPolicyKnowledgeBase,
    SemanticEmbeddingPolicyKnowledgeBase,
    TfidfPolicyKnowledgeBase,
)


def test_rag_knowledge_base_retrieve_with_status(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy.txt").write_text("高校毕业生创业补贴需要身份证明和毕业证书。", encoding="utf-8")

    kb = RAGPolicyKnowledgeBase(raw_docs_dir=str(raw_dir), persist_dir=str(tmp_path / "rag"))
    evidences = kb.retrieve("毕业生补贴材料")
    assert evidences
    assert any("毕业证书" in item.snippet for item in evidences)
    assert kb.status()["backend"] in {"rag", "fallback"}


def test_tfidf_knowledge_base_retrieve_with_status(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy.txt").write_text("高校毕业生创业补贴需要身份证明和毕业证书。", encoding="utf-8")

    kb = TfidfPolicyKnowledgeBase(raw_docs_dir=str(raw_dir))
    evidences = kb.retrieve("毕业生补贴材料")

    assert evidences
    assert any("毕业证书" in item.snippet for item in evidences)
    assert kb.status()["backend"] in {"tfidf", "fallback"}


def test_semantic_embedding_knowledge_base_falls_back_without_model(tmp_path):
    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy.txt").write_text("高校毕业生创业补贴需要身份证明和毕业证书。", encoding="utf-8")

    kb = SemanticEmbeddingPolicyKnowledgeBase(raw_docs_dir=str(raw_dir), persist_dir=str(tmp_path / "embedding"))
    evidences = kb.retrieve("毕业生补贴材料")

    assert evidences
    assert any("毕业证书" in item.snippet for item in evidences)
    assert kb.status()["backend"] in {"embedding", "fallback"}


def test_semantic_embedding_knowledge_base_retrieve_with_fake_model(tmp_path, monkeypatch):
    class FakeEmbeddingModel:
        def encode(self, texts, **kwargs):
            vectors = []
            for text in texts:
                if "身份证明" in text or "毕业证书" in text or "材料" in text:
                    vectors.append([1.0, 0.0, 0.0])
                else:
                    vectors.append([0.0, 1.0, 0.0])
            return np.asarray(vectors, dtype="float32")

    raw_dir = tmp_path / "raw_docs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (raw_dir / "policy_a.txt").write_text("高校毕业生创业补贴需要身份证明和毕业证书。", encoding="utf-8")
    (raw_dir / "policy_b.txt").write_text("窗口受理后进入审核和公示流程。", encoding="utf-8")

    monkeypatch.setattr(
        SemanticEmbeddingPolicyKnowledgeBase,
        "_load_embedding_model",
        lambda self: FakeEmbeddingModel(),
    )

    kb = SemanticEmbeddingPolicyKnowledgeBase(raw_docs_dir=str(raw_dir), persist_dir=str(tmp_path / "embedding"))
    evidences = kb.retrieve("毕业生补贴材料")

    assert evidences[0].title == "policy_a"
    assert kb.status()["backend"] == "embedding"
    assert kb.status()["ready"] is True
