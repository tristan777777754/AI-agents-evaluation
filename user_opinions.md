# AI Evaluation Workbench — Senior AI Engineer Review

> Reviewed on 2026-04-21

---

## 核心問題（根本上有缺陷）

### 1. Scorer 根本沒有能力評估 LLM 的真實輸出

現在只有兩個 scorer：
- `rule_based` — 完全基於 adapter 回來的 termination reason，等於 agent 自己評分自己，毫無意義
- `keyword_overlap` — 比對關鍵字，但 LLM 輸出語義相同、字詞不同就會 fail

這兩個都不是真正的 AI 評估。你要比較的是「agent 有沒有變好」，但評估標準本身就很弱，結果是：**即使 agent 真的變好了，你也量不出來。**

**應該加的：**
- **LLM-as-judge scorer** — 用 Claude/GPT 給出 0-1 的 correctness 分數，加 reasoning
- **Embedding similarity scorer** — cosine similarity 比對 expected vs actual output
- **Rubric-based scorer** — dataset 裡有 `rubric_json` 欄位但根本沒用到

---

### 2. Registry 是 hardcoded fixtures，不能 runtime 新增 agent

`backend/app/services/registry.py` 用 `@lru_cache` 從 JSON 讀固定的 agent versions。想測一個新的 prompt version 要改程式碼然後重啟 server。

這根本違背 evaluation workbench 的核心用途。你應該能隨時 register 一個新的 agent version（URL、model、prompt、config），然後馬上跑 eval。

**應該做的：** Agent registry 存進 database，提供 `POST /api/v1/registry/agents` CRUD API。

---

### 3. 沒有 statistical significance，數字沒有意義

Compare 頁面顯示 success rate delta（例如 +3.2%），但完全沒有：
- 樣本數是否足夠的判斷
- Confidence interval
- p-value 或 bootstrap test

一個 100 題的 dataset 從 72% 到 75%，根本不能說「變好了」。這是現在最大的知識性缺陷。

**應該加的：** Compare endpoint 回傳 `is_significant: bool`、`p_value: float`、`confidence_interval: [low, high]`（用 scipy 兩行就能算）。

---

## 如何正確評估 Agent Ability

### 「丟題目看答案」只測到最淺的一層

Agent ability 有四個層次：

```
Layer 4: 能不能在新情境 generalize？       ← 泛化能力
Layer 3: 過程對不對（即使答案對）？        ← 推理品質
Layer 2: 答案對不對？                      ← 結果正確性
Layer 1: 有沒有完成任務？                  ← 任務完成率
```

現在這個 project 只量到 Layer 1，偶爾碰到 Layer 2。

### 正確的評估需要三個維度

**維度一：Trajectory Evaluation（過程評估）**

不只看最終答案，要看 agent 的每一步。同樣答對了同一題，Agent A 用 2 步完成，Agent B 用 10 步完成，B 比 A 差但現在的系統兩個都給 pass。

要量的指標：
- 最少步數完成任務比（optimal path ratio）：`efficiency_score = optimal_steps / actual_steps`
- 多餘 tool call 次數
- 有沒有做不必要的迴圈

**維度二：Behavioral Consistency（行為一致性）**

同樣的問題問三次，agent 應該給出一致的答案。LLM 的 variance 很高，所以：
- 一個問題要跑 3-5 次取平均
- 量 standard deviation，不只量 mean
- **現在每個 input 只跑一次，統計上根本不可信**

**維度三：Distribution Coverage（測試分佈）**

好的 dataset 要有：

| 類型 | 用途 |
|------|------|
| Happy path cases | 量基本能力 |
| Edge cases | 量處理邊界的能力 |
| Adversarial inputs | 量被誤導的機率 |
| Ambiguous inputs | 量 agent 如何問回去 |
| Long-horizon tasks | 量多步推理能力 |
| Out-of-distribution | 量 generalization |

只有 happy path 的 dataset，讓 agent 從 70% 升到 90% 沒有意義。

---

## Trace 資料有但沒有用到

系統已經記錄了每一個 step 的 trace，但 `runs.py` 對 trace 只做三件事：

```python
step_count = len(trace_events)
tool_calls_count = sum(1 for e in trace_events if e.get("type") == "tool_call")
failure_reason = _classify_failure(trace_events)  # 只是 if-else 判斷有沒有壞
```

Trace 進來了，但每一步的內容完全沒被評估。應該要做的：

1. **每一步的品質評分** — 用 LLM-as-judge 看每個決策點是否合理
2. **Optimal path analysis** — `rubric_json["max_steps"]` 欄位已經有了，`efficiency_score = optimal_steps / actual_steps` 兩行就能算
3. **Trace-level regression detection** — 兩個 run 的同一個 task，baseline 用 2 步答對，candidate 用 4 步答對，這是 regression，現在完全看不出來

---

## Dataset 問題：不應該要自己手動定義題目

### Dataset 應該從三個來源來

**來源一：Production logs（最有價值）**

真實 user 的 query 是最好的 dataset。現在這個 project 沒有任何 log ingestion 功能。

**來源二：LLM 自動生成 test cases**

貼入 agent system prompt → LLM 幫你生成 dataset（含 input + expected behavior + rubric）。

應該有 `POST /api/v1/datasets/generate` endpoint，生成 prompt 範例：
```
你是一個 QA engineer，為以下 AI agent 設計評估測試案例。
Agent System Prompt: {user_pasted_prompt}
請生成 {N} 個測試案例：
- 40% happy path、40% edge case、20% adversarial
格式：{ input_text, category, expected_behavior, rubric: { must_do, must_not_do, max_steps } }
```

**來源三：從失敗案例反向建立**

