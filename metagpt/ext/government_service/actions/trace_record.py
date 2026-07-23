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


class TraceRecordStore:
    """Read persisted trace records for audit and demo inspection."""

    def __init__(self, trace_dir: str | Path | None = None):
        self.trace_dir = Path(trace_dir) if trace_dir else TRACE_DIR

    @property
    def trace_path(self) -> Path:
        return self.trace_dir / "trace_records.jsonl"

    def find_by_trace_id(self, trace_id: str) -> dict | None:
        target = trace_id.strip()
        if not target or not self.trace_path.exists():
            return None
        for record in reversed(self._read_records()):
            if record.get("trace_id") == target:
                return record
        return None

    def list_recent(self, limit: int = 20) -> list[dict]:
        if not self.trace_path.exists():
            return []
        records = self._read_records()
        return list(reversed(records[-max(limit, 0) :]))

    def _read_records(self) -> list[dict]:
        records: list[dict] = []
        if not self.trace_path.exists():
            return records
        with self.trace_path.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records
