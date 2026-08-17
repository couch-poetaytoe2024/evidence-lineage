import asyncio

import httpx

from backend.agents.source_tracer import normalize_doi, resolve_doi
from backend.models.schemas import SourceResolutionStatus
from backend.services.crossref import CrossrefClient


def test_normalizes_doi_urls() -> None:
    assert normalize_doi("https://doi.org/10.1000/ABC.1") == "10.1000/abc.1"
    assert normalize_doi("not a doi") is None


def test_resolves_crossref_metadata() -> None:
    async def scenario() -> object:
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "message": {
                        "DOI": "10.1000/ABC.1",
                        "title": ["A real test paper"],
                        "published-online": {"date-parts": [[2024, 5, 1]]},
                    }
                },
            )
        )
        async with httpx.AsyncClient(transport=transport) as http_client:
            return await resolve_doi("10.1000/abc.1", CrossrefClient(http_client))

    result = asyncio.run(scenario())
    assert result.status == SourceResolutionStatus.RESOLVED
    assert result.paper is not None
    assert result.paper.title == "A real test paper"
    assert result.paper.year == 2024


def test_missing_doi_is_explicitly_unresolved() -> None:
    async def scenario() -> object:
        transport = httpx.MockTransport(lambda request: httpx.Response(404))
        async with httpx.AsyncClient(transport=transport) as http_client:
            return await resolve_doi("10.1000/missing", CrossrefClient(http_client))

    result = asyncio.run(scenario())
    assert result.status == SourceResolutionStatus.CITATION_UNRESOLVED
    assert result.paper is None


def test_network_failure_is_source_unavailable() -> None:
    async def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    async def scenario() -> object:
        transport = httpx.MockTransport(fail)
        async with httpx.AsyncClient(transport=transport) as http_client:
            return await resolve_doi("10.1000/test", CrossrefClient(http_client))

    result = asyncio.run(scenario())
    assert result.status == SourceResolutionStatus.SOURCE_UNAVAILABLE
    assert result.paper is None
