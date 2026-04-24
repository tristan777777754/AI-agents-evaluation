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

The implementation was broken into phases — each with a defined scope, acceptance criteria, and a smoke test before the next began. Each phase covered one vertical slice of the system, from the initial skeleton through dataset management, evaluation execution, trace inspection, scoring, run comparison, real provider integration, reliability hardening, and experiment governance.

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

The core evaluation loop is fully implemented and running with a real OpenAI adapter. The repository includes a working frontend, backend API, and smoke test path covering dataset management, run execution, trace inspection, summary dashboard, run comparison, and review queue.

The repository includes:

- `frontend/`: Next.js + React + TypeScript dataset upload, run launch, trace viewer, summary dashboard, compare, and review surfaces
- `backend/`: FastAPI dataset, run, task trace, compare, and review APIs plus SQLAlchemy-backed persistence
- `shared/`: shared TypeScript contract mirrors aligned to backend schemas
- `docs/tasks/` and `docs/reports/`: harness artifacts for scoped phase work
- `scripts/smoke.sh`: minimum smoke entrypoint

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
