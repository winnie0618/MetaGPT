from __future__ import annotations

from metagpt.actions import Action
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence


class MaterialChecklistAction(Action):
    name: str = "MaterialChecklistAction"

    async def run(self, query: str, evidences: list[PolicyEvidence] | None = None) -> list[MaterialItem]:
        extracted = self._extract_from_context(query, evidences)
        if extracted:
            return extracted
        return [
            MaterialItem(name="身份证明", required=True, note="用于核验申请人身份"),
            MaterialItem(name="毕业证书", required=True, note="用于证明高校毕业生身份"),
            MaterialItem(name="就业或创业证明", required=True, note="用于核验补贴申请类型"),
            MaterialItem(name="银行卡信息", required=False, note="部分地区用于补贴发放"),
        ]

    @staticmethod
    def _extract_from_context(query: str, evidences: list[PolicyEvidence] | None) -> list[MaterialItem]:
        evidence_text = "\n".join(f"{e.title}\n{e.snippet}" for e in evidences or [])
        combined_text = f"{query}\n{evidence_text}".lower()
        matched: list[tuple[str, bool, str]] = []
        rules: list[tuple[str, bool, tuple[str, ...], str]] = [
            (
                "身份证明",
                True,
                ("身份证明", "身份证", "居民身份证", "身份材料", "身份信息", "身份证号", "申请人身份"),
                "用于核验申请人身份和实名信息。",
            ),
            (
                "毕业证书",
                True,
                ("毕业证书", "毕业证", "学历证明", "高校毕业生身份", "毕业年度", "毕业证明"),
                "用于证明高校毕业生身份、毕业年度或学历信息。",
            ),
            (
                "就业协议",
                True,
                ("就业协议", "劳动合同", "就业证明", "就业证明材料", "就业材料"),
                "用于证明就业状态或劳动关系。",
            ),
            (
                "创业证明",
                True,
                ("创业证明", "营业执照", "创业材料", "创业证明材料", "自主创业", "首次创业"),
                "用于证明创业状态、经营主体或创业补贴申请类型。",
            ),
            (
                "银行卡信息",
                False,
                ("银行卡信息", "银行卡", "银行账户", "账户信息", "收款账户", "资金账户", "到账"),
                "用于补贴发放、资金到账或账户核验。",
            ),
            (
                "申请表",
                True,
                ("申请表", "申请书", "申报表", "申请材料表"),
                "用于记录申请人基础信息和申请事项。",
            ),
            (
                "承诺书",
                False,
                ("承诺书", "诚信承诺", "真实性承诺"),
                "用于承诺材料真实性和申请合规性。",
            ),
        ]

        for material_name, required, aliases, note in rules:
            if any(alias in combined_text for alias in aliases):
                matched.append((material_name, required, note))

        if not matched:
            return []

        return [MaterialItem(name=name, required=required, note=note) for name, required, note in matched]
