from __future__ import annotations

import os
from pathlib import Path

from metagpt.const import DATA_PATH, DEFAULT_WORKSPACE_ROOT

RAW_DOCS_DIR: Path = DATA_PATH / "government_service" / "raw_docs"
TRACE_DIR: Path = DEFAULT_WORKSPACE_ROOT / "government_service" / "traces"

DEFAULT_TOP_K: int = 3

ANSWER_MODES: set[str] = {"template", "llm", "rag_llm"}
DEFAULT_ANSWER_MODE: str = os.getenv("GOVTRACE_ANSWER_MODE", "template")
DEFAULT_LLM_PROVIDER: str = os.getenv("GOVTRACE_LLM_PROVIDER", "openai_compatible")
DEFAULT_LLM_MODEL: str = os.getenv("GOVTRACE_LLM_MODEL", "qwen2.5:7b-instruct")
DEFAULT_LLM_BASE_URL: str = os.getenv("GOVTRACE_LLM_BASE_URL", "http://127.0.0.1:11434/v1")
