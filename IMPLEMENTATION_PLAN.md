# IMPLEMENTATION_PLAN.md

## 計畫定位

這份文件是 `Agent Evaluation Workbench` 的執行路線圖。它把執行藍圖轉成適合 coding agent 直接落地的 Markdown 版本。

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
| P7 | 真實 OpenAI adapter 與 benchmark dataset | 將 compare 訊號建立在真實 provider run 上 | 可用真實 adapter 跑出可觀察差異 |
| P8 | Reliability 與 harness hardening | 強化 rerun、狀態守衛與可重放驗證 | 中斷後可恢復且 replay 穩定 |
| P9 | Evaluation quality 與 scorer calibration | 用 golden set 驗證 scorer 可信度 | 可量化 scorer precision / recall |
| P10 | Dataset governance 與 experiment management | 讓 compare 結論可追溯到快照與實驗設定 | dataset snapshot、lineage、baseline 可追查 |
| P11 | Evaluation credibility | 提升 scorer 與 compare 判讀的可信度 | 分數與顯著性判讀可支援 release discussion |
| P12 | Trace intelligence | 把 trace 轉成可比較、可診斷的 evidence | 能看見同題 path regression 與效率退化 |
| P13 | Dataset flywheel | 建立 dataset 持續生成、回流、分群機制 | dataset 可從多來源累積且保持 lineage |
| P14 | Registry and run ergonomics | 把日常操作成本降到可接受範圍 | registry、quick run、progress、auto-compare 可用 |
| P15 | Reliability sampling | 把 variance 與 consistency 納入評估 | repeated-run evidence 可量化穩定性 |
| P16 | Multi-model eval governance | 制度化 generator / agent / judge 關係 | 多模型評估規則與審計軌跡完整 |

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

## Phase 7: 真實 OpenAI adapter 與 benchmark dataset

### 目標

在不破壞 deterministic test harness 的前提下，接入真實 provider adapter，讓 compare 與 benchmark evidence 不再只依賴 stub world。

### Deliverables

- `OpenAIAgentAdapter`
- `adapter_type = openai` 的 dispatch path
- 平台管理的 provider credential 設定
- 與自然語言輸出相容的 `keyword_overlap` scorer
- 至少一份可用於真實 compare 的 benchmark dataset
- 真實 run evidence 與 acceptance report

### Acceptance Criteria

- 設定 provider credential 後可跑出至少一個真實 OpenAI-backed run
- compare 可對兩個不同 agent version 產生可觀測差異，或明確標記為 inconclusive
- 既有 CI / unit test 仍可在 `stub` adapter 下獨立通過
- benchmark dataset 足以支撐 category breakdown 與 compare 檢視

### Non-Goals

- 不移除 stub adapter
- 不把 CI 綁到外部 API
- 不引入 LLM-as-judge
- 不擴張成多模型 benchmark 平台

### 實作重點

- 真實 provider integration 是附加能力，不得破壞 deterministic harness
- compare 訊號必須來自持久化 task records，而不是臨時計算或人工挑選案例

## Phase 8: Reliability 與 harness hardening

### 目標

讓 run 在中斷、部分失敗與聚合不一致時仍可恢復、重跑與審計。

### Deliverables

- rerun failed / pending tasks 的服務路徑
- run / task state transition guard
- run-level aggregation repair utility
- deterministic replay fixture 與 smoke 驗證
- acceptance report

### Acceptance Criteria

- rerun 不會重跑已完成 task
- 非法狀態轉換會被拒絕且不改變既有狀態
- repair utility 可由 task records 重算 run-level counts
- replay fixture 在相同 config 下可穩定重現相同 summary 指標

### Non-Goals

- 不重寫 queue 架構
- 不新增產品面功能
- 不引入自動 prompt optimization

### 實作重點

- 核心是 recoverability 與 auditability
- 所有 reliability 機制都必須相容既有 compare / review flow

## Phase 9: Evaluation quality 與 scorer calibration

### 目標

讓 workbench 不只會打分，還能量化這套打分邏輯是否可信。

### Deliverables

- human-labelled golden set
- calibration runner
- calibration report schema 與 API
- calibration summary UI
- acceptance report

