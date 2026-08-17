"""Source Tracer MVP: resolve a DOI to authoritative paper metadata."""

from __future__ import annotations

import re

from backend.models.schemas import Paper, SourceResolution, SourceResolutionStatus
from backend.services.crossref import CrossrefClient, CrossrefNotFoundError, CrossrefUnavailableError

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$", re.IGNORECASE)


def normalize_doi(value: str) -> str | None:
    cleaned = value.strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip()
            break
    cleaned = cleaned.rstrip(".,;)")
    return cleaned.lower() if _DOI_RE.fullmatch(cleaned) else None


def _first_string(value: object) -> str | None:
    if isinstance(value, list) and value and isinstance(value[0], str):
        return value[0].strip() or None
    return None


def _publication_year(message: dict[str, object]) -> int | None:
    for key in ("published-print", "published-online", "issued"):
        date = message.get(key)
        if not isinstance(date, dict):
            continue
        parts = date.get("date-parts")
        if (
            isinstance(parts, list)
            and parts
            and isinstance(parts[0], list)
            and parts[0]
            and isinstance(parts[0][0], int)
        ):
            return parts[0][0]
    return None


async def resolve_doi(value: str, client: CrossrefClient) -> SourceResolution:
    doi = normalize_doi(value)
    if doi is None:
        return SourceResolution(
            status=SourceResolutionStatus.CITATION_UNRESOLVED,
            reason="Input is not a valid DOI.",
        )

    try:
        message = await client.fetch_work(doi)
    except CrossrefNotFoundError:
        return SourceResolution(
            status=SourceResolutionStatus.CITATION_UNRESOLVED,
            reason="Crossref has no work for this DOI.",
        )
    except CrossrefUnavailableError:
        return SourceResolution(
            status=SourceResolutionStatus.SOURCE_UNAVAILABLE,
            reason="Crossref is temporarily unavailable or returned invalid data.",
        )

    title = _first_string(message.get("title"))
    if title is None:
        return SourceResolution(
            status=SourceResolutionStatus.SOURCE_UNAVAILABLE,
            reason="Crossref metadata did not include a usable title.",
        )

    canonical_doi = message.get("DOI")
    resolved_doi = canonical_doi.lower() if isinstance(canonical_doi, str) else doi
    return SourceResolution(
        status=SourceResolutionStatus.RESOLVED,
        paper=Paper(
            id=f"doi:{resolved_doi}",
            title=title,
            doi=resolved_doi,
            url=f"https://doi.org/{resolved_doi}",
            year=_publication_year(message),
        ),
    )
