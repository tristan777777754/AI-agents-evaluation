# IMPLEMENTATION_PLAN.md

## 計畫定位

這份文件是 `Agent Evaluation Workbench` 的執行路線圖。它把原本的六階段執行藍圖轉成適合 coding agent 直接落地的 Markdown 版本。

搭配文件：

- [README.md](/Users/tristan/AI-agents-evaluation/README.md)
- [AGENTS.md](/Users/tristan/AI-agents-evaluation/AGENTS.md)
- [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)
- [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)
- [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md)

執行原則：

- 嚴格按照 phase 順序執行
- 一次只做一個 phase
- 每個 phase 完成後，先驗證與回歸，再進下一個 phase
- 任何 dashboard 或 compare 功能都不得建立在 fake data 之上

## 總覽

| Phase | 名稱 | 主要目標 | 完成判定 |
| --- | --- | --- | --- |
| P1 | 專案骨架與規格落地 | 建立 repo 結構與 shared contract | 專案可啟動且文件齊全 |
| P2 | Dataset 管理流程 | 完成 dataset schema、匯入、驗證、列表 | 能成功上傳並讀取測試集 |
| P3 | Evaluation Run 引擎 | 建立 run 建立、任務執行、狀態更新 | 可批量執行測試題 |
| P4 | Trace 與單題檢視 | 完整記錄單題執行軌跡 | 可定位單題失敗原因 |
| P5 | Summary Dashboard | 呈現成功率、延遲、成本與分類表現 | 可從總覽判斷表現優劣 |
| P6 | 版本比較與 polish | 比較兩次 run，補齊 demo 細節 | 能展示前後版本差異 |

## Phase 1: 專案骨架與規格落地

### 目標

建立可持續開發的基礎結構，避免 agent 在沒有護欄的情況下亂長。

### Deliverables

- 前端、後端、shared types、docs 的目錄結構
- dataset、eval run、eval task run、trace 的 shared schema
- `README.md`、`AGENTS.md`、開發命令與驗收方式
- 基本首頁或 skeleton 頁面
- 最低限度的 CI / lint / typecheck 指令
- 最小 harness artifacts：schema contract、fixture 目錄、smoke script 入口、phase acceptance report 模板

### Acceptance Criteria

- clone 後可在本地成功啟動
- 關鍵資料結構已有明確定義
- 後續 phase 不需再大改資料契約
- repo 已具備可持續演進的基礎骨架

### Non-Goals

- 不做完整 dataset upload
- 不做完整 evaluation runner
- 不做 dashboard、compare、trace viewer 的完整功能

### 實作重點

- 這一階段只做結構與 contract
- 不准偷做後面 phase 的主要功能

## Phase 2: Dataset 管理流程

### 目標

完成測試題庫的最小閉環，讓平台可以接收、驗證並展示 dataset。

### Deliverables

- dataset 與 `dataset_item` 資料表
- dataset `JSON / CSV` schema
- upload API
- list / detail API
- dataset preview 頁面
- 欄位驗證與錯誤提示

### Acceptance Criteria

- 能上傳一份有效 dataset
- 無效格式會被清楚拒絕
- 使用者可在 UI 看見每筆測試題
- dataset 與 dataset items 可正確持久化

### Non-Goals

- 不碰 evaluation runner
- 不做 run engine
- 不做 fake summary 頁面

### 實作重點

- 專注資料模型與驗證流程
- Dataset 是後面所有 phase 的地基

## Phase 3: Evaluation Run 引擎

### 目標

建立真正可運行的 evaluation 流程，能逐題執行並記錄結果。

### Deliverables

- `eval_run`、`eval_task_run` 或對應的實體 / 資料表
- create run API
- run 查詢 API
- executor / runner
- run progress UI 或狀態顯示
- 每題輸出、耗時、基礎分數落庫

### Acceptance Criteria

- 可對一份 dataset 成功跑完整批測試
- 每題結果都能持久化保存
- 單題失敗不會讓整個 run 無法回收狀態
- run 狀態至少支援 `pending`、`running`、`completed`、`failed`

### Non-Goals

- 不先做漂亮 dashboard
- 不以 mock data 假裝 run 完成

### 實作重點

- 先保證 evaluation 真的跑得起來
- 真實執行比畫面完整更重要

## Phase 4: Trace 與單題檢視

### 目標

讓系統不只知道結果好壞，還能知道為什麼好或為什麼壞。

### Deliverables

- trace schema
- trace logging
- trace detail API
- case detail / trace viewer UI
- input_text / expected_output / actual output / trace 顯示頁
- 錯誤原因顯示區

### Acceptance Criteria

- 至少能看見單題完整執行脈絡
- 能區分回答錯誤、工具錯誤、格式錯誤與執行失敗
- 開發者可依 trace 定位問題
- trace contract 與底層資料一致

### Non-Goals

- 不只做有畫面但資料不完整的 viewer
- 不把 trace 簡化成只有最終輸出

### 實作重點

- 這一階段是整個專案的靈魂
- trace 必須足以支撐 debug 與 root-cause 分析

## Phase 5: Summary Dashboard

### 目標

把一堆 run result 轉成可判斷品質的管理視角。

### Deliverables

