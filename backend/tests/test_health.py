from fastapi.testclient import TestClient


def test_root_endpoint_exposes_phase_marker(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["phase"] == "phase7"


def test_health_endpoint_reports_service_status(client: TestClient) -> None:
    response = client.get("/api/v1/meta/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["phase"] == "phase7"
