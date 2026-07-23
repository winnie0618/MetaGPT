from __future__ import annotations


def contains_hit(answer: str, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    hit = sum(1 for kw in expected_keywords if kw in answer)
    return hit / len(expected_keywords)


def keyword_hit_rate(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    hit = sum(1 for kw in keywords if kw in text)
    return hit / len(keywords)


def exact_match(value: str, expected: str) -> float:
    return 1.0 if value == expected else 0.0


def bool_match(value: bool, expected: bool) -> float:
    return 1.0 if value == expected else 0.0
