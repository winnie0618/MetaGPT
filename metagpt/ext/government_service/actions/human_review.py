from __future__ import annotations

from metagpt.actions import Action


class HumanReviewAction(Action):
    name: str = "HumanReviewAction"

    async def run(self) -> str:
        return (
            "该问题涉及资格认定、审批结果或权益判断，需要人工复核。"
            "以下内容仅作为政策依据和办理建议，不构成最终行政结论。"
        )
