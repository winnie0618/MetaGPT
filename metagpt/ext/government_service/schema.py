from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


IntentType = Literal[
    "policy_query",
    "material_checklist",
    "process_plan",
    "qualification_check",
    "high_risk_decision",
    "mixed",
]

RiskLevel = Literal["low", "medium", "high"]


class ServiceIntent(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = ""


class PolicyEvidence(BaseModel):
    doc_id: str
    title: str
    snippet: str
    score: float = Field(ge=0.0)


class MaterialItem(BaseModel):
    name: str
    required: bool = True
    note: str = ""


class ProcessStep(BaseModel):
    step_no: int = Field(ge=1)
    title: str
    detail: str = ""


class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    human_review_required: bool
    reason: str


class TraceRecord(BaseModel):
    trace_id: str
    query: str
    intent: IntentType
    retrieved_docs: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    human_review_required: bool
    answer: str
    timestamp: datetime


class ServiceResponse(BaseModel):
    direct_answer: str
    policy_evidence: list[PolicyEvidence] = Field(default_factory=list)
    process_steps: list[ProcessStep] = Field(default_factory=list)
    materials: list[MaterialItem] = Field(default_factory=list)
    risk_assessment: RiskAssessment
    human_review_message: str = ""
    trace_id: str
