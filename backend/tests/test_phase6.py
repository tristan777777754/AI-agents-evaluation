from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )
    assert response.status_code == 201


def _create_run(
    client: TestClient,
    *,
    agent_version_id: str,
    adapter_config: dict[str, object],
) -> str:
    response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": agent_version_id,
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": adapter_config,
        },
    )
    assert response.status_code == 201
    return str(response.json()["run_id"])


def test_compare_api_returns_improvements_and_regressions(client: TestClient) -> None:
    _upload_dataset(client)

    baseline_run_id = _create_run(
        client,
        agent_version_id="av_support_qa_v1",
        adapter_config={
            "failure_map": {"ds_item_003": True},
            "answer_incorrect_map": {"ds_item_005": True},
        },
    )
    candidate_run_id = _create_run(
        client,
        agent_version_id="av_support_qa_v2",
        adapter_config={
            "tool_failure_map": {"ds_item_010": True},
        },
    )

    response = client.get(
        "/api/v1/runs/compare",
        params={
            "baseline_run_id": baseline_run_id,
            "candidate_run_id": candidate_run_id,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["baseline_run_id"] == baseline_run_id
    assert body["candidate_run_id"] == candidate_run_id
    assert body["compared_task_count"] == 12
    assert body["improvement_count"] == 2
    assert body["regression_count"] == 1
    assert body["success_rate"]["baseline"] == 83.33
    assert body["success_rate"]["candidate"] == 91.67
    assert body["success_rate"]["delta"] == 8.34
    assert {item["dataset_item_id"] for item in body["improvements"]} == {
        "ds_item_003",
        "ds_item_005",
    }
    assert body["regressions"][0]["dataset_item_id"] == "ds_item_010"


def test_review_queue_and_task_review_persist_reviewer_verdict(client: TestClient) -> None:
    _upload_dataset(client)

    run_id = _create_run(
        client,
        agent_version_id="av_support_qa_v1",
        adapter_config={
            "failure_map": {"ds_item_003": True},
            "tool_failure_map": {"ds_item_010": True},
        },
    )

    task_response = client.get(f"/api/v1/runs/{run_id}/tasks")
    assert task_response.status_code == 200
    task_run_id = next(
        item["task_run_id"]
        for item in task_response.json()["items"]
        if item["dataset_item_id"] == "ds_item_003"
    )

    queue_response = client.get("/api/v1/reviews/queue")
    assert queue_response.status_code == 200
    queue_body = queue_response.json()
    assert queue_body["total_count"] == 2
    assert queue_body["pending_count"] == 2
    assert queue_body["reviewed_count"] == 0

    review_response = client.put(
        f"/api/v1/task-runs/{task_run_id}/review",
        json={
            "reviewer_id": "reviewer_demo",
            "verdict": "confirmed_issue",
            "failure_label": "execution_failed",
            "note": "The trace shows a deterministic execution failure.",
        },
    )
    assert review_response.status_code == 200
    review_body = review_response.json()
    assert review_body["task_run_id"] == task_run_id
    assert review_body["verdict"] == "confirmed_issue"

    task_detail_response = client.get(f"/api/v1/task-runs/{task_run_id}")
    assert task_detail_response.status_code == 200
    assert task_detail_response.json()["review"]["note"] == (
        "The trace shows a deterministic execution failure."
    )

    queue_refresh = client.get("/api/v1/reviews/queue")
    assert queue_refresh.status_code == 200
    refreshed_body = queue_refresh.json()
    assert refreshed_body["pending_count"] == 1
    assert refreshed_body["reviewed_count"] == 1
    reviewed_entry = next(
        item for item in refreshed_body["items"] if item["task_run_id"] == task_run_id
    )
    assert reviewed_entry["review_status"] == "reviewed"
    assert reviewed_entry["review"]["verdict"] == "confirmed_issue"
