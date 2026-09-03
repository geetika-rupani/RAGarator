"""Dashboard job API used by the React frontend."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "rag_methods.txt"
client = TestClient(app)


def test_multipart_analyze_returns_job_and_result():
    payload = SAMPLE.read_bytes()
    started = client.post(
        "/api/analyze",
        files={"file": ("rag_methods.txt", payload, "text/plain")},
    )
    assert started.status_code == 202
    job_id = started.json()["jobId"]
    assert job_id

    result = None
    for _ in range(40):
        status = client.get(f"/api/analyze/{job_id}/status")
        assert status.status_code == 200
        body = status.json()
        assert "logs" in body
        if body["status"] == "error":
            raise AssertionError(body["error"])
        if body["status"] == "complete":
            fetched = client.get(f"/api/analyze/{job_id}/result")
            assert fetched.status_code == 200
            result = fetched.json()
            break
        time.sleep(0.15)

    assert result is not None
    assert result["recommendedStrategyId"] in {"fixed", "recursive", "sentence", "token"}
    assert len(result["strategies"]) == 4
    assert result["defaultWeights"]["retrieval"] == 60
    assert result["reasoning"]
    assert result["uncertainty"]["summary"]
    winner = next(item for item in result["strategies"] if item["id"] == result["recommendedStrategyId"])
    assert 0 <= winner["overall"] <= 100
    assert "dims" in winner
    assert winner["evidence"]["text"]
