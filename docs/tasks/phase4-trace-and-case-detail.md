# Task: Phase 4 trace and case detail

## Current Phase
Phase 4

## Goal
Deliver real trace persistence, trace detail APIs, deterministic failure classification, and a case-level viewer backed by persisted task and trace data.

## In Scope
- Add `trace` persistence linked to `eval_task_run`.
- Persist ordered trace events and trace summary fields during run execution.
- Implement task detail and trace detail APIs for single-case inspection.
- Classify deterministic stub failures into answer, tool, format, and execution categories.
- Build frontend case detail and trace viewer pages backed by real backend APIs.
- Add Phase 4 tests, smoke checks, and acceptance artifacts.

## Out of Scope
- Summary dashboard
- Run comparison
- Review queue workflows
- S3 object storage integration beyond stable trace storage path metadata

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
- SQLAlchemy trace model and task-to-trace linkage
- Trace detail schemas and APIs
- Deterministic trace logging and failure classification in the stub execution path
- Frontend task detail and trace viewer UI
- Phase 4 smoke script support
- Phase 4 acceptance report

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase4`

## Acceptance Checks
- When creating a run with deterministic trace behaviors, then persisted task runs expose linked trace summaries.
- Given a tool or execution failure case, `GET /api/v1/task-runs/{id}/trace` returns ordered trace events and the correct failure classification.
- Given a wrong-answer or format-error case, task detail APIs expose `input_text`, `expected_output`, `actual output`, and the persisted failure reason without fake data.
- After opening a task detail page from the run UI, the viewer renders real trace events and failure metadata from the backend.

## Contract Checks
- Backend Pydantic schemas remain the canonical contract source.
- Core entity names remain `agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, `trace`, `score`, and `review`.
- Canonical run statuses remain unchanged.
- No summary, compare, or review contract is introduced early.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks
- API responses for task detail and trace detail
- Phase 4 acceptance report

## Rollback / Recovery Notes
- Revert the Phase 4 trace-specific files if trace persistence or failure classification is invalid.
- Drop and recreate the local test database before rerunning tests if schema drift occurs.

## Stop And Ask Conditions
- Phase 4 requires changing core entity names, canonical run statuses, or summary/compare contracts.
- Phase 4 cannot complete without fake trace data or undocumented contract changes.
- Source-of-truth docs conflict on trace APIs or failure classification expectations.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
