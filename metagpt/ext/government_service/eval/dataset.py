from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class EvalSample(BaseModel):
    id: str
    query: str
    intent: str = ""
    expected_answer_contains: list[str] = Field(default_factory=list)
    expected_risk_level: str = ""
    expected_human_review_required: bool = False
    expected_evidence_keywords: list[str] = Field(default_factory=list)


def load_samples(path: str | Path) -> list[EvalSample]:
    samples: list[EvalSample] = []
    p = Path(path)
    if not p.exists():
        return samples
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(EvalSample.model_validate(json.loads(line)))
    return samples
