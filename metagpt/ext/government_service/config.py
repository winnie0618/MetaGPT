from __future__ import annotations

from pathlib import Path

from metagpt.const import DATA_PATH, DEFAULT_WORKSPACE_ROOT

RAW_DOCS_DIR: Path = DATA_PATH / "government_service" / "raw_docs"
TRACE_DIR: Path = DEFAULT_WORKSPACE_ROOT / "government_service" / "traces"

DEFAULT_TOP_K: int = 3
