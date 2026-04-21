# Phase 3 Acceptance Report

## Implementation Result
- Added `eval_run`, `eval_task_run`, and `score` persistence with SQLAlchemy-backed status and snapshot fields.
- Implemented a deterministic stub adapter plus Celery integration with eager local/test support and fail-fast validation when async execution is requested without Celery installed.
- Added run create/list/detail/task APIs and fixture-backed registry APIs for `agent_version` and `scorer_config`.
- Added frontend run launch and run detail pages backed by real backend APIs.
- Updated contracts, smoke coverage, and tests for Phase 3 run execution, adapter validation, and Celery fallback behavior.

## Acceptance Result
- Phase 3 checks passed.

## Commands Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase3`

## Passed Checks
- Backend lint passed with `All checks passed!`
- Backend typecheck passed with `Success: no issues found in 26 source files`
- Backend unit tests passed with `17 passed`
- Backend unit tests now cover unsupported adapter rejection and Celery fail-fast behavior for non-eager mode
- Frontend lint passed
- Frontend typecheck passed
- Frontend unit tests passed with `3 passed`
- Smoke path passed: dataset upload, registry read, deterministic partial-success run, and task query all completed

## Failed Checks
- None

## Manual Verification Steps Performed
- Verified that creating a run against a persisted dataset writes `eval_run` and `eval_task_run` records through the API.
- Verified that a fixed `failure_map` produces a deterministic `partial_success` run with isolated failed tasks.
- Verified that unsupported `adapter_type` values are rejected at the API boundary instead of being silently accepted.
- Verified that requesting non-eager execution without Celery installed now fails fast instead of falling back to synchronous local execution.
- Verified that the frontend home page now exposes run launch and recent run surfaces alongside the dataset workflow.
- Verified that the run detail route is wired to the real backend run detail and task APIs.

## Known Gaps
- Trace persistence and trace detail APIs are intentionally deferred to Phase 4.
- Summary aggregation, compare flows, and review queue are intentionally deferred to later phases.

## Remaining Work
- Phase 4 should add trace persistence, trace detail APIs, and a case-level viewer using the task results produced in Phase 3.

## Next Phase Prerequisite Status
- Ready. Run creation, execution, deterministic failure isolation, and task result persistence are in place without crossing into trace, summary, compare, or review scope.
