# EvidenceLineage

**EvidenceLineage** is a multi-agent scientific claim auditor that traces claims backward through citations and checks whether the original evidence actually supports what later papers say.

## Why this exists

A citation can be real while the claim attached to it has drifted. EvidenceLineage focuses on the evidence chain itself: what the primary source reported, how later papers paraphrased it, and whether a later claim became overstated, unsupported, or contradicted.

## Planned agent workflow

1. **Claim Miner** — extracts verifiable claims and attached citations.
2. **Source Tracer** — resolves papers and follows citation chains toward primary evidence.
3. **Evidence Agent** — builds the strongest evidence-based case that a claim is supported.
4. **Skeptic Agent** — independently looks for mismatches, overstatement, changed conditions, or contradictory evidence.
5. **Judge Agent** — compares both sides and produces an auditable verdict.

Target verdicts: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `UNSUPPORTED`, `INSUFFICIENT_EVIDENCE`.

## Current status

Hackathon scaffold is in place. The first implementation target is the **Claim Miner MVP**.

See:

- `AGENTS.md` for persistent Codex/AI instructions
- `docs/PROJECT_SPEC.md` for the product source of truth
- `docs/PROJECT_STATUS.md` for current progress
- `docs/HACKATHON_RULES.md` for the working competition rules

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Local model

Install Ollama, then download the default model:

```powershell
ollama pull qwen3:4b
ollama list
```

The backend connects to Ollama at `http://localhost:11434` and uses `qwen3:4b`
by default. Copy `.env.example` to `.env` if you need different values. Set
`OLLAMA_ENABLED=false` to run only the deterministic Claim Miner.

`POST /claims` uses Ollama unless the request includes `"use_llm": false`. If
Ollama is unavailable or returns invalid data, the response clearly reports that
the deterministic fallback was used.

### Automatic paper investigation

`POST /investigations/paper` accepts a DOI, OpenAlex work ID, paper title, or a
DOI/OpenAlex/PubMed/arXiv paper link:

```json
{
  "identifier": "10.1038/nature12373",
  "max_references": 8,
  "use_llm": true
}
```

The backend resolves the paper through OpenAlex, mines claims from its available
abstract, discovers referenced works automatically, retrieves their available
abstracts as evidence leads, builds citation edges, and asks the Evidence Agent
for a source-ID-grounded support argument. Missing abstracts, unavailable sources,
and unverified claim-to-reference associations are reported as limitations.

Researchers can also provide `claim_text` containing their own claim or paragraph
and use `identifier` for the paper they cite. In this mode the cited paper is treated
as direct retrieved evidence, Evidence and Skeptic independently analyze it, and the
Judge returns a verdict plus a 0–100 claim-support score. If `claim_text` is omitted,
the automatic paper-claim workflow remains available.

The browser uses `POST /investigations/paper/stream`, an NDJSON endpoint that emits
real agent state transitions as they occur and finishes with the complete structured
case. `POST /investigations/paper` remains available for non-streaming API clients.

Run tests:

```bash
pytest
```

## Hackathon focus

The system is deliberately not a generic research chatbot. The submission should demonstrate genuine multi-agent collaboration, traceable evidence, failure handling, a reliable real-world demo case, and practical cost tracking.
