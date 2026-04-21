# Task: Phase 7 real OpenAI agent adapter and benchmark dataset

## Current Phase
Phase 7

## Goal
Add a real `OpenAIAgentAdapter` alongside the existing stub adapter, introduce a keyword-overlap scorer that works with natural-language outputs, and produce two real runs (v1 vs v2 with different system prompts) so the compare page shows genuine real-run signal rather than only deterministic stub results.

## In Scope
- Add `backend/app/adapters/openai_adapter.py` with `OpenAIAgentAdapter` calling `openai` Python SDK.
- Update `backend/app/services/runs.py` `_build_adapter` to dispatch on `adapter_type == "openai"`.
- Add `OPENAI_API_KEY` to `backend/app/config.py` and `.env.example`.
- Add a `keyword_overlap` scorer path alongside the existing `rule_based` path; keyword overlap checks whether key phrases from `expected_output` appear in `final_output` (case-insensitive, no LLM call needed).
- Update `backend/tests/fixtures/agent_version_v1.json` to use `adapter_type: "openai"` + a basic system prompt config.
- Update `backend/tests/fixtures/agent_version_v2.json` to use `adapter_type: "openai"` + an improved system prompt config.
- Expand `backend/tests/fixtures/dataset_valid.json` to at least 20 items across at least 4 categories so category breakdown is meaningful.
- Keep `StubAgentAdapter` intact and default all existing unit tests to `adapter_type: "stub"` so CI does not require an API key.
- Update smoke script with a `phase7` path that runs two real OpenAI runs back-to-back and asserts compare returns either an observable improvement/regression signal or a clearly reported inconclusive result backed by persisted task records.
- Phase 7 acceptance report.

## Out of Scope
- Removing or deprecating the stub adapter.
- Async or Celery-based execution.
- LLM-as-judge scoring.
- Multi-model comparison beyond the v1/v2 pair.
- Frontend UI changes beyond what already exists.

## Files Allowed To Touch
- `backend/app/adapters/`
- `backend/app/services/runs.py`
- `backend/app/config.py`
- `backend/tests/fixtures/`
- `backend/tests/`
- `scripts/smoke.sh`
- `.env.example`
- `docs/`

## Files Forbidden To Touch
- `AGENTS.md`
- `PROJECT_OVERVIEW.md`
- `TECH_SPEC.md`
- `IMPLEMENTATION_PLAN.md`
- `TESTING.md`
- `TASK_TEMPLATE.md`
- `frontend/`
- `shared/`

## Inputs / Dependencies
- Existing Phase 6 run, compare, and review persistence.
- `OPENAI_API_KEY` set in local `.env` (not committed).
- `openai` Python package installable via `pyproject.toml`.
- `backend/tests/fixtures/dataset_valid.json` (to be expanded).
- `backend/tests/fixtures/agent_version_v1.json` and `agent_version_v2.json` (to be updated).

## Required Output Artifacts
- `backend/app/adapters/openai_adapter.py`
- Updated `backend/app/services/runs.py` with openai dispatch path.
- Updated `.env.example` with `OPENAI_API_KEY` placeholder.
- Updated `backend/tests/fixtures/agent_version_v1.json` and `agent_version_v2.json` with real openai config.
- Expanded `backend/tests/fixtures/dataset_valid.json` with ≥20 items.
- `scripts/smoke.sh` phase7 block.
- `docs/reports/phase7-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase7`

## Acceptance Checks
- When `OPENAI_API_KEY` is set and `adapter_type` is `"openai"`, then `POST /api/v1/runs/{id}/execute` returns a completed run where `final_output` is a real non-stub string for at least one task.
- When the keyword-overlap scorer is used, then a task whose `final_output` contains all key phrases from `expected_output` receives `correctness >= 0.8` and `pass_fail = true`.
- Given two completed openai runs over the same 20-item dataset with different system prompts, `GET /api/v1/runs/compare` returns either at least one improvement/regression case or an explicit inconclusive result with persisted evidence.
- Given `adapter_type: "stub"` in the run config, all existing unit tests pass without `OPENAI_API_KEY` set.
- After running `./scripts/smoke.sh phase7`, the compare output is derived from real task records and is either non-zero or explicitly reported as inconclusive with preserved evidence.

## Contract Checks
- `adapter_type` values `"stub"` and `"openai"` are both valid; no other adapter types are introduced.
- Core entity names (`agent_version`, `dataset`, `eval_run`, `eval_task_run`, `trace`, `score`, `review`) remain unchanged.
- Canonical run statuses remain unchanged.
- `keyword_overlap` scorer is a new scorer type path and does not replace or break existing `rule_based` scorer config.
- `OPENAI_API_KEY` is never committed to the repo; only the placeholder in `.env.example` is committed.

## Evidence To Attach
- Command outputs for lint, typecheck, unit test, and smoke checks.
- Example `GET /api/v1/runs/compare` response showing real improvement/regression cases or an inconclusive result with evidence.
- Example task result showing real `final_output` from OpenAI.
- Phase 7 acceptance report.

## Rollback / Recovery Notes
- If the OpenAI adapter causes CI failures, verify `OPENAI_API_KEY` is not required in unit tests by confirming all tests use `adapter_type: "stub"`.
- If the keyword-overlap scorer produces unexpected scores, revert `backend/app/services/runs.py` scorer path and fall back to `rule_based`.
- Drop and recreate the local test database if schema drift occurs.

## Stop And Ask Conditions
- The OpenAI API returns a response format that does not fit the existing `run_task` return contract.
- Expanding the dataset requires changing `dataset_item` schema beyond what Phase 2 established.
- The keyword-overlap scorer cannot produce a meaningful signal without also changing the `score` schema.
- Two openai runs over the same dataset produce identical results with no compare signal and no defensible explanation for treating the run pair as inconclusive.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
