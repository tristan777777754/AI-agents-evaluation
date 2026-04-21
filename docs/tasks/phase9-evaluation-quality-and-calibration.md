# Task: Phase 9 evaluation quality and scorer calibration

## Current Phase
Phase 9

## Goal
Make the scores and verdicts produced by the workbench trustworthy: introduce a golden set with known correct labels, run scorer calibration to measure scorer accuracy, and expose a calibration summary that shows where the scorer and human reviewer disagree.

## In Scope
- Define a golden set fixture (≥10 items) with pre-labelled `expected_verdict` (`pass` / `fail`) and `expected_failure_reason` per item.
- Add a calibration runner service that executes the golden set through the current scorer and compares `score.pass_fail` against `expected_verdict`.
- Add a calibration report schema and endpoint (`GET /api/v1/calibration/latest`) returning precision, recall, and per-category accuracy of the scorer against the golden set.
- Add a calibration UI panel on the homepage showing scorer accuracy metrics from the latest calibration report.
- Update smoke script with a `phase9` path that runs calibration and asserts precision ≥ 0.7 on the golden set.
- Phase 9 acceptance report.

## Out of Scope
- LLM-as-judge calibration (human-labelled golden set only).
- Multi-scorer comparison.
- Automated re-scoring of historical runs.
- Changing the existing scorer weights or thresholds.

## Files Allowed To Touch
- `backend/app/services/`
- `backend/app/api/`
- `backend/app/schemas/`
- `backend/tests/fixtures/`
- `backend/tests/`
- `frontend/app/`
- `frontend/components/`
- `frontend/lib/`
- `scripts/smoke.sh`
- `docs/`

## Files Forbidden To Touch
- `AGENTS.md`
- `PROJECT_OVERVIEW.md`
- `TECH_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `TESTING.md`
- `TASK_TEMPLATE.md`
- `shared/`

## Inputs / Dependencies
- Phase 7 keyword-overlap scorer.
- Phase 8 replay fixture and deterministic run path.
- Human-labelled golden set fixture to be authored as part of this phase.

## Required Output Artifacts
- `backend/tests/fixtures/golden_set.json` with ≥10 labelled items.
- Calibration runner service.
- Calibration report schema and `GET /api/v1/calibration/latest` endpoint.
- Homepage calibration panel UI.
- `scripts/smoke.sh` phase9 block.
- `docs/reports/phase9-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase9`

## Acceptance Checks
- When `GET /api/v1/calibration/latest` is called after running calibration over the golden set, then the response includes `precision`, `recall`, `accuracy`, and a `per_category` breakdown derived from real scorer vs. label comparisons.
- Given the golden set with ≥5 known-pass and ≥5 known-fail items, the calibration report correctly counts true positives, false positives, and false negatives against the pre-labelled verdicts.
- After calibration, the homepage calibration panel displays scorer accuracy metrics backed by the calibration endpoint, not hardcoded values.
- `./scripts/smoke.sh phase9` asserts scorer precision ≥ 0.7 on the golden set and fails with a clear message if the threshold is not met.

## Contract Checks
- Calibration endpoint is a new read-only path and does not modify existing run, score, or review records.
- Golden set fixture uses the same `dataset_item` schema as `dataset_valid.json` with additional `expected_verdict` and `expected_failure_reason` fields in `metadata_json`.
- No changes to the canonical `score` schema on existing run records.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks.
- Example `GET /api/v1/calibration/latest` response.
- Golden set fixture file.
- Phase 9 acceptance report.

## Rollback / Recovery Notes
- If calibration precision falls below 0.7, do not change the golden set labels; investigate and fix the scorer logic instead.
- If the calibration endpoint causes schema conflicts, revert the new schemas and isolate calibration behind a separate module before retrying.

## Stop And Ask Conditions
- The golden set cannot be labelled without running real OpenAI calls (i.e., the expected verdicts depend on unknown model behavior).
- Calibration requires changing the canonical `score` schema in a way that breaks Phase 6 review records.
- Scorer precision on the golden set is below 0.5 after a first pass, indicating the scorer logic needs a more fundamental fix before calibration is meaningful.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
