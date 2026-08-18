from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_mentions_workshop():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "From Backend Code to the Cloud" in body["talk"]
    assert "health" in body["hint"]


def test_echo():
    response = client.post("/echo", json={"message": "ship it"})
    assert response.status_code == 200
    assert response.json() == {"ok": True, "echo": "ship it", "ready_for_aws": True}
