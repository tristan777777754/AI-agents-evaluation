from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
    adapter_type: Literal["stub", "openai"] = "stub"
    adapter_config: dict[str, object] = Field(default_factory=dict)


class RunScoreSchema(BaseModel):
    correctness: float | None = None
    tool_use: float | None = None
    formatting: float | None = None
    pass_fail: bool
    review_needed: bool = False


class RunTaskResultSchema(BaseModel):
    task_run_id: str
    run_id: str
    dataset_item_id: str
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


class RegistryListSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    agent_versions: list[AgentVersionSchema] = Field(default_factory=list)
    scorer_configs: list[ScorerConfigSchema] = Field(default_factory=list)
