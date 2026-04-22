# Task: Phase 12 trace intelligence

## Current Phase
Phase 12

## Goal
Turn traces from passive debug records into active diagnostic evidence by deriving path-quality signals, exposing side-by-side trace comparison for the same dataset item across runs, and surfacing regressions that do not show up in pass/fail alone.

## In Scope
- Add trace-derived metrics such as `efficiency_score`, derived step counts, and derived tool-use signals while preserving raw trace payloads.
- Add a side-by-side trace compare endpoint for the same `dataset_item_id` across two runs.
- Add backend logic to detect trace-level regressions such as more steps, more tool calls, different failure point, or lower efficiency on the same item.
- Add frontend UI for side-by-side trace comparison with clear baseline/candidate separation.
- Add deterministic trace fixtures covering at least one improvement and one regression path.
- Update smoke script with a `phase12` path and write a Phase 12 acceptance report.

## Out of Scope
- Replacing the existing raw trace viewer.
- Full automatic root-cause clustering across all runs.
- New object storage backend changes.
- Mandatory judge use for every trace event.

## Files Allowed To Touch
- `backend/app/services/`
- `backend/app/api/`
- `backend/app/schemas/`
- `backend/app/models/`
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
- Phase 4 trace storage and trace viewer path.
- Phase 6 compare workflow and improvement/regression concepts.
- Phase 10 lineage support so run provenance remains intact.
- Phase 11 rubric and credibility additions where `rubric_json.max_steps` may exist.

## Required Output Artifacts
- Trace-derived metrics service logic.
- `GET /api/v1/compare/traces?baseline=&candidate=&dataset_item_id=` endpoint.
- Side-by-side trace compare frontend view or compare panel integration.
- Deterministic trace regression fixtures.
- `scripts/smoke.sh` phase12 block.
- `docs/reports/phase12-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase12`

## Acceptance Checks
- When `GET /api/v1/compare/traces?baseline=&candidate=&dataset_item_id=` is called for two known runs, then the response returns both traces plus derived metrics for the same dataset item.
- Given a fixture where the candidate reaches the same final answer with more steps than the baseline, then trace compare flags a path regression even if both tasks pass.
- Given a fixture with `rubric_json.max_steps`, `efficiency_score` is derived deterministically from the trace and remains stable across repeated test runs.
- After loading the trace compare UI, the user can visually inspect baseline and candidate steps side by side without losing access to the raw trace event payload.
- `./scripts/smoke.sh phase12` validates both raw trace access and derived regression signals.

## Contract Checks
- Raw trace payload structure remains readable through existing task trace APIs.
- New trace-derived metrics are additive and do not replace raw trace fields.
- Compare response semantics remain backward-compatible; trace comparison is introduced via a dedicated endpoint or additive nested block.
- Existing task, trace, and review IDs remain unchanged.

## Evidence To Attach
- Command outputs for lint, typecheck, unit tests, and smoke checks.
- Example side-by-side trace compare response.
- Screenshot or captured UI evidence of baseline/candidate trace comparison.
- Phase 12 acceptance report.

## Rollback / Recovery Notes
- If derived metrics slow trace reads excessively, isolate them behind a computed service layer instead of persisting them directly on every read path.
- If the side-by-side compare UI becomes too brittle, keep the compare API and degrade the UI to a simpler baseline/candidate panel without losing the underlying evidence.
- If `efficiency_score` proves ambiguous without stronger rubric coverage, fall back to simpler deterministic path metrics while preserving API compatibility.

## Stop And Ask Conditions
- Side-by-side trace comparison requires changing core trace storage in a way that invalidates existing Phase 4 trace records.
- Trace regression logic cannot be implemented without redefining canonical compare semantics established in Phase 6.
- Derived metrics require fake reconstructed trace data instead of real persisted traces.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
