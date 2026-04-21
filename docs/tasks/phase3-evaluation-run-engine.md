# Task: Phase 3 evaluation run engine

## Current Phase
Phase 3

## Goal
Deliver a real evaluation run loop with deterministic execution, run/task persistence, and a UI for launching and inspecting runs.

## In Scope
- Add `eval_run`, `eval_task_run`, and `score` persistence.
- Implement create/list/detail run APIs and task result API.
- Implement a deterministic stub adapter and Celery-backed execution path.
- Expose real `agent_version` and `scorer_config` registry inputs through backend APIs.
- Build frontend run launch and run detail views against real backend APIs.
- Add Phase 3 tests, smoke checks, and acceptance artifacts.

## Out of Scope
- Trace viewer and trace detail API
- Summary dashboard
- Run comparison
- Review queue

## Files Allowed To Touch
- `backend/**`
- `frontend/**`
- `shared/**`
- `docs/**`
- `scripts/**`
- `README.md`

## Files Forbidden To Touch
- `AGENTS.md`
- `PROJECT_OVERVIEW.md`
- `TECH_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `TESTING.md`
- `TASK_TEMPLATE.md`

## Inputs / Dependencies
- `AGENTS.md`
- `PROJECT_OVERVIEW.md`
- `TECH_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `TESTING.md`
- `TASK_TEMPLATE.md`
- `backend/tests/fixtures/dataset_valid.json`
- `backend/tests/fixtures/agent_version_v1.json`
- `backend/tests/fixtures/agent_version_v2.json`
- `backend/tests/fixtures/scorer_config.json`

## Required Output Artifacts
- SQLAlchemy run and score models
- Deterministic stub adapter and execution worker path
- Run APIs and frontend run launcher/detail UI
- Phase 3 smoke script support
- Phase 3 acceptance report

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase3`

## Acceptance Checks
- When creating a run for a persisted dataset, then `POST /api/v1/runs` returns `201` and persists `eval_run` plus `eval_task_run` records.
- Given a deterministic failure map, run status becomes `partial_success` and failed tasks are persisted without hanging the run.
- Given an existing run, `GET /api/v1/runs` and `GET /api/v1/runs/{id}/tasks` return real persisted status and task result data.
- After launching a run from the frontend, the UI can navigate to a run detail page backed by the real backend.

## Contract Checks
- Backend Pydantic schemas remain the canonical contract source.
- Core entity names remain `agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, and `score`.
- Canonical run statuses remain unchanged.
- No trace detail, summary, compare, or review contract is introduced early.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks
- API responses for completed and partial-success runs
- Phase 3 acceptance report

## Rollback / Recovery Notes
- Revert the Phase 3 run-specific files if execution persistence or state transitions prove invalid.
- Drop and recreate the local Phase 3 test database before rerunning tests if schema drift occurs.

## Stop And Ask Conditions
- Phase 3 requires changing core entity names, canonical run statuses, or summary/compare contracts.
- Phase 3 cannot complete without fake run data or undocumented contract changes.
- Source-of-truth docs conflict on run status transitions or deterministic execution rules.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
