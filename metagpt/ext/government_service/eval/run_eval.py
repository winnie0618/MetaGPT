from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from metagpt.ext.government_service.eval.dataset import load_samples
from metagpt.ext.government_service.eval.metrics import bool_match, contains_hit, exact_match, keyword_hit_rate
from metagpt.ext.government_service.workflow import GovServiceWorkflow


async def _run(dataset_path: str) -> None:
    samples = load_samples(dataset_path)
    if not samples:
        print("未加载到评估样本。")
        return

    workflow = GovServiceWorkflow()
    answer_scores = []
    evidence_scores = []
    risk_scores = []
    human_review_scores = []
    material_scores = []
    process_scores = []
    material_samples = []
    process_samples = []
    high_risk_samples = []

    for sample in samples:
        resp = await workflow.run(sample.query)
        answer_scores.append(contains_hit(resp.direct_answer, sample.expected_answer_contains))
        evidence_scores.append(keyword_hit_rate(" ".join(e.snippet for e in resp.policy_evidence), sample.expected_evidence_keywords))
        risk_scores.append(exact_match(resp.risk_assessment.risk_level, sample.expected_risk_level))
        human_review_scores.append(bool_match(resp.risk_assessment.human_review_required, sample.expected_human_review_required))

        if sample.expected_materials:
            material_samples.append(sample)
            material_scores.append(contains_hit(" ".join(m.name for m in resp.materials), sample.expected_materials))

        if sample.expected_process_steps:
            process_samples.append(sample)
            process_scores.append(contains_hit(" ".join(s.title for s in resp.process_steps), sample.expected_process_steps))

        if sample.expected_risk_level == "high":
            high_risk_samples.append(sample)

    result = {
        "sample_count": len(samples),
        "answer_keyword_hit_rate": sum(answer_scores) / len(answer_scores),
        "evidence_keyword_hit_rate": sum(evidence_scores) / len(evidence_scores),
        "risk_accuracy": sum(risk_scores) / len(risk_scores),
        "human_review_accuracy": sum(human_review_scores) / len(human_review_scores),
        "material_hit_rate": (sum(material_scores) / len(material_scores)) if material_scores else None,
        "process_step_hit_rate": (sum(process_scores) / len(process_scores)) if process_scores else None,
        "material_sample_count": len(material_samples),
        "process_sample_count": len(process_samples),
        "high_risk_sample_count": len(high_risk_samples),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True, help="jsonl 数据集路径")
    parser.add_argument("--output", type=str, default="", help="输出 json 文件路径")
    args = parser.parse_args()
    result = asyncio.run(_run(args.dataset))
    if args.output and result:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
