# Phase 14 Acceptance Report

## Scope Confirmation

- Phase 14 only: database-backed registry CRUD, persisted quick-run defaults, additive auto-compare, real run progress polling, and pagination/filtering for runs, dataset items, and review queue views.
- No Phase 15+ repeated-run sampling, variance analysis, or multi-model governance work was added.

## Implementation Result

- Replaced fixture-only registry lookup with database-backed runtime registry storage for:
  - `agent`
  - `agent_version`
  - persisted registry defaults for quick-run dataset/scorer selection
- Preserved immutable `agent_version` semantics by allowing create/list only; no update path was added.
- Kept scorer contracts backward-compatible while continuing to seed baseline scorer configs into the registry/defaults flow.
- Added registry API ergonomics:
  - `POST /api/v1/registry/agents`
  - `POST /api/v1/registry/agent-versions`
  - `PUT /api/v1/registry/defaults`
  - additive `agents` and `defaults` fields on `GET /api/v1/registry`
- Added quick-run and auto-compare APIs:
  - `POST /api/v1/runs/quick`
  - `GET /api/v1/runs/{run_id}/auto-compare`
- Updated run execution so `completed_tasks` / `failed_tasks` are persisted during execution instead of only at the end, enabling honest polling.
- Added additive pagination/filtering support:
  - runs: `page`, `per_page`, `status`, `dataset_id`, `agent_version_id` via query params plus response headers
  - dataset items: `page`, `per_page`, `tag`, `category`
  - review queue: `page`, `per_page`, `review_status`, `failure_reason`
- Updated frontend for:
  - runtime registry management
  - persisted quick-run defaults
  - quick-run redirect into compare when a baseline is immediately available
  - run detail polling from real backend state
  - paginated runs, dataset items, and review queue views

## Acceptance Result

- When a new agent version is created through the registry API, it appears in registry reads immediately and is selectable without backend restart.
- Given persisted default dataset/scorer IDs, quick run creates a real `eval_run` using those defaults and returns an additive auto-compare suggestion/result.
- During execution, `GET /api/v1/runs/{run_id}` reports intermediate `completed_tasks / total_tasks` values sourced from persisted task completion state.
- Given more rows than one page, the runs list, dataset item view, and review queue all return bounded page payloads and expose next-page state.
- `./scripts/smoke.sh phase14` covers registry CRUD, quick-run defaults, auto-compare, pagination, and progress polling evidence.

## Example Evidence

- Registry create/list excerpt:

```json
{
  "created_agent_version": {
    "agent_version_id": "av_support_qa_report_v3",
    "agent_id": "agent_support_qa",
    "version_name": "v3",
    "model": "gpt-4.1-mini",
    "prompt_hash": "sha256:report-v3"
  },
  "registry_excerpt": {
    "defaults": {
      "default_dataset_id": "dataset_support_faq_v1",
      "default_scorer_config_id": "sc_rule_based_v1"
    },
    "latest_agent_version": {
      "agent_version_id": "av_support_qa_report_v3",
      "agent_id": "agent_support_qa",
      "version_name": "v3"
    }
  }
}
```

- Run detail progress excerpt from a polled in-flight run:

```json
{
  "run_id": "run_690a1b630c53",
  "status": "running",
  "completed_tasks": 1,
  "total_tasks": 20,
  "failed_tasks": 0
}
```

## Verification Commands

- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase14`

## Verification Summary

- `ruff check backend/`: passed
- `mypy backend/app`: passed
- `pytest backend/tests/`: passed (`48 passed`)
- `npm run lint`: passed
- `npm run typecheck`: passed
- `npm run test`: passed (`8 files, 11 tests`)
- `./scripts/smoke.sh phase14`: passed

## Remaining Work

- No additional Phase 14 scope is required for acceptance.
- Phase 15 can build on the new quick-run ergonomics and persisted progress counters without changing canonical run/compare semantics.

## Next Phase Prerequisite Status

- Satisfied.
- Registry CRUD is runtime-backed and does not require fixture edits or restart to add a new version.
- Quick-run defaults are persisted and do not rely on fake client-side placeholders.
- Progress polling, pagination, and auto-compare all have automated coverage plus deterministic smoke evidence.