- summary metrics 聚合邏輯
- summary API
- dashboard UI
- category breakdown 卡片或表格
- 最近 runs 清單
- 從 dashboard 進入失敗案例的導航

### Acceptance Criteria

- 使用者能在總覽頁快速看懂這版 agent 的表現
- metrics 與底層結果一致
- 能從 dashboard 進入 trace 細節頁
- 關鍵 KPI 至少包含 success rate、latency、cost、category breakdown

### Non-Goals

- 不手填數字
- 不依賴 fake data
- 不做複雜 BI 平台化能力

### 實作重點

- 所有數字都必須由真實 run 聚合
- 這一階段才開始重視展示感

## Phase 6: 版本比較與產品 Polish

### 目標

讓專案從可用工具升級成可 demo、可說服他人的作品。

### Deliverables

- compare runs 邏輯
- compare API
- compare UI
- improvement / regression case 清單
- 基本 review queue workflow 與 reviewer verdict 流程
- UX polish：空狀態、錯誤提示、loading
- demo data、展示說明、部署說明
- E2E smoke test

### Acceptance Criteria

- 能清楚回答 `v2` 是否比 `v1` 更好
- 使用者可看見 regression 與 improvement
- reviewer 可對需要人工覆核的案例留下 verdict 與 note
- UI 在主要路徑上不再粗糙或破碎
- 整體專案足以作為 portfolio 展示

### Non-Goals

- 不任意擴張功能
- polish 不等於加新系統

### 實作重點

- 這一階段是收斂，不是擴張
- 所有 polish 都要服務於 demo 與可理解性

## 建議的 Agent 工作方式

每個 phase 都應建立獨立任務文件，至少包含：

- Scope
- Non-goals
- Files to touch
- Acceptance criteria

任務文件格式應直接採用 [TASK_TEMPLATE.md](/Users/tristan/AI-agents-evaluation/TASK_TEMPLATE.md)。

每個 phase 完成後都要先跑：

- `lint`
- `typecheck`
- `unit test`
- `smoke test`

驗證方式應對齊 [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)，再進入下一個 phase。

每個 phase 結束時，至少要留下一個可重用的 harness artifact，例如：

- 固定 fixture
- smoke script
- schema snapshot
- migration
- acceptance report

## Task Template

所有 phase 任務都應使用以下固定格式，避免 scope 漂移、假完成與跨 phase 偷做功能。

### Required Task Format

每次任務至少要包含以下欄位：

1. `Task Name`
2. `Current Phase`
3. `Goal`
4. `In Scope`
5. `Out of Scope`
6. `Files Allowed To Touch`
7. `Files Forbidden To Touch`
8. `Inputs / Dependencies`
9. `Required Output Artifacts`
10. `Commands To Run`
11. `Acceptance Checks`
12. `Contract Checks`
13. `Evidence To Attach`
14. `Rollback / Recovery Notes`
15. `Stop And Ask Conditions`
16. `Completion Report`

### Acceptance Check Style

好的寫法：

- `POST /datasets` 上傳合法 JSON 時回傳 `201`
- dataset detail API 回傳 item 數量與 fixture 相同
- preview page 能顯示 category、input_text、expected_output 三欄

不好的寫法：

- 能成功上傳
- 看起來正常
- UI 完成

### Stop And Ask Conditions

以下情況必須停止並回報，不可自行猜測：

- 需要跨 phase 改動核心 contract
- 需要重命名核心 domain entity 或 API
- 原始文件與現有實作衝突
- 驗收條件無法由現有 fixture 或測試驗證
- 必須引入新的基礎設施或技術方向
- 需要用 fake data 才能把頁面做出來

### Copy-Paste Template

```md
# Task: <task name>

## Current Phase
<Phase 1-6>

## Goal
<one clear outcome>

## In Scope
- ...
- ...

## Out of Scope
- ...
- ...

## Files Allowed To Touch
- ...
- ...

## Files Forbidden To Touch
- ...
- ...

## Inputs / Dependencies
- ...
- ...

## Required Output Artifacts
- ...
- ...

## Commands To Run
- ...
- ...

## Acceptance Checks
- ...
- ...

## Contract Checks
- ...
- ...

## Evidence To Attach
- ...
- ...

## Rollback / Recovery Notes
- ...
- ...

## Stop And Ask Conditions
- ...
- ...

## Completion Report
- Implementation result:
- Acceptance result:
- Remaining work:
- Next phase prerequisite status:
```

## 風險與控制方式

| 風險 | 表現方式 | 控制方法 |
| --- | --- | --- |
| Scope 爆掉 | 一開始就想做多租戶、BYO API、多模型 | MVP 僅做單模型、單人路徑、單一核心流程 |
| 假完成 | 前端看起來完整，但底層只是 mock data | 每個頁面都要追溯到真實資料來源與真實 API |
| Agent drift | API 命名、資料欄位、頁面邏輯前後不一致 | 每個 phase 固定 contract，禁止 agent 自作主張改 schema |
| Debug 困難 | run 失敗後不知道壞在哪 | 強制在 P4 完成 trace 與錯誤分類 |

## 最後結論

這個專案適合用 phase-driven 的 harness engineering 方式落地，不適合靠一個大 prompt 一次做完。只要按這六個 phase 推進，並在每一階段嚴格驗收，整體難度是可控的，而且非常適合做成 AI engineer portfolio。
