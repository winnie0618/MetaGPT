import pytest

from metagpt.ext.government_service.local_web_demo import BACKENDS, INDEX_HTML, build_payload


def test_local_web_demo_exposes_retrieval_backends():
    assert {"keyword", "rag", "tfidf"}.issubset(BACKENDS)
    assert "/api/query" in INDEX_HTML


def test_local_web_demo_rejects_unknown_backend():
    with pytest.raises(ValueError, match="Unsupported backend"):
        build_payload("测试问题", backend="unknown")
