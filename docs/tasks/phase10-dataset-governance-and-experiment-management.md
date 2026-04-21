# Task: Phase 10 dataset governance and experiment management

## Current Phase
Phase 10

## Goal
Give datasets, baselines, and compare results a governance layer so that any compare conclusion can be traced back to an exact dataset snapshot, agent version snapshot, and scorer config — and so that dataset updates are visible diffs, not silent overwrites.

## In Scope
- Add dataset versioning: each upload creates a new immutable snapshot rather than overwriting the existing dataset.
- Add a dataset diff endpoint (`GET /api/v1/datasets/{id}/diff?from_snapshot=&to_snapshot=`) returning added, removed, and changed items between two snapshots.
- Add baseline pinning: a run can be marked as `baseline = true`; compare always surfaces the baseline run in the selector with a visual indicator.
- Add an experiment metadata field to runs (`experiment_tag`, `notes`) captured at run creation and visible in run detail and compare views.
- Add a lineage block to compare responses that lists the exact dataset snapshot ID, agent version snapshot hash, and scorer config ID used in each run.
- Update smoke script with a `phase10` path that uploads two dataset versions, diffs them, and asserts the diff reflects the actual item changes.
- Phase 10 acceptance report.

## Out of Scope
- Automated dataset generation or augmentation.
- Multi-tenant dataset ownership.
- Retroactive re-tagging of Phase 1-9 historical runs.
- Storage backend changes (keep the repository's existing local dev database strategy).

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
- Phase 7 real run records with agent version snapshots already stored on the run record.
- Phase 8 replay fixture showing stable run re-execution.
- Phase 9 calibration report linking scorer config to evidence.
- Existing dataset upload and list APIs.

## Required Output Artifacts
- Dataset snapshot model and immutable upload path.
- Dataset diff endpoint and service logic.
- Baseline pin field on `EvalRunRecord` and exposed via API and UI.
- `experiment_tag` and `notes` fields on run creation schema and run detail schema.
- Lineage block in compare response.
- `scripts/smoke.sh` phase10 block.
- `docs/reports/phase10-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase10`

## Acceptance Checks
- When a dataset is uploaded a second time with one item changed, the system creates a new snapshot and the original snapshot remains readable and unchanged.
- When `GET /api/v1/datasets/{id}/diff?from_snapshot=&to_snapshot=` is called for two known snapshots, the response lists exactly the items that were added, removed, or changed between them.
- When a run is marked as baseline, `GET /api/v1/runs` returns it with `baseline: true` and the compare launcher UI visually distinguishes it.
- When `GET /api/v1/runs/compare` is called for two runs, the response includes a `lineage` block containing `dataset_snapshot_id`, `agent_version_snapshot_hash`, and `scorer_config_id` for each run.
- `./scripts/smoke.sh phase10` uploads two dataset versions, diffs them, and asserts the diff item count matches the known change count.

## Contract Checks
- Dataset upload now creates a versioned snapshot; existing dataset IDs from Phase 2 remain readable but the upload endpoint response includes a new `snapshot_id` field.
- Run creation schema gains optional `experiment_tag` (string) and `notes` (string) fields; existing runs without these fields are unaffected.
- Compare response gains a `lineage` key; existing keys are unchanged.
- Baseline pin is an optional boolean on the run record; existing runs default to `baseline: false`.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks.
- Example dataset diff response showing added and changed items.
- Example compare response showing lineage block.
- Phase 10 acceptance report.

## Rollback / Recovery Notes
- If the dataset versioning migration breaks existing dataset item queries, revert the migration and keep the single-version model while redesigning the snapshot FK structure.
- If the lineage block introduces circular dependency between run and dataset schemas, isolate lineage as a computed read-only field in the compare service rather than a stored FK.

## Stop And Ask Conditions
- Dataset versioning requires changing the `dataset_item` FK structure in a way that breaks Phase 3-6 run records that reference item IDs.
- The diff algorithm cannot handle the item count in the fixture without a schema change to `dataset_item`.
- Baseline pinning requires multi-user authorization logic that is outside the single-user MVP scope.

## Completion Report
- Implementation result: Added immutable dataset snapshots, diff API, baseline pinning endpoint, run experiment metadata, compare lineage, updated frontend bindings, and Phase 10 smoke/test coverage.
- Acceptance result: Backend/frontend lint, typecheck, unit tests, and `./scripts/smoke.sh phase10` all pass.
- Remaining work: None within the planned Phase 10 scope.
- Next phase prerequisite status: Phase 10 is the final planned roadmap phase; no additional phase prerequisite is pending.
