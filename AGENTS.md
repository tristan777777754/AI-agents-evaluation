# AGENTS.md

## Project Goal

本專案要建立一個 `Agent Evaluation Workbench`，用來系統化評估 AI Agent 的品質、穩定性、成本與延遲。這不是另一個被測 Agent，而是一個讓團隊可以註冊版本、匯入資料集、執行批次評估、查看 trace、比較 run 差異的評估工作台。

本專案的核心目標是把「主觀 demo 判斷」轉成「可重複、可比較、可追蹤」的工程流程。

## Repository

- GitHub: `https://github.com/tristan777777754/AI-agents-evaluation`
- Default branch: `main`

## Current Scope

目前只做 MVP 到可展示版本，範圍嚴格限制為：

- 單一 agent 類型的 evaluation workflow
- Agent version registry
- Dataset 匯入與驗證
- Evaluation run 建立、執行、狀態追蹤
- Task-level result 持久化
- Trace 記錄與單題檢視
- Summary dashboard
- Run comparison
- 基本 review queue

正式路線分成三段：

- `Phase 1-6` 為 MVP 與 demo-ready 主線
- `Phase 7-10` 為建立在已完成 MVP 之上的 post-MVP hardening / governance roadmap
- `Phase 11-16` 為建立在 `Phase 7-10` 之上的 evaluation credibility、trace intelligence、dataset flywheel、operator ergonomics、reliability sampling 與 multi-model eval governance 延伸路線

`Phase 7-10` 可以擴充可重現性、真實 adapter、校準與治理能力，但不得推翻前六個 phase 已固定的核心 domain、compare 原則與單租戶前提。

`Phase 11-16` 可以提升評分可信度、trace 診斷能力、dataset 累積能力與多模型評估治理，但不得把專案改造成多租戶 SaaS、通用 benchmark marketplace 或脫離既有 harness engineering 原則的研究型平台。

明確不在目前 scope 內的內容：

- Multi-agent orchestration
- Production live traffic monitoring
- 自動 prompt optimization / self-healing
- Bring-your-own-model / bring-your-own-key
- 多租戶 SaaS 架構
- 完整商業化 billing
- 複雜 RBAC / enterprise-grade 權限系統
- 以 fake data 支撐 dashboard 或 compare 頁面
- 直接監控 production live traffic 的 agent 行為本身
- 自動修 agent、代替人工做 release 決策的 autonomous optimizer

## Tech Assumptions

若未來 repo 尚未完全落地，請以以下技術方向為預設，不要隨意改向：

- Frontend: `Next.js` + `React` + `TypeScript`
- Backend: `FastAPI`
- Database: `PostgreSQL`
- Queue / Cache: `Redis`
- Background worker: `Celery`（固定選用，不得改成 RQ 或 Dramatiq）
- Object storage: S3-compatible storage for large trace payloads
- Data access: `SQLAlchemy`
- 後端測試框架: `pytest`
- 前端測試框架: `Vitest`

產品與模型假設：

- MVP 使用平台管理的 builder-authenticated configuration
- 終端使用者在 MVP 不提供自己的 API key
- 先支援單租戶、內部工具型使用情境
- 若後續 phase 接入真實模型供應商金鑰，仍屬平台管理設定，不得演變成 BYOK 模式

## Directory Structure

Phase 1 建立的目錄骨架必須符合以下結構，後續 phase 不得改變頂層目錄命名：

```
/
├── frontend/          # Next.js + React + TypeScript
├── backend/           # FastAPI + Celery worker
│   ├── app/
│   │   ├── api/       # route handlers
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # business logic
│   │   └── worker/    # Celery tasks
│   └── tests/
│       └── fixtures/  # pytest fixtures
├── shared/            # 跨前後端共用 TypeScript types
├── docs/              # 額外說明文件
├── docker-compose.yml # 本地 PostgreSQL + Redis
└── .env.example       # 環境變數範本
```

## Required Environment Variables

Phase 1 必須建立 `.env.example`，包含以下所有變數。實際值放 `.env`（不 commit）：

