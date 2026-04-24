# Agent Evaluation Workbench

Agent Evaluation Workbench is a side project built to practice **Harness Engineering** — a structured, document-driven approach to building software with AI coding agents in a phased, auditable way.

The project itself is a quality workbench for evaluating AI agents: upload a dataset, run a batch evaluation against a registered agent version, inspect traces, and compare runs with real metrics to determine whether a prompt or model change actually improved things.

## How This Was Built — Harness Engineering

Instead of coding freeform, the entire project was driven by a set of planning and specification documents that acted as the harness for each phase of work. Each phase had a defined scope, acceptance criteria, and a smoke test path before the next phase began.

The documents that formed the harness are:

| File | Role |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Defines how AI coding agents must behave inside this repo — what to read first, what not to touch, how to validate work |
| [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) | Product framing, target users, MVP scope, and success criteria |
| [`TECH_SPEC.md`](TECH_SPEC.md) | System modules, data flow, API contracts, and technical design decisions |
| [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) | Phase-by-phase delivery plan with per-phase acceptance criteria |
| [`TESTING.md`](TESTING.md) | Validation strategy, smoke paths, and demo requirements |
| [`TASK_TEMPLATE.md`](TASK_TEMPLATE.md) | Standard task brief format used to scope each phase of work |

The implementation was broken into 10 phases, each delivered and validated before the next began:

- **Phase 1** — Project skeleton and shared contracts
- **Phase 2** — Dataset management (upload, validation, preview)
- **Phase 3** — Evaluation run engine (stub adapter, Celery execution)
- **Phase 4** — Trace persistence and case-level inspection
- **Phase 5** — Run summary dashboard
- **Phase 6** — Run comparison and review queue
- **Phase 7** — Real OpenAI adapter and benchmark dataset
- **Phase 8** — Reliability hardening (rerun, state guards, repair)
- **Phase 9** — Scorer calibration and golden set
- **Phase 10** — Dataset governance, snapshots, and experiment lineage

This phased approach kept scope contained at each step and made it possible to validate the system end-to-end before adding complexity. It also demonstrated that AI agents can be directed reliably when given well-structured context rather than open-ended instructions.

---

## What This Project Is

This project is building a workbench for agent quality engineering.

The core idea is simple:

- register a stable agent version
- upload or select an evaluation dataset
- run a batch evaluation
- inspect summary metrics and failed traces
- compare runs to understand whether a change helped or hurt

The product is designed to turn agent iteration from ad hoc prompt tweaking into a measurable workflow.

## Why It Exists

AI teams can usually build agent demos quickly. The harder problem is knowing whether a new version is actually better.

Common breakdowns in existing workflows:

- manual testing is inconsistent and hard to reproduce
- prompt, model, or tool changes introduce regressions that are easy to miss
- raw logs are noisy and do not support product decisions on their own
- teams struggle to separate bad reasoning, bad tool choice, missing context, formatting errors, timeouts, and cost issues

This workbench exists to make those questions answerable.

## Who It Is For

The primary users are:

- AI engineers who need repeatable evaluation runs and trace-level debugging
- PMs or product leads who need quality, latency, and cost signals for release decisions
- reviewers or analysts who need to inspect failed cases and label failure reasons
- applied AI teams who want version-by-version evidence instead of anecdotal examples

## Core Workflow

The intended MVP workflow is:

1. Create or select an `Agent Version`
2. Upload or select a `Dataset`
3. Choose a `Scorer`
4. Start an `Evaluation Run`
5. Review the `Summary Dashboard`
6. Inspect failed cases in the `Trace Viewer`
7. Compare completed runs

By the end of that loop, a team should be able to answer three questions:

- Did the latest version improve?
- Where is it failing?
- Is it ready for wider release?

## MVP Scope

The current MVP is intentionally narrow. It includes:

- one supported agent type
- agent version registry with stable configuration snapshots
- dataset import and validation
- evaluation run creation, execution, and status tracking
- task-level result persistence
- trace recording and case-level inspection
- summary dashboard
- run comparison
- a basic review queue

The MVP is meant to be credible and end-to-end, not broad.

## What The MVP Does Not Include

The current scope explicitly excludes:

