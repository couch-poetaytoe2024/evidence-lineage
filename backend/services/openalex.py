"""OpenAlex paper discovery, reference traversal, and abstract reconstruction."""

from __future__ import annotations

import re
from urllib.parse import quote
from urllib.parse import unquote, urlparse

import httpx


class OpenAlexError(RuntimeError):
    pass


class OpenAlexNotFoundError(OpenAlexError):
    pass


class OpenAlexClient:
    BASE_URL = "https://api.openalex.org"

    def __init__(self, http_client: httpx.AsyncClient | None = None, *, contact_email: str | None = None) -> None:
        self._http_client = http_client
        self.contact_email = contact_email

    async def resolve_work(self, identifier: str) -> dict[str, object]:
        cleaned = normalize_paper_identifier(identifier)
        if cleaned.lower().startswith(("10.", "https://doi.org/", "http://doi.org/")):
            doi = cleaned.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
            path = f"/works/https://doi.org/{quote(doi, safe='/')}"
            return await self._get_object(path)
        if cleaned.upper().startswith("W") and cleaned[1:].isdigit():
            return await self._get_object(f"/works/{cleaned.upper()}")
        if cleaned.lower().startswith("pmid:") and cleaned[5:].isdigit():
            return await self._get_object(f"/works/{cleaned.lower()}")
        results = await self._get_object("/works", params={"search": cleaned, "per-page": "1"})
        items = results.get("results")
        if not isinstance(items, list) or not items or not isinstance(items[0], dict):
            raise OpenAlexNotFoundError(cleaned)
        return items[0]

    async def get_works(self, ids: list[str]) -> list[dict[str, object]]:
        if not ids:
            return []
        short_ids = [item.rsplit("/", 1)[-1] for item in ids[:25]]
        payload = await self._get_object(
            "/works",
            params={"filter": f"openalex_id:{'|'.join(short_ids)}", "per-page": str(len(short_ids))},
        )
        results = payload.get("results")
        return [item for item in results if isinstance(item, dict)] if isinstance(results, list) else []

    async def _get_object(self, path: str, params: dict[str, str] | None = None) -> dict[str, object]:
        owns_client = self._http_client is None
        headers = {"User-Agent": "EvidenceLineage/0.1"}
        query = dict(params or {})
        if self.contact_email:
            query["mailto"] = self.contact_email
        client = self._http_client or httpx.AsyncClient(timeout=20.0, headers=headers)
        try:
            response = await client.get(f"{self.BASE_URL}{path}", params=query)
            if response.status_code == 404:
                raise OpenAlexNotFoundError(path)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise OpenAlexError("OpenAlex returned non-object JSON")
            return payload
        except OpenAlexNotFoundError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise OpenAlexError(str(exc)) from exc
        finally:
            if owns_client:
                await client.aclose()


_DOI_IN_TEXT = re.compile(r"10\.\d{4,9}/[^\s?#]+", re.IGNORECASE)


def normalize_paper_identifier(identifier: str) -> str:
    """Convert common scholarly URLs to identifiers OpenAlex can resolve."""
    cleaned = identifier.strip()
    if not cleaned:
        raise OpenAlexNotFoundError("empty identifier")
    if not cleaned.lower().startswith(("http://", "https://")):
        return cleaned
    parsed = urlparse(cleaned)
    host = parsed.netloc.lower().removeprefix("www.")
    path = unquote(parsed.path).strip("/")
    if host == "doi.org":
        return path
    if host in {"openalex.org", "explore.openalex.org"}:
        match = re.search(r"(?:^|/)(W\d+)(?:$|/)", path, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    if host in {"pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov"}:
        match = re.search(r"(?:pubmed/)?(\d+)", path)
        if match:
            return f"pmid:{match.group(1)}"
    if host in {"arxiv.org", "export.arxiv.org"}:
        match = re.search(r"(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", path, re.IGNORECASE)
        if match:
            return f"arXiv:{match.group(1)}"
    doi_match = _DOI_IN_TEXT.search(unquote(cleaned))
    if doi_match:
        return doi_match.group(0).rstrip(".,;)")
    raise OpenAlexNotFoundError(
        "Unsupported URL. Use a DOI, OpenAlex, PubMed, or arXiv paper link."
    )


def reconstruct_abstract(index: object) -> str | None:
    if not isinstance(index, dict):
        return None
    positions: list[tuple[int, str]] = []
    for word, values in index.items():
        if not isinstance(word, str) or not isinstance(values, list):
            continue
        positions.extend((pos, word) for pos in values if isinstance(pos, int))
    return " ".join(word for _, word in sorted(positions)) or None
