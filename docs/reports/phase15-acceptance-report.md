# Phase 15 Acceptance Report

## Scope Confirmation

- Phase 15 only: repeated-run sampling launch, additive sampling metadata on persisted runs, summary variability metrics, compare-side stability interpretation, frontend sampling display, and deterministic `phase15` smoke coverage.
- No Phase 16+ multi-model governance work was added.
- Core status values, canonical `run_id`, and existing single-run endpoints remain intact.

## Implementation Result

- Added additive sampling metadata to `eval_run` records:
  - `sample_group_id`
  - `sample_index`
  - `sample_count`
  - `sampling_config_json`
- Added sampled launch API:
  - `POST /api/v1/runs/sampling`
- Extended run/detail contracts with optional nested `sampling` metadata instead of replacing the canonical single-run shape.
- Extended summary responses with `sampling` metrics derived from persisted sibling runs in the same sample group:
  - mean
  - stddev
  - variance
  - min / max
  - consistency rate
- Extended compare responses with additive `sampling` evidence and an interpretation layer:
  - `stable_improvement`
  - `unstable_improvement`
  - `stable_regression`
  - `unstable_regression`
  - `stable_tie`
  - `unstable_tie`
- Updated the frontend to launch repeated runs from the existing launcher and display sampling-backed metrics on:
  - homepage dashboard
  - run detail header
  - compare page
  - run list
- Added deterministic automated coverage:
  - `backend/tests/test_phase15.py`
  - `frontend/lib/phase15.test.ts`
  - `./scripts/smoke.sh phase15`

## Acceptance Result

### Acceptance Checks

- When a repeated-run request is made with a fixed sample count, then the system persists multiple individual runs linked by shared sampling metadata rather than overwriting a single run.
- Given a repeated-run fixture with intentionally varied outcomes, the summary shows mean performance plus variability metrics derived from actual persisted samples.
- When compare analyzes a stable baseline and an unstable candidate, then the response distinguishes instability from deterministic regression using persisted sample evidence.
- Deterministic replay coverage remains intact through `./scripts/smoke.sh phase15`.
- Frontend sampling displays are backed by additive API fields, not fake placeholder recomputation.

### Example Summary Evidence

```json
{
  "sampling": {
    "sample_count": 3,
    "completed_sample_count": 3,
    "consistency_rate": 80.0,
    "success_rate": {
      "mean": 91.67,
      "stddev": 8.5,
      "variance": 72.22
    }
  }
}
```

### Example Compare Evidence

```json
{
  "sampling": {
    "interpretation": "unstable_regression",
    "baseline": {
      "sample_count": 3,
      "is_stable": true
    },
    "candidate": {
      "sample_count": 3,
      "success_rate_mean": 91.67,
      "success_rate_stddev": 8.5,
      "consistency_rate": 80.0,
      "is_stable": false
    }
  }
}
```

## Checks Run

- `backend/.venv/bin/ruff check backend/`: passed
- `backend/.venv/bin/mypy backend/app`: passed
- `backend/.venv/bin/pytest backend/tests/`: passed (`51 passed`)
- `cd frontend && npm run lint`: passed
- `cd frontend && npm run typecheck`: passed
- `cd frontend && npm run test`: passed (`14 passed`)
- `./scripts/smoke.sh phase15`: passed

## Remaining Work

- No additional Phase 15 scope is required for task acceptance.
- Future Phase 16 work can build on the additive sampling metadata, but must not replace the canonical single-run contract with governance-only abstractions.

## Next Phase Prerequisite Status

- Phase 15 deliverables are implemented and verified.
- Required lint, typecheck, unit test, and smoke coverage all passed.
- Deterministic replay remains available in the same repo state.
- The repo is ready for a Phase 16 task, subject to a separate Phase 16 task spec.
