"""API-level tests for upload validation and analyze wiring."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLE = Path(__file__).resolve().parents[2] / "samples" / "rag_methods.txt"
client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_rejects_bad_extension():
    response = client.post(
        "/api/upload",
        files={"file": ("notes.exe", b"not a document", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "UNSUPPORTED_FILE"


def test_analyze_unknown_file():
    response = client.post("/api/analyze", json={"file_id": "missingfile1234"})
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "FILE_NOT_FOUND"


def test_upload_and_analyze_sample():
    payload = SAMPLE.read_bytes()
    uploaded = client.post(
        "/api/upload",
        files={"file": ("rag_methods.txt", payload, "text/plain")},
    )
    assert uploaded.status_code == 200
    file_id = uploaded.json()["file_id"]
    analyzed = client.post("/api/analyze", json={"file_id": file_id})
    assert analyzed.status_code == 200
    body = analyzed.json()
    assert body["recommendation"]["recommended_strategy"]
    assert len(body["recommendation"]["ranking"]) == 4
    assert body["document"]["char_count"] > 80
