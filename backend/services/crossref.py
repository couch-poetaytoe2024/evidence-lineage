"""Crossref metadata access kept separate from Source Tracer reasoning."""

from __future__ import annotations

from urllib.parse import quote

import httpx


class CrossrefNotFoundError(LookupError):
    """Crossref has no work matching the supplied DOI."""


class CrossrefUnavailableError(RuntimeError):
    """Crossref could not be reached or returned an unusable response."""


class CrossrefClient:
    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        self._http_client = http_client

    async def fetch_work(self, doi: str) -> dict[str, object]:
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "EvidenceLineage/0.1 (research hackathon project)"},
        )
        try:
            response = await client.get(f"{self.BASE_URL}/{quote(doi, safe='')}")
            if response.status_code == 404:
                raise CrossrefNotFoundError(doi)
            response.raise_for_status()
            payload = response.json()
            message = payload.get("message") if isinstance(payload, dict) else None
            if not isinstance(message, dict):
                raise CrossrefUnavailableError("Crossref response has no message object")
            return message
        except CrossrefNotFoundError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            raise CrossrefUnavailableError(str(exc)) from exc
        finally:
            if owns_client:
                await client.aclose()