```
# Database
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/eval_workbench

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# Object Storage (S3-compatible)
STORAGE_BUCKET=eval-traces
STORAGE_ENDPOINT_URL=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin

# Judge Model (for scorer)
JUDGE_MODEL_API_KEY=
JUDGE_MODEL_NAME=<configured-judge-model>

# Post-MVP provider integration
OPENAI_API_KEY=

# App
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

## Operating Rules

### Phase Discipline

- 必須依照 `IMPLEMENTATION_PLAN.md` 的 phase 順序執行
- 一次只能做一個 phase
- 未完成當前 phase 的 acceptance criteria，不得提前做下一個 phase
- 不要在同一輪工作中同時偷做 2 個以上 phase 的功能
- 若某個需求跨 phase，先完成當前 phase 所需的最小 contract，再把延伸內容留到後續 phase
- 每次任務輸入必須遵循 [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md) 中的 task template

### Repository Workflow

- 每完成一次 update，預設要自動 commit 並 push 到 GitHub `origin`
- 若工作樹中所有變更都屬於當前任務範圍，push 前不需要再次詢問使用者
- 若變更內容混入明顯無關或風險不明的修改，才允許停止並回報

### Contract Discipline

- 優先保證 shared schema、API contract、資料流正確
- `backend/app/schemas/` 中的 backend schema 為 canonical contract source，`shared/` 中的 TypeScript types 必須對齊同一份 contract，不可雙方各自演化
- 不得在沒有必要時重命名核心資料欄位
- 不得讓前端頁面依賴尚未存在的假 API
- 不得以 mock data 偽裝功能完成
- 每個頁面都必須可以追溯到真實資料來源、真實資料模型與真實 API
- 牽涉資料模型、狀態流轉、summary、scoring、compare 的實作，必須對齊 [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md) 中的 implementation contracts

### Coding Rules

- 先做可用且可驗證的最小版本，不要過早抽象化
- 優先單體應用加背景 worker，不要過早拆微服務
- Trace、score、summary 的資料結構要可擴充，但 MVP 只做必要欄位
- 大型 trace payload 不要直接塞進主查詢表，應保留摘要與索引欄位
- 單題失敗不得拖垮整個 run
- 所有 summary / compare 數字都必須來自真實 run result 聚合
- UI 可以簡潔，但資料流與狀態流轉必須完整
- 每個 `eval_run` 必須保留足夠的 metadata，以支援 compare 與歷史結果追蹤

### Files And Areas That Must Not Be Changed Casually

以下內容沒有明確理由不得亂改：

- 核心 domain 命名：`agent`, `agent_version`, `dataset`, `dataset_item`, `eval_run`, `eval_task_run`, `trace`, `score`, `review`
- Phase 順序與 phase 定義
- MVP 邊界與 non-goals
- 單一 agent type、單租戶、平台管理模型設定的前提
- 「比較頁與 dashboard 必須基於真實 run」這個原則
- 核心狀態模型，例如 `pending`, `running`, `completed`, `failed`, `cancelled`, `partial_success`

若確實需要調整上述內容，先同步更新：

- [PROJECT_OVERVIEW.md](/Users/tristan/AI-agents-evaluation/PROJECT_OVERVIEW.md)
- [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)
- [IMPLEMENTATION_PLAN.md](/Users/tristan/AI-agents-evaluation/IMPLEMENTATION_PLAN.md)

## Required Phase Order

1. `Phase 1` 專案骨架與規格落地
2. `Phase 2` Dataset 管理流程
3. `Phase 3` Evaluation Run 引擎
4. `Phase 4` Trace 與單題檢視
5. `Phase 5` Summary Dashboard
6. `Phase 6` 版本比較與產品 polish
7. `Phase 7` 真實 OpenAI adapter 與 benchmark dataset
8. `Phase 8` Reliability 與 harness hardening
9. `Phase 9` Evaluation quality 與 scorer calibration
10. `Phase 10` Dataset governance 與 experiment management
11. `Phase 11` Evaluation credibility
12. `Phase 12` Trace intelligence
13. `Phase 13` Dataset flywheel
14. `Phase 14` Registry and run ergonomics
15. `Phase 15` Reliability sampling
16. `Phase 16` Multi-model eval governance
## Checks Before Moving To Next Phase

每完成一個 phase，至少要跑與記錄以下檢查：

- `lint`
- `typecheck`
- `unit test`
- `smoke test` 或最小手動驗證流程

若 repo 尚未有完整腳本，至少要補上對應命令或占位命令，並確保：

- 前後端可啟動
- API 與 shared schema 一致
- 本 phase 的主要資料流可以真的走通
- 本 phase 的 acceptance criteria 已逐項驗證
- 驗證方式符合 [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)

## Per-Phase Working Method

每次開始新 phase 前，先確認以下四件事：

- 這次只做哪一個 phase
- 本 phase 的 scope 是什麼
- 本 phase 的 non-goals 是什麼
- 本 phase 允許 touched files 的範圍

任務描述格式必須直接使用 [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md) 中的 task template。

每次完成 phase 後，產出至少包含：

- 實作結果
- 驗收結果
- 尚未做的內容
- 下一個 phase 的前置條件是否已滿足
- 本 phase 新增或更新的驗收產物（例如 fixture、schema snapshot、smoke script、migration、acceptance report）

若本次工作涉及 demo path，還必須確認是否符合 [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md) 中的 demo specification。

## Stop And Ask Conditions

遇到以下情況，必須停止並回報，不可自行猜測繼續：

- 需要跨 phase 修改核心 contract
- 需要變更核心 entity、status、summary 或 compare 定義
- 需要用 fake data 才能完成頁面
- 原始文件之間存在衝突
- 驗收條件無法由現有 fixture 或測試驗證
- 需要改變既定技術方向或引入新的基礎設施

## Phase-Specific Guardrails

### Phase 1

- 只做 repo 結構、skeleton、shared contract、基本文件
- 不要偷做完整 dataset upload、runner、dashboard

### Phase 2

- 專注 dataset schema、匯入、驗證、列表、預覽
- 不要過早接 evaluation runner

### Phase 3

- 優先保證 run 可以真的執行與落庫
- 不要用假 summary 或假 dashboard 取代真實執行結果

### Phase 4

- trace contract 必須完整且可追蹤單題失敗原因
- 不要只做一個有畫面但資料不完整的 viewer

### Phase 5

- 所有 dashboard 數字必須由真實 run 聚合而來
- 不可手填、硬編碼或從 fake data 生成

### Phase 6

- 重點是 compare、regression、polish、demo path
- 不要把 polish 當成任意加新功能的藉口

### Phase 7

- 只在 Phase 6 的真實 run / compare 基礎上接入真實 provider adapter
- 必須保留 deterministic stub adapter，不能讓 CI 與單元測試依賴外部 API
- 真實 provider credential 只能是平台管理設定，不得引入 BYOK
- compare 與 dashboard 仍必須基於真實持久化 run，不得用 demo 假訊號補畫面

### Phase 8

- 專注 rerun、state guard、repair utility、可重放 fixture
- 不得藉 reliability 名義改寫核心 status enum 或 compare 定義
- deterministic replay 仍然必須靠 stub / fixed fixture，不得改成機率式 smoke

### Phase 9

- 專注 scorer quality、golden set、calibration reporting
- 不得把 calibration 結果寫回既有 run 的 canonical score schema
- human-labelled golden set 是校準依據，不得用即時模型輸出反推標籤

### Phase 10

- 專注 dataset snapshot、diff、baseline pin、experiment metadata、lineage
- dataset versioning 必須保證舊 snapshot 可讀，不得以 overwrite 破壞 compare 可追溯性
- compare lineage 應補充既有 compare response，而不是破壞既有欄位語義
- 不得引入多租戶權限模型或超出單租戶前提的治理系統

### Phase 11

- 專注 scorer credibility、judge routing 與 compare 統計判讀
- 必須保留既有 canonical score / compare contract 的向後相容性，以補充欄位方式擴充
- 不得讓同一 provider 同時扮演受測 agent 與 judge 的預設路徑
- 不得以更花俏的 UI 掩蓋 scorer 本身不可信的問題

### Phase 12

- 專注 trace intelligence、step-level analysis、side-by-side trace compare
- 不得把 trace intelligence 簡化成只有額外幾個 aggregate counters
- trace regression 必須以同一 dataset item 的持久化 trace 為基礎，不得臨時拼接假資料
- 新增 trace metrics 不得覆寫既有 trace raw payload 與 summary 索引

### Phase 13

- 專注 dataset 來源擴充、review-to-regression 回流、dataset diff 與 subset execution metadata
- prompt 生成 dataset 只能作為來源之一，不得取代人工 curated dataset 與 failed-case promotion
- generated dataset 必須保留 source metadata 與人工 review 狀態，不得直接視為可信 benchmark
- 不得讓 dataset flywheel 破壞 snapshot immutability 與 lineage

### Phase 14

- 專注 registry DB 化、quick run、auto-compare、progress tracking、分頁與基本操作體驗
- 不得為了方便性而繞過既有 immutable agent version snapshot 原則
- quick run 與 auto-compare 必須仍然使用真實持久化 dataset、scorer 與 run records
- 不得把 ergonomics phase 擴張成新產品面功能集合

### Phase 15

- 專注 repeated runs、variance、consistency 與 sampling-based reliability 指標
- 不得把 repeated-run 結果混寫回單次 run 的 canonical metrics，必須保留樣本層級與聚合層級區分
- deterministic smoke 與 stub / replay fixture 必須持續存在，不得改成只能靠外部模型驗證
- 不得以 sampling 為理由修改既有核心 status enum、compare 定義或 baseline 語義

### Phase 16

- 專注 generator / agent / judge 三角色治理、provider compatibility rule、judge audit trail、calibration extension
- 多模型治理仍以平台管理 credential 為前提，不得轉向 BYOK
- judge / generator metadata 應補充既有 scorer 與 compare contract，不得破壞既有欄位語義
- 不得把此 phase 擴張成通用模型供應商 marketplace 或多租戶治理系統

## Definition Of Done

一個 phase 只有在以下條件都滿足時才算完成：

- 本 phase 的 deliverables 已落地
- acceptance criteria 全部滿足
- checks 已執行
- 沒有破壞前一 phase 的 contract
- 沒有擴張到非當前 phase 的 scope

## Source Of Truth

如有衝突，請依以下順序對齊：

1. `AGENTS.md`
2. `PROJECT_OVERVIEW.md`
3. `TECH_SPEC.md`
4. `IMPLEMENTATION_PLAN.md`
5. `TESTING.md`

這些文件共同構成 agent 的工作護欄。若實作與文件衝突，先修正理解，再動程式碼。