Review queue 裡的 failed case 應該有「一鍵加入 dataset」按鈕，變成 regression test。現在這個按鈕不存在。

### 正確的 Dataset 生成流程

```
Step 1: 貼入 agent system prompt
Step 2: 選生成參數（數量、難度分佈、類型分佈）
Step 3: LLM 生成 dataset
Step 4: 人工 review 生成的題目（不能跳過，垃圾進垃圾出）
Step 5: Approve → 變成可用 dataset
```

---

## Multi-Model 評估架構（Self-Evaluation Bias 問題）

### 新開 context window 不夠

用同一個 LLM 出題和答題，即使開新的 context window，model weights 沒變。它傾向出自己擅長的題型，它的知識盲點和 agent 的盲點高度重疊。這叫做 **self-evaluation bias**，是 LLM eval 最有名的陷阱。

### 正確架構：三個角色用不同模型

```
出題者（Generator）  →  受測 Agent  →  裁判（Judge）
     OpenAI               Claude           OpenAI
```

**核心規則：受測者跟裁判不能是同一家。**

裁判盡量不要跟受測者同一家——OpenAI 的模型不適合當 OpenAI agent 的裁判，Claude 當裁判更客觀，反之亦然。

### 只有 Claude 和 OpenAI 的情況下

```
OpenAI 出題  →  Claude 答題  →  OpenAI 當裁判
```
或：
```
Claude 出題  →  OpenAI 答題  →  Claude 當裁判
```

出題者是誰比較不重要，重要的是**答題跟裁判不能同一家**。

### Scorer config 應該加的設定

```json
{
  "scorer_type": "llm_judge",
  "judge_model": "claude-sonnet-4-6",
  "generator_model": "gpt-4.1",
  "agent_model": "你的 agent"
}
```

現在這三個角色全部 hardcoded 或根本不存在，這個設定頁面應該要有。

---

## 嚴重不方便（每天用都會痛）

### 4. 跑一次 eval 要手動做太多步驟

現在的流程：
1. 上傳 dataset → 拿 dataset_id
2. 去 registry 找 agent_version_id 和 scorer_config_id
3. 手動填這三個 ID 到 RunLauncherForm
4. 等跑完
5. 去 summary 看
6. 再去 compare 選兩個 run 比

**應該有的：**
- **Quick Run** — 選「agent version」就能直接跑，自動用最新 dataset + 預設 scorer
- **Auto-compare** — 跑完後自動跟上一個同 agent 的 baseline run 比，不需要手動選

---

### 5. 沒有 run-level progress tracking

`execute_run` 是 Celery task，但 frontend 沒有 WebSocket 或 polling 顯示進度。你只能刷新頁面猜有沒有跑完。

**應該加的：** Run 頁面自動 poll `/api/v1/runs/{id}`，顯示 `tasks_completed / tasks_total` 進度條。

---

### 6. Failure classification 太粗糙

`_classify_failure()` 只有四個類別：`tool_error`, `format_error`, `answer_incorrect`, `execution_failed`。真實的 agent failure 會有幾十種模式（幻覺、截斷、context lost、工具呼叫順序錯誤...）。classification 邏輯在 `runs.py` 第 303–327 行，是一堆 if-else，加新類別很容易出錯。

---

### 7. 前端沒有分頁，資料一多就壞

- Run list 無限列全部 runs
- Dataset items 全部載
- Review queue 全部載

---

## 缺少但應該有的功能

### 8. Side-by-side trace comparison

現在 compare 只有 aggregate metrics。最有價值的是：**同一個 input，baseline 的 trace 跟 candidate 的 trace 到底哪裡不同？**

應該有：`GET /api/v1/compare/traces?run_a={id}&run_b={id}&dataset_item_id={id}` → 並排顯示兩個 trace。

---

### 9. 沒有 tag/label 系統

目前只有 `category` 欄位，是 dataset 層面的。應該有 task-level tags（edge case、regression suite、smoke test），讓你可以只跑 subset。

---

### 10. Dataset 版本 diff 沒實作

`DatasetSnapshotRecord` 有 version number 但沒有 diff API。加了 10 個新 test cases 到底哪些是新的完全看不出來。

---

## 優先級總結

| 優先級 | 問題 | 工作量 |
|--------|------|--------|
| P0 | LLM-as-judge scorer（跨 provider，judge ≠ agent） | 中（~2天） |
| P0 | Statistical significance 在 compare | 小（半天） |
| P0 | Dataset generator — 貼 prompt 自動生成題目 | 中（2天） |
| P1 | Agent registry CRUD API（不再 hardcoded） | 中（2天） |
| P1 | Run progress polling | 小（半天） |
| P1 | Trace-level evaluation（efficiency score、step quality） | 中（2天） |
| P1 | Side-by-side trace compare | 中（2天） |
| P2 | Rubric-based scorer（利用現有 rubric_json 欄位） | 小（1天） |
| P2 | Promote failed case → dataset（一鍵加入 regression suite） | 小（1天） |
| P2 | Task tags / subset run | 中（2天） |
| P2 | Frontend 分頁 | 小（1天） |
| P2 | Multi-model config UI（generator/agent/judge 分開設定） | 中（2天） |

---

## 最重要的結論

1. **評估框架本身的信心度太低** — scorer 太弱 + 沒有 statistical significance，現在產出的數字不能信
2. **Trace 資料有但沒用** — 最寶貴的資料躺在 DB 裡沒有被分析
3. **Dataset 來源錯了** — 手動定義題目測不到真實失敗情境，應該從 production logs + LLM 生成 + failed cases 三個來源自動累積
4. **Self-evaluation bias** — 同一家模型出題又當裁判，分數會虛高，必須強制 agent provider ≠ judge provider
