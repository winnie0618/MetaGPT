from __future__ import annotations

import argparse
import asyncio

from metagpt.ext.government_service.eval.dataset import load_samples
from metagpt.ext.government_service.eval.metrics import contains_hit
from metagpt.ext.government_service.workflow import GovServiceWorkflow


async def _run(dataset_path: str) -> None:
    samples = load_samples(dataset_path)
    if not samples:
        print("未加载到评估样本。")
        return

    workflow = GovServiceWorkflow()
    scores = []
    for sample in samples:
        resp = await workflow.run(sample.query)
        score = contains_hit(resp.direct_answer, sample.expected_answer_contains)
        scores.append(score)

    avg = sum(scores) / len(scores)
    print(f"样本数: {len(scores)}")
    print(f"平均命中率: {avg:.4f}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="jsonl 数据集路径")
    args = parser.parse_args()
    asyncio.run(_run(args.dataset))


if __name__ == "__main__":
    main()
