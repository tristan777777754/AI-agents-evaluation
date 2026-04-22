# Phase 11 Acceptance Report

## Scope

- Added additive `llm_judge` and `rubric_based` scorer paths.
- Added judge compatibility validation that rejects same-provider judge scoring by default.
- Extended compare responses with credibility statistics and labels.
- Updated frontend compare/dashboard/task detail surfaces to render credibility signals and score evidence.
- Added deterministic Phase 11 fixtures, tests, and smoke coverage.

## Verification

- `backend/.venv/bin/ruff check backend/`
  - Passed
- `backend/.venv/bin/mypy backend/app`
  - Passed
- `backend/.venv/bin/pytest backend/tests/`
  - Passed (`39 passed`)
- `cd frontend && npm run lint`
  - Passed
- `cd frontend && npm run typecheck`
  - Passed
- `cd frontend && npm run test`
  - Passed (`7 files, 10 tests`)
- `./scripts/smoke.sh phase11`
  - Passed (`Backend smoke checks passed. Frontend smoke checks passed.`)

## Acceptance Mapping

- When a run uses `scorer_type = "llm_judge"`, task score records now persist additive `evidence_json` with `score_method`, `judge_provider`, `judge_model`, `judge_verdict`, and token-match evidence while leaving task result fields unchanged.
- Given a dataset item with `rubric_json.must_do`, `rubric_json.must_not_do`, and `rubric_json.max_steps`, the rubric scorer now evaluates those clauses and persists per-clause evidence in `evidence_json`.
- Compare responses now include `sample_size`, `confidence_interval`, `p_value`, `is_significant`, and a derived `credibility.label`.
- Compare UI now distinguishes directional movement from statistically significant movement.
- The deterministic smoke path fails if judge evidence, rubric evidence, or compare credibility fields are missing.

## Example Compare Evidence

```json
{
  "sample_size": 20,
  "confidence_interval": {
    "lower": -4.8,
    "upper": 14.8
  },
  "p_value": 0.3173,
  "is_significant": false,
  "credibility": {
    "label": "directional_improvement",
    "sample_size": 20,
    "confidence_interval": {
      "lower": -4.8,
      "upper": 14.8
    },
    "p_value": 0.3173,
    "is_significant": false
  }
}
```

## Example Judge Evidence

```json
{
  "score_method": "llm_judge",
  "judge_model": "claude-3-5-sonnet",
  "judge_provider": "anthropic",
  "judge_verdict": "pass",
  "matched_token_ratio": 1.0,
  "reasoning_summary": "Deterministic judge proxy accepted the answer because the expected evidence tokens were present."
}
```

## Remaining Gaps

- No historical backfill was performed; existing persisted scores remain unchanged.
- Judge scoring remains deterministic and fixture-backed in tests; no external judge provider execution was introduced.
- Phase 12 trace intelligence work remains untouched.
