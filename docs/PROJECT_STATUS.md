# Project Status

## Current milestone

Claim Miner MVP

## Working

- Public GitHub repository exists on `main`.
- Persistent AI/Codex instructions defined in `AGENTS.md`.
- Core project specification and hackathon constraints documented.
- FastAPI skeleton includes `/health` and `/claims` endpoints.
- Shared Pydantic claim/evidence/verdict models started.
- Deterministic Claim Miner baseline extracts sentence-level candidate claims, simple citation markers, and coarse claim types.
- Claim Miner unit tests added.

## In progress

- Improve Claim Miner semantics and eventually connect it to a model-provider abstraction while retaining deterministic tests.

## Not started

- LLM provider abstraction
- Source Tracer
- OpenAlex/Crossref/Semantic Scholar integrations
- PDF parsing
- Evidence Agent
- Skeptic Agent
- Judge Agent
- Orchestrator/shared ResearchCase state
- Cost tracking
- Execution trace
- Frontend
- Citation-lineage graph
- Final demo case

## Known limitations

- Current Claim Miner is heuristic, not semantically robust.
- Citation extraction only handles basic numeric brackets and simple author-year forms.
- No external research-source retrieval exists yet.
- Hackathon model-policy wording is still ambiguous in the supplied event copy.

## Decisions

- Keep EvidenceLineage focused on evidence lineage/citation drift rather than generic research assistance.
- Favor a lightweight inspectable Python orchestrator over a large agent framework for the MVP.
- Evidence and Skeptic agents must independently inspect source evidence.
- Never hallucinate through missing sources; expose failure states instead.

## Next recommended task

Implement the **LLM provider abstraction + structured Claim Miner path** while preserving the deterministic fallback and current tests.

## Last updated

2026-08-12
