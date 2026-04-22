# Task: Phase 14 registry and run ergonomics

## Current Phase
Phase 14

## Goal
Remove the daily friction of using the workbench by replacing hardcoded registry behavior with runtime CRUD, adding quick-run and auto-compare flows, exposing honest run progress, and introducing pagination so the UI remains usable as data grows.

## In Scope
- Replace hardcoded registry loading with database-backed agent and agent-version CRUD that works without service restart.
- Add a quick-run path that launches a run from a selected agent version using a real persisted default dataset and scorer configuration.
- Add auto-compare behavior that offers or executes comparison against the latest relevant baseline run.
- Add run progress polling and visible `tasks_completed / tasks_total` progress UI.
- Add pagination and basic filtering for runs, dataset items, and review queue views.
- Update smoke script with a `phase14` path and write a Phase 14 acceptance report.

## Out of Scope
- Reworking immutable agent version snapshot semantics.
- Fake progress indicators disconnected from real task completion.
- New product areas unrelated to run launch and navigation ergonomics.
- Multi-user permissioning for registry edits.

## Files Allowed To Touch
- `backend/app/models/`
- `backend/app/services/`
- `backend/app/api/`
- `backend/app/schemas/`
- `backend/tests/fixtures/`
- `backend/tests/`
- `frontend/app/`
- `frontend/components/`
- `frontend/lib/`
- `shared/`
- `scripts/smoke.sh`
- `docs/reports/`

## Files Forbidden To Touch
- `AGENTS.md`
- `PROJECT_OVERVIEW.md`
- `TECH_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `TESTING.md`
- `TASK_TEMPLATE.md`
- `docs/tasks/`

## Inputs / Dependencies
- Existing registry routes and registry service behavior.
- Phase 3 run creation and execution path.
- Phase 6 compare flow and baseline concepts.
- Phase 10 baseline pinning and experiment metadata.

## Required Output Artifacts
- Database-backed registry CRUD path and API/schema support.
- Quick-run flow and default selection logic.
- Auto-compare support against the latest baseline or latest comparable run.
- Run progress polling support and UI.
- Pagination/filter support for large lists.
- `scripts/smoke.sh` phase14 block.
- `docs/reports/phase14-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase14`

## Acceptance Checks
- When a new agent version is created through the registry API, then it becomes selectable for run launch without editing fixture files or restarting the backend.
- Given a configured default dataset and scorer, quick run creates a real `eval_run` using persisted IDs rather than fake client-side placeholders.
- When tasks complete during run execution, then the run detail page updates `tasks_completed / tasks_total` through polling from real backend state.
- Given more records than one page, runs, dataset items, and review queue views paginate rather than rendering the entire table at once.
- `./scripts/smoke.sh phase14` covers registry CRUD, quick run, progress polling evidence, and auto-compare using real persisted run records.

## Contract Checks
- Agent and agent version entity names remain unchanged.
- Immutable agent version snapshots remain immutable after creation; CRUD may add or list versions but must not silently mutate version payloads after runs depend on them.
- Run creation and compare contracts remain backward-compatible; quick-run and auto-compare are additive convenience paths.
- Pagination parameters are additive and must not break existing list consumers that omit them.

## Evidence To Attach
- Command outputs for lint, typecheck, unit tests, and smoke checks.
- Example registry create/list response.
- Example run detail response showing progress counters.
- Phase 14 acceptance report.

## Rollback / Recovery Notes
- If registry DB migration conflicts with existing fixture-based assumptions, preserve read compatibility with old records while deprecating file-backed registry lookup behind a feature flag or compatibility layer.
- If auto-compare produces ambiguous baseline selection, degrade to an explicit “suggested baseline” UI while preserving the underlying latest-baseline query.
- If pagination complicates existing views, keep default page size generous but bounded instead of falling back to unbounded list rendering.

## Stop And Ask Conditions
- Runtime registry CRUD requires redefining the core `agent_version` identity model in a way that breaks existing run lineage.
- Quick run cannot be implemented without introducing fake defaults or client-only placeholder IDs.
- Progress tracking requires a new infrastructure dependency beyond the project’s accepted stack when polling from existing APIs should suffice.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