### Acceptance Criteria

- 可產出 precision、recall、accuracy 與 per-category scorer quality 指標
- golden set 同時覆蓋 pass 與 fail 案例
- calibration 指標來自真實 scorer 與標記比對，而非硬編碼
- calibration 流程不改寫既有 run score records

### Non-Goals

- 不做自動 re-score 歷史資料
- 不做多 scorer tournament
- 不以即時模型輸出取代人工標記 golden set

### 實作重點

- calibration 是品質保證層，不是另一套 production scoring pipeline
- 指標重點是可解釋與可追蹤，不是追求漂亮數字

## Phase 10: Dataset governance 與 experiment management

### 目標

補齊 dataset、baseline、compare lineage 的治理層，讓任何比較結論都可追溯到精確快照。

### Deliverables

- immutable dataset snapshots
- dataset diff API
- baseline pinning
- run experiment metadata
- compare lineage block
- acceptance report

### Acceptance Criteria

- dataset 重複上傳時會產生新 snapshot，舊 snapshot 仍可讀
- 可準確列出兩個 dataset snapshots 的 added / removed / changed items
- compare response 可指出 dataset snapshot、agent version snapshot 與 scorer snapshot
- baseline run 可在 compare 流程中被穩定辨識

### Non-Goals

- 不做自動資料集生成
- 不做多租戶治理
- 不為歷史資料強制 retroactive backfill 全部新欄位

### 實作重點

- governance 重點是 lineage 與 immutability
- 所有新增 metadata 都必須服務於 compare 可追溯性，而不是抽象平台化

## Phase 11: Evaluation credibility

### 目標

補齊 scorer 與 compare 的可信度缺口，讓分數更接近可用於 release discussion 的 evidence，而不是方向性參考。

### Deliverables

- `llm_judge` scorer
- `rubric-based` scorer
- judge compatibility rule（預設 `judge_provider != agent_provider`）
- compare statistical summary：`sample_size`、`confidence_interval`、`p_value`、`is_significant`
- compare / dashboard credibility label 與 acceptance report

### Acceptance Criteria

- judge-based scorer 可對既有 task result 產出持久化 score records
- rubric-based scorer 會實際讀取 `rubric_json`，而不是忽略欄位
- compare response 可回傳顯著性相關欄位，且可由固定 fixture 重算
- UI 可區分方向性 improvement 與 statistically significant improvement

### Non-Goals

- 不建立完整多模型 benchmark marketplace
- 不以即時 judge 輸出覆寫既有歷史 canonical score
- 不把 scorer credibility 問題簡化成只有換一個更強模型

### 實作重點

- 核心是判讀可信度，不是單純新增一種 scorer 選項
- 統計摘要必須作為 compare evidence 的補充層，而不是取代既有 task-level records

## Phase 12: Trace intelligence

### 目標

把已持久化的 trace 從 debug artifact 升級為可比較、可診斷的 regression evidence。

### Deliverables

- `efficiency_score` 與 step / tool path 衍生指標
- trace-level evaluation path
- side-by-side trace compare API 與 UI
- trace regression signals：步數增加、tool calls 增加、繞路或失敗點改變
- acceptance report

### Acceptance Criteria

- 同一 dataset item 可檢視 baseline / candidate 的並排 trace
- trace compare 可指出至少一種 path regression 或 path improvement evidence
- `efficiency_score` 可由 trace events 與 rubric / expected path metadata 穩定重算
- trace intelligence 不會覆蓋或遺失原始 trace payload

### Non-Goals

- 不把 trace intelligence 簡化成只有更多 aggregate counters
- 不把所有 trace 評估都綁死在單一 judge provider
- 不重寫既有 trace storage 架構

### 實作重點

- 重點是讓 compare 回答「哪裡變差」而不只是「有沒有變差」
- derived trace metrics 必須與 raw trace 分離保存，維持審計性

## Phase 13: Dataset flywheel

### 目標

讓 dataset 從一次性匯入清單，升級成可由多來源持續累積、回流與分群的可治理資產。

### Deliverables

