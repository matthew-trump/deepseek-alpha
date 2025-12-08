from fastapi.testclient import TestClient

from services.rag_api.app.inference import get_inference_client
from services.rag_api.app.main import get_app


class FakeClient:
    def __init__(self, value: str = "stubbed") -> None:
        self.value = value

    def generate(self, prompt: str, max_new_tokens: int, temperature: float) -> str:  # noqa: ARG002
        return f"{self.value}: {prompt}"


def override_client():
    return FakeClient()


def test_health_check():
    client = TestClient(get_app())
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_uses_client(monkeypatch):
    app = get_app()
    app.dependency_overrides = {}
    app.dependency_overrides[get_inference_client] = override_client
    client = TestClient(app)

    resp = client.post("/chat", json={"prompt": "hello", "max_new_tokens": 10, "temperature": 0.0})
    assert resp.status_code == 200
    assert resp.json()["text"].startswith("stubbed")


def test_reason_returns_depth(monkeypatch):
    app = get_app()
    app.dependency_overrides = {}
    app.dependency_overrides[get_inference_client] = override_client
    client = TestClient(app)

    resp = client.post(
        "/reason",
        json={"prompt": "reason", "max_new_tokens": 10, "temperature": 0.0, "depth": 2},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["text"].startswith("stubbed")
    assert body["depth"] == 2
