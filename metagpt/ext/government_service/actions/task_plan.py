from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import PolicyEvidence, ProcessStep


class TaskPlanAction(Action):
    name: str = "TaskPlanAction"

    async def run(self, query: str, evidences: list[PolicyEvidence] | None = None) -> list[ProcessStep]:
        _ = query, evidences
        return [
            ProcessStep(step_no=1, title="确认申请条件", detail="核对是否满足补贴对象、时限、身份等基础条件。"),
            ProcessStep(step_no=2, title="准备申请材料", detail="按指南准备身份证明、毕业证明、就业或创业相关证明。"),
            ProcessStep(step_no=3, title="提交办理申请", detail="通过线上政务平台或线下窗口提交材料。"),
            ProcessStep(step_no=4, title="等待审核与反馈", detail="关注受理状态，按通知补充材料或领取结果。"),
        ]
