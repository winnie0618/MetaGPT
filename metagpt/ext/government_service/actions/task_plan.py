from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import PolicyEvidence, ProcessStep


class TaskPlanAction(Action):
    name: str = "TaskPlanAction"

    async def run(self, query: str, evidences: list[PolicyEvidence] | None = None) -> list[ProcessStep]:
        _ = query
        extracted = self._extract_from_evidences(evidences)
        if extracted:
            return extracted
        return [
            ProcessStep(step_no=1, title="确认申请条件", detail="核对是否满足补贴对象、时限、身份等基础条件。"),
            ProcessStep(step_no=2, title="准备申请材料", detail="按指南准备身份证明、毕业证明、就业或创业相关证明。"),
            ProcessStep(step_no=3, title="提交办理申请", detail="通过线上政务平台或线下窗口提交材料。"),
            ProcessStep(step_no=4, title="等待审核与反馈", detail="关注受理状态，按通知补充材料或领取结果。"),
        ]

    @staticmethod
    def _extract_from_evidences(evidences: list[PolicyEvidence] | None) -> list[ProcessStep]:
        if not evidences:
            return []

        combined_text = "\n".join(f"{e.title}\n{e.snippet}" for e in evidences).lower()
        steps: list[tuple[str, str]] = []
        rules = [
            ("提交申请", "提交申请材料并完成受理登记。"),
            ("受理", "完成受理和初步登记。"),
            ("审核", "进入审核与材料核验流程。"),
            ("公示", "进行公示或结果告知。"),
            ("补正材料", "如材料不齐，按通知补正材料。"),
            ("人工复核", "如有争议或高风险情况，启动人工复核。"),
            ("发放", "完成补贴发放或资金到账。"),
        ]

        for keyword, detail in rules:
            if keyword in combined_text:
                steps.append((keyword, detail))

        if not steps:
            return []

        return [ProcessStep(step_no=idx, title=title, detail=detail) for idx, (title, detail) in enumerate(steps, start=1)]
