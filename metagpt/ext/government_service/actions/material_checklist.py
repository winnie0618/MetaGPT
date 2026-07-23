from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence


class MaterialChecklistAction(Action):
    name: str = "MaterialChecklistAction"

    async def run(self, query: str, evidences: list[PolicyEvidence] | None = None) -> list[MaterialItem]:
        _ = query, evidences
        return [
            MaterialItem(name="身份证明", required=True, note="用于核验申请人身份"),
            MaterialItem(name="毕业证书", required=True, note="用于证明高校毕业生身份"),
            MaterialItem(name="就业或创业证明", required=True, note="用于核验补贴申请类型"),
            MaterialItem(name="银行卡信息", required=False, note="部分地区用于补贴发放"),
        ]