- prompt-to-dataset generation path
- generated dataset review / approval flow
- failed case promote-to-dataset workflow
- dataset source metadata：`manual`、`generated`、`promoted_from_failure`
- task tags / subset run filter
- dataset diff / lineage acceptance report

### Acceptance Criteria

- 使用者可由 prompt 生成 dataset draft，且需經 review 才能成為可用 dataset
- review queue 中的 failed case 可升級為 regression case 並保留來源鏈路
- subset run 可只執行帶特定 tag 的 dataset items
- dataset snapshot 與 lineage 在 generated / promoted 流程下仍可追溯

### Non-Goals

- 不讓 generated dataset 直接取代人工 curated benchmark
- 不把 dataset generator 當成自動品質保證
- 不破壞既有 snapshot immutability 規則

### 實作重點

- dataset flywheel 的價值在於回流與累積，不在於一次生成大量題目
- 任何自動生成來源都必須帶有 source metadata 與 review 狀態

## Phase 14: Registry and run ergonomics

### 目標

降低日常操作摩擦，讓 registry、run launch、compare 與進度追蹤達到可天天使用的程度。

### Deliverables

- database-backed agent registry 與 CRUD API
- quick run workflow
- auto-compare to latest baseline
- run progress polling / progress bar
- list pagination 與基本 filter / sort
- acceptance report

### Acceptance Criteria

- 可在不改程式碼、不重啟服務的情況下新增 agent version 並啟動 eval
- quick run 會使用真實持久化 dataset 與 scorer config 建立 run
- run detail 頁可顯示 `tasks_completed / tasks_total` 等進度資訊
- runs、dataset items、review queue 在資料量增加後仍可分頁瀏覽

### Non-Goals

- 不改變 immutable agent version snapshot 原則
- 不用 fake progress 製造看似流暢的體驗
- 不把 ergonomics 當成任意加功能的理由

### 實作重點

- 這一階段重點是日常操作成本，而不是功能邊界擴張
- 所有 convenience flow 仍然必須建立在真實 run、dataset、scorer records 之上

## Phase 15: Reliability sampling

### 目標

把 repeated runs、variance 與 consistency 納入 evaluation evidence，避免單次 run 被誤解為穩定能力。

### Deliverables

- repeated-run execution support
- run-group / sample metadata
- consistency、variance、stddev summary 指標
- compare 支援 deterministic regression 與 unstable regression 的區分
- deterministic replay-compatible acceptance report

### Acceptance Criteria

- 同一組輸入可在固定 sampling config 下執行多次並保留樣本層級紀錄
- summary 可同時顯示 mean 與 variability 指標
- compare 可指出 candidate 是穩定退化還是不穩定波動
- deterministic smoke 與 replay fixture 仍可在不依賴外部模型條件下通過

### Non-Goals

- 不以 sampling 取代 deterministic smoke
- 不把 repeated-run 聚合覆寫成單次 run 的 canonical metrics
- 不修改既有核心 status enum 或 baseline 語義

### 實作重點

- 重點是「穩定性 evidence」，不是追求更昂貴的跑法
- 抽樣層與單次 run 層必須清楚分離

## Phase 16: Multi-model eval governance

### 目標

把 generator、agent、judge 三個角色制度化，建立 provider compatibility rule、審計軌跡與多模型評估治理。

### Deliverables

- scorer / evaluation config 的 generator-agent-judge 分離設定
- provider compatibility rules
- judge audit trail：prompt、model、version、reasoning metadata
- cross-judge / calibration extension report
- acceptance report

### Acceptance Criteria

- evaluation config 可清楚記錄 generator、agent、judge 的 provider 與 model
- 系統可拒絕不符合 compatibility rule 的高風險配置
- judge decision 可追溯到具體 prompt / model / version metadata
- calibration extension report 可比較不同 judge 對同一批案例的一致性

### Non-Goals

- 不導入 BYOK
- 不擴張成多租戶模型治理平台
- 不破壞既有 scorer 與 compare response 語義

### 實作重點

- 治理的核心是可審計與可解釋，不是單純多放幾個 provider 選單
- 所有新 metadata 必須服務於 evaluation credibility 與 harness repeatability

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
<Phase 1-16>

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
