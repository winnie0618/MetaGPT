import pytest

from metagpt.ext.government_service.local_web_demo import ANSWER_MODES, BACKENDS, INDEX_HTML, build_payload


def test_local_web_demo_exposes_retrieval_backends():
    assert {"keyword", "rag", "tfidf", "embedding"}.issubset(BACKENDS)
    assert "/api/query" in INDEX_HTML
    assert "/api/trace/" in INDEX_HTML
    assert "traceQuery" in INDEX_HTML
    assert "answerModeGroup" in INDEX_HTML
    assert "Embedding" in INDEX_HTML
    assert {"template", "llm", "rag_llm"}.issubset(ANSWER_MODES)


def test_local_web_demo_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unsupported backend"):
        build_payload("测试问题", backend="unknown")


def test_local_web_demo_rejects_unknown_answer_mode():
    with pytest.raises(ValueError, match="Unsupported answer_mode"):
        build_payload("测试问题", backend="keyword", answer_mode="unknown")
