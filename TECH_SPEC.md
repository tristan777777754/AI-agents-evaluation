# TECH_SPEC.md

## 技術定位

`Agent Evaluation Workbench` 是一個內部使用的評估平台，不是被測 Agent 本身。系統的技術目標是支援可重複的 evaluation、完整 trace、可比較的 run 結果，以及可擴充的資料模型與 adapter 層。

MVP 預設：

- 單租戶
- 單一 agent type
- 平台管理的 Codex / builder-authenticated configuration
- 單體應用加背景 worker，而不是微服務

Roadmap 補充：

- `Phase 1-6` 為 MVP 與 demo-ready 主線
- `Phase 7-10` 為建立在 MVP 之上的 provider integration、harness hardening、calibration、governance 延伸階段
- 後續 phase 若接入真實模型供應商，仍採平台管理 credential，不改成 BYOK

## 建議技術堆疊

- Frontend: `Next.js` / `React` + `TypeScript`
- Backend API: `FastAPI`
- Task Queue: `Celery`（固定選用）
- Database: `PostgreSQL`
- Cache / Broker: `Redis`
- Object Storage: S3-compatible storage
- ORM: `SQLAlchemy`

## System Modules

### 1. Workbench UI

責任：

- 建立 Agent Version、Dataset、Run
- 顯示 summary dashboard、task list、trace detail、compare view
- 提供 review queue 與基本操作回饋

### 2. API Service

責任：

- 提供 CRUD API
- 驗證資源存在與權限
- 啟動 run orchestration
- 回傳 summary、task、trace、compare 查詢結果

### 3. Eval Run Orchestrator

責任：

- 建立 `eval_run`
- 將 dataset items 拆成 task execution jobs
- 追蹤 run 狀態
- 在全部 task 完成後觸發 summary aggregation

### 4. Eval Worker

責任：

- 拉取 queue 任務
- 呼叫 agent adapter 執行單題
- 寫入 trace、result、score
- 處理 retry、failure isolation、partial success

### 5. Agent Adapter Layer

責任：

- 統一外部 agent 執行介面
- 避免系統直接耦合特定 framework
- 封裝 deterministic stub 與真實 provider adapter 的差異

建議介面：

```ts
runTask(inputText, config) => { result, trace }
```

#### Phase 3 Stub Adapter

Phase 3 實作 run engine 時，必須先建立一個 stub adapter 供測試使用，真實 agent 不在 Phase 3 範圍內。

stub adapter 的最小規格：

```python
class StubAgentAdapter:
    def run_task(self, input_text: str, config: dict) -> dict:
        # 固定回傳結構，模擬 agent 執行
        return {
            "final_output": f"[stub] answer for: {input_text[:50]}",
            "latency_ms": 120,
            "token_usage": {"prompt": 100, "completion": 50},
            "cost": 0.001,
            "termination_reason": "completed",
            "error": None,
            "trace_events": [
                {"step_index": 0, "event_type": "agent_start", "input": input_text},
                {"step_index": 1, "event_type": "final_output", "output": "stub answer"},
            ],
        }
```

stub adapter 必須：
- 放在 `backend/app/adapters/stub.py`
- 可被 worker 通過 `adapter_type: "stub"` 選用
- 預設必須支援 deterministic mode，用固定 `seed`、`failure_mode` 或 `failure_map` 控制失敗案例
- 允許用固定配置製造 `partial_success` 路徑，但不得讓 smoke test 依賴未控制的機率式失敗

#### Phase 7 Real Provider Adapter

Phase 7 起可在不破壞既有 deterministic harness 的前提下，新增真實 provider adapter。

最小規格：

- 放在 `backend/app/adapters/openai_adapter.py`
- 可被 worker 透過 `adapter_type: "openai"` 選用
- 使用平台管理的 `OPENAI_API_KEY`
- 回傳結構必須與 `run_task` contract 相容，不得為真實 adapter 自創另一套 payload
- CI 與預設 unit test 不得依賴此 adapter；deterministic stub path 必須持續存在

### 6. Tool Execution Layer

