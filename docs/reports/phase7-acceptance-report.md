# Phase 7 Acceptance Report

## Implementation Result

- Added `backend/app/adapters/openai_adapter.py` with an `OpenAIAgentAdapter` that uses the OpenAI Python SDK through the shared `run_task` contract.
- Extended `backend/app/services/runs.py` to support `adapter_type: "openai"` while preserving the deterministic `stub` path.
- Added provider credential gating via `OPENAI_API_KEY` in `backend/app/config.py` and sanitized `.env.example` back to a placeholder-only state.
- Added a second scorer config, `sc_keyword_overlap_v1`, and implemented keyword-overlap scoring for natural-language outputs without introducing LLM-as-judge behavior.
- Expanded `backend/tests/fixtures/dataset_valid.json` to a 20-item benchmark fixture across multiple categories for compare/category-breakdown coverage.
- Updated smoke coverage so `./scripts/smoke.sh phase7` first verifies the existing deterministic stub path and only runs OpenAI integration when `RUN_OPENAI_INTEGRATION_SMOKE=1` and `OPENAI_API_KEY` are both set.

## Acceptance Result

- `backend/.venv/bin/ruff check backend/` passed.
- `backend/.venv/bin/mypy backend/app` passed.
- `backend/.venv/bin/pytest backend/tests/` passed.
- `cd frontend && npm run lint` passed.
- `cd frontend && npm run typecheck` passed.
- `cd frontend && npm run test` passed.
- `./scripts/smoke.sh phase7` passed in deterministic-safe mode and reported `OpenAI integration smoke skipped` because external provider execution was not explicitly enabled in this session.

## Remaining Work

- Run the Phase 7 OpenAI integration smoke with:
  - `OPENAI_API_KEY` set in local `.env`
  - `RUN_OPENAI_INTEGRATION_SMOKE=1`
  - network access available to reach the OpenAI API
- Capture and attach:
  - one real task result showing non-stub `final_output`
  - one real compare response showing either improvement/regression or a defensible inconclusive outcome backed by persisted task records

## Next Phase Prerequisite Status

- Partially ready.
- Phase 7 implementation and regression safety are in place.
- Phase 8 should not start until the missing real-provider acceptance evidence has been captured.
