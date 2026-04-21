# TESTING.md

## Purpose

這份文件定義 `Agent Evaluation Workbench` 的驗證方式。目標不是追求測試數量，而是讓每個 phase 都有可重複、可執行、可回歸的驗證路徑。

每完成一個 phase，都必須先通過這份文件要求的檢查，再進入下一個 phase。

## Testing Principles

- 驗證優先於展示
- 先驗證真實資料流，再驗證 UI 呈現
- 所有 dashboard / compare 驗證都必須使用真實 run data
- 不允許用 fake data 取代核心資料流
- 每個 phase 至少要有一條最小 smoke path
- 測試失敗時，不得直接宣稱 phase 完成

## Test Framework

| 層級 | 框架 | 執行指令 |
|------|------|---------|
| 後端 lint | `ruff` | `ruff check backend/` |
| 後端 typecheck | `mypy` | `mypy backend/app` |
| 後端 unit test | `pytest` | `pytest backend/tests/` |
| 前端 lint | `eslint` | `npm run lint` |
| 前端 typecheck | `tsc` | `npm run typecheck` |
| 前端 unit test | `vitest` | `npm run test` |
| smoke test | shell script | `./scripts/smoke.sh` |

## Determinism Rules

- 所有 smoke test 必須在可重跑條件下執行，不可依賴未控制的隨機行為
- Phase 3 的 stub adapter 必須支援 deterministic mode，例如固定 `seed`、`failure_mode` 或 `failure_map`
- 若測試需要覆蓋 `partial_success`，必須使用固定失敗案例，而不是機率式失敗
- fixture 產生的 task 數、pass/fail 數、summary 指標在同一份 contract 下必須穩定可重現
- 除非文件明確允許，smoke path 不得依賴即時外部服務回應差異

### External Integration Rule

- `Phase 1-6` 的預設 smoke path 必須可在無外部 provider credential 下執行
- 若 `Phase 7` 需要驗證真實 provider adapter，必須將其標記為 integration smoke，並以環境變數顯式啟用
- integration smoke 不得取代 deterministic smoke；兩者需並存
- integration smoke 的 acceptance 應驗證「有真實輸出、資料有持久化、compare 有可觀測 signal 或可解釋的 inconclusive evidence」，不得假設外部模型一定產生固定文字

## Minimum Test Layers

每個 phase 至少要覆蓋以下四層：

### 1. Lint

目的：

- 保證基本風格與靜態品質
- 後端用 `ruff`，前端用 `eslint`

### 2. Typecheck

目的：

- 保證 shared schema、API types、UI types 一致
- 後端用 `mypy`，前端用 `tsc`

### 3. Unit Test

目的：

- 驗證資料驗證、狀態轉換、聚合邏輯、scorer 規則等純邏輯功能
- 後端用 `pytest`，前端用 `vitest`

### 4. Smoke Test

目的：

- 驗證一條最小真實路徑能走通
- 統一放在 `./scripts/smoke.sh`，可接受 phase 參數（如 `./scripts/smoke.sh phase2`）

## Required Test Categories By Phase

### Phase 1

必測：

- 前後端 skeleton 可啟動
- shared schema 可被前後端共同引用
- 基本首頁或 skeleton route 可載入

最小 smoke path：

- 啟動前後端
- 讀取健康檢查或首頁

### Phase 2

必測：

- dataset schema validation
- JSON / CSV 匯入
- row-level error handling
- dataset list / detail API

最小 smoke path：

1. 上傳合法 dataset
2. API 回傳成功
3. DB 中有 dataset 與 dataset items
4. UI preview 可看到資料

### Phase 3

必測：

- create run API
- task creation
- run status transition
- 單題失敗隔離
- result persistence

最小 smoke path：

1. 選定一個 dataset 與 agent version
2. 建立 run
3. worker 執行所有 tasks
4. run 進入 `completed` 或 `partial_success`
5. task results 可查詢

### Phase 4

必測：

