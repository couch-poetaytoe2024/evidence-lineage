"""Claim Miner MVP.

This deterministic implementation is intentionally small and testable. It gives the
project a working baseline before we connect an LLM provider. It extracts sentence-like
claims, detects simple citation markers, and assigns a coarse claim type.
"""

from __future__ import annotations

import re

from backend.models.schemas import Claim, ClaimType

_CITATION_RE = re.compile(r"(?:\[(?P<bracket>\d+(?:\s*,\s*\d+)*)\]|\((?P<author>[A-Z][A-Za-z-]+(?:\s+et\s+al\.)?,?\s+\d{4})\))")
_PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_CAUSAL_WORDS = ("caused", "causes", "led to", "results in", "resulted in", "because of")
_COMPARATIVE_WORDS = ("higher than", "lower than", "more than", "less than", "compared with", "compared to", "outperformed", "improved")


def _sentences(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]


def _claim_type(sentence: str) -> ClaimType:
    lowered = sentence.lower()
    if _PERCENT_RE.search(sentence) or _NUMBER_RE.search(sentence):
        return ClaimType.QUANTITATIVE
    if any(word in lowered for word in _CAUSAL_WORDS):
        return ClaimType.CAUSAL
    if any(word in lowered for word in _COMPARATIVE_WORDS):
        return ClaimType.COMPARATIVE
    return ClaimType.GENERAL


def _citation(sentence: str) -> str | None:
    match = _CITATION_RE.search(sentence)
    if not match:
        return None
    return match.group("bracket") or match.group("author")


def extract_claims(text: str) -> list[Claim]:
    """Extract a lightweight set of candidate scientific claims from text.

    This is a baseline, not the final semantic claim extractor. Future versions can
    replace/augment it with an LLM while retaining the same typed output contract.
    """
    claims: list[Claim] = []
    for index, sentence in enumerate(_sentences(text), start=1):
        # Skip extremely short fragments that are unlikely to be useful claims.
        if len(sentence.split()) < 5:
            continue
        claims.append(
            Claim(
                id=f"claim_{index:03d}",
                text=sentence,
                citation=_citation(sentence),
                claim_type=_claim_type(sentence),
            )
        )
    return claims
