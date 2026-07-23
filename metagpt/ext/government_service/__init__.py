"""Government service multi-agent extension."""

from .schema import (
    MaterialItem,
    PolicyEvidence,
    ProcessStep,
    RiskAssessment,
    ServiceIntent,
    ServiceResponse,
    TraceRecord,
)
from .knowledge_base import RAGPolicyKnowledgeBase, SimplePolicyKnowledgeBase, TfidfPolicyKnowledgeBase
from .workflow import GovServiceWorkflow

__all__ = [
    "GovServiceWorkflow",
    "SimplePolicyKnowledgeBase",
    "RAGPolicyKnowledgeBase",
    "TfidfPolicyKnowledgeBase",
    "ServiceIntent",
    "PolicyEvidence",
    "MaterialItem",
    "ProcessStep",
    "RiskAssessment",
    "TraceRecord",
    "ServiceResponse",
]