- trace event recording
- trace detail API
- case detail rendering
- failure classification rendering

最小 smoke path：

1. 執行一個包含 tool call 或錯誤的 task
2. 取得 trace detail
3. UI 顯示 input_text、actual output、expected_output、trace events

### Phase 5

必測：

- summary aggregation logic
- category breakdown
- latency / cost metrics
- dashboard navigation to failed case

最小 smoke path：

1. 以真實 run data 產生 summary
2. dashboard 顯示 KPI
3. 從 dashboard 進入單題 detail

### Phase 6

必測：

- compare runs API
- improvement / regression detection
- review queue verdict flow
- compare UI
- 主要 demo path 不破

最小 smoke path：

1. 建立兩個 run
2. compare API 回傳差異
3. reviewer 可對至少一個 `review_needed` 案例留下 verdict
4. UI 顯示 improvement 與 regression

### Phase 7

必測：

- real provider adapter dispatch
- provider credential gating
- keyword-overlap scorer
- benchmark dataset coverage
- stub path regression safety

最小 smoke path：

1. 以 `stub` adapter 跑既有 deterministic smoke，確認 MVP path 未退化
2. 在明確設定 provider credential 後，執行一條 real adapter integration smoke
3. 產生兩個真實 run，保存 compare evidence
4. compare 回傳 improvement / regression，或明確標記為 inconclusive 並附持久化 evidence

### Phase 8

必測：

- rerun failed/pending tasks
- run / task state transition guard
- aggregation repair utility
- deterministic replay fixture

最小 smoke path：

1. 建立一個包含失敗 task 的 run
2. rerun 僅重跑 failed / pending tasks
3. 驗證 completed task records 未被覆寫
4. 用 replay fixture 跑兩次並比對 summary 指標一致

### Phase 9

必測：

- golden set fixture integrity
- calibration runner
- calibration report API
- calibration panel data binding

最小 smoke path：

1. 載入 human-labelled golden set
2. 執行 calibration runner
3. 取得 calibration report
4. 驗證 precision / recall / accuracy 與 confusion-style counts 可由 fixture 重算

### Phase 10

必測：

- dataset snapshot immutability
- dataset diff accuracy
- baseline pinning
- run experiment metadata persistence
- compare lineage integrity

最小 smoke path：

1. 上傳同一 dataset 的兩個版本
2. 取得 diff 並驗證 added / removed / changed item counts
3. 對其中一個 run 標記 baseline
4. compare 回傳 lineage，包含 dataset、agent version 與 scorer snapshots

## Acceptance Check Style Guide

所有 acceptance checks 都應寫成以下格式：

- `When <action>, then <observable result>`
- `Given <fixture>, API returns <status/body>`
- `After <workflow>, DB contains <records>`

範例：

- `When uploading valid dataset fixture, POST /datasets returns 201`
- `Given one failed task, run status becomes partial_success instead of hanging`
- `After summary aggregation, dashboard shows category breakdown matching fixture counts`

## Blocking Conditions

以下任一情況成立時，phase 不可視為完成：

- lint 未通過
- typecheck 未通過
- 核心 smoke path 未通過
- acceptance checks 無法由真實資料驗證
- dashboard / compare 僅靠 fake data 成立
- 核心 contract 已被改動但文件未同步

## Fixture Requirements

測試與 smoke path 必須依賴固定 fixture，而不是臨時手造資料。

所有 fixture 統一放在 `backend/tests/fixtures/`，檔名固定如下：

| 檔案 | 用途 |
|------|------|
| `dataset_valid.json` | 合法 dataset，MVP 建議 12-20 筆；若兼作 Phase 7 benchmark 可擴到 20+ 筆 |
| `dataset_invalid.json` | 非法 dataset，含格式錯誤與缺欄位 |
| `agent_version_v1.json` | agent v1 版本 snapshot |
| `agent_version_v2.json` | agent v2 版本 snapshot（用於 compare） |
| `scorer_config.json` | 基本 rule-based scorer config |
| `replay_manifest.json` | deterministic replay fixture（Phase 8） |
| `golden_set.json` | human-labelled scorer calibration fixture（Phase 9） |

