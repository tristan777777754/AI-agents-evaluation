from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient) -> None:
    with (FIXTURE_DIR / "dataset_valid.json").open("rb") as handle:
        response = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )
    assert response.status_code == 201, response.text


def test_registry_runtime_crud_makes_new_version_immediately_selectable(
    client: TestClient,
) -> None:
    create_agent = client.post(
        "/api/v1/registry/agents",
        json={
            "agent_id": "agent_refund_triage",
            "name": "Refund Triage",
            "description": "Runtime-created agent",
            "owner_id": "ai_eng",
        },
    )
    assert create_agent.status_code == 201, create_agent.text

    create_version = client.post(
        "/api/v1/registry/agent-versions",
        json={
            "agent_version_id": "av_refund_triage_v1",
            "agent_id": "agent_refund_triage",
            "version_name": "v1",
            "model": "gpt-4.1-mini",
            "prompt_hash": "sha256:refund-triage-v1",
            "config_json": {"system_prompt": "Route refund tickets carefully."},
        },
    )
    assert create_version.status_code == 201, create_version.text

    registry = client.get("/api/v1/registry")
    assert registry.status_code == 200, registry.text
    body = registry.json()
    assert any(agent["agent_id"] == "agent_refund_triage" for agent in body["agents"])
    assert any(
        version["agent_version_id"] == "av_refund_triage_v1"
        for version in body["agent_versions"]
    )


def test_quick_run_uses_persisted_defaults_and_auto_compare(client: TestClient) -> None:
    _upload_dataset(client)

    defaults = client.put(
        "/api/v1/registry/defaults",
        json={
            "default_dataset_id": "dataset_support_faq_v1",
            "default_scorer_config_id": "sc_rule_based_v1",
        },
    )
    assert defaults.status_code == 200, defaults.text

    baseline = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_003": True}},
        },
    )
    assert baseline.status_code == 201, baseline.text
    baseline_run_id = baseline.json()["run_id"]
    pin_baseline = client.post(f"/api/v1/runs/{baseline_run_id}/baseline", json={"baseline": True})
    assert pin_baseline.status_code == 200, pin_baseline.text

    quick_run = client.post(
        "/api/v1/runs/quick",
        json={
            "agent_version_id": "av_support_qa_v2",
            "adapter_type": "stub",
            "adapter_config": {},
            "experiment_tag": "phase14-quick",
            "notes": "Quick run path",
        },
    )
    assert quick_run.status_code == 201, quick_run.text
    body = quick_run.json()
    assert body["run"]["dataset_id"] == "dataset_support_faq_v1"
    assert body["run"]["scorer_config_id"] == "sc_rule_based_v1"
    assert body["auto_compare"]["baseline_run_id"] == baseline_run_id
    assert body["auto_compare"]["selection_reason"] == "latest_baseline"
    assert body["auto_compare"]["comparison"]["candidate_run_id"] == body["run"]["run_id"]


def test_runs_endpoint_paginates_and_filters_with_headers(client: TestClient) -> None:
    _upload_dataset(client)

    for agent_version_id in ("av_support_qa_v1", "av_support_qa_v2", "av_support_qa_v1"):
        run = client.post(
            "/api/v1/runs",
            json={
                "dataset_id": "dataset_support_faq_v1",
                "agent_version_id": agent_version_id,
                "scorer_config_id": "sc_rule_based_v1",
                "adapter_type": "stub",
                "adapter_config": {},
            },
        )
        assert run.status_code == 201, run.text

    response = client.get(
        "/api/v1/runs",
        params={"page": 2, "per_page": 1, "agent_version_id": "av_support_qa_v1"},
    )
    assert response.status_code == 200, response.text
    assert response.headers["X-Page"] == "2"
    assert response.headers["X-Per-Page"] == "1"
    assert response.headers["X-Total-Count"] == "2"
    body = response.json()
    assert len(body) == 1
    assert body[0]["agent_version_id"] == "av_support_qa_v1"


def test_dataset_items_and_review_queue_paginate_with_filters(client: TestClient) -> None:
    payload = json.loads((FIXTURE_DIR / "dataset_valid.json").read_text(encoding="utf-8"))
    for index, item in enumerate(payload["items"]):
        item["tags"] = ["priority"] if index < 2 else ["control"]

    upload = client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "dataset_valid.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )
    assert upload.status_code == 201, upload.text

    run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_001": True, "ds_item_002": True}},
        },
    )
    assert run.status_code == 201, run.text
    run_id = run.json()["run_id"]
    tasks = client.get(f"/api/v1/runs/{run_id}/tasks").json()["items"]
    failed_task_id = tasks[0]["task_run_id"]

    review = client.put(
        f"/api/v1/task-runs/{failed_task_id}/review",
        json={
            "reviewer_id": "reviewer_demo",
            "verdict": "confirmed_issue",
            "failure_label": "execution_failed",
            "note": "Reviewed in phase14 test.",
        },
    )
    assert review.status_code == 200, review.text

    item_page = client.get(
        "/api/v1/datasets/dataset_support_faq_v1/items",
        params={"page": 1, "per_page": 1, "tag": "priority"},
    )
    assert item_page.status_code == 200, item_page.text
    item_body = item_page.json()
    assert item_body["total_count"] == 2
    assert item_body["page"] == 1
    assert item_body["per_page"] == 1
    assert item_body["has_next_page"] is True
    assert item_body["items"][0]["tags"] == ["priority"]

    review_queue = client.get(
        "/api/v1/reviews/queue",
        params={"page": 1, "per_page": 1, "review_status": "reviewed"},
    )
    assert review_queue.status_code == 200, review_queue.text
    review_body = review_queue.json()
    assert review_body["page"] == 1
    assert review_body["per_page"] == 1
    assert review_body["items"][0]["review_status"] == "reviewed"
