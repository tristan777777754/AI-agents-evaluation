# Task: Phase 6 run comparison and product polish

## Current Phase
Phase 6

## Goal
Deliver a real run comparison workflow, a minimal persisted review queue, and polish the main demo path without introducing fake data or scope creep.

## In Scope
- Add compare schemas and service logic backed by persisted run and task data.
- Add a compare API for a baseline and candidate run pair.
- Add persisted review records plus a minimal review queue and reviewer verdict update flow.
- Build compare and review UI backed by real backend APIs.
- Polish primary empty, loading, and error states across the main demo path.
- Update smoke checks, tests, contracts, and acceptance artifacts for Phase 6.

## Out of Scope
- New scoring systems
- Multi-run analytics beyond pairwise compare
- Collaborative review assignment workflows
- Fake demo dashboards or compare data
- New product areas outside compare and review

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
- Existing Phase 5 run, summary, and trace persistence

## Required Output Artifacts
- Compare schemas and service code
- Review queue schemas, persistence, and service code
- Compare and review APIs
- Compare and review UI backed by real API data
- Phase 6 smoke script support
- Phase 6 acceptance report

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase6`

## Acceptance Checks
- When requesting `GET /api/v1/runs/compare?baseline_run_id=<id>&candidate_run_id=<id>`, then the API returns metric deltas plus improvement and regression cases derived from persisted task results.
- Given two completed or partial-success runs over the same dataset, the compare API returns category deltas and case-level links without fake data.
- When requesting `GET /api/v1/reviews/queue`, then review-needed task runs are returned with existing review state and links back to real task detail routes.
- When submitting a reviewer verdict for a task run, then the review is persisted and visible from both the task detail view and the review queue.
- After loading the main UI with at least two runs and at least one review-needed case, the compare and review flows are reachable from the homepage and task detail pages.

## Contract Checks
- Backend Pydantic schemas remain the canonical contract source.
- Core entity names remain `agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, `trace`, `score`, and `review`.
- Canonical run statuses remain unchanged.
- Compare and review contracts are introduced only in Phase 6 and remain backed by persisted run and task data.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks
- Example compare API response
- Example persisted review response
- Phase 6 acceptance report

## Rollback / Recovery Notes
- Revert the Phase 6 compare and review files if compare deltas or review persistence diverge from persisted task results.
- Drop and recreate the local test database before rerunning tests if schema drift occurs.

## Stop And Ask Conditions
- Phase 6 requires changing canonical run statuses or core entity names.
- Phase 6 cannot complete without fake compare or review data.
- Source-of-truth docs conflict on compare or review workflow scope.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
