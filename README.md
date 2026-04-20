# Agent Evaluation Workbench

`Agent Evaluation Workbench` 是一個內部型評估工作台，用來把 AI Agent 的測試、trace、summary 與 compare 變成可重複、可比較、可追蹤的工程流程。

這個 repo 目前先以規格、phase 護欄與 implementation contract 為主，適合用 phase-driven Harness Engineering 方式逐步落地，而不是一次用大 prompt 直接生成整個系統。

## Source Of Truth

文件優先順序如下：

1. [AGENTS.md](/Users/tristan/AI-agents-evaluation/AGENTS.md)
2. [PROJECT_OVERVIEW.md](/Users/tristan/AI-agents-evaluation/PROJECT_OVERVIEW.md)
3. [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)
4. [IMPLEMENTATION_PLAN.md](/Users/tristan/AI-agents-evaluation/IMPLEMENTATION_PLAN.md)
5. [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)
6. [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md)

## Current Scope

- 單一 agent 類型的 evaluation workflow
- agent version registry
- dataset 匯入與驗證
- evaluation run 建立、執行、狀態追蹤
- task-level result persistence
- trace 記錄與單題檢視
- summary dashboard
- run comparison
- 基本 review queue

## Non-Goals

- multi-agent orchestration
- production traffic monitoring
- 自動 prompt optimization / self-healing
- bring-your-own-model / bring-your-own-key
- 多租戶 SaaS 架構
- 完整商業化 billing
- 以 fake data 支撐 dashboard 或 compare

## Canonical Contracts

實作時請固定使用以下 canonical names：

- Core entities: `agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, `trace`, `score`, `review`
- Run status: `pending`, `running`, `completed`, `failed`, `cancelled`, `partial_success`
- Task status: `pending`, `running`, `completed`, `failed`, `skipped`
- Dataset item fields: `input_text`, `category`, `expected_output`, `rubric_json`, `reference_context`, `metadata_json`

Canonical schema source:

- backend 的 schema contract 以 `backend/app/schemas/` 為主
- `shared/` 中的 TypeScript types 必須對齊同一份 contract，不可自行分叉

更完整的 contract 請看 [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)。

## Working Method

每次只做一個 phase。任務輸入必須使用 [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md)。

每完成一個 phase，至少要記錄：

- `lint`
- `typecheck`
- `unit test`
- `smoke test`

驗收標準與 demo path 請看 [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)。

## Phase Order

1. Phase 1: 專案骨架與規格落地
2. Phase 2: Dataset 管理流程
3. Phase 3: Evaluation Run 引擎
4. Phase 4: Trace 與單題檢視
5. Phase 5: Summary Dashboard
6. Phase 6: 版本比較與產品 polish

## Repository Status

目前 repo 以文件為主，尚未包含完整可執行的前後端程式碼。當實作開始後，請把實際專案命令補齊到 repo scripts 中，並同步更新：

- 啟動方式
- `lint`
- `typecheck`
- `test`
- `smoke`

## Recommended Bootstrap

若尚未開始實作，建議從 Phase 1 起手：

1. 建立前端、後端、shared contracts、docs 的目錄骨架
2. 固定 shared schema 與 API contract
3. 補上最小可執行的 healthcheck 與 skeleton route
4. 建立 phase 驗收與 smoke command
