import json

from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app
from backend.models.schemas import ExecutionEvent, ResearchCase, RetrievalStatus


def test_claims_can_explicitly_use_deterministic_path() -> None:
    response = TestClient(app).post(
        "/claims",
        json={
            "text": "Treatment improved recovery by 20% compared with control [4].",
            "use_llm": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["method"] == "heuristic"


def test_investigation_stream_emits_events_and_result(monkeypatch) -> None:
    async def fake_investigation(*args, on_event=None, **kwargs):
        event = ExecutionEvent(agent="claim_miner", status="RUNNING", detail="Mining claims.")
        await on_event(event)
        return ResearchCase(
            status=RetrievalStatus.PARTIAL,
            execution_trace=[event],
            limitations=["Test limitation"],
        )

    monkeypatch.setattr(main_module, "investigate_paper", fake_investigation)
    response = TestClient(app).post(
        "/investigations/paper/stream",
        json={"identifier": "10.1000/test", "use_llm": False},
    )
    messages = [json.loads(line) for line in response.text.splitlines()]
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert [message["type"] for message in messages] == ["event", "result", "complete"]
    assert messages[0]["event"]["status"] == "RUNNING"
