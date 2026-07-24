from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import PolicyEvidence, ProcessStep


class TaskPlanAction(Action):
    name: str = "TaskPlanAction"

    async def run(self, query: str, evidences: list[PolicyEvidence] | None = None) -> list[ProcessStep]:
        extracted = self._extract_from_context(query, evidences)
        if extracted:
            return extracted
        return [
            ProcessStep(step_no=1, title="确认申请条件", detail="核对是否满足补贴对象、时限、身份等基础条件。"),
            ProcessStep(step_no=2, title="准备申请材料", detail="按指南准备身份证明、毕业证明、就业或创业相关证明。"),
            ProcessStep(step_no=3, title="提交办理申请", detail="通过线上政务平台或线下窗口提交材料。"),
            ProcessStep(step_no=4, title="等待审核与反馈", detail="关注受理状态，按通知补充材料或领取结果。"),
        ]

    @staticmethod
    def _extract_from_context(query: str, evidences: list[PolicyEvidence] | None) -> list[ProcessStep]:
        evidence_text = "\n".join(f"{e.title}\n{e.snippet}" for e in evidences or [])
        combined_text = f"{query}\n{evidence_text}".lower()
        selected: set[str] = set()
        rules: list[tuple[str, tuple[str, ...], str]] = [
            (
                "提交申请",
                ("提交申请", "提交材料", "提交", "递交", "上传", "申请", "申报", "线上提交", "在线申请", "窗口提交", "重新提交"),
                "通过线上政务平台或线下窗口提交申请材料，并保留受理凭证。",
            ),
            (
                "受理",
                ("受理", "窗口办理", "线下窗口", "经办窗口", "窗口"),
                "经办机构对申请材料进行接收、登记和形式审查。",
            ),
            (
                "补正材料",
                ("补正材料", "补正", "补充材料", "材料不齐", "材料不完整", "退回", "补正通知"),
                "材料不齐或不符合要求时，按补正通知补充或重新提交相关材料。",
            ),
            (
                "审核",
                ("审核", "审批", "核验", "审查", "资格核验", "通过审核", "审核通过"),
                "经办机构核验申请资格、材料真实性和政策适用条件。",
            ),
            (
                "公示",
                ("公示", "公示名单", "名单"),
                "对拟补贴对象或审核结果进行公示，接受异议或复核申请。",
            ),
            (
                "发放",
                ("发放", "到账", "资金到账", "补贴发放", "银行卡"),
                "公示无异议并完成审批后，按规定将补贴发放至申请人账户。",
            ),
            (
                "人工复核",
                ("人工复核", "复核", "申诉", "异议", "争议"),
                "涉及争议、申诉或高风险判断时，转入人工复核或经办机构确认。",
            ),
        ]

        for title, aliases, _detail in rules:
            if any(alias in combined_text for alias in aliases):
                selected.add(title)

        process_requested = any(token in combined_text for token in ("流程", "步骤", "怎么走", "下一步", "办理"))
        if process_requested:
            selected.update({"提交申请", "审核"})
        if any(token in combined_text for token in ("线上", "在线", "窗口", "线下")):
            selected.update({"提交申请", "受理"})
        if any(token in combined_text for token in ("补正", "退回", "材料不齐", "材料不完整")):
            selected.update({"补正材料", "提交申请", "审核"})
        if any(token in combined_text for token in ("申诉", "复核", "异议")):
            selected.add("人工复核")

        ordered_steps = [(title, detail) for title, _aliases, detail in rules if title in selected]
        return [
            ProcessStep(step_no=idx, title=title, detail=detail)
            for idx, (title, detail) in enumerate(ordered_steps, start=1)
        ]
