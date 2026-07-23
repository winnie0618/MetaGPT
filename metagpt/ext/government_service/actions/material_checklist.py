from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence


class MaterialChecklistAction(Action):
    name: str = "MaterialChecklistAction"

    async def run(self, query: str, evidences: list[PolicyEvidence] | None = None) -> list[MaterialItem]:
        _ = query
        extracted = self._extract_from_evidences(evidences)
        if extracted:
            return extracted
        return [
            MaterialItem(name="身份证明", required=True, note="用于核验申请人身份"),
            MaterialItem(name="毕业证书", required=True, note="用于证明高校毕业生身份"),
            MaterialItem(name="就业或创业证明", required=True, note="用于核验补贴申请类型"),
            MaterialItem(name="银行卡信息", required=False, note="部分地区用于补贴发放"),
        ]

    @staticmethod
    def _extract_from_evidences(evidences: list[PolicyEvidence] | None) -> list[MaterialItem]:
        if not evidences:
            return []

        combined_text = "\n".join(f"{e.title}\n{e.snippet}" for e in evidences).lower()
        matched: list[tuple[str, bool, str]] = []
        rules = [
            ("身份证明", True, "身份证明"),
            ("毕业证书", True, "毕业证书"),
            ("就业协议", True, "就业协议"),
            ("创业证明", True, "创业证明"),
            ("银行卡信息", False, "银行卡"),
            ("申请表", True, "申请表"),
            ("承诺书", False, "承诺书"),
        ]

        for material_name, required, keyword in rules:
            if keyword in combined_text:
                matched.append((material_name, required, f"根据政策证据识别出的{material_name}"))

        if not matched:
            return []

        return [MaterialItem(name=name, required=required, note=note) for name, required, note in matched]
