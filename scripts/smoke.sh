#!/usr/bin/env bash
set -euo pipefail

PHASE="${1:-phase1}"

if [[ "$PHASE" != "phase1" ]]; then
  echo "Unsupported phase: $PHASE" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="$ROOT_DIR/backend"

python3 - <<'PY'
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
health = client.get("/api/v1/meta/health")
assert health.status_code == 200, health.text
assert health.json()["status"] == "ok", health.json()

contracts = client.get("/api/v1/meta/contracts")
assert contracts.status_code == 200, contracts.text
body = contracts.json()
assert body["phase"]["current_phase"] == "Phase 1", body
assert "partial_success" in body["run_statuses"], body
print("Backend smoke checks passed.")
PY

if [[ -f "frontend/package-lock.json" || -d "frontend/node_modules" ]]; then
  (cd frontend && npm run test >/dev/null)
  echo "Frontend smoke checks passed."
else
  echo "Frontend dependencies not installed; backend smoke checks passed and frontend execution was skipped."
fi
