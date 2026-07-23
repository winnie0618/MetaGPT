from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from metagpt.const import DEFAULT_WORKSPACE_ROOT
from metagpt.ext.government_service.eval.run_eval import evaluate


VARIANTS: dict[str, dict[str, bool]] = {
    "full": {
        "enable_process_planner": True,
        "enable_risk_auditor": True,
        "enable_trace_record": True,
    },
    "no_process_planner": {
        "enable_process_planner": False,
        "enable_risk_auditor": True,
        "enable_trace_record": True,
    },
    "no_risk_auditor": {
        "enable_process_planner": True,
        "enable_risk_auditor": False,
        "enable_trace_record": True,
    },
    "no_trace_record": {
        "enable_process_planner": True,
        "enable_risk_auditor": True,
        "enable_trace_record": False,
    },
}

METRIC_COLUMNS = [
    "answer_keyword_hit_rate",
    "evidence_keyword_hit_rate",
    "risk_accuracy",
    "human_review_accuracy",
    "material_hit_rate",
    "process_step_hit_rate",
    "trace_recorded_rate",
]


async def run_ablation(dataset_path: str, knowledge_backend: str = "rag") -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for variant, options in VARIANTS.items():
        trace_dir = DEFAULT_WORKSPACE_ROOT / "government_service" / "ablation_traces" / variant
        result = await evaluate(
            dataset_path=dataset_path,
            knowledge_backend=knowledge_backend,
            trace_dir=str(trace_dir),
            **options,
        )
        if result:
            result = {"variant": variant, **result}
            results.append(result)
    return {
        "dataset": dataset_path,
        "knowledge_backend": knowledge_backend,
        "variants": list(VARIANTS),
        "results": results,
        "markdown_table": to_markdown_table(results),
    }


def to_markdown_table(results: list[dict[str, Any]]) -> str:
    headers = ["variant", *METRIC_COLUMNS]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for result in results:
        cells = [str(result.get("variant", ""))]
        for metric in METRIC_COLUMNS:
            value = result.get(metric)
            cells.append("" if value is None else f"{float(value):.4f}")
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="jsonl 数据集路径")
    parser.add_argument("--output", type=str, default="", help="输出 json 文件路径")
    parser.add_argument(
        "--knowledge-backend",
        type=str,
        choices=["keyword", "rag", "tfidf"],
        default="rag",
        help="用于消融实验的检索后端",
    )
    args = parser.parse_args()
    result = asyncio.run(run_ablation(dataset_path=args.dataset, knowledge_backend=args.knowledge_backend))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
