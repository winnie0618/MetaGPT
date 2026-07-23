from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from metagpt.ext.government_service.eval.run_eval import evaluate


METRIC_COLUMNS = [
    "answer_keyword_hit_rate",
    "evidence_keyword_hit_rate",
    "risk_accuracy",
    "human_review_accuracy",
    "material_hit_rate",
    "process_step_hit_rate",
]


async def compare(dataset_path: str, backends: list[str]) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for backend in backends:
        result = await evaluate(dataset_path=dataset_path, knowledge_backend=backend)
        if result:
            results.append(result)
    return {
        "dataset": dataset_path,
        "backends": backends,
        "results": results,
        "markdown_table": to_markdown_table(results),
    }


def to_markdown_table(results: list[dict[str, Any]]) -> str:
    headers = ["backend", "actual_backend_counts", *METRIC_COLUMNS]
    rows = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for result in results:
        cells = [
            str(result.get("requested_backend", "")),
            json.dumps(result.get("actual_backend_counts", {}), ensure_ascii=False),
        ]
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
        "--backends",
        nargs="+",
        choices=["keyword", "rag"],
        default=["keyword", "rag"],
        help="需要对比的知识库后端",
    )
    args = parser.parse_args()
    result = asyncio.run(compare(dataset_path=args.dataset, backends=args.backends))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
