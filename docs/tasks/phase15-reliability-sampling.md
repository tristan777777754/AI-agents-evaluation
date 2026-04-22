# Task: Phase 15 reliability sampling

## Current Phase
Phase 15

## Goal
Add repeated-run sampling and consistency analysis so the workbench can tell the difference between stable improvements and unstable variance, without breaking deterministic replay or collapsing multi-sample evidence into a misleading single-run metric.

## In Scope
- Add repeated-run execution support for the same dataset and agent version under a declared sampling configuration.
- Add grouping or sample metadata so repeated runs can be analyzed together while preserving individual run records.
- Add summary metrics for consistency, variance, and standard deviation alongside mean performance.
- Extend compare logic so it can differentiate deterministic regression from unstable regression or unstable improvement.
- Update smoke script with a `phase15` path and write a Phase 15 acceptance report.

## Out of Scope
- Replacing deterministic stub smoke with probabilistic external-model smoke.
- Changing the canonical run status enum.
- Monte Carlo infrastructure or distributed experiment orchestration.
- Reinterpreting every single-run metric as a sampling metric.

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
- Phase 8 deterministic replay and repair utilities.
- Phase 11 credibility metrics and compare statistical framing.
- Phase 14 registry and quick-run ergonomics where repeated runs may be launched from the UI.
- Existing run summary and compare services.

## Required Output Artifacts
- Repeated-run execution path and sampling metadata support.
- Summary and compare support for variability metrics.
- Deterministic fixtures for multi-sample analysis.
- `scripts/smoke.sh` phase15 block.
- `docs/reports/phase15-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase15`

## Acceptance Checks
- When a repeated-run request is made with a fixed sample count, then the system persists multiple individual runs or samples linked by shared sampling metadata rather than overwriting a single run.
- Given a repeated-run fixture with intentionally varied outcomes, the summary shows both mean performance and variability metrics derived from the actual samples.
- When compare analyzes a stable baseline and an unstable candidate, then the response can distinguish instability from deterministic regression using persisted sample evidence.
- Deterministic replay coverage remains intact: `./scripts/smoke.sh phase15` still exercises a repeatable fixture path without depending on uncontrolled randomness.
- Frontend views that display sampling metrics are backed by real API responses rather than client-side recomputation from fake placeholder data.

## Contract Checks
- Existing single-run APIs remain valid when sampling metadata is absent.
- Run grouping or sample metadata is additive and does not replace the canonical `run_id`.
- Core status values remain unchanged.
- Compare semantics are extended additively; baseline/candidate meaning remains intact.

## Evidence To Attach
- Command outputs for lint, typecheck, unit tests, and smoke checks.
- Example summary response showing mean and variability metrics.
- Example compare response showing unstable-vs-stable interpretation.
- Phase 15 acceptance report.

## Rollback / Recovery Notes
- If repeated-run grouping complicates existing run list behavior, keep grouped views separate from the canonical run list until the grouping model is stable.
- If variability metrics are hard to compute from current fixtures, simplify the first pass to deterministic sample sets before expanding to broader sampling modes.
- If sampling metadata leaks into single-run contracts, move it behind optional nested objects instead of top-level required fields.

## Stop And Ask Conditions
- Reliability sampling requires changing canonical run or compare semantics established in earlier phases instead of extending them.
- The only feasible implementation depends on uncontrolled external-model randomness rather than deterministic or replayable fixtures.
- Sample grouping requires a new infrastructure component outside the accepted stack.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
