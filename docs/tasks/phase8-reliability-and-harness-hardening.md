# Task: Phase 8 reliability and harness hardening

## Current Phase
Phase 8

## Goal
Harden the evaluation harness so that runs backed by real OpenAI calls can be recovered after interruption, re-executed with the same config, and audited for state consistency without manual DB repair.

## In Scope
- Add a `rerun` endpoint or service path that re-executes only `failed` or `pending` task runs within an existing run, preserving completed task results.
- Add a run state transition guard that rejects invalid status transitions (e.g., `completed → running`) and logs the attempted transition.
- Add a repair utility that recomputes `completed_tasks` and `failed_tasks` from `eval_task_run` records when the run-level aggregation is inconsistent.
- Add a replay fixture: a fixed dataset + fixed adapter config (stub, deterministic) that can be re-executed at any time and should always produce the same summary metrics.
- Update smoke script with a `phase8` path that runs the replay fixture twice and asserts the summary metrics match.
- Phase 8 acceptance report.

## Out of Scope
- Async or queue-based workers.
- New frontend UI changes.
- LLM-as-judge scoring.
- Automatic prompt optimization.

## Files Allowed To Touch
- `backend/app/services/runs.py`
- `backend/app/api/runs.py`
- `backend/app/models/`
- `backend/tests/`
- `backend/tests/fixtures/`
- `scripts/smoke.sh`
- `docs/`

## Files Forbidden To Touch
- `AGENTS.md`
- `PROJECT_OVERVIEW.md`
- `TECH_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `TESTING.md`
- `TASK_TEMPLATE.md`
- `frontend/`
- `shared/`

## Inputs / Dependencies
- Phase 7 real adapter and persisted run records.
- Existing run status enum and task run schema.
- `StubAgentAdapter` for deterministic replay fixture.

## Required Output Artifacts
- Rerun service path (partial re-execution of failed/pending tasks only).
- State transition guard on `EvalRunRecord` and `EvalTaskRunRecord`.
- Aggregation repair utility callable from a management endpoint or CLI.
- Replay fixture (`backend/tests/fixtures/replay_manifest.json`) with deterministic expected summary.
- `scripts/smoke.sh` phase8 block.
- `docs/reports/phase8-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase8`

## Acceptance Checks
- When a run with some `failed` task runs is re-executed via the rerun path, then previously `completed` task runs are not re-executed and their records are unchanged.
- When an invalid state transition is attempted (e.g., setting a `completed` run back to `running`), then the API returns `409` and the run status is unchanged.
- When the aggregation repair utility is called on a run where `completed_tasks` is inconsistent with actual task records, then the run-level count is corrected without deleting any task records.
- After running the replay fixture twice with identical adapter config, both runs produce the same `success_rate`, `avg_latency_ms`, and `category_breakdown` within a deterministic tolerance.
- `./scripts/smoke.sh phase8` passes without requiring `OPENAI_API_KEY`.

## Contract Checks
- No new top-level entity names or schema fields are introduced beyond what Phase 7 established.
- Canonical run statuses remain unchanged; the state guard enforces the existing enum, not a new one.
- The rerun path reuses existing `POST /api/v1/runs/{id}/execute` or adds a narrowly scoped sub-path; it does not change the run creation contract.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks.
- Example showing rerun skipping completed task runs.
- Example showing `409` on invalid state transition attempt.
- Replay manifest and two matching summary responses.
- Phase 8 acceptance report.

## Rollback / Recovery Notes
- If the state transition guard breaks existing test flows, verify that the guard only rejects transitions explicitly listed as invalid.
- If the repair utility produces incorrect counts, revert to a read-only diagnostic version and fix the counting logic before re-enabling writes.

## Stop And Ask Conditions
- The rerun path requires changing the core `eval_run` or `eval_task_run` schema in a way that breaks Phase 6 compare or review records.
- The state transition guard rejects transitions that the existing smoke tests depend on.
- Deterministic replay cannot be achieved without changing the stub adapter contract.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
