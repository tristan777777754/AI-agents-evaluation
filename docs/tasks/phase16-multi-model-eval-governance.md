# Task: Phase 16 multi-model eval governance

## Current Phase
Phase 16

## Goal
Formalize generator, agent, and judge as separate governed roles so evaluation setups are auditable, compatibility rules are enforceable, and cross-judge consistency can be analyzed without breaking the platform-managed credential model.

## In Scope
- Extend evaluation and scorer configuration so generator, agent, and judge provider/model metadata are explicitly stored and retrievable.
- Add compatibility rules that reject risky or disallowed configurations, especially high-risk self-judge setups where provider separation is required.
- Add judge audit-trail persistence for prompt/version/model metadata and judge reasoning metadata where available.
- Add cross-judge or judge-consistency reporting on a fixed evidence set.
- Update smoke script with a `phase16` path and write a Phase 16 acceptance report.

## Out of Scope
- Bring-your-own-key or tenant-specific provider credentials.
- General provider marketplace.
- Full experiment orchestration beyond evaluation governance.
- Replacing the existing scorer abstraction with an entirely new evaluation platform.

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
- Phase 11 judge-based scorer and credibility contract.
- Phase 13 dataset flywheel where generated datasets may include generator provenance.
- Phase 15 reliability sampling and compare extensions.
- Existing platform-managed credential assumptions from Phases 7-10.

## Required Output Artifacts
- Config/model/schema support for generator-agent-judge metadata.
- Compatibility-rule validation path and surfaced API errors.
- Judge audit trail persistence and read path.
- Cross-judge consistency or calibration-extension reporting.
- `scripts/smoke.sh` phase16 block.
- `docs/reports/phase16-acceptance-report.md`.

## Commands To Run
- `backend/.venv/bin/ruff check backend/`
- `backend/.venv/bin/mypy backend/app`
- `backend/.venv/bin/pytest backend/tests/`
- `cd frontend && npm run lint`
- `cd frontend && npm run typecheck`
- `cd frontend && npm run test`
- `./scripts/smoke.sh phase16`

## Acceptance Checks
- When an evaluation config is created with explicit generator, agent, and judge metadata, then the API persists and returns those fields without ambiguity.
- Given a configuration that violates a compatibility rule, the API rejects it with a clear validation error before run execution starts.
- After a judge-based run completes, the system can retrieve audit-trail metadata showing the judge provider, model, prompt version, and reasoning metadata or a clearly documented placeholder when reasoning is unavailable.
- Given at least two judge configurations over the same fixed evidence set, the system can produce a cross-judge consistency report derived from persisted evaluation artifacts.
- `./scripts/smoke.sh phase16` validates one rejected config, one accepted config, and one auditable judge result path.

## Contract Checks
- Platform-managed provider credential assumptions remain unchanged; no BYOK fields are introduced.
- Generator, judge, and compatibility metadata are additive to existing scorer/run config contracts.
- Existing compare and score semantics remain backward-compatible.
- Core entity names and status enums remain unchanged.

## Evidence To Attach
- Command outputs for lint, typecheck, unit tests, and smoke checks.
- Example rejected compatibility-rule response.
- Example judge audit-trail response.
- Phase 16 acceptance report.

## Rollback / Recovery Notes
- If generator-agent-judge config changes destabilize existing scorer config consumers, preserve older config shapes and introduce the new metadata as optional nested fields first.
- If audit-trail persistence becomes too coupled to run execution, store the audit record as a separate read-only evidence object rather than inflating the canonical score record.
- If cross-judge reporting is too broad for a first pass, limit it to a fixed fixture-driven report while keeping the schema forward-compatible.

## Stop And Ask Conditions
- Multi-model governance requires changing the platform-managed credential assumption to BYOK or tenant-scoped credentials.
- Compatibility-rule enforcement conflicts with already committed Phase 11 scoring contracts in a non-additive way.
- Audit-trail persistence would require storing unavailable proprietary provider data that cannot be accessed through the supported adapters.

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
