# TASK_TEMPLATE.md

## Purpose

這份文件定義每次 phase 任務的固定輸入格式。所有 coding agent、Harness workflow 或人工協作任務都必須沿用這份模板，避免 scope 漂移、跨 phase 偷做功能或在缺少驗收條件時直接開工。

搭配文件：

- [AGENTS.md](/Users/tristan/AI-agents-evaluation/AGENTS.md)
- [IMPLEMENTATION_PLAN.md](/Users/tristan/AI-agents-evaluation/IMPLEMENTATION_PLAN.md)
- [TECH_SPEC.md](/Users/tristan/AI-agents-evaluation/TECH_SPEC.md)
- [TESTING.md](/Users/tristan/AI-agents-evaluation/TESTING.md)

## Usage Rules

- 一次任務只能對應一個 `Current Phase`
- `In Scope` 與 `Out of Scope` 必須明確，不可留白
- `Files Allowed To Touch` 必須具體到目錄或檔案
- `Acceptance Checks` 必須可觀察、可驗證、可重跑
- `Contract Checks` 必須明確指出本次是否影響 schema、status、summary、compare 或 API envelope
- `Evidence To Attach` 必須列出要提交的測試輸出、畫面、DB 驗證或 acceptance report
- `Rollback / Recovery Notes` 必須說明失敗時如何回復到安全狀態
- 若任務需要修改 core contract，必須先更新文件再執行

## Required Task Format

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

## Acceptance Check Style

建議使用以下格式：

- `When <action>, then <observable result>`
- `Given <fixture>, API returns <status/body>`
- `After <workflow>, DB contains <records>`

避免使用：

- `看起來正常`
- `功能完成`
- `大致可用`

## Copy-Paste Template

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
