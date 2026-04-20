from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint_exposes_phase_marker() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["phase"] == "phase1"


def test_health_endpoint_reports_service_status() -> None:
    response = client.get("/api/v1/meta/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
