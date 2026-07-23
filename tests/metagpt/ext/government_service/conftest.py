import pytest


@pytest.fixture(scope="function", autouse=True)
def llm_mock():
    """Government-service tests are rule-based and do not need the global LLM mock."""
    yield
