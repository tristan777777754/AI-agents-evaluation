from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )
    assert response.status_code == 201


def test_registry_lists_fixture_backed_agent_versions_and_scorers(client: TestClient) -> None:
    response = client.get("/api/v1/registry")

    assert response.status_code == 200
    body = response.json()
    assert {item["agent_version_id"] for item in body["agent_versions"]} == {
        "av_support_qa_v1",
        "av_support_qa_v2",
    }
    assert body["scorer_configs"][0]["scorer_config_id"] == "sc_rule_based_v1"


def test_create_run_persists_completed_task_results(client: TestClient) -> None:
    _upload_dataset(client)

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["total_tasks"] == 12
    assert body["completed_tasks"] == 12
    assert body["failed_tasks"] == 0

    run_id = body["run_id"]
    task_response = client.get(f"/api/v1/runs/{run_id}/tasks")
    assert task_response.status_code == 200
    tasks = task_response.json()
    assert tasks["total_count"] == 12
    assert all(item["status"] == "completed" for item in tasks["items"])
    assert all(item["score"]["pass_fail"] is True for item in tasks["items"])


def test_create_run_isolates_task_failures_into_partial_success(client: TestClient) -> None:
    _upload_dataset(client)

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_003": True, "ds_item_010": True}},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "partial_success"
    assert body["completed_tasks"] == 10
    assert body["failed_tasks"] == 2

    run_id = body["run_id"]
    tasks = client.get(f"/api/v1/runs/{run_id}/tasks").json()["items"]
    failed_task_ids = {task["dataset_item_id"] for task in tasks if task["status"] == "failed"}
    assert failed_task_ids == {"ds_item_003", "ds_item_010"}


def test_run_summary_aggregates_real_metrics_and_failed_cases(client: TestClient) -> None:
    _upload_dataset(client)

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {
                "failure_map": {"ds_item_003": True},
                "answer_incorrect_map": {"ds_item_005": True},
                "tool_failure_map": {"ds_item_010": True},
                "format_failure_map": {"ds_item_012": True},
            },
        },
    )

    assert response.status_code == 201
    run_id = response.json()["run_id"]

    summary_response = client.get(f"/api/v1/runs/{run_id}/summary")

    assert summary_response.status_code == 200
    body = summary_response.json()
    assert body["run_id"] == run_id
    assert body["total_tasks"] == 12
    assert body["successful_tasks"] == 8
    assert body["failed_tasks"] == 4
    assert body["review_needed_count"] == 4
    assert body["success_rate"] == 66.67
    assert body["average_latency_ms"] == 120.0
    assert body["total_cost"] == 0.0108
    assert {item["failure_reason"] for item in body["failed_cases"]} == {
        "execution_failed",
        "answer_incorrect",
        "tool_error",
        "format_error",
    }
    assert {item["failure_reason"]: item["count"] for item in body["failure_breakdown"]} == {
        "answer_incorrect": 1,
        "execution_failed": 1,
        "format_error": 1,
        "tool_error": 1,
    }
    assert any(
        row["category"] == "refund_policy" and row["failed_tasks"] == 1
        for row in body["category_breakdown"]
    )


def test_create_run_returns_404_for_unknown_dataset(client: TestClient) -> None:
    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "missing_dataset",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )

    assert response.status_code == 404


def test_create_run_rejects_unsupported_adapter_type(client: TestClient) -> None:
    _upload_dataset(client)

    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "unknown_adapter",
            "adapter_config": {},
        },
    )

    assert response.status_code == 422


def test_celery_fallback_requires_eager_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "celery":
            raise ModuleNotFoundError("No module named 'celery'")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "false")
    monkeypatch.setattr(builtins, "__import__", fake_import)

    for module_name in ("app.worker.celery_app", "app.config"):
        sys.modules.pop(module_name, None)

    with pytest.raises(RuntimeError, match="Celery is required"):
        importlib.import_module("app.worker.celery_app")

    for module_name in ("app.worker.celery_app", "app.config"):
        sys.modules.pop(module_name, None)
