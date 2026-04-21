from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.models import EvalRunRecord, EvalTaskRunRecord

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient, fixture_name: str = "dataset_valid.json") -> str:
    with (FIXTURE_DIR / fixture_name).open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": (fixture_name, handle, "application/json")},
        )
    assert response.status_code == 201
    return str(response.json()["dataset"]["dataset_id"])


def _create_run(
    client: TestClient,
    *,
    dataset_id: str,
    agent_version_id: str = "av_support_qa_v1",
    scorer_config_id: str = "sc_rule_based_v1",
    adapter_type: str = "stub",
    adapter_config: dict[str, object] | None = None,
) -> str:
    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": agent_version_id,
            "scorer_config_id": scorer_config_id,
            "adapter_type": adapter_type,
            "adapter_config": adapter_config or {},
        },
    )
    assert response.status_code == 201
    return str(response.json()["run_id"])


def _task_map(client: TestClient, run_id: str) -> dict[str, dict[str, object]]:
    response = client.get(f"/api/v1/runs/{run_id}/tasks")
    assert response.status_code == 200
    return {item["dataset_item_id"]: item for item in response.json()["items"]}


def test_rerun_only_reexecutes_failed_or_pending_tasks(client: TestClient) -> None:
    dataset_id = _upload_dataset(client)
    run_id = _create_run(
        client,
        dataset_id=dataset_id,
        adapter_config={"failure_map": {"ds_item_003": True, "ds_item_010": True}},
    )

    before = _task_map(client, run_id)
    completed_before = before["ds_item_001"]
    failed_before = before["ds_item_003"]

    with SessionLocal() as session:
        pending_task = session.get(EvalTaskRunRecord, before["ds_item_010"]["task_run_id"])
        assert pending_task is not None
        pending_task.status = "pending"
        pending_task.final_output = None
        pending_task.completed_at = None
        session.commit()

    rerun = client.post(f"/api/v1/runs/{run_id}/rerun")
    assert rerun.status_code == 200
    assert rerun.json()["status"] == "partial_success"

    after = _task_map(client, run_id)
    completed_after = after["ds_item_001"]
    failed_after = after["ds_item_003"]
    pending_after = after["ds_item_010"]

    assert completed_after["started_at"] == completed_before["started_at"]
    assert completed_after["completed_at"] == completed_before["completed_at"]
    assert completed_after["final_output"] == completed_before["final_output"]

    assert failed_after["started_at"] != failed_before["started_at"]
    assert failed_after["completed_at"] != failed_before["completed_at"]
    assert failed_after["status"] == "failed"
    assert pending_after["status"] == "failed"


def test_invalid_run_status_transition_returns_conflict(client: TestClient) -> None:
    dataset_id = _upload_dataset(client)
    run_id = _create_run(client, dataset_id=dataset_id)

    response = client.post(f"/api/v1/runs/{run_id}/status", json={"status": "running"})

    assert response.status_code == 409
    assert "completed -> running" in response.json()["detail"]

    detail = client.get(f"/api/v1/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"


def test_repair_endpoint_recomputes_inconsistent_aggregation(client: TestClient) -> None:
    dataset_id = _upload_dataset(client)
    run_id = _create_run(client, dataset_id=dataset_id)

    with SessionLocal() as session:
        run = session.get(EvalRunRecord, run_id)
        assert run is not None
        run.completed_tasks = 0
        run.failed_tasks = 7
        session.commit()

    repair = client.post(f"/api/v1/runs/{run_id}/repair")

    assert repair.status_code == 200
    body = repair.json()
    assert body["completed_tasks"] == 20
    assert body["failed_tasks"] == 0
    assert body["status"] == "completed"


def test_replay_manifest_produces_deterministic_summary(client: TestClient) -> None:
    manifest = json.loads((FIXTURE_DIR / "replay_manifest.json").read_text(encoding="utf-8"))
    dataset_id = _upload_dataset(client, str(manifest["dataset_fixture"]))

    run_ids = [
        _create_run(
            client,
            dataset_id=dataset_id,
            agent_version_id=str(manifest["agent_version_id"]),
            scorer_config_id=str(manifest["scorer_config_id"]),
            adapter_type=str(manifest["adapter_type"]),
            adapter_config=dict(manifest["adapter_config"]),
        )
        for _ in range(2)
    ]

    summaries = []
    for run_id in run_ids:
        response = client.get(f"/api/v1/runs/{run_id}/summary")
        assert response.status_code == 200
        summaries.append(response.json())

    expected_summary = manifest["expected_summary"]
    assert (
        summaries[0]["success_rate"]
        == summaries[1]["success_rate"]
        == expected_summary["success_rate"]
    )
    assert (
        summaries[0]["average_latency_ms"]
        == summaries[1]["average_latency_ms"]
        == expected_summary["average_latency_ms"]
    )
    assert summaries[0]["category_breakdown"] == summaries[1]["category_breakdown"]
    for expected in expected_summary["category_breakdown"]:
        actual = next(
            row
            for row in summaries[0]["category_breakdown"]
            if row["category"] == expected["category"]
        )
        assert actual["success_rate"] == expected["success_rate"]
        assert actual["failed_tasks"] == expected["failed_tasks"]
