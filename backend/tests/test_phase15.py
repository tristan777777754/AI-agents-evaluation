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
    assert response.status_code == 201, response.text


def test_sampled_run_launch_persists_group_metadata(client: TestClient) -> None:
    _upload_dataset(client)

    response = client.post(
        "/api/v1/runs/sampling",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
            "sampling": {
                "sample_count": 3,
                "sample_overrides": [],
            },
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["sample_count"] == 3
    assert len(body["runs"]) == 3
    assert len({run["run_id"] for run in body["runs"]}) == 3
    assert {run["sampling"]["sample_index"] for run in body["runs"]} == {1, 2, 3}
    assert all(run["sampling"]["group_id"] == body["group_id"] for run in body["runs"])
    assert all(run["sampling"]["sample_count"] == 3 for run in body["runs"])


def test_summary_reports_mean_variance_and_consistency_from_real_samples(
    client: TestClient,
) -> None:
    _upload_dataset(client)

    sampled = client.post(
        "/api/v1/runs/sampling",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
            "sampling": {
                "sample_count": 3,
                "sample_overrides": [
                    {},
                    {
                        "failure_map": {
                            "ds_item_003": True,
                            "ds_item_004": True,
                            "ds_item_005": True,
                            "ds_item_006": True,
                        }
                    },
                    {"failure_map": {"ds_item_003": True}},
                ],
            },
        },
    )
    assert sampled.status_code == 201, sampled.text
    representative_run_id = sampled.json()["runs"][0]["run_id"]

    summary = client.get(f"/api/v1/runs/{representative_run_id}/summary")
    assert summary.status_code == 200, summary.text
    body = summary.json()

    assert body["sampling"]["group_id"] == sampled.json()["group_id"]
    assert body["sampling"]["sample_count"] == 3
    assert body["sampling"]["completed_sample_count"] == 3
    assert body["sampling"]["success_rate"]["mean"] == 91.67
    assert body["sampling"]["success_rate"]["stddev"] == 8.5
    assert body["sampling"]["success_rate"]["variance"] == 72.22
    assert body["sampling"]["consistency_rate"] == 80.0


def test_compare_distinguishes_stable_and_unstable_runs_with_sampling_evidence(
    client: TestClient,
) -> None:
    _upload_dataset(client)

    stable_baseline = client.post(
        "/api/v1/runs/sampling",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
            "sampling": {
                "sample_count": 3,
                "sample_overrides": [],
            },
        },
    )
    assert stable_baseline.status_code == 201, stable_baseline.text

    unstable_candidate = client.post(
        "/api/v1/runs/sampling",
        json={
            "dataset_id": "dataset_support_faq_v1",
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
            "sampling": {
                "sample_count": 3,
                "sample_overrides": [
                    {},
                    {
                        "failure_map": {
                            "ds_item_003": True,
                            "ds_item_004": True,
                            "ds_item_005": True,
                            "ds_item_006": True,
                        }
                    },
                    {"failure_map": {"ds_item_003": True}},
                ],
            },
        },
    )
    assert unstable_candidate.status_code == 201, unstable_candidate.text

    comparison = client.get(
        "/api/v1/runs/compare",
        params={
            "baseline_run_id": stable_baseline.json()["runs"][0]["run_id"],
            "candidate_run_id": unstable_candidate.json()["runs"][0]["run_id"],
        },
    )
    assert comparison.status_code == 200, comparison.text
    body = comparison.json()

    assert body["sampling"]["interpretation"] == "unstable_regression"
    assert body["sampling"]["baseline"]["is_stable"] is True
    assert body["sampling"]["candidate"]["is_stable"] is False
    assert body["sampling"]["candidate"]["sample_count"] == 3
    assert body["sampling"]["candidate"]["success_rate_mean"] == 91.67
    assert body["sampling"]["candidate"]["success_rate_stddev"] == 8.5
    assert body["sampling"]["candidate"]["consistency_rate"] == 80.0
