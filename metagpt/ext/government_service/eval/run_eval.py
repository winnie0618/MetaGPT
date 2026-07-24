from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from pathlib import Path

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.ext.government_service.actions.trace_record import TraceRecordStore
from metagpt.ext.government_service.config import ANSWER_MODES, DEFAULT_ANSWER_MODE
from metagpt.ext.government_service.eval.dataset import load_samples
from metagpt.ext.government_service.eval.metrics import bool_match, contains_hit, exact_match, keyword_hit_rate
from metagpt.ext.government_service.workflow import GovServiceWorkflow


async def evaluate(
    dataset_path: str,
    knowledge_backend: str = "rag",
    answer_mode: str = DEFAULT_ANSWER_MODE,
    enable_process_planner: bool = True,
    enable_risk_auditor: bool = True,
    enable_trace_record: bool = True,
    trace_dir: str | None = None,
) -> dict | None:
    samples = load_samples(dataset_path)
    if not samples:
        print("未加载到评估样本。")
        return None

    effective_trace_dir = trace_dir or str(DEFAULT_WORKSPACE_ROOT / "government_service" / "traces")
    trace_store = TraceRecordStore(trace_dir=effective_trace_dir)
    workflow = GovServiceWorkflow(
        knowledge_backend=knowledge_backend,
        answer_mode=answer_mode,
        trace_dir=effective_trace_dir,
        enable_process_planner=enable_process_planner,
        enable_risk_auditor=enable_risk_auditor,
        enable_trace_record=enable_trace_record,
    )
    answer_scores = []
    evidence_scores = []
    risk_scores = []
    human_review_scores = []
    material_scores = []
    process_scores = []
    trace_recorded_scores = []
    material_samples = []
    process_samples = []
    high_risk_samples = []
    backend_counter: Counter[str] = Counter()

    for sample in samples:
        resp = await workflow.run(sample.query)
        kb_status = workflow.coordinator.policy_expert.last_status
        backend_counter[kb_status.get("backend", "unknown")] += 1
        answer_scores.append(contains_hit(resp.direct_answer, sample.expected_answer_contains))
        evidence_scores.append(keyword_hit_rate(" ".join(e.snippet for e in resp.policy_evidence), sample.expected_evidence_keywords))
        risk_scores.append(exact_match(resp.risk_assessment.risk_level, sample.expected_risk_level))
        human_review_scores.append(bool_match(resp.risk_assessment.human_review_required, sample.expected_human_review_required))
        trace_recorded_scores.append(1.0 if trace_store.find_by_trace_id(resp.trace_id) else 0.0)

        if sample.expected_materials:
            material_samples.append(sample)
            material_scores.append(contains_hit(" ".join(m.name for m in resp.materials), sample.expected_materials))

        if sample.expected_process_steps:
            process_samples.append(sample)
            process_scores.append(contains_hit(" ".join(s.title for s in resp.process_steps), sample.expected_process_steps))

        if sample.expected_risk_level == "high":
            high_risk_samples.append(sample)

    result = {
        "requested_backend": knowledge_backend,
        "answer_mode": answer_mode,
        "actual_backend_counts": dict(sorted(backend_counter.items())),
        "sample_count": len(samples),
        "answer_keyword_hit_rate": sum(answer_scores) / len(answer_scores),
        "evidence_keyword_hit_rate": sum(evidence_scores) / len(evidence_scores),
        "risk_accuracy": sum(risk_scores) / len(risk_scores),
        "human_review_accuracy": sum(human_review_scores) / len(human_review_scores),
        "material_hit_rate": (sum(material_scores) / len(material_scores)) if material_scores else None,
        "process_step_hit_rate": (sum(process_scores) / len(process_scores)) if process_scores else None,
        "trace_recorded_rate": sum(trace_recorded_scores) / len(trace_recorded_scores),
        "material_sample_count": len(material_samples),
        "process_sample_count": len(process_samples),
        "high_risk_sample_count": len(high_risk_samples),
        "enable_process_planner": enable_process_planner,
        "enable_risk_auditor": enable_risk_auditor,
        "enable_trace_record": enable_trace_record,
    }
    return result


async def _run(
    dataset_path: str,
    knowledge_backend: str = "rag",
    answer_mode: str = DEFAULT_ANSWER_MODE,
    enable_process_planner: bool = True,
    enable_risk_auditor: bool = True,
    enable_trace_record: bool = True,
) -> dict | None:
    result = await evaluate(
        dataset_path=dataset_path,
        knowledge_backend=knowledge_backend,
        answer_mode=answer_mode,
        enable_process_planner=enable_process_planner,
        enable_risk_auditor=enable_risk_auditor,
        enable_trace_record=enable_trace_record,
    )
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="jsonl 数据集路径")
    parser.add_argument("--output", type=str, default="", help="输出 json 文件路径")
    parser.add_argument(
        "--knowledge-backend",
        type=str,
        choices=["keyword", "rag", "tfidf"],
        default="rag",
        help="知识库后端：keyword 使用关键词检索，rag 使用本地 FAISS 检索，tfidf 使用统计向量检索",
    )
    parser.add_argument(
        "--answer-mode",
        type=str,
        choices=sorted(ANSWER_MODES),
        default=DEFAULT_ANSWER_MODE,
        help="回答生成模式：template 离线模板，llm 模型直接生成，rag_llm 基于检索证据生成",
    )
    parser.add_argument("--disable-process-planner", action="store_true", help="消融：关闭材料和流程规划模块")
    parser.add_argument("--disable-risk-auditor", action="store_true", help="消融：关闭风险审核模块")
    parser.add_argument("--disable-trace-record", action="store_true", help="消融：关闭追溯日志写入")
    args = parser.parse_args()
    result = asyncio.run(
        _run(
            args.dataset,
            knowledge_backend=args.knowledge_backend,
            answer_mode=args.answer_mode,
            enable_process_planner=not args.disable_process_planner,
            enable_risk_auditor=not args.disable_risk_auditor,
            enable_trace_record=not args.disable_trace_record,
        )
    )
    if args.output and result:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
