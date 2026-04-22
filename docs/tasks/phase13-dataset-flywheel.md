# Task: Phase 13 dataset flywheel

## Current Phase
Phase 13

## Goal
Make datasets accumulate as a managed quality asset by adding prompt-derived dataset drafts, review-gated approval, failed-case promotion into regression suites, and tag-based subset execution without breaking snapshot lineage or immutability.

## In Scope
- Add a prompt-to-dataset generation flow that creates dataset drafts rather than immediately published datasets.
- Add review and approval state for generated dataset drafts before they become runnable dataset snapshots.
- Add a “promote failed case to dataset” workflow from review queue or task detail into a regression-oriented dataset path.
- Add dataset source metadata such as `manual`, `generated`, and `promoted_from_failure`.
- Add task tags or equivalent subset-selection metadata so runs can target tagged subsets.
- Update smoke script with a `phase13` path and write a Phase 13 acceptance report.

## Out of Scope
- Fully autonomous dataset generation without human review.
- Production log ingestion pipeline.
- Replacing the existing manual dataset upload path.
- Multi-tenant dataset ownership or approval workflow.

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
- Phase 2 dataset upload and validation path.
- Phase 6 review queue and reviewer verdict flow.
- Phase 10 dataset snapshot immutability and diff support.
- Phase 11 rubric support where generated items may include structured rubric hints.

## Required Output Artifacts
- Dataset draft generation path and backing schema/model support.
- Review/approval flow for generated dataset drafts.
- Failed-case promotion path into a dataset or dataset draft.
- Tag or subset metadata support on dataset items and run launch.
- `scripts/smoke.sh` phase13 block.
- `docs/reports/phase13-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase13`

## Acceptance Checks
- When a user submits a prompt-derived dataset generation request, then the system creates a dataset draft with source metadata `generated` rather than silently publishing it as a live dataset.
- Given a generated draft that has not been approved, the run launcher rejects it or hides it from runnable dataset selectors.
- When a failed reviewed case is promoted, then a new dataset item is created with source metadata `promoted_from_failure` and lineage back to the original task run.
- Given a dataset with tagged items, a subset run only executes items matching the requested tag filter.
- `./scripts/smoke.sh phase13` covers generation draft creation, approval, failed-case promotion, and subset execution using deterministic fixtures.

## Contract Checks
- Existing dataset upload API remains valid for manually curated datasets.
- Dataset snapshot immutability remains intact; generated and promoted items create new snapshots rather than mutating old ones in place.
- Run creation schema only gains additive dataset selection or tag-filter fields.
- Existing dataset item IDs and lineage semantics remain backward-compatible.

## Evidence To Attach
- Command outputs for lint, typecheck, unit tests, and smoke checks.
- Example generated dataset draft response.
- Example promoted failure case record showing lineage back to the task run.
- Phase 13 acceptance report.

## Rollback / Recovery Notes
- If generated drafts complicate the existing dataset list UX, keep draft records behind a dedicated view rather than mixing them immediately with published datasets.
- If failed-case promotion introduces schema ambiguity, preserve lineage through metadata first before adding additional relational links.
- If tag filtering destabilizes run launch contracts, isolate it as an optional additive filter rather than a required parameter.

## Stop And Ask Conditions
- Prompt-based generation requires introducing fake datasets that bypass review or snapshot lineage.
- Failed-case promotion requires changing review queue semantics in a way that breaks Phase 6 reviewer records.
- Subset execution requires redefining canonical dataset or run entities rather than extending them additively.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
