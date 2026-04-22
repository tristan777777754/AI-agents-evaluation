# Phase 12 Acceptance Report

## Scope

- Phase 12 only: trace intelligence, side-by-side trace compare, and derived path diagnostics.
- No Phase 13+ dataset flywheel, ergonomics, sampling, or governance work was added.

## Implementation Result

- Added a dedicated `GET /api/v1/compare/traces` endpoint backed by a new trace-intelligence service layer.
- Added additive trace-derived metrics:
  - `efficiency_score`
  - `max_steps`
  - `excess_step_count`
  - `failure_step_index`
  - tool-path signals and event counters
- Added trace-level regression / improvement evidence detection for:
  - more or fewer steps
  - more or fewer tool calls
  - efficiency-score deltas
  - failure-mode changes
  - failure-step shifts
- Integrated a compare-page trace panel with baseline / candidate side-by-side raw events and derived metrics.
- Added deterministic Phase 12 fixtures and tests covering one regression path and one improvement path.
- Added `phase12` coverage to `scripts/smoke.sh`.

## Acceptance Result

### Commands

- `backend/.venv/bin/ruff check backend/`
  - Passed
- `backend/.venv/bin/mypy backend/app`
  - Passed
- `backend/.venv/bin/pytest backend/tests/`
  - Passed (`41 passed`)
- `cd frontend && npm run lint`
  - Passed
- `cd frontend && npm run typecheck`
  - Passed
- `cd frontend && npm run test`
  - Passed (`8 files, 11 tests`)
- `./scripts/smoke.sh phase12`
  - Passed

### Acceptance Checks

- When `GET /api/v1/compare/traces?baseline=&candidate=&dataset_item_id=` is called for two known runs, the response returns both traces and derived metrics for the same dataset item.
- Given a deterministic fixture where the candidate reaches the same final answer with more steps than the baseline, trace compare flags a regression via `more_steps`, `more_tool_calls`, and `efficiency_score`.
- Given `rubric_json.max_steps` on `ds_item_006`, `efficiency_score` is stably recomputed as `1.0` for the baseline path and `0.5` for the longer candidate path.
- The compare UI keeps raw trace event payloads visible while showing baseline / candidate derived metrics side by side.
- `./scripts/smoke.sh phase12` validates both raw trace access and derived regression / improvement signals.

## Example Trace Compare Response

```json
{
  "dataset_item_id": "ds_item_006",
  "overall_label": "regression",
  "same_final_output": true,
  "baseline": {
    "derived_metrics": {
      "step_count": 2,
      "tool_count": 0,
      "max_steps": 2,
      "efficiency_score": 1.0
    }
  },
  "candidate": {
    "derived_metrics": {
      "step_count": 4,
      "tool_count": 2,
      "max_steps": 2,
      "efficiency_score": 0.5
    }
  },
  "regression_signals": [
    {
      "signal_key": "more_steps",
      "direction": "regression"
    },
    {
      "signal_key": "more_tool_calls",
      "direction": "regression"
    },
    {
      "signal_key": "efficiency_score",
      "direction": "regression"
    }
  ]
}
```

## Contract Check Result

- Existing task trace APIs still expose raw trace payloads without schema breakage.
- New derived metrics are additive and computed in a service layer; raw trace storage remains intact.
- Existing run compare semantics remain unchanged; trace comparison lives behind a dedicated endpoint.
- Existing run, task, trace, and review identifiers remain unchanged.

## Remaining Work

- No additional Phase 12 scope is required for acceptance.
- Future Phase 13+ work should build on these trace-evidence contracts rather than replacing them.

## Next Phase Prerequisite Status

- Phase 12 acceptance criteria are satisfied.
- Required lint, typecheck, unit test, and smoke validations were completed successfully.
- The repo is ready for the next documented phase once the user explicitly authorizes Phase 13 work.
