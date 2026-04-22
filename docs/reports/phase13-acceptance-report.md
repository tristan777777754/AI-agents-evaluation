# Phase 13 Acceptance Report

## Scope Confirmation

- Phase 13 only: dataset drafts, approval flow, failed-case promotion, source metadata, and tag-based subset execution.
- No Phase 14+ ergonomics, pagination, quick-run shortcuts, repeated-run sampling, or multi-model governance work was added.

## Implementation Result

- Added dataset lifecycle metadata to the canonical contract:
  - `source_origin`: `manual`, `generated`, `promoted_from_failure`
  - `lifecycle_status`: `draft`, `published`
  - `approval_status`: `pending_review`, `approved`
- Added additive dataset lineage fields:
  - `generated_prompt`, `approved_by`, `approved_at`
  - `dataset_snapshot.parent_snapshot_id`
  - `dataset_item.source_task_run_id`
  - `dataset_item.tags`
- Added prompt-derived dataset draft generation at `POST /api/v1/datasets/drafts/generate`.
- Added dedicated draft listing at `GET /api/v1/datasets/drafts`.
- Added explicit draft approval at `POST /api/v1/datasets/{dataset_id}/approve`, which creates a new immutable published snapshot rather than mutating the draft snapshot in place.
- Added failed-case promotion at `POST /api/v1/task-runs/{task_run_id}/promote`, preserving lineage back to the reviewed task run.
- Added optional `dataset_tag_filter` to run creation so subset runs execute only matching tagged items.
- Updated the homepage and task-detail UI with:
  - draft generation
  - draft approval
  - failed-case promotion
  - tag-filtered run launch

## Acceptance Result

- When a prompt-derived generation request is submitted, the system creates a dataset with `source_origin = generated`, `lifecycle_status = draft`, and `approval_status = pending_review`.
- Generated drafts are hidden from the default runnable dataset list and run creation rejects draft datasets until approval.
- Approving a generated draft produces a new immutable snapshot with `parent_snapshot_id` pointing back to the draft snapshot.
- Promoted failed cases create dataset items with `source_origin = promoted_from_failure`, preserve `source_task_run_id`, and carry regression tags.
- Subset runs only execute items whose tags intersect the requested `dataset_tag_filter`.
- Phase 12 trace intelligence remained healthy after the Phase 13 changes:
  - `backend/tests/test_phase12.py` passed
  - Phase 12 smoke path still passed before Phase 13 work continued

## Example Evidence

- Example generated draft response shape:

```json
{
  "dataset_id": "dataset_refund_edge_cases_<suffix>",
  "source_origin": "generated",
  "lifecycle_status": "draft",
  "approval_status": "pending_review",
  "snapshot_version": 1
}
```

- Example promoted failure lineage:

```json
{
  "promoted_item": {
    "source_origin": "promoted_from_failure",
    "source_task_run_id": "run_<id>__task_003",
    "tags": ["regression", "refunds", "execution_failed"]
  }
}
```

## Verification Commands

- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase13`

## Verification Summary

- `ruff check backend/`: passed
- `mypy backend/app`: passed
- `pytest backend/tests/`: passed (`44 passed`)
- `npm run lint`: passed
- `npm run typecheck`: passed
- `npm run test`: passed (`8 files, 11 tests`)
- `./scripts/smoke.sh phase13`: passed

## Remaining Work

- No additional Phase 13 scope is required for acceptance.
- Future Phase 14 work can build on the new dataset draft and promotion contracts, but should not replace them with quick-run or pagination concerns.

## Next Phase Prerequisite Status

- Satisfied.
- Dataset lineage remains immutable and additive.
- Run creation only gained additive tag-filter fields.
- Draft approval, promotion lineage, and subset execution all have deterministic automated coverage.
