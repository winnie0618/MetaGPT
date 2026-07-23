from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import IntentType, ServiceIntent


class IntentRecognizeAction(Action):
    name: str = "IntentRecognizeAction"

    async def run(self, query: str) -> ServiceIntent:
        q = query.strip().lower()

        high_risk_keywords = [
            "审批结果",
            "审批结论",
            "补贴金额",
            "金额",
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
        material_keywords = ["材料", "清单", "证明", "证件", "提交什么"]
        process_keywords = ["流程", "步骤", "怎么办", "如何办理", "办理地点", "时限"]
        qualification_keywords = [
            "资格",
            "条件",
            "是否符合",
            "能否申请",
            "能不能申请",
            "还能申请",
            "可以申请",
            "材料不齐全",
            "影响申请",
            "毕业年度",
            "重复申领",
            "不予受理",
            "跨地区",
        ]

        has_material = any(k in q for k in material_keywords)
        has_process = any(k in q for k in process_keywords)

        if any(k in q for k in high_risk_keywords):
            intent: IntentType = "high_risk_decision"
            reason = "问题涉及审批结果、金额或权益裁定等高风险判断"
            confidence = 0.95
        elif has_material and has_process:
            intent = "mixed"
            reason = "问题同时包含材料与流程诉求"
            confidence = 0.9
        elif has_material:
            intent = "material_checklist"
            reason = "问题重点是材料清单"
            confidence = 0.9
        elif has_process:
            intent = "process_plan"
            reason = "问题重点是办理流程"
            confidence = 0.88
        elif any(k in q for k in qualification_keywords):
            intent = "qualification_check"
            reason = "问题重点是资格或条件判断"
            confidence = 0.86
        else:
            intent = "policy_query"
            reason = "问题以政策咨询为主"
            confidence = 0.8

        return ServiceIntent(intent=intent, confidence=confidence, reason=reason)
