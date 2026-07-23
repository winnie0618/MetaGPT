from __future__ import annotations

import json
from pathlib import Path

from metagpt.actions import Action
from metagpt.ext.government_service.config import TRACE_DIR
from metagpt.ext.government_service.schema import TraceRecord


class TraceRecordAction(Action):
    name: str = "TraceRecordAction"
    trace_dir: str | None = None

    def _get_trace_path(self) -> Path:
        base_dir = Path(self.trace_dir) if self.trace_dir else TRACE_DIR
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / "trace_records.jsonl"

    async def run(self, record: TraceRecord) -> str:
        trace_path = self._get_trace_path()
        with trace_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")
        return record.trace_id
