import json
from datetime import datetime

import pytest

from metagpt.ext.government_service.actions.trace_record import TraceRecordAction
from metagpt.ext.government_service.schema import TraceRecord


@pytest.mark.asyncio
async def test_trace_record_save_jsonl(tmp_path):
    action = TraceRecordAction(trace_dir=str(tmp_path))
    record = TraceRecord(
        trace_id="20260723-000001",
        query="毕业生创业补贴需要哪些材料？",
        intent="material_checklist",
        retrieved_docs=["policy_001"],
        actions=["IntentRecognizeAction", "PolicyRetrieveAction", "MaterialChecklistAction", "RiskAssessAction"],
        risk_level="low",
        human_review_required=False,
        answer="需要身份证明和毕业证书等材料。",
        timestamp=datetime.now(),
    )

    trace_id = await action.run(record)
    assert trace_id == "20260723-000001"

    trace_file = tmp_path / "trace_records.jsonl"
    assert trace_file.exists()

    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["trace_id"] == "20260723-000001"
