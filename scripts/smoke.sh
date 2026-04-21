#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-phase6}"

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
from fastapi.testclient import TestClient

from app.main import app

with TestClient(app) as client:
    health = client.get("/api/v1/meta/health")
    assert health.status_code == 200, health.text
    assert health.json()["status"] == "ok", health.json()
    assert health.json()["phase"] == "phase6", health.json()

    contracts = client.get("/api/v1/meta/contracts")
    assert contracts.status_code == 200, contracts.text
    body = contracts.json()
    assert body["phase"]["current_phase"] == "Phase 6", body
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
    assert upload_body["dataset"]["item_count"] == 12, upload_body

    dataset_list = client.get("/api/v1/datasets")
    assert dataset_list.status_code == 200, dataset_list.text
    assert any(item["dataset_id"] == dataset_id for item in dataset_list.json()), dataset_list.json()

    items = client.get(f"/api/v1/datasets/{dataset_id}/items")
    assert items.status_code == 200, items.text
    assert items.json()["total_count"] == 12, items.json()

    if __import__("os").environ["PHASE"] == "phase2":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    registry = client.get("/api/v1/registry")
    assert registry.status_code == 200, registry.text
    registry_body = registry.json()
    assert registry_body["agent_versions"], registry_body
    assert registry_body["scorer_configs"], registry_body

    run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": registry_body["agent_versions"][0]["agent_version_id"],
            "scorer_config_id": registry_body["scorer_configs"][0]["scorer_config_id"],
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
    assert task_results.json()["total_count"] == 12, task_results.json()

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
    assert summary_body["success_rate"] == 91.67, summary_body
    assert summary_body["failed_cases"][0]["task_run_id"] == failed_task["task_run_id"], summary_body

    if __import__("os").environ["PHASE"] == "phase5":
        print("Backend smoke checks passed.")
        raise SystemExit(0)

    candidate_run = client.post(
        "/api/v1/runs",
        json={
            "dataset_id": dataset_id,
            "agent_version_id": registry_body["agent_versions"][1]["agent_version_id"],
            "scorer_config_id": registry_body["scorer_configs"][0]["scorer_config_id"],
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

print("Backend smoke checks passed.")
PY

if [[ -f "frontend/package-lock.json" || -d "frontend/node_modules" ]]; then
  (cd frontend && npm run test >/dev/null)
  echo "Frontend smoke checks passed."
else
  echo "Frontend dependencies not installed; backend smoke checks passed and frontend execution was skipped."
fi
