from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(
    client: TestClient,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    body = payload
    if body is None:
        body = json.loads((FIXTURE_DIR / "dataset_valid.json").read_text(encoding="utf-8"))

    response = client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "dataset_valid.json",
                json.dumps(body).encode("utf-8"),
                "application/json",
            )
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_prompt_generation_creates_draft_and_run_rejects_until_approved(client: TestClient) -> None:
    generated = client.post(
        "/api/v1/datasets/drafts/generate",
        json={
            "name": "Refund Edge Cases",
            "prompt": "Create refund escalation support cases with billing tags.",
            "item_count": 3,
            "tags": ["refunds", "billing"],
        },
    )
    assert generated.status_code == 201, generated.text
    generated_body = generated.json()
    dataset_id = generated_body["dataset_id"]
    assert generated_body["source_origin"] == "generated"
    assert generated_body["lifecycle_status"] == "draft"
    assert generated_body["approval_status"] == "pending_review"

    published_list = client.get("/api/v1/datasets")
    assert published_list.status_code == 200, published_list.text
    assert all(item["dataset_id"] != dataset_id for item in published_list.json())

    draft_list = client.get("/api/v1/datasets/drafts")
    assert draft_list.status_code == 200, draft_list.text
    assert any(item["dataset_id"] == dataset_id for item in draft_list.json()["items"])

    blocked_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert blocked_run.status_code == 400, blocked_run.text
    assert "approved" in blocked_run.json()["detail"]

    approved = client.post(
        f"/api/v1/datasets/{dataset_id}/approve",
        json={"reviewer_id": "reviewer_demo", "note": "Approved for benchmark use."},
    )
    assert approved.status_code == 200, approved.text
    approved_body = approved.json()
    assert approved_body["lifecycle_status"] == "published"
    assert approved_body["approval_status"] == "approved"
    assert approved_body["snapshot_version"] == 2

    snapshots = client.get(f"/api/v1/datasets/{dataset_id}/snapshots")
    assert snapshots.status_code == 200, snapshots.text
    assert (
        snapshots.json()["snapshots"][1]["parent_snapshot_id"]
        == snapshots.json()["snapshots"][0]["dataset_snapshot_id"]
    )


def test_promoted_failed_case_creates_lineage_back_to_task_run(client: TestClient) -> None:
    _upload_dataset(client)

    run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_003": True}},
        },
    )
    assert run.status_code == 201, run.text

    failed_task = next(
        item
        for item in client.get(f"/api/v1/runs/{run.json()['run_id']}/tasks").json()["items"]
        if item["dataset_item_id"] == "ds_item_003"
    )
    review = client.put(
        f"/api/v1/task-runs/{failed_task['task_run_id']}/review",
        json={
            "reviewer_id": "reviewer_demo",
            "verdict": "confirmed_issue",
            "failure_label": "execution_failed",
            "note": "Promote this to regression coverage.",
        },
    )
    assert review.status_code == 200, review.text

    promoted = client.post(
        f"/api/v1/task-runs/{failed_task['task_run_id']}/promote",
        json={
            "target_dataset_id": "dataset_regression_promoted",
            "target_dataset_name": "Regression Promotions",
            "tags": ["refunds", "regression"],
        },
    )
    assert promoted.status_code == 200, promoted.text
    promoted_body = promoted.json()
    assert promoted_body["promoted_item"]["source_origin"] == "promoted_from_failure"
    assert promoted_body["promoted_item"]["source_task_run_id"] == failed_task["task_run_id"]
    assert "regression" in promoted_body["promoted_item"]["tags"]

    dataset_items = client.get("/api/v1/datasets/dataset_regression_promoted/items")
    assert dataset_items.status_code == 200, dataset_items.text
    promoted_item = dataset_items.json()["items"][0]
    assert promoted_item["source_origin"] == "promoted_from_failure"
    assert promoted_item["source_task_run_id"] == failed_task["task_run_id"]


def test_subset_runs_execute_only_matching_tagged_items(client: TestClient) -> None:
    payload = json.loads((FIXTURE_DIR / "dataset_valid.json").read_text(encoding="utf-8"))
    for index, item in enumerate(payload["items"]):
        if index < 3:
            item["tags"] = ["subset", "refunds"]
        else:
            item["tags"] = ["control"]

    _upload_dataset(client, payload)

    subset_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "dataset_tag_filter": ["subset"],
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert subset_run.status_code == 201, subset_run.text
    subset_body = subset_run.json()
    assert subset_body["dataset_tag_filter"] == ["subset"]
    assert subset_body["total_tasks"] == 3

    tasks = client.get(f"/api/v1/runs/{subset_body['run_id']}/tasks")
    assert tasks.status_code == 200, tasks.text
    assert tasks.json()["total_count"] == 3
    assert all("subset" in item["dataset_item_tags"] for item in tasks.json()["items"])
