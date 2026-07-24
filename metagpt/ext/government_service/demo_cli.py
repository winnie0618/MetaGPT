from __future__ import annotations

import argparse
import asyncio

from metagpt.ext.government_service.config import ANSWER_MODES, DEFAULT_ANSWER_MODE
from metagpt.ext.government_service.workflow import GovServiceWorkflow


def _print_response(resp) -> None:
    print("\n=== 最终回答 ===")
    print(resp.direct_answer)

    print("\n=== 政策依据 ===")
    if not resp.policy_evidence:
        print("无")
    else:
        for item in resp.policy_evidence:
            print(f"- [{item.doc_id}] {item.title} (score={item.score})")
            print(f"  {item.snippet}")

    print("\n=== 材料清单 ===")
    if not resp.materials:
        print("无")
    else:
        for item in resp.materials:
            required = "必需" if item.required else "可选"
            print(f"- {item.name}（{required}）：{item.note}")

    print("\n=== 办理步骤 ===")
    if not resp.process_steps:
        print("无")
    else:
        for step in resp.process_steps:
            print(f"{step.step_no}. {step.title}：{step.detail}")

    print("\n=== 风险评估 ===")
    print(f"风险等级：{resp.risk_assessment.risk_level}")
    print(f"是否需要人工复核：{resp.risk_assessment.human_review_required}")
    if resp.human_review_message:
        print(f"人工复核提示：{resp.human_review_message}")

    print(f"\ntrace_id: {resp.trace_id}\n")


async def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--knowledge-backend",
        choices=["keyword", "rag", "tfidf"],
        default="rag",
        help="知识库后端",
    )
    parser.add_argument(
        "--answer-mode",
        choices=sorted(ANSWER_MODES),
        default=DEFAULT_ANSWER_MODE,
        help="回答生成模式：template、llm 或 rag_llm",
    )
    args = parser.parse_args()

    workflow = GovServiceWorkflow(knowledge_backend=args.knowledge_backend, answer_mode=args.answer_mode)
    print("GovTrace-Agent 命令行演示，输入 exit 退出。")
    while True:
        query = input("\n请输入政务服务问题：").strip()
        if query.lower() in {"exit", "quit"}:
            print("已退出。")
            return
        if not query:
            print("请输入有效问题。")
            continue

        resp = await workflow.run(query)
        _print_response(resp)


if __name__ == "__main__":
    asyncio.run(_main())
