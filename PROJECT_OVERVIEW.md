# PROJECT_OVERVIEW.md

## 專案是什麼

`Agent Evaluation Workbench` 是一個用來評估 AI Agent 品質的工作台。它讓團隊可以用固定資料集、結構化分數、執行 trace 與版本比較來判斷某個 agent 版本是否真的變好，而不是只靠主觀 demo 或零散人工測試。

## 解決什麼問題

AI 團隊常常可以很快做出 agent demo，但缺少一套可重複、可比較、可追查失敗原因的評估機制。常見問題包括：

- 人工測試不一致，覆蓋率低
- prompt / model / tool 調整容易引入 regression
- logs 很吵，但難以轉成產品洞察
- 團隊分不清失敗來自推理、工具選擇、缺少 context、格式錯誤還是 timeout

這個專案的價值是把 agent 開發從「玄學調參」轉成「資料化品質工程」。

## User 是誰

主要使用者：

- `AI Engineer`：驗證新版本是否改善，找出 prompt / model / tool 配置的差異
- `PM / Product Lead`：看懂品質、延遲、成本的 trade-off，做 release 決策
- `Research / Applied AI Team`：分析 failure mode，沉澱可複用知識
- `Reviewer / Analyst`：覆核低分或高風險案例，校準評分品質

## Core Workflow

1. 建立或選擇 `Agent Version`
2. 匯入或選擇 `Dataset`
3. 選擇 `Scorer`
4. 啟動 `Evaluation Run`
5. 查看 `Run Summary`
6. 檢查失敗案例與 `Trace`
7. 比較兩次 `Run` 或兩個版本的差異

這條 workflow 的目標是讓團隊可以清楚回答三個問題：

- 最新版本有沒有變好
- 主要失敗發生在哪裡
- 現在是否適合更大範圍釋出

## MVP 包含哪些功能

- 單一 agent 類型的支援
- Agent Registry 與 immutable version snapshot
- Dataset 上傳與管理，支援 `JSON` 或 `CSV`
- Dataset item 的 `input_text`、`expected_output`、`category` 等 metadata
- 批次 evaluation run，支援約 `50-100` 題
- 基本評分：`success`、`correctness / relevance`、`latency`、`cost`
- Task-level 結果保存
- Trace Viewer：顯示 steps、tool calls、輸出與錯誤
- Run Summary：success rate、category breakdown、latency、cost
- Run Compare：比較兩次 completed run
- 基本 review queue

MVP 中的 review queue 定位為：

- 收集 `review_needed = true` 或高風險案例
- 允許 reviewer 補 `verdict`、`failure_label`、`note`
- 以最小 workflow 為主，不做完整協作標註系統

## MVP 不包含哪些功能

- Multi-agent orchestration
- Production traffic monitoring
- 自動 prompt optimization 或 self-correction system
- 進階 root-cause clustering
- 完整團隊協作權限與標註流程
- 多租戶架構
- Bring-your-own-model / API key
- 完整商業化 billing

## MVP 成功標準

- 使用者可在 `10 分鐘` 內完成一次 end-to-end eval run
- 使用者能根據 summary 與 compare 判斷哪個版本更好
- 使用者能透過 trace 找到主要 failure mode
- 使用者不需要再逐題手動 ad-hoc 測試 agent

## Post-MVP 路線

在 `Phase 1-6` 完成 MVP 與 demo-ready 路徑後，後續 `Phase 7-10` 的正式延伸方向是：

- 接入真實 provider adapter，讓 compare 建立在真實 run evidence 上
- 強化 rerun、replay、state guard 與 repair utility，提升 harness 穩定性
- 用 golden set 與 calibration report 驗證 scorer quality
- 導入 dataset snapshot、baseline 與 lineage，讓 compare 結論可追溯

這些延伸 phase 的定位是 hardening 與 governance，不是擴張產品邊界。

## 一句話總結

這個專案不是要做出更酷的 agent，而是要做一個讓 agent 可以被系統化驗證、比較、追蹤與持續迭代的品質工作台。
