from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import IntentType, RiskAssessment


class RiskAssessAction(Action):
    name: str = "RiskAssessAction"

    async def run(self, query: str, intent: IntentType) -> RiskAssessment:
        q = query.strip().lower()

        high_keywords = [
            "审批结果",
            "审批结论",
            "补贴金额",
            "金额",
            "资格最终认定",
            "最终认定",
            "最终资格",
            "最终批准",
            "批准意见",
            "行政处罚",
            "权益裁定",
            "虚假材料",
            "审核不通过",
            "申诉",
            "到账",
            "确定发放",
            "一定能拿到",
            "保证",
            "公示名单",
            "能不能批",
            "能通过吗",
            "是否通过",
            "多少钱",
        ]
        medium_keywords = [
            "资格初步判断",
            "资格",
            "材料是否齐全",
            "材料齐全",
            "材料不齐全",
            "流程适用性",
            "是否符合",
            "能否申请",
            "能不能申请",
            "还能申请",
            "影响申请",
            "毕业年度",
            "重复申领",
            "不予受理",
            "跨地区",
        ]
        low_keywords = ["政策", "材料查询", "办理地点", "时限", "流程", "清单"]

        if intent == "high_risk_decision" or any(k in q for k in high_keywords):
            return RiskAssessment(
                risk_level="high",
                human_review_required=True,
                reason="问题涉及审批结论、金额、资格最终认定或权益裁定，属于高风险事项。",
            )

        if intent == "qualification_check" or any(k in q for k in medium_keywords):
            return RiskAssessment(
                risk_level="medium",
                human_review_required=False,
                reason="问题涉及资格或流程适配等判断，建议谨慎解释。",
            )

        if any(k in q for k in low_keywords) or intent in {"policy_query", "material_checklist", "process_plan", "mixed"}:
            return RiskAssessment(
                risk_level="low",
                human_review_required=False,
                reason="问题以政策解释与流程信息为主，风险较低。",
            )

        return RiskAssessment(
            risk_level="medium",
            human_review_required=False,
            reason="问题语义不完全明确，默认按中风险处理。",
        )
