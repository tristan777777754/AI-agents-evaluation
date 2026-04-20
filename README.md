# Agent Evaluation Workbench

Agent Evaluation Workbench is an internal product for evaluating AI agents in a structured, repeatable way.

It is not another agent. It is a quality workbench for teams that need to measure whether an agent version actually improved, inspect why failures happened, and compare runs over time using evidence instead of subjective demos.

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

This repository is currently documentation-first.

The project is still in the planning and scaffold stage, with the goal of implementing the system phase by phase rather than generating the full product in one pass.

The implementation path is intentionally structured around six phases:

1. Project skeleton and contracts
2. Dataset management
3. Evaluation run engine
4. Trace and case detail
5. Summary dashboard
6. Run comparison and product polish

## Repository Guide

If you want to understand the project quickly, start here:

1. [PROJECT_OVERVIEW.md](/Users/tristan/AI-agents-evaluation/PROJECT_OVERVIEW.md)
   Product framing, target users, MVP, and value proposition
2. [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)
   System modules, data flow, contracts, and technical design
3. [IMPLEMENTATION_PLAN.md](/Users/tristan/AI-agents-evaluation/IMPLEMENTATION_PLAN.md)
   Phase-by-phase delivery plan and acceptance criteria
4. [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)
   Validation strategy, smoke paths, and demo requirements
5. [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md)
   Standard task template for scoped phase work

If you are using this repo with an AI coding workflow or harness-driven execution, read:

- [AGENTS.md](/Users/tristan/AI-agents-evaluation/AGENTS.md)

## Source Of Truth

This README is an introduction to the project.

The canonical planning and implementation rules live in the project documents below:

1. [AGENTS.md](/Users/tristan/AI-agents-evaluation/AGENTS.md)
2. [PROJECT_OVERVIEW.md](/Users/tristan/AI-agents-evaluation/PROJECT_OVERVIEW.md)
3. [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)
4. [IMPLEMENTATION_PLAN.md](/Users/tristan/AI-agents-evaluation/IMPLEMENTATION_PLAN.md)
5. [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)
6. [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md)

If this README ever conflicts with those documents, the documents above should win.
