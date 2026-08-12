# EvidenceLineage — Project Specification

## Product definition

EvidenceLineage is a multi-agent scientific claim auditor that traces claims backward through citations to determine whether the original evidence actually supports what later papers say.

The product is about **evidence lineage and citation drift**, not generic paper summarization.

## Core user problem

Scientific statements can become stronger, broader, or numerically different as later papers cite intermediate papers instead of checking the primary evidence. A citation may be valid while the claim attached to it is not.

EvidenceLineage should make that transformation inspectable and auditable.

## Target workflow

Input may eventually be a paper, DOI, PDF, paragraph, or specific claim.

The system should:

1. Extract important verifiable claims and their citations.
2. Resolve cited papers using reliable metadata sources.
3. Follow citations toward likely primary/original evidence.
4. Retrieve the passages/results relevant to the claim.
5. Have an Evidence Agent independently construct the strongest support case.
6. Have a Skeptic Agent independently challenge the claim using the same underlying evidence.
7. Have a Judge Agent compare both arguments and issue a verdict.
8. Preserve evidence, provenance, execution trace, uncertainty, and estimated cost.
9. Visualize the citation/evidence lineage.

## Agent roles

### Claim Miner
Extracts specific verifiable scientific claims, citation markers, and claim type.

### Source Tracer
Resolves citations and follows citation chains using tools such as OpenAlex, Crossref, Semantic Scholar, arXiv, PubMed when appropriate, DOI metadata, and user-provided PDFs.

### Evidence Agent
Finds the strongest legitimate evidence supporting the target claim, including conditions, numbers, methods, relevant passages, and limitations.

### Skeptic Agent
Independently searches for reasons the claim is overstated or unsupported: changed populations, changed conditions, correlation-to-causation shifts, percentage errors, overgeneralization, weak intermediary wording, or contradictory evidence.

### Judge Agent
Compares the target claim, source evidence, support argument, and skeptic challenge. Produces an auditable verdict rather than a free-form answer.

## Verdict set

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `OVERSTATED`
- `CONTRADICTED`
- `UNSUPPORTED`
- `INSUFFICIENT_EVIDENCE`

Confidence values must not be described as statistically calibrated unless actual calibration is implemented.

## Shared state

Prefer typed structures such as:

- `ResearchCase`
- `Claim`
- `Paper`
- `CitationEdge`
- `EvidenceItem`
- `AgentArgument`
- `Verdict`
- `ExecutionEvent`
- `CostRecord`

Use structured state rather than passing all important data as unstructured prose.

## Auditability requirement

A useful final result must expose:

- the target claim
- the citation chain
- the primary evidence used
- relevant source passages/locators
- Evidence Agent argument
- Skeptic Agent challenge
- Judge verdict and limitations
- unresolved source failures
- execution/cost information

## Technical direction

Initial architecture:

```text
React / Next.js frontend
        |
        v
Python + FastAPI backend
        |
        v
Agent orchestrator
  |-- Claim Miner
  |-- Source Tracer
  |-- Evidence Agent
  |-- Skeptic Agent
  `-- Judge Agent
        |
        v
Research APIs + PDF parsing + cache
```

Avoid adopting a large agent framework unless it gives a clear, measurable benefit. A small inspectable Python orchestrator is preferred for the MVP.

Keep model/provider calls behind a narrow abstraction so model policy can change without rewriting the system.

## Demo goal

One excellent real research case is more valuable than many unreliable features. The three-minute demo should visibly show claim extraction, source tracing, evidence retrieval, Evidence/Skeptic disagreement, the Judge verdict, evidence lineage, source inspection, and cost information.

## Non-goals

Do not let the project become primarily:

- a generic research chatbot
- a generic literature-review generator
- a paper summarizer
- a citation formatter
- a generic RAG demo
- an autonomous-scientist claim generator
- five agents chatting without distinct tool/state responsibilities
