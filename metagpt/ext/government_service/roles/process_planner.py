from __future__ import annotations

from metagpt.ext.government_service.actions.material_checklist import MaterialChecklistAction
from metagpt.ext.government_service.actions.task_plan import TaskPlanAction
from metagpt.ext.government_service.schema import MaterialItem, PolicyEvidence, ProcessStep


class ProcessPlanner:
    def __init__(self):
        self.task_plan_action = TaskPlanAction()
        self.material_action = MaterialChecklistAction()

    async def build_steps(self, query: str, evidences: list[PolicyEvidence]) -> list[ProcessStep]:
        return await self.task_plan_action.run(query, evidences)

    async def build_materials(self, query: str, evidences: list[PolicyEvidence]) -> list[MaterialItem]:
        return await self.material_action.run(query, evidences)

