from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.agents.claim_miner import mine_claims
from backend.agents.source_tracer import resolve_doi
from backend.config import Settings
from backend.models.schemas import (
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    HealthResponse,
    PaperInvestigationRequest,
    ResearchCase,
    SourceResolution,
    SourceResolutionRequest,
)
from backend.orchestration.paper_investigation import investigate_paper
from backend.services.crossref import CrossrefClient
from backend.services.ollama import OllamaClient
from backend.services.openalex import OpenAlexClient

settings = Settings.from_env()

app = FastAPI(
    title="EvidenceLineage API",
    description="Multi-agent scientific evidence-lineage auditor.",
    version="0.1.0",
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

if settings.ollama_enabled:
    app.state.llm_client = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
    )


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse("frontend/index.html")


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    client = getattr(app.state, "llm_client", None)
    available = await client.is_available() if isinstance(client, OllamaClient) else False
    return HealthResponse(
        status="ok",
        llm_provider="ollama" if client is not None else "none",
        llm_model=client.model if isinstance(client, OllamaClient) else None,
        llm_available=available,
    )


@app.post("/claims", response_model=ClaimExtractionResponse)
async def claims_endpoint(request: ClaimExtractionRequest) -> ClaimExtractionResponse:
    # Provider implementations can be configured at startup without coupling the
    # agent to a vendor SDK. With none configured, the deterministic miner is used.
    client = getattr(app.state, "llm_client", None) if request.use_llm else None
    return await mine_claims(request.text, client=client)


@app.post("/sources/resolve-doi", response_model=SourceResolution)
async def resolve_doi_endpoint(request: SourceResolutionRequest) -> SourceResolution:
    return await resolve_doi(request.doi, CrossrefClient())


@app.post("/investigations/paper", response_model=ResearchCase)
async def investigate_paper_endpoint(request: PaperInvestigationRequest) -> ResearchCase:
    llm = getattr(app.state, "llm_client", None) if request.use_llm else None
    return await investigate_paper(
        request.identifier,
        openalex=OpenAlexClient(contact_email=settings.contact_email),
        llm=llm,
        max_references=request.max_references,
        claim_text=request.claim_text,
    )
