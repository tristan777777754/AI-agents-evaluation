# Task: Phase 5 summary dashboard

## Current Phase
Phase 5

## Goal
Deliver a real summary dashboard backed by persisted run, task, score, and trace data, with KPI aggregation and navigation into failed case detail.

## In Scope
- Add summary aggregation schema and service logic.
- Add a summary API for a single run.
- Build a homepage dashboard using the latest persisted run.
- Render KPI cards, category breakdown, failure breakdown, and failed case links.
- Update smoke checks, tests, and acceptance artifacts for Phase 5.

## Out of Scope
- Run comparison
- Review queue workflows
- BI-style filtering or time-series analytics
- Fake or hard-coded dashboard metrics

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
- Existing Phase 3 and Phase 4 run, score, and trace persistence

## Required Output Artifacts
- Summary aggregation schemas and service code
- Run summary API
- Homepage dashboard UI backed by real API data
- Phase 5 smoke script support
- Phase 5 acceptance report

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase5`

## Acceptance Checks
- When requesting `GET /api/v1/runs/{id}/summary`, then success rate, latency, cost, and review-needed count match persisted task results.
- Given failed tasks across multiple failure reasons, the summary API returns category and failure breakdowns derived from real records.
- After loading the homepage with at least one run, the dashboard shows KPI cards and failed case links backed by the latest persisted run.
- When selecting a failed case from the dashboard, the link targets the existing task trace viewer route.

## Contract Checks
- Backend Pydantic schemas remain the canonical contract source.
- Core entity names remain `agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, `trace`, `score`, and `review`.
- Canonical run statuses remain unchanged.
- No compare or review contract is introduced early.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks
- Example summary API response
- Phase 5 acceptance report

## Rollback / Recovery Notes
- Revert the Phase 5 summary-specific files if aggregated metrics diverge from persisted task data.
- Drop and recreate the local test database before rerunning tests if schema drift occurs.

## Stop And Ask Conditions
- Phase 5 requires changing core entity names, canonical run statuses, or compare/review contracts.
- Phase 5 cannot complete without fake dashboard data or undocumented contract changes.
- Source-of-truth docs conflict on summary KPI definitions or dashboard scope.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
