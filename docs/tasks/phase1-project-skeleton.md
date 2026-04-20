# Task: Phase 1 project skeleton and contracts

## Current Phase
Phase 1

## Goal
Establish the repository skeleton, canonical contracts, and minimum startup surfaces needed to begin later phases without reworking core structure.

## In Scope
- Create the required top-level directories and backend/frontend skeletons.
- Define canonical backend schemas for core entities and shared TypeScript contract mirrors.
- Add `.env.example`, `docker-compose.yml`, fixture placeholders, smoke entrypoint, and acceptance report artifact.
- Provide a minimum frontend homepage and backend health routes.

## Out of Scope
- Dataset upload workflow
- Evaluation run execution
- Trace viewer implementation
- Dashboard, compare, or review queue features

## Files Allowed To Touch
- `frontend/**`
- `backend/**`
- `shared/**`
- `docs/**`
- `scripts/**`
- `.env.example`
- `docker-compose.yml`
- `.gitignore`
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

## Required Output Artifacts
- Repo skeleton under `frontend/`, `backend/`, `shared/`, `docs/`
- Canonical schema files in `backend/app/schemas/`
- Shared TypeScript contract mirror in `shared/types/`
- Phase 1 smoke script at `scripts/smoke.sh`
- Phase 1 acceptance report at `docs/reports/phase1-acceptance-report.md`

## Commands To Run
- `ruff check backend/`
- `mypy backend/app`
- `pytest backend/tests/`
- `npm run lint` in `frontend/`
- `npm run typecheck` in `frontend/`
- `npm run test` in `frontend/`
- `./scripts/smoke.sh phase1`

## Acceptance Checks
- When opening the repo after setup, then the required top-level Phase 1 directories exist.
- Given the backend app, API returns `200` from `GET /api/v1/meta/health`.
- Given the frontend app, the homepage renders the Phase 1 marker and canonical run statuses.
- After importing shared contracts into the frontend, TypeScript typecheck passes without local contract duplication.

## Contract Checks
- Backend `Pydantic` schema remains the canonical contract source.
- Shared TypeScript types mirror the same Phase 1 fields for `agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, `trace`, `score`, and `review`.
- Canonical run status values remain `pending`, `running`, `completed`, `failed`, `cancelled`, `partial_success`.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks
- Health endpoint response
- Phase 1 acceptance report with passed and failed checks

## Rollback / Recovery Notes
- Remove newly added skeleton directories and files if the scaffold must be reset.
- Re-run smoke and test commands after any contract changes before treating the branch as safe.

## Stop And Ask Conditions
- Any required Phase 1 file conflicts with the source-of-truth docs.
- Phase 1 contract cannot stay aligned between backend schema and shared TypeScript types.
- Completing the scaffold would require implementing Dataset, Run, Trace, Dashboard, or Compare workflows early.

## Completion Report
- Implementation result: Required repo skeleton, canonical backend schemas, shared TypeScript contracts, minimum frontend/backend startup surfaces, fixture placeholders, smoke script, and acceptance report were added.
- Acceptance result: Backend lint, backend typecheck, backend unit tests, frontend lint, frontend typecheck, frontend unit tests, and Phase 1 smoke checks all passed.
- Remaining work: Phase 2 should build dataset schema validation, import APIs, persistence, and preview UI on top of the Phase 1 contracts.
- Next phase prerequisite status: Satisfied.
