from fastapi.testclient import TestClient

from backend.main import app


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
