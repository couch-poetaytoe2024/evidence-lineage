from backend.agents.claim_miner import extract_claims
from backend.models.schemas import ClaimType


def test_extracts_quantitative_claim_and_citation() -> None:
    text = "Our approach increased classification accuracy by 40% compared with the baseline [12]."
    claims = extract_claims(text)

    assert len(claims) == 1
    assert claims[0].citation == "12"
    assert claims[0].claim_type == ClaimType.QUANTITATIVE
    assert "40%" in claims[0].text


def test_empty_text_returns_no_claims() -> None:
    assert extract_claims("   ") == []


def test_short_fragment_is_ignored() -> None:
    assert extract_claims("Results were good.") == []