責任：

- 以白名單方式提供工具
- 記錄 tool call input、output、latency、status、error

MVP 可先支援：

- `search`
- `calculator`
- `document_lookup`

### 7. Trace Store

責任：

- 保存 trace 索引、摘要與大型 payload
- 支援查詢與 step-by-step 顯示

設計原則：

- 大 payload 放 object storage
- DB 只留索引與摘要欄位

### 8. Scoring Engine

責任：

- 執行 rule-based scorer
- 執行 keyword-overlap scorer
- 在需要時執行 judge-model scorer
- 輸出 structured score object
- 提供 calibration 所需的 scorer-vs-label comparison inputs

### 9. Metrics Aggregator

責任：

- 聚合 run-level summary
- 計算 category breakdown、latency、cost、top failure reasons

### 10. Review Queue

責任：

- 收集低分、judge 不確定、高風險案例
- 允許 reviewer 補 verdict、failure label、review note

### 11. Calibration Reporter

責任：

- 讀取 golden set 與 scorer 輸出
- 計算 precision、recall、accuracy 與 per-category quality metrics
- 保存 calibration summary 供首頁或 dashboard 顯示

## End-to-End Data Flow

1. 前端呼叫 `POST /runs`
2. API 驗證 `agent_version`、`dataset`、`scorer_config` 與權限
3. 建立 `eval_run`
4. 讀取 `dataset_items`，為每筆建立 `eval_task_run`
5. 將 `task_run_id` 推入 queue
6. Worker 執行單題 agent task
7. 若發生 tool call，Tool Execution Layer 寫入 tool event
8. Agent 結束後產出 final answer、latency、token usage、termination reason、error state
9. Scoring Engine 產生 score record 與 pass/fail
10. Worker 寫回結果
11. 全部 task 完成後觸發 summary aggregation
12. 前端讀取 summary、task list、trace detail、compare view

## Canonical Schema Source

- backend 的 `Pydantic` schema 與 API contract 為 canonical source
- `shared/` 中的 TypeScript types 必須由同一份 contract 對齊，不可讓 frontend 與 backend 各自演化
- 若 schema source 需要改變，必須先同步更新 `AGENTS.md`、`README.md` 與本文件

## Core Data Models

### Agent

用途：邏輯上的 agent 主體

核心欄位：

- `agent_id`
- `name`
- `description`
- `owner_id`
- `created_at`

### AgentVersion

用途：可測試、不可變的具體版本快照

核心欄位：

- `agent_version_id`
- `agent_id`
- `version_name`
- `model`
- `prompt_hash`
- `config_json`
- `created_at`

版本快照應保存：

- model name
- system prompt hash
- tool config
- temperature
- max steps
- timeout policy

### Dataset

用途：資料集主表

核心欄位：

- `dataset_id`
- `name`
- `description`
- `schema_version`
- `source_type`
- `latest_snapshot_id`

### DatasetItem

用途：資料集中的單筆測試題

核心欄位：

- `dataset_item_id`
- `dataset_id`
- `input_text`
- `category`
- `difficulty`
- `expected_output`
- `rubric_json`

每筆 item 至少要有：

- `input_text`
- `category`

可選欄位：

- `expected_output`
- `rubric_json`
- `reference_context`
- `metadata_json`

### DatasetSnapshot

用途：資料集不可變版本快照

核心欄位：

- `dataset_snapshot_id`
- `dataset_id`
- `version_number`
- `checksum`
- `created_at`

可選欄位：

- `created_by`
- `source_note`

規則：

- dataset 重複上傳時必須建立新 snapshot，而不是 overwrite 舊內容
- 舊 snapshot 必須持續可讀，以支援 compare lineage 與歷史重放

### ScorerConfig

用途：評分設定

核心欄位：

- `scorer_config_id`
- `name`
- `type`
- `weights_json`
- `judge_model`
- `thresholds_json`

### EvalRun

用途：一次批次評估

核心欄位：

- `run_id`
- `agent_version_id`
- `dataset_id`
- `scorer_config_id`
- `status`
- `started_at`
- `completed_at`
- `baseline`
- `experiment_tag`
- `notes`

