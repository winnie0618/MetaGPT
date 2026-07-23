import json

from metagpt.ext.government_service.actions.trace_record import TraceRecordStore


def test_trace_record_store_find_by_trace_id(tmp_path):
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir(parents=True)
    trace_path = trace_dir / "trace_records.jsonl"
    records = [
        {"trace_id": "trace-1", "query": "问题1"},
        {"trace_id": "trace-2", "query": "问题2"},
    ]
    trace_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records), encoding="utf-8")

    store = TraceRecordStore(trace_dir=trace_dir)

    assert store.find_by_trace_id("trace-2")["query"] == "问题2"
    assert store.find_by_trace_id("missing") is None


def test_trace_record_store_list_recent(tmp_path):
    trace_dir = tmp_path / "traces"
    trace_dir.mkdir(parents=True)
    trace_path = trace_dir / "trace_records.jsonl"
    records = [{"trace_id": f"trace-{idx}", "query": f"问题{idx}"} for idx in range(3)]
    trace_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in records), encoding="utf-8")

    store = TraceRecordStore(trace_dir=trace_dir)
    recent = store.list_recent(limit=2)

    assert [item["trace_id"] for item in recent] == ["trace-2", "trace-1"]
