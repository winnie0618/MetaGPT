from __future__ import annotations


def contains_hit(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    hit = sum(1 for kw in expected_keywords if kw in answer)
    return hit / len(expected_keywords)
