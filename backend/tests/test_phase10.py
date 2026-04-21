from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _upload_dataset(client: TestClient, payload: dict[str, object]) -> dict[str, object]:
    response = client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "dataset_valid.json",
                json.dumps(payload).encode("utf-8"),
                "application/json",
            )
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _load_dataset_fixture() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "dataset_valid.json").read_text(encoding="utf-8"))


def test_dataset_snapshots_are_immutable_and_diffable(client: TestClient) -> None:
    payload_v1 = _load_dataset_fixture()
    upload_v1 = _upload_dataset(client, payload_v1)
    snapshot_v1 = upload_v1["snapshot_id"]

    payload_v2 = _load_dataset_fixture()
    items_v2 = list(payload_v2["items"])
    items_v2[1]["expected_output"] = "Refunds for annual plans are available within 21 days."
    items_v2 = [item for item in items_v2 if item["dataset_item_id"] != "ds_item_020"]
    items_v2.append(
        {
            "dataset_item_id": "ds_item_021",
            "input_text": "Can enterprise admins enforce SSO for all members?",
            "category": "security",
            "difficulty": "medium",
            "expected_output": (
                "Yes. Enterprise admins can require SSO enforcement for all members."
            ),
            "metadata_json": {"source": "phase10"},
        }
    )
    payload_v2["items"] = items_v2

    upload_v2 = _upload_dataset(client, payload_v2)
    snapshot_v2 = upload_v2["snapshot_id"]

    assert snapshot_v1 == "dataset_support_faq_v1__snapshot_001"
    assert snapshot_v2 == "dataset_support_faq_v1__snapshot_002"

    original_items = client.get(
        "/api/v1/datasets/dataset_support_faq_v1/items",
        params={"snapshot_id": snapshot_v1},
    )
    latest_items = client.get(
        "/api/v1/datasets/dataset_support_faq_v1/items",
        params={"snapshot_id": snapshot_v2},
    )
    diff = client.get(
        "/api/v1/datasets/dataset_support_faq_v1/diff",
        params={"from_snapshot": snapshot_v1, "to_snapshot": snapshot_v2},
    )

    assert original_items.status_code == 200
    assert latest_items.status_code == 200
    assert diff.status_code == 200

    original_body = original_items.json()
    latest_body = latest_items.json()
    diff_body = diff.json()

    assert original_body["snapshot_id"] == snapshot_v1
    assert latest_body["snapshot_id"] == snapshot_v2
    assert any(item["dataset_item_id"] == "ds_item_020" for item in original_body["items"])
    assert not any(item["dataset_item_id"] == "ds_item_020" for item in latest_body["items"])
    assert any(item["dataset_item_id"] == "ds_item_021" for item in latest_body["items"])
    assert diff_body["added_count"] == 1
    assert diff_body["removed_count"] == 1
    assert diff_body["changed_count"] == 1
    assert diff_body["added"][0]["dataset_item_id"] == "ds_item_021"
    assert diff_body["removed"][0]["dataset_item_id"] == "ds_item_020"
    assert diff_body["changed"][0]["dataset_item_id"] == "ds_item_002"


def test_run_baseline_and_compare_lineage_are_persisted(client: TestClient) -> None:
    payload = _load_dataset_fixture()
    upload_v1 = _upload_dataset(client, payload)
    snapshot_v1 = upload_v1["snapshot_id"]

    baseline_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_003": True}},
            "experiment_tag": "baseline-governance",
            "notes": "Phase 10 baseline candidate run",
        },
    )
    assert baseline_run.status_code == 201, baseline_run.text
    baseline_body = baseline_run.json()
    assert baseline_body["dataset_snapshot_id"] == snapshot_v1
    assert baseline_body["experiment_tag"] == "baseline-governance"
    assert baseline_body["notes"] == "Phase 10 baseline candidate run"

    pinned = client.post(
        f"/api/v1/runs/{baseline_body['run_id']}/baseline",
        json={"baseline": True},
    )
    assert pinned.status_code == 200, pinned.text
    assert pinned.json()["baseline"] is True

    payload_v2 = _load_dataset_fixture()
    payload_v2["items"][0]["expected_output"] = (
        "Annual subscriptions can be refunded within 14 days."
    )
    upload_v2 = _upload_dataset(client, payload_v2)
    snapshot_v2 = upload_v2["snapshot_id"]

    candidate_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
            "experiment_tag": "candidate-governance",
            "notes": "Uses updated dataset snapshot.",
        },
    )
    assert candidate_run.status_code == 201, candidate_run.text
    candidate_body = candidate_run.json()
    assert candidate_body["dataset_snapshot_id"] == snapshot_v2

    run_list = client.get("/api/v1/runs")
    assert run_list.status_code == 200
    listed_baseline = next(
        item for item in run_list.json() if item["run_id"] == baseline_body["run_id"]
    )
    assert listed_baseline["baseline"] is True

    comparison = client.get(
        "/api/v1/runs/compare",
        params={
            "baseline_run_id": baseline_body["run_id"],
            "candidate_run_id": candidate_body["run_id"],
        },
    )
    assert comparison.status_code == 200, comparison.text
    comparison_body = comparison.json()

    assert comparison_body["lineage"]["baseline"]["dataset_snapshot_id"] == snapshot_v1
    assert comparison_body["lineage"]["candidate"]["dataset_snapshot_id"] == snapshot_v2
    assert comparison_body["lineage"]["baseline"]["baseline"] is True
    assert comparison_body["lineage"]["candidate"]["baseline"] is False
    assert (
        comparison_body["lineage"]["baseline"]["experiment_tag"] == "baseline-governance"
    )
    assert (
        comparison_body["lineage"]["candidate"]["experiment_tag"] == "candidate-governance"
    )
    assert comparison_body["lineage"]["baseline"]["agent_version_snapshot_hash"]
    assert comparison_body["lineage"]["candidate"]["scorer_snapshot_hash"]