- multi-agent orchestration
- production live traffic monitoring
- automatic prompt optimization or self-healing
- bring-your-own-model or bring-your-own-key
- multi-tenant SaaS architecture
- full billing and commercialization flows
- complex enterprise-grade RBAC
- dashboards or compare views powered by fake data

## Product Principles

Several principles shape the project:

- real runs over fake demos
- repeatability over one-off examples
- traceability over opaque outputs
- stable version snapshots over mutable live settings
- real run-based summary and comparison metrics over mocked dashboards
- a narrow, coherent MVP over a wide but shallow platform

## High-Level Architecture

The planned MVP architecture is:

- `frontend/`: Next.js + React + TypeScript
- `backend/`: FastAPI + background worker
- `PostgreSQL`: metadata and run results
- `Redis`: queue and cache
- `Celery`: background execution
- S3-compatible object storage: large trace payloads

At a system level, the workbench is expected to include:

- a Workbench UI
- an API service
- an evaluation run orchestrator
- background workers
- an agent adapter layer
- a scoring engine
- a trace store
- a metrics aggregation layer

## Current Status

Phase 6 run comparison and review queue workflows are now implemented on top of the Phase 5
summary dashboard and the Phase 4 trace-backed execution flow.

The formal roadmap now has ten phases:

- `Phase 1-6`: MVP and demo-ready path
- `Phase 7-10`: post-MVP hardening, calibration, and governance

The repository includes:

- `frontend/`: Next.js + React + TypeScript dataset upload, run launch, trace viewer, summary dashboard, compare, and review surfaces
- `backend/`: FastAPI dataset, run, task trace, compare, and review APIs plus SQLAlchemy-backed persistence
- `shared/`: shared TypeScript contract mirrors aligned to backend schemas
- `docs/tasks/` and `docs/reports/`: harness artifacts for scoped phase work
- `scripts/smoke.sh`: minimum smoke entrypoint

The implementation path remains intentionally structured around ten phases:

1. Project skeleton and contracts
2. Dataset management
3. Evaluation run engine
4. Trace and case detail
5. Summary dashboard
6. Run comparison and product polish
7. Real OpenAI adapter and benchmark dataset
8. Reliability and harness hardening
9. Evaluation quality and scorer calibration
10. Dataset governance and experiment management

## Phase 1 Deliverables

- required top-level repository skeleton
- canonical backend contract definitions in `backend/app/schemas/contracts.py`
- shared TypeScript contract mirror in `shared/types/contracts.ts`
- minimum frontend homepage and frontend health route
- minimum backend root route plus `/api/v1/meta/health` and `/api/v1/meta/contracts`
- `.env.example`, `docker-compose.yml`, fixture placeholders, and acceptance artifacts

## Phase 2 Deliverables

Phase 2 adds the first real product workflow and keeps the later phases intentionally untouched.

Delivered in this phase:

- SQLAlchemy-backed `dataset` and `dataset_item` persistence
- `POST /api/v1/datasets` with JSON and CSV import support
- `GET /api/v1/datasets`, `GET /api/v1/datasets/{id}`, and `GET /api/v1/datasets/{id}/items`
- server-side row validation with structured import errors
- frontend dataset upload, list, and preview pages backed by real API data
- Phase 2 tests and `./scripts/smoke.sh phase2`

## Phase 3 Deliverables

Phase 3 adds the first executable evaluation loop while keeping trace, summary, compare, and review flows deferred.

Delivered in this phase:

- SQLAlchemy-backed `eval_run`, `eval_task_run`, and `score` persistence
- `POST /api/v1/runs`, `GET /api/v1/runs`, `GET /api/v1/runs/{id}`, and `GET /api/v1/runs/{id}/tasks`
- deterministic stub adapter in `backend/app/adapters/stub.py`
- Celery-backed execution path with eager local/test mode
- fixture-backed `GET /api/v1/registry` for available `agent_version` and `scorer_config`
- frontend run launcher and run detail pages backed by real API data
- Phase 3 tests and `./scripts/smoke.sh phase3`

## Phase 4 Deliverables

Phase 4 adds real trace persistence and case-level inspection while keeping summary, compare, and review flows deferred.

