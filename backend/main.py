from fastapi import FastAPI

from backend.agents.claim_miner import extract_claims
from backend.models.schemas import ClaimExtractionRequest, ClaimExtractionResponse

app = FastAPI(
    title="EvidenceLineage API",
    description="Multi-agent scientific evidence-lineage auditor.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/claims", response_model=ClaimExtractionResponse)
def mine_claims(request: ClaimExtractionRequest) -> ClaimExtractionResponse:
    return ClaimExtractionResponse(claims=extract_claims(request.text))