至少需要：

- 一份合法 dataset fixture
- 一份非法 dataset fixture
- 一個最小 agent version fixture
- 一個 scorer config fixture
- 一組可比較的 `v1` / `v2` run fixture 或可重放配置

此外，fixture 或可重放配置必須能支援：

- 至少一個 `completed` run
- 至少一個 `partial_success` run
- 至少一個 compare baseline/candidate 組合

若進入 `Phase 7-10`，還應補充：

- 一份可供真實 provider integration 使用的 benchmark dataset
- 一份 deterministic replay manifest
- 一份 human-labelled golden set
- 至少一組 dataset snapshot diff fixture 或可重放上傳路徑

## Suggested Reporting Format

每次 phase 驗證完成後，應回報：

- Commands run
- Passed checks
- Failed checks
- Manual verification steps performed
- Known gaps

## Repository Commands

當 repo 正式建立後，需把以下命令補齊到實際專案腳本中：

- `lint`
- `typecheck`
- `test`
- `smoke`

若目前尚未存在，phase 任務中必須明確寫出對應替代指令。

## Demo Specification

這一節固定本專案的展示場景，避免後期為了 demo 臨時改動資料模型、頁面邏輯或產品敘事。

### Demo Objective

展示 `Agent Evaluation Workbench` 如何用同一份測試集評估兩個 agent 版本，找出：

- 哪個版本整體更好
- 哪些案例退步
- 問題是發生在答案品質、工具使用、格式，還是執行失敗

### Fixed Demo Scenario

MVP demo 固定使用：

- 單一 agent 類型：`tool-using QA agent`
- 單一資料集類型：客服 / FAQ / policy lookup 類問答
- 單一工具集合：
  - `document_lookup`
  - `calculator`
  - 可選 `search`

### Demo Artifacts

Demo 至少需要以下固定素材：

- `agent v1`
- `agent v2`
- 一份 sample dataset
- 一個 scorer config
- 至少一個成功 run
- 至少一個可比較 run

### Sample Dataset Requirements

建議 sample dataset 至少有 `12-20` 題；若同時承擔 `Phase 7` benchmark，建議擴到 `20+` 題，涵蓋：

- `policy_lookup`
- `calculation`
- `multi-step lookup`
- `format-sensitive`
- `failure case`

每筆資料至少包含：

- `input_text`
- `category`
- `expected_output` 或 `rubric`

建議至少刻意放入：

- 2 題會因工具選擇錯誤而失敗
- 1 題會因格式不合要求而失敗
- 1 題會因 timeout 或 tool error 而失敗

### Required Demo Flow

1. 展示 `Agent Version` 清單與 `v1` / `v2` 差異
2. 展示 dataset 預覽與 category 分布
3. 啟動 evaluation run 或展示已完成 run
4. 展示 summary dashboard
5. 打開一個失敗案例的 trace
6. 比較 `v1` 與 `v2` 的兩次 run

### Expected Comparison Story

建議固定敘事如下：

- `v2` 整體 success rate 高於 `v1`
- `v2` 在 `policy_lookup` 類別改善明顯
- `v2` 成本可能略高或 latency 略高，形成真實 trade-off
- 至少保留 1-2 個 regression cases 供 compare view 展示

### Demo Must Not Depend On

- 假資料 summary
- 手工編造 compare 結果
- 未持久化的暫存資料
- 不可重跑的臨時 agent config

### Demo Completion Criteria

當以下條件都成立時，才算 demo-ready：

- 同一份 dataset 可對 `v1` 與 `v2` 跑出兩個真實 run
- summary 與 compare 結果可重現
- 至少一個失敗案例可打開 trace detail
- 使用者可在 3-5 分鐘內走完整條 demo path