Delivered in this phase:

- SQLAlchemy-backed `trace` persistence linked to `eval_task_run`
- deterministic trace event and failure-reason persistence during run execution
- `GET /api/v1/task-runs/{id}` and `GET /api/v1/task-runs/{id}/trace`
- frontend task detail and trace viewer pages backed by real API data
- Phase 4 tests and `./scripts/smoke.sh phase4`

## Phase 5 Deliverables

Phase 5 adds a real run-backed summary dashboard while keeping compare and review flows deferred.

Delivered in this phase:

- `GET /api/v1/runs/{id}/summary` backed by persisted task, score, and trace records
- success rate, average latency, total cost, review-needed count, and category breakdown aggregation
- failure breakdown plus failed-case navigation links into the existing trace viewer
- homepage dashboard wired to the latest persisted run without fake data
- Phase 5 tests and `./scripts/smoke.sh phase5`

## Phase 6 Deliverables

Phase 6 adds persisted run comparison and review workflows while polishing the main demo path.

Delivered in this phase:

- `GET /api/v1/runs/compare` backed by persisted run, task, score, and trace rows
- improvement and regression case detection across two real runs over the same dataset
- persisted `review` records plus `GET /api/v1/reviews/queue` and `PUT /api/v1/task-runs/{id}/review`
- frontend compare page, homepage compare launcher, review queue page, and task-level review editor
- Phase 6 tests and `./scripts/smoke.sh phase6`

## Phase 7-10 Direction

After the MVP path is complete, the roadmap continues with four hardening phases:

- Phase 7 adds a real OpenAI-backed adapter, a benchmark dataset, and natural-language-friendly keyword overlap scoring while preserving the deterministic stub path for CI.
- Phase 8 adds rerun, status transition guards, repair utilities, and replay fixtures so the harness can recover and be audited.
- Phase 9 adds a golden set, calibration reporting, and scorer-quality visibility so teams can measure whether the scorer agrees with human labels.
- Phase 10 adds dataset snapshots, diffing, baseline pinning, experiment metadata, and compare lineage so every comparison can be traced to exact inputs and configs.

## Local Setup

### Backend

1. Create a virtual environment if you want isolation.
2. Install backend dependencies:

```bash
python3 -m pip install -e "backend[dev]"
```

3. Start the API:

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

### Frontend

1. Install frontend dependencies:

```bash
cd frontend && npm install
```

2. Start the Next.js app:

```bash
cd frontend && npm run dev
```

By default the frontend expects the backend at `http://localhost:8000`. Override with `NEXT_PUBLIC_BACKEND_BASE_URL` if needed.

### Local Infrastructure

Start the local infrastructure stack with Docker Compose:

```bash
docker compose up -d
```

This starts:

- PostgreSQL on `5432`
- Redis on `6379`
- MinIO on `9000` with console on `9001`

## Validation Commands

Backend:

```bash
ruff check backend/
mypy backend/app
pytest backend/tests/
```

Frontend:

```bash
cd frontend && npm run lint
cd frontend && npm run typecheck
cd frontend && npm run test
```

Smoke:

```bash
./scripts/smoke.sh phase6
```

## Repository Guide

If you want to understand the project quickly, start here:

1. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
   Product framing, target users, MVP, and value proposition
2. [TECH_SPEC.md](TECH_SPEC.md)
   System modules, data flow, contracts, and technical design
3. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
   Phase-by-phase delivery plan and acceptance criteria
4. [TESTING.md](TESTING.md)
   Validation strategy, smoke paths, and demo requirements
5. [TASK_TEMPLATE.md](TASK_TEMPLATE.md)
   Standard task template for scoped phase work

If you are using this repo with an AI coding workflow or harness-driven execution, read:

- [AGENTS.md](AGENTS.md)

## Source Of Truth

This README is an introduction to the project.

The canonical planning and implementation rules live in the project documents below:

1. [AGENTS.md](AGENTS.md)
2. [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
3. [TECH_SPEC.md](TECH_SPEC.md)
4. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
5. [TESTING.md](TESTING.md)
6. [TASK_TEMPLATE.md](TASK_TEMPLATE.md)

If this README ever conflicts with those documents, the documents above should win.
