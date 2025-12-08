import os
from fastapi.testclient import TestClient

from services.r1_inference.app.main import get_app


def test_health_check():
    client = TestClient(get_app())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_generate_mock_mode(monkeypatch):
    monkeypatch.setenv("MODEL_MODE", "mock")
    client = TestClient(get_app())

    payload = {"prompt": "Hello", "max_new_tokens": 10, "temperature": 0.0}
    resp = client.post("/generate", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["mode"] == "mock"
    assert body["text"].startswith(payload["prompt"])
    assert "mock" in body["text"]
