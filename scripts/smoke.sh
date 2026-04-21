#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-phase10}"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="$ROOT_DIR/backend"
export DATABASE_URL="sqlite+pysqlite:///$ROOT_DIR/backend/tests/smoke_phase.db"
export PHASE

rm -f "$ROOT_DIR/backend/tests/smoke_phase.db"

PYTHON_BIN="python3"
if [[ -x "$ROOT_DIR/backend/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/backend/.venv/bin/python"
fi

"$PYTHON_BIN" - <<'PY'
import os

from fastapi.testclient import TestClient

from app.main import app

with TestClient(app) as client:
    health = client.get("/api/v1/meta/health")
    assert health.status_code == 200, health.text
    assert health.json()["status"] == "ok", health.json()
    assert health.json()["phase"] == "phase10", health.json()

    contracts = client.get("/api/v1/meta/contracts")
    assert contracts.status_code == 200, contracts.text
    body = contracts.json()
    assert body["phase"]["current_phase"] == "Phase 10", body
    assert "partial_success" in body["run_statuses"], body

    if __import__("os").environ["PHASE"] == "phase1":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    with open("backend/tests/fixtures/dataset_valid.json", "rb") as handle:
        upload = client.post(
            "/api/v1/datasets",
            files={"file": ("dataset_valid.json", handle, "application/json")},
        )

    assert upload.status_code == 201, upload.text
    upload_body = upload.json()
    dataset_id = upload_body["dataset"]["dataset_id"]
    assert upload_body["dataset"]["item_count"] == 20, upload_body

    dataset_list = client.get("/api/v1/datasets")
    assert dataset_list.status_code == 200, dataset_list.text
    assert any(item["dataset_id"] == dataset_id for item in dataset_list.json()), dataset_list.json()

    items = client.get(f"/api/v1/datasets/{dataset_id}/items")
    assert items.status_code == 200, items.text
    assert items.json()["total_count"] == 20, items.json()

    if __import__("os").environ["PHASE"] == "phase2":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    registry = client.get("/api/v1/registry")
    assert registry.status_code == 200, registry.text
    registry_body = registry.json()
    assert registry_body["agent_versions"], registry_body
    assert registry_body["scorer_configs"], registry_body

    scorer_by_id = {item["scorer_config_id"]: item for item in registry_body["scorer_configs"]}
    run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": "av_support_qa_v1",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {"failure_map": {"ds_item_003": True}},
        },
    )
    assert run.status_code == 201, run.text
    run_body = run.json()
    assert run_body["status"] == "partial_success", run_body
    assert run_body["failed_tasks"] == 1, run_body

    task_results = client.get(f"/api/v1/runs/{run_body['run_id']}/tasks")
    assert task_results.status_code == 200, task_results.text
    assert task_results.json()["total_count"] == 20, task_results.json()

    if __import__("os").environ["PHASE"] == "phase3":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    failed_task = next(
        item for item in task_results.json()["items"] if item["dataset_item_id"] == "ds_item_003"
    )
    assert failed_task["failure_reason"] == "execution_failed", failed_task
    assert failed_task["trace_summary"]["error_flag"] is True, failed_task

    task_detail = client.get(f"/api/v1/task-runs/{failed_task['task_run_id']}")
    assert task_detail.status_code == 200, task_detail.text
    assert task_detail.json()["trace_summary"]["step_count"] == 2, task_detail.json()

    trace_detail = client.get(f"/api/v1/task-runs/{failed_task['task_run_id']}/trace")
    assert trace_detail.status_code == 200, trace_detail.text
    trace_body = trace_detail.json()
    assert trace_body["failure_reason"] == "execution_failed", trace_body
    assert trace_body["events"][1]["event_type"] == "agent_error", trace_body

    if __import__("os").environ["PHASE"] == "phase4":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    summary_detail = client.get(f"/api/v1/runs/{run_body['run_id']}/summary")
    assert summary_detail.status_code == 200, summary_detail.text
    summary_body = summary_detail.json()
    assert summary_body["failed_tasks"] == 1, summary_body
    assert summary_body["success_rate"] == 95.0, summary_body
    assert summary_body["failed_cases"][0]["task_run_id"] == failed_task["task_run_id"], summary_body

    if __import__("os").environ["PHASE"] == "phase5":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    candidate_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
        },
    )
    assert candidate_run.status_code == 201, candidate_run.text
    candidate_body = candidate_run.json()
    assert candidate_body["status"] == "completed", candidate_body

    compare = client.get(
        "/api/v1/runs/compare",
        params={
            "baseline_run_id": run_body["run_id"],
            "candidate_run_id": candidate_body["run_id"],
        },
    )
    assert compare.status_code == 200, compare.text
    compare_body = compare.json()
    assert compare_body["improvement_count"] == 1, compare_body
    assert compare_body["regression_count"] == 0, compare_body

    queue = client.get("/api/v1/reviews/queue")
    assert queue.status_code == 200, queue.text
    queue_body = queue.json()
    assert queue_body["total_count"] >= 1, queue_body
    assert queue_body["pending_count"] >= 1, queue_body

    review = client.put(
        f"/api/v1/task-runs/{failed_task['task_run_id']}/review",
        json={
            "reviewer_id": "reviewer_demo",
            "verdict": "confirmed_issue",
            "failure_label": "execution_failed",
            "note": "Smoke review persisted.",
        },
    )
    assert review.status_code == 200, review.text
    review_body = review.json()
    assert review_body["verdict"] == "confirmed_issue", review_body

    reviewed_task = client.get(f"/api/v1/task-runs/{failed_task['task_run_id']}")
    assert reviewed_task.status_code == 200, reviewed_task.text
    assert reviewed_task.json()["review"]["note"] == "Smoke review persisted.", reviewed_task.json()

    if os.environ["PHASE"] == "phase6":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    run_openai_integration = (
        os.environ.get("RUN_OPENAI_INTEGRATION_SMOKE", "").lower() in {"1", "true", "yes"}
    )
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    if not run_openai_integration:
        if os.environ["PHASE"] == "phase7":
            print("Backend smoke checks passed. OpenAI integration smoke skipped.")
            raise SystemExit(0)
    else:
        assert openai_api_key, "OPENAI_API_KEY is required when RUN_OPENAI_INTEGRATION_SMOKE=1."
        assert "sc_keyword_overlap_v1" in scorer_by_id, scorer_by_id

        openai_v1 = client.post(
            "/api/v1/runs",
            json={
                "dataset_id": dataset_id,
                "agent_version_id": "av_support_qa_v1",
                "scorer_config_id": "sc_keyword_overlap_v1",
                "adapter_type": "openai",
                "adapter_config": {},
            },
        )
        assert openai_v1.status_code == 201, openai_v1.text
        openai_v1_body = openai_v1.json()
        assert openai_v1_body["adapter_type"] == "openai", openai_v1_body
        assert openai_v1_body["status"] in {"completed", "partial_success"}, openai_v1_body

        openai_v2 = client.post(
            "/api/v1/runs",
            json={
                "dataset_id": dataset_id,
                "agent_version_id": "av_support_qa_v2",
                "scorer_config_id": "sc_keyword_overlap_v1",
                "adapter_type": "openai",
                "adapter_config": {},
            },
        )
        assert openai_v2.status_code == 201, openai_v2.text
        openai_v2_body = openai_v2.json()
        assert openai_v2_body["adapter_type"] == "openai", openai_v2_body
        assert openai_v2_body["status"] in {"completed", "partial_success"}, openai_v2_body

        openai_compare = client.get(
            "/api/v1/runs/compare",
            params={
                "baseline_run_id": openai_v1_body["run_id"],
                "candidate_run_id": openai_v2_body["run_id"],
            },
        )
        assert openai_compare.status_code == 200, openai_compare.text
        compare_body = openai_compare.json()

        baseline_tasks = client.get(f"/api/v1/runs/{openai_v1_body['run_id']}/tasks")
        candidate_tasks = client.get(f"/api/v1/runs/{openai_v2_body['run_id']}/tasks")
        assert baseline_tasks.status_code == 200, baseline_tasks.text
        assert candidate_tasks.status_code == 200, candidate_tasks.text
        baseline_items = baseline_tasks.json()["items"]
        candidate_items = candidate_tasks.json()["items"]
        assert any(item["final_output"] and not item["final_output"].startswith("[stub]") for item in baseline_items), baseline_items
        assert any(item["final_output"] and not item["final_output"].startswith("[stub]") for item in candidate_items), candidate_items

        if compare_body["improvement_count"] == 0 and compare_body["regression_count"] == 0:
            assert compare_body["compared_task_count"] == 20, compare_body
            assert len(baseline_items) == 20, baseline_items
            assert len(candidate_items) == 20, candidate_items
            if os.environ["PHASE"] == "phase7":
                print("Backend smoke checks passed. OpenAI compare result was inconclusive with persisted evidence.")
                raise SystemExit(0)

        if os.environ["PHASE"] == "phase7":
            print("Backend smoke checks passed.")
            raise SystemExit(0)

    import json

    with open("backend/tests/fixtures/replay_manifest.json", "r", encoding="utf-8") as handle:
        replay_manifest = json.load(handle)

    replay_runs = []
    for _ in range(2):
        replay_run = client.post(
            "/api/v1/runs",
            json={
                "dataset_id": dataset_id,
                "agent_version_id": replay_manifest["agent_version_id"],
                "scorer_config_id": replay_manifest["scorer_config_id"],
                "adapter_type": replay_manifest["adapter_type"],
                "adapter_config": replay_manifest["adapter_config"],
            },
        )
        assert replay_run.status_code == 201, replay_run.text
        replay_runs.append(replay_run.json()["run_id"])

    replay_summaries = []
    for replay_run_id in replay_runs:
        replay_summary = client.get(f"/api/v1/runs/{replay_run_id}/summary")
        assert replay_summary.status_code == 200, replay_summary.text
        replay_summaries.append(replay_summary.json())

    expected = replay_manifest["expected_summary"]
    assert replay_summaries[0]["success_rate"] == replay_summaries[1]["success_rate"] == expected["success_rate"], replay_summaries
    assert replay_summaries[0]["average_latency_ms"] == replay_summaries[1]["average_latency_ms"] == expected["average_latency_ms"], replay_summaries
    assert replay_summaries[0]["category_breakdown"] == replay_summaries[1]["category_breakdown"], replay_summaries
    for expected_row in expected["category_breakdown"]:
        actual_row = next(
            row for row in replay_summaries[0]["category_breakdown"] if row["category"] == expected_row["category"]
        )
        assert actual_row["success_rate"] == expected_row["success_rate"], actual_row
        assert actual_row["failed_tasks"] == expected_row["failed_tasks"], actual_row

    if os.environ["PHASE"] == "phase8":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    calibration = client.get("/api/v1/calibration/latest")
    assert calibration.status_code == 200, calibration.text
    calibration_body = calibration.json()
    assert calibration_body["fixture_id"] == "golden_set_support_faq_v1", calibration_body
    assert calibration_body["scorer_config_id"] == "sc_keyword_overlap_v1", calibration_body
    assert calibration_body["precision"] >= 0.7, calibration_body
    assert calibration_body["recall"] >= 0.7, calibration_body
    assert calibration_body["accuracy"] >= 0.7, calibration_body
    assert calibration_body["true_positive_count"] + calibration_body["false_negative_count"] >= 5, calibration_body
    assert calibration_body["true_negative_count"] + calibration_body["false_positive_count"] >= 5, calibration_body

    if os.environ["PHASE"] == "phase9":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    latest_dataset = client.get(f"/api/v1/datasets/{dataset_id}")
    assert latest_dataset.status_code == 200, latest_dataset.text
    first_snapshot_id = latest_dataset.json()["snapshot_id"]

    with open("backend/tests/fixtures/dataset_valid.json", "r", encoding="utf-8") as handle:
        dataset_v2 = json.load(handle)

    dataset_v2["items"][1]["expected_output"] = (
        "Refunds for annual plans are available within 21 days."
    )
    dataset_v2["items"] = [
        item for item in dataset_v2["items"] if item["dataset_item_id"] != "ds_item_020"
    ]
    dataset_v2["items"].append(
        {
            "dataset_item_id": "ds_item_021",
            "input_text": "Can enterprise admins enforce SSO for all members?",
            "category": "security",
            "difficulty": "medium",
            "expected_output": "Yes. Enterprise admins can require SSO enforcement for all members.",
            "metadata_json": {"source": "phase10"},
        }
    )
    upload_v2 = client.post(
        "/api/v1/datasets",
        files={
            "file": (
                "dataset_valid.json",
                json.dumps(dataset_v2).encode("utf-8"),
                "application/json",
            )
        },
    )
    assert upload_v2.status_code == 201, upload_v2.text
    upload_v2_body = upload_v2.json()
    second_snapshot_id = upload_v2_body["snapshot_id"]
    assert second_snapshot_id != first_snapshot_id, upload_v2_body

    original_snapshot_items = client.get(
        f"/api/v1/datasets/{dataset_id}/items",
        params={"snapshot_id": first_snapshot_id},
    )
    assert original_snapshot_items.status_code == 200, original_snapshot_items.text
    assert any(
        item["dataset_item_id"] == "ds_item_020"
        for item in original_snapshot_items.json()["items"]
    ), original_snapshot_items.json()

    diff = client.get(
        f"/api/v1/datasets/{dataset_id}/diff",
        params={
            "from_snapshot": first_snapshot_id,
            "to_snapshot": second_snapshot_id,
        },
    )
    assert diff.status_code == 200, diff.text
    diff_body = diff.json()
    assert diff_body["added_count"] == 1, diff_body
    assert diff_body["removed_count"] == 1, diff_body
    assert diff_body["changed_count"] == 1, diff_body

    baseline_pin = client.post(
        f"/api/v1/runs/{run_body['run_id']}/baseline",
        json={"baseline": True},
    )
    assert baseline_pin.status_code == 200, baseline_pin.text
    assert baseline_pin.json()["baseline"] is True, baseline_pin.json()

    lineage_candidate = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": "av_support_qa_v2",
            "scorer_config_id": "sc_rule_based_v1",
            "adapter_type": "stub",
            "adapter_config": {},
            "experiment_tag": "phase10-smoke",
            "notes": "Uses the latest immutable dataset snapshot.",
        },
    )
    assert lineage_candidate.status_code == 201, lineage_candidate.text
    lineage_candidate_body = lineage_candidate.json()
    assert lineage_candidate_body["dataset_snapshot_id"] == second_snapshot_id, lineage_candidate_body

    governance_compare = client.get(
        "/api/v1/runs/compare",
        params={
            "baseline_run_id": run_body["run_id"],
            "candidate_run_id": lineage_candidate_body["run_id"],
        },
    )
    assert governance_compare.status_code == 200, governance_compare.text
    governance_compare_body = governance_compare.json()
    assert governance_compare_body["lineage"]["baseline"]["dataset_snapshot_id"] == first_snapshot_id, governance_compare_body
    assert governance_compare_body["lineage"]["candidate"]["dataset_snapshot_id"] == second_snapshot_id, governance_compare_body
    assert governance_compare_body["lineage"]["baseline"]["baseline"] is True, governance_compare_body
    assert governance_compare_body["lineage"]["candidate"]["experiment_tag"] == "phase10-smoke", governance_compare_body

print("Backend smoke checks passed.")
PY

if [[ -f "frontend/package-lock.json" || -d "frontend/node_modules" ]]; then
  (cd frontend && npm run test >/dev/null)
  echo "Frontend smoke checks passed."
else
  echo "Frontend dependencies not installed; backend smoke checks passed and frontend execution was skipped."
fi