建議狀態：

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`
- `partial_success`

### EvalTaskRun

用途：單題執行記錄

核心欄位：

- `task_run_id`
- `run_id`
- `dataset_item_id`
- `status`
- `final_output`
- `latency_ms`
- `token_usage`
- `cost`

### TraceSummary / Trace

用途：trace 索引與摘要

核心欄位：

- `trace_id`
- `task_run_id`
- `step_count`
- `tool_count`
- `error_flag`
- `storage_path`

可選欄位：

- `payload_checksum`
- `payload_size_bytes`
- `storage_backend`

### Score

用途：單題評分結果

核心欄位：

- `score_id`
- `task_run_id`
- `correctness`
- `tool_use`
- `format_compliance`
- `pass_fail`
- `review_needed`
- `scorer_type`

### Review

用途：人工覆核結果

核心欄位：

- `review_id`
- `task_run_id`
- `reviewer_id`
- `verdict`
- `failure_label`
- `note`

可選欄位：

- 無

### CalibrationReport

用途：scorer 校準結果報表

核心欄位：

- `calibration_report_id`
- `scorer_config_id`
- `dataset_snapshot_id`
- `precision`
- `recall`
- `accuracy`
- `created_at`

可選欄位：

- `per_category_json`
- `confusion_matrix_json`
- `notes`

## Trace / Result / Run / Dataset 結構重點

### Dataset 結構

- `Dataset` 持有 metadata
- `DatasetItem` 持有逐題輸入、分類、預期輸出與 rubric
- 必須支援 `CSV` / `JSON` 匯入
- 必須有 server-side validation、preview、錯誤列回報

### Run 結構

- 一個 `EvalRun` 對多個 `EvalTaskRun`
- run 啟動時由 dataset items 拆出 task records
- run summary 可以由 task runs 聚合或額外快取

### Result 結構

- 每個 `EvalTaskRun` 保存單題輸出、狀態、耗時、token usage、cost
- 單題失敗只標記 task failure，不中斷整個 run

### Trace 結構

每個 task run 至少應記錄：

- input_text
- start / end timestamp
- step count
- tool calls
- final output
- termination reason
- error state

建議 trace event 結構：

```json
{
  "step_index": 3,
  "event_type": "tool_call",
  "tool_name": "document_lookup",
  "input": { "query": "refund policy" },
  "output": { "snippet": "..." },
  "latency_ms": 231,
  "status": "success"
}
```

## API List

### Agent / Version

- `POST /agents`
- `GET /agents` — 列出所有 agents
- `POST /agent-versions`
- `GET /agent-versions` — 列出所有 agent versions（可篩選 agent_id）
- `GET /agent-versions/{id}`

### Dataset

- `POST /datasets`
- `GET /datasets` — 列出所有 datasets
- `GET /datasets/{id}`
- `GET /datasets/{id}/items`
- `GET /datasets/{id}/diff?from_snapshot=&to_snapshot=`

### Scorer

- `POST /scorers`
- `GET /scorers` — 列出所有 scorer configs

### Run

- `POST /runs`
- `GET /runs` — 列出所有 runs（可篩選 status、agent_version_id）
- `GET /runs/{id}`
- `GET /runs/{id}/summary` — 回傳聚合後的 run summary
- `GET /runs/{id}/tasks`
- `POST /runs/{id}/execute`
- `POST /runs/{id}/rerun`

### Task / Trace

- `GET /task-runs/{id}`
- `GET /task-runs/{id}/trace`

### Compare / Review

- `GET /compare/runs?baseline={id}&candidate={id}`
- `POST /reviews`
- `GET /reviews` — 列出待覆核案例（可篩選 review_needed=true）

### Calibration

- `GET /calibration/latest`

### `POST /runs` 範例

```json
{
  "agent_version_id": "av_001",
  "dataset_id": "ds_001",
  "scorer_config_id": "sc_001",
  "experiment_tag": "prompt-v2-benchmark",
  "notes": "Phase 10 baseline candidate run",
  "execution_config": {
    "parallelism": 4,
    "max_retries": 1,
    "timeout_seconds": 90
  }
}
```

回應：

```json
{
  "run_id": "run_20260420_001",
  "status": "pending",
  "task_count": 50,
  "created_at": "2026-04-20T10:30:00Z"
}
```

## Scoring Design

### 單題評分維度

- `Correctness`
- `Groundedness / Evidence use`
- `Tool-use quality`
- `Format compliance`
- `Latency / cost`

### 評分器類型

- `Rule-based`
- `Keyword overlap`
- `Judge model`
- `Human review`

### Score Object 建議

```json
{
  "correctness": 0.84,
  "tool_use": 1.0,
  "format_compliance": 0.0,
  "overall_score": 0.72,
  "pass_fail": false,
  "review_needed": true,
  "judge_reason": "Answer is relevant but violates required JSON schema."
}
```

## Non-Functional Requirements

- 單題失敗不應導致整個 run 崩潰
- 支援 partial success
- 50-100 題應可在合理時間內完成
- 所有 run 都要有 summary 與 task-level trace
- adapter interface 必須模組化
- 資料模型必須可擴充 scorer、tool、agent type
- 目標是 10 分鐘內完成一次 run 的建立與查看
- summary 與 compare 的結論必須可追溯到真實 run evidence

## Security And Access Control

- MVP 可用簡單 `session` 或 `JWT`
- 至少區分 `viewer`、`editor`、`admin`
- `editor` 以上才可建立 run 與上傳 dataset
- 外部工具必須白名單化，禁止任意 shell command
- secrets 應存放於 environment variables 或 secrets manager
- trace 與 dataset 若含敏感資訊，需控制下載與審計

## Error Handling And Recovery

### 失敗類型

- `Input validation failure`
- `Adapter failure`
- `Tool failure`
- `Scoring failure`
- `Persistence failure`

### 處理策略

- 單題隔離
- 對 transient error 做有限次 retry
- judge model 失敗時允許降級到 rule-based 結果並標記 `review_needed`
- 前端需透明顯示 `failed`、`partial`、`retrying`

## Phase-By-Phase Implementation Notes

### Phase 1

- 先落地 repo 結構、shared schema、基本文件
- 確保後續 phase 不必大改 core contract

### Phase 2

- 完成 dataset schema、匯入、驗證、preview
- 這是所有後續 phase 的基礎

### Phase 3

- 完成 run API、queue、worker、單題結果落庫
- 核心要求是 evaluation 真的跑得起來

### Phase 4

- 完成 trace schema、trace logging、case detail UI
- 核心要求是能定位失敗原因

### Phase 5

- 完成 summary aggregation 與 dashboard
- 所有 metrics 必須由真實 run 計算

### Phase 6

- 完成 run compare、regression view、demo polish
- 重點是說服力與展示品質，不是功能擴張

### Phase 7

- 接入真實 provider adapter 與 benchmark dataset
- compare 必須開始支援真實 provider evidence，但 deterministic stub 仍是預設測試基礎

### Phase 8

- 補齊 rerun、state guard、repair utility、replay fixture
- 核心是 recoverability 與 state consistency

### Phase 9

- 補齊 golden set、calibration runner、calibration report
- 核心是 scorer quality visibility，而不是取代既有 scoring pipeline

### Phase 10

- 補齊 dataset snapshot、diff、baseline pinning、experiment metadata、compare lineage
- 核心是 reproducibility 與 governance

## MVP 邊界

MVP 要做：

- 單一 agent type adapter
- Dataset JSON/CSV 匯入
- Agent Version 建立
- 基本 scorer config
- 批次 run 與 queue
- 單題 trace viewer
- summary dashboard
- run comparison
- 基本 review queue

MVP 不做：

- 多 agent 編排
- production traffic monitoring
- 自動 prompt optimization
- synthetic dataset generation
- 複雜工作空間 / 多租戶
- 完整 A/B testing 平台

Post-MVP `Phase 7-10` 可做：

- 真實 provider adapter integration
- harness hardening 與 replay
- scorer calibration
- dataset governance 與 lineage

## Implementation Contracts

這一節定義實作層面的硬規格。若實作與本節衝突，應先修正文檔或回報衝突，不應自行偏離。

### Domain Entities

#### Agent

Required fields：

- `agent_id: string`
- `name: string`
- `created_at: datetime`

Optional fields：

- `description: string`
- `owner_id: string`

Rules：

- `agent_id` 必須唯一
- `name` 不可為空

#### AgentVersion

Required fields：

- `agent_version_id: string`
- `agent_id: string`
- `version_name: string`
- `model: string`
- `config_json: object`
- `created_at: datetime`

Optional fields：

- `prompt_hash: string`
- `notes: string`

Rules：

- `agent_version_id` 必須唯一
- 建立後不可被原地覆寫
- run 必須綁定到明確的 `agent_version_id`

#### Dataset

Required fields：

- `dataset_id: string`
- `name: string`
- `schema_version: string`
- `source_type: enum(json, csv)`

Optional fields：

- `description: string`
- `created_at: datetime`
- `latest_snapshot_id: string`

#### DatasetItem

Required fields：

- `dataset_item_id: string`
- `dataset_id: string`
- `input_text: string`
- `category: string`

Optional fields：

- `difficulty: string`
- `expected_output: string`
- `rubric_json: object`
- `reference_context: object|string`
- `metadata_json: object`

Rules：

- 每筆 item 必須至少有 `input_text` 與 `category`
- 匯入失敗必須回傳 row-level errors

#### DatasetSnapshot

Required fields：

- `dataset_snapshot_id: string`
- `dataset_id: string`
- `version_number: string|number`
- `checksum: string`
- `created_at: datetime`

Optional fields：

- `created_by: string`
- `source_note: string`

Rules：

- dataset 重複上傳時必須建立新 snapshot，而不是 overwrite 舊內容
- 舊 snapshot 必須持續可讀，以支援 compare lineage 與歷史重放

#### ScorerConfig

Required fields：

- `scorer_config_id: string`
- `name: string`
- `type: enum(rule_based, keyword_overlap, judge_model, hybrid)`

Optional fields：

- `weights_json: object`
- `judge_model: string`
- `thresholds_json: object`

#### EvalRun

Required fields：

- `run_id: string`
- `agent_version_id: string`
- `dataset_id: string`
- `scorer_config_id: string`
- `status: RunStatus`
- `created_at: datetime`

Optional fields：

- `started_at: datetime`
- `completed_at: datetime`
- `execution_config_json: object`
- `dataset_snapshot_id: string`
- `dataset_checksum: string`
- `scorer_snapshot_json: object`
- `adapter_type: string`
- `adapter_version: string`
- `tool_config_snapshot_json: object`
- `git_commit_sha: string`
- `execution_seed: string|number`
- `runtime_metadata_json: object`
- `baseline: boolean`
- `experiment_tag: string`
- `notes: string`

#### EvalTaskRun

Required fields：

- `task_run_id: string`
- `run_id: string`
- `dataset_item_id: string`
- `status: TaskStatus`

Optional fields：

- `final_output: string|object`
- `latency_ms: number`
- `token_usage: object`
- `cost: number`
- `termination_reason: string`
- `error_code: string`
- `error_message: string`
- `attempt_count: number`
- `retry_count: number`
- `failure_type: string`
- `worker_id: string`
- `started_at: datetime`
- `completed_at: datetime`

#### TraceSummary

Required fields：

- `trace_id: string`
- `task_run_id: string`
- `step_count: number`
- `tool_count: number`
- `error_flag: boolean`
- `storage_path: string`
- `created_at: datetime`

#### Score

Required fields：

- `score_id: string`
- `task_run_id: string`
- `pass_fail: boolean`
- `overall_score: number`
- `created_at: datetime`

Optional fields：

- `correctness: number`
- `tool_use: number`
- `format_compliance: number`
- `review_needed: boolean`
- `judge_reason: string`
- `scorer_type: string`

#### Review

Required fields：

- `review_id: string`
- `task_run_id: string`
- `verdict: string`
- `created_at: datetime`

Optional fields：

- `reviewer_id: string`
- `failure_label: string`
- `note: string`

#### CalibrationReport

Required fields：

- `calibration_report_id: string`
- `scorer_config_id: string`
- `dataset_snapshot_id: string`
- `precision: number`
- `recall: number`
- `accuracy: number`
- `created_at: datetime`

Optional fields：

- `per_category_json: object`
- `confusion_matrix_json: object`
- `notes: string`

### Status Contracts

#### RunStatus

允許值：

- `pending`
- `running`
- `completed`
- `failed`
- `cancelled`
- `partial_success`

狀態規則：

- `pending -> running`
- `running -> completed`
- `running -> partial_success`
- `running -> failed`
- `running -> cancelled`

限制：

- `completed`、`failed`、`cancelled`、`partial_success` 為終態
- 只要存在至少一個成功 task 且至少一個失敗 task，run 應標記為 `partial_success`
- run 一旦進入終態，不可再回到 `running`

#### TaskStatus

允許值：

- `pending`
- `running`
- `completed`
- `failed`
- `skipped`

規則：

- `pending -> running`
- `running -> completed`
- `running -> failed`
- `running -> skipped`
- 單題失敗不得使整個 run 停滯
- task 必須在終態時具備可查詢結果或錯誤資訊

### Reproducibility Contract

每個 `eval_run` 必須保留足夠資訊，讓同一批輸入可被重新執行並與歷史結果比較。最小要求如下：

- `agent_version_id` 必須對應 immutable snapshot
- `dataset_id` 之外，必須保存 `dataset_snapshot_id` 或 `dataset_checksum`
- 必須保存 scorer 當下使用的 snapshot，而不是只保存可變名稱
- 必須保存 `adapter_type`、`adapter_version`
- 必須保存工具白名單與工具設定 snapshot
- 必須保存 `execution_seed` 或等價 deterministic config
- 必須保存 `git_commit_sha` 與必要 runtime metadata

若缺少上述資訊，該 run 不應被視為 fully reproducible。

### Trace Contract

每個 task run 至少要能追溯以下資訊：

- input_text
- start time
- end time
- final output
- termination reason
- error state

`event_type` 至少支援：

- `agent_start`
- `model_output`
- `tool_call`
- `tool_result`
- `error`
- `final_output`

### Scoring Contract

#### Score Range

- 所有分項分數範圍固定為 `0.0 - 1.0`
- `overall_score` 範圍固定為 `0.0 - 1.0`

#### Minimum Dimensions

- `correctness`
- `tool_use`
- `format_compliance`

#### Pass / Fail Rule

MVP 預設規則：

- 若 `overall_score >= threshold` 且沒有 blocking format error，則 `pass_fail = true`
- 若輸出格式不符合 required schema，可直接 `pass_fail = false`
- 若 judge model 失敗但 rule-based 可計算，仍可產出部分分數並標記 `review_needed = true`

MVP default threshold：

- `threshold = 0.7`

實作時不得在未更新文件時任意變更。

#### Keyword Overlap Rule

在 `Phase 7` 導入的 `keyword_overlap` scorer 用於自然語言輸出的最小可用評分：

- 以 `expected_output` 中的關鍵詞或關鍵片語為比對基礎
- 比對必須大小寫不敏感
- scorer 必須可在無 judge model 的情況下執行
- 此 scorer 是 `rule_based` 之外的新 path，不得覆寫既有 canonical score 欄位語義

#### Calibration Rule

在 `Phase 9`，calibration 應比較 scorer 輸出與 human-labelled golden set：

- calibration 結果是獨立報表，不得回寫覆蓋既有 run score
- golden set 的 label source 必須可追溯
- precision / recall / accuracy 與 per-category breakdown 必須可由原始 comparison records 重算

### Summary Contract

每個 run summary 至少包含：

- `run_id`
- `total_tasks`
- `completed_tasks`
- `failed_tasks`
- `pass_rate`
- `average_latency_ms`
- `average_cost`
- `category_breakdown`

`pass_rate` 定義：

- `pass_count / total_scored_tasks`

`average_latency_ms` 定義：

- `sum(latency_ms for terminal task runs with measured latency) / task_count_with_latency`

`average_cost` 定義：

- `sum(cost for terminal task runs with measured cost) / task_count_with_cost`

`failed_tasks` 定義：

- `task status = failed` 的 task 數量

`completed_tasks` 定義：

- `task status = completed` 的 task 數量

`total_tasks` 定義：

- 建立 run 時拆出的全部 `eval_task_run` 數量

`category_breakdown` 至少包含：

- `category`
- `task_count`
- `pass_rate`
- `average_latency_ms`

所有 summary 指標都必須由同一個 run 的真實 `eval_task_run` 與 `score` 聚合，不可由假資料、手填值或未持久化的暫存結果生成。

### Compare Contract

compare runs 至少需要：

- `baseline_run_id`
- `candidate_run_id`
- `pass_rate_delta`
- `latency_delta`
- `cost_delta`
- `category_deltas`
- `improved_cases`
- `regressed_cases`
- `lineage`

`regressed_case` 定義：

- baseline 為 pass，candidate 為 fail
- 或 candidate `overall_score` 低於 baseline 至少 `0.2`
- 同一 `dataset_item_id` 才可進入 compare pairing

`improved_case` 定義：

- baseline 為 fail，candidate 為 pass
- 或 candidate `overall_score` 高於 baseline 至少 `0.2`
- 同一 `dataset_item_id` 才可進入 compare pairing

若 baseline 與 candidate 使用的 `dataset_id` 不同，系統必須拒絕 compare 或明確標記為 non-comparable。

`lineage` 至少應包含：

- baseline / candidate 各自的 `dataset_snapshot_id`
- baseline / candidate 各自的 `agent_version_id` 或 snapshot hash
- baseline / candidate 各自的 `scorer_config_id` 或 scorer snapshot reference

### API Contract Minimums

#### Error Envelope

所有非 `2xx` API 回應至少應包含：

- `error_code`
- `message`
- `details`
- `request_id`

#### POST /datasets

成功：

- `201 Created`

失敗：

- `400 Bad Request` 用於 schema / row validation failure

成功回應至少包含：

- `dataset_id`
- `name`
- `source_type`
- `item_count`
- `created_at`

失敗回應至少包含：

- `error_code`
- `message`
- `details`
- `request_id`
- `row_errors`

#### POST /runs

成功：

- `201 Created`
- 回傳 `run_id`、`status`、`task_count`

失敗：

- `400` 無效輸入
- `404` 找不到 agent version / dataset / scorer

#### GET /runs/{id}

必須回傳：

- run metadata
- current status
- summary fields if available

若 summary 已完成，至少包含：

- `total_tasks`
- `completed_tasks`
- `failed_tasks`
- `pass_rate`
- `average_latency_ms`
- `average_cost`

#### GET /task-runs/{id}/trace

必須回傳：

- task metadata
- trace summary
- ordered trace events

其中 task metadata 至少包含：

- `task_run_id`
- `run_id`
- `dataset_item_id`
- `status`
- `final_output`
- `termination_reason`
- `error_code`
- `error_message`

### File And Schema Change Policy

以下變更屬於 contract-level change，必須先更新文件再實作：

- entity renamed
- status renamed or added
- scoring rule changed
- summary metric definition changed
- compare diff definition changed
- API response field removed or repurposed

## Local Development Setup

本地開發使用 `docker-compose` 啟動基礎設施，不依賴外部服務：

```yaml
# docker-compose.yml 最小配置
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: eval_workbench
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

啟動指令：`docker-compose up -d`

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

每個 phase 完成後必須全部通過，才可進入下一個 phase。

## 一句話總結

這份規格的技術核心不是「怎麼做一個會回答的 agent」，而是「怎麼做一個能穩定驗證 agent 品質的工程系統」。
