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


def test_task_run_detail_and_trace_detail_expose_tool_failure_case(client: TestClient) -> None:
    _upload_dataset(client)

    run_response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"tool_failure_map": {"ds_item_003": True}},
        },
    )

    assert run_response.status_code == 201
    run_body = run_response.json()
    failed_task = next(
        item
        for item in client.get(f"/api/v1/runs/{run_body['run_id']}/tasks").json()["items"]
        if item["dataset_item_id"] == "ds_item_003"
    )

    task_detail = client.get(f"/api/v1/task-runs/{failed_task['task_run_id']}")
    assert task_detail.status_code == 200
    task_body = task_detail.json()
    assert task_body["failure_reason"] == "tool_error"
    assert task_body["trace_summary"]["tool_count"] == 1

    trace_detail = client.get(f"/api/v1/task-runs/{failed_task['task_run_id']}/trace")
    assert trace_detail.status_code == 200
    trace_body = trace_detail.json()
    assert trace_body["failure_reason"] == "tool_error"
    assert trace_body["summary"]["error_flag"] is True
    assert trace_body["events"][1]["event_type"] == "tool_call"
    assert trace_body["events"][1]["status"] == "error"


def test_trace_classification_distinguishes_answer_and_format_failures(client: TestClient) -> None:
    _upload_dataset(client)

    run_response = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {
                "answer_incorrect_map": {"ds_item_004": True},
                "format_failure_map": {"ds_item_005": True},
                "tool_call_map": {"ds_item_004": True},
            },
        },
    )

    assert run_response.status_code == 201
    tasks = client.get(f"/api/v1/runs/{run_response.json()['run_id']}/tasks").json()["items"]

    answer_task = next(item for item in tasks if item["dataset_item_id"] == "ds_item_004")
    format_task = next(item for item in tasks if item["dataset_item_id"] == "ds_item_005")

    assert answer_task["failure_reason"] == "answer_incorrect"
    assert answer_task["score"]["pass_fail"] is False
    assert answer_task["trace_summary"]["tool_count"] == 1

    assert format_task["failure_reason"] == "format_error"
    assert format_task["score"]["formatting"] == 0.0

    format_trace = client.get(f"/api/v1/task-runs/{format_task['task_run_id']}/trace")
    assert format_trace.status_code == 200
    assert format_trace.json()["events"][1]["event_type"] == "format_error"
