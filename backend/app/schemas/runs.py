from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.contracts import (
    AgentVersionSchema,
    EvalRunSchema,
    FailureReason,
    RunStatus,
    ScorerConfigSchema,
    TraceSummarySchema,
)


class RunCreateRequestSchema(BaseModel):
    dataset_id: str
    agent_version_id: str
    scorer_config_id: str
    dataset_tag_filter: list[str] = Field(default_factory=list)
    adapter_type: Literal["stub", "openai"] = "stub"
    adapter_config: dict[str, object] = Field(default_factory=dict)
    experiment_tag: str | None = None
    notes: str | None = None


class RunScoreSchema(BaseModel):
    correctness: float | None = None
    tool_use: float | None = None
    formatting: float | None = None
    pass_fail: bool
    review_needed: bool = False
    evidence_json: dict[str, object] | None = None


class RunTaskResultSchema(BaseModel):
    task_run_id: str
    run_id: str
    dataset_item_id: str
    dataset_item_tags: list[str] = Field(default_factory=list)
    status: RunStatus
    input_text: str
    category: str
    difficulty: str | None = None
    expected_output: str | None = None
    final_output: str | None = None
    latency_ms: int | None = None
    token_usage: dict[str, int] | None = None
    cost: float | None = None
    termination_reason: str | None = None
    error_message: str | None = None
    failure_reason: FailureReason | None = None
    trace_summary: TraceSummarySchema | None = None
    score: RunScoreSchema | None = None
    started_at: str | None = None
    completed_at: str | None = None


class RunTaskListSchema(BaseModel):
    run_id: str
    total_count: int
    items: list[RunTaskResultSchema]


class RunSummarySchema(EvalRunSchema):
    adapter_type: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int


class RunDetailSchema(RunSummarySchema):
    agent_version: AgentVersionSchema
    scorer_config: ScorerConfigSchema


class RunListPageSchema(BaseModel):
    items: list[RunSummarySchema] = Field(default_factory=list)
    total_count: int
    page: int
    per_page: int
    has_next_page: bool


class QuickRunRequestSchema(BaseModel):
    agent_version_id: str
    adapter_type: Literal["stub", "openai"] = "stub"
    adapter_config: dict[str, object] = Field(default_factory=dict)
    experiment_tag: str | None = None
    notes: str | None = None


class AutoCompareSchema(BaseModel):
    baseline_run_id: str | None = None
    candidate_run_id: str
    selection_reason: str | None = None
    comparison: dict[str, object] | None = None


class QuickRunResponseSchema(BaseModel):
    run: RunDetailSchema
    auto_compare: AutoCompareSchema
