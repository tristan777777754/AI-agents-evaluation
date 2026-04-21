# Task: Phase 2 dataset management workflow

## Current Phase
Phase 2

## Goal
Deliver a real dataset management loop with persistence, import validation, list/detail APIs, and a UI preview backed by real API data.

## In Scope
- Add SQLAlchemy-backed dataset and dataset item persistence.
- Implement JSON and CSV dataset upload with server-side validation and clear row-level errors.
- Implement dataset list, detail, and item preview APIs.
- Build frontend dataset upload, list, and detail preview views against the real backend.
- Add Phase 2 tests, smoke checks, and acceptance artifacts.

## Out of Scope
- Evaluation runner or run orchestration
- Trace viewer
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
- `backend/tests/fixtures/dataset_invalid.json`

## Required Output Artifacts
- SQLAlchemy dataset models and DB session plumbing
- Dataset import and query APIs
- Frontend dataset upload/list/detail UI
- Phase 2 smoke script support
- Phase 2 acceptance report

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase2`

## Acceptance Checks
- When uploading the valid JSON fixture, then `POST /api/v1/datasets` returns `201` and persists all dataset items.
- When uploading an invalid dataset fixture, then the API returns `422` with row-level validation errors.
- Given an uploaded dataset, `GET /api/v1/datasets`, `GET /api/v1/datasets/{id}`, and `GET /api/v1/datasets/{id}/items` return real persisted data.
- After loading the frontend dataset pages, the UI can list datasets and preview each dataset item without mock data.

## Contract Checks
- Backend Pydantic schemas remain the canonical contract source.
- Core entity names remain `dataset` and `dataset_item`.
- Canonical run status values remain unchanged.
- No run, trace, summary, compare, or review contract is introduced early.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks
- API responses for valid and invalid dataset uploads
- Phase 2 acceptance report

## Rollback / Recovery Notes
- Revert the Phase 2 dataset-specific files if import contracts or persistence logic prove invalid.
- Drop and recreate the local Phase 2 test database before rerunning tests if schema drift occurs.

## Stop And Ask Conditions
- Dataset requirements require changing core entity names or run status contracts.
- Phase 2 cannot complete without implementing the evaluation runner or fake dashboard data.
- Source-of-truth docs conflict on dataset import shape or persistence rules.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
