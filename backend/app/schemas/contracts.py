from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    partial_success = "partial_success"


class FailureReason(str, Enum):
    answer_incorrect = "answer_incorrect"
    tool_error = "tool_error"
    format_error = "format_error"
    execution_failed = "execution_failed"


class SourceType(str, Enum):
    json = "json"
    csv = "csv"
    fixture = "fixture"


class PhaseMarker(BaseModel):
    current_phase: str = "Phase 7"
    scope: list[str]
    non_goals: list[str]


class AgentSchema(BaseModel):
    agent_id: str = Field(..., examples=["agent_support_qa"])
    name: str
    description: str | None = None
    owner_id: str | None = None
    created_at: str | None = None


class AgentVersionSchema(BaseModel):
    agent_version_id: str = Field(..., examples=["av_support_qa_v1"])
    agent_id: str
    version_name: str
    model: str
    prompt_hash: str
    config_json: dict[str, object] = Field(default_factory=dict)
    created_at: str | None = None


class DatasetSchema(BaseModel):
    dataset_id: str = Field(..., examples=["dataset_support_faq_v1"])
    name: str
    description: str | None = None
    schema_version: str = "1.0"
    source_type: SourceType


class DatasetItemSchema(BaseModel):
    dataset_item_id: str = Field(..., examples=["ds_item_001"])
    dataset_id: str
    input_text: str
    category: str
    difficulty: str | None = None
    expected_output: str | None = None
    rubric_json: dict[str, object] | None = None
    reference_context: str | None = None
    metadata_json: dict[str, object] | None = None


class ScorerConfigSchema(BaseModel):
    scorer_config_id: str = Field(..., examples=["sc_rule_based_v1"])
    name: str
    type: str
    weights_json: dict[str, float] = Field(default_factory=dict)
    judge_model: str | None = None
    thresholds_json: dict[str, float] = Field(default_factory=dict)


class EvalRunSchema(BaseModel):
    run_id: str = Field(..., examples=["run_20260420_001"])
    agent_version_id: str
    dataset_id: str
    scorer_config_id: str
    status: RunStatus
    started_at: str | None = None
    completed_at: str | None = None


class EvalTaskRunSchema(BaseModel):
    task_run_id: str = Field(..., examples=["task_run_001"])
    run_id: str
    dataset_item_id: str
    status: RunStatus
    final_output: str | None = None
    latency_ms: int | None = None
    token_usage: dict[str, int] | None = None
    cost: float | None = None


class TraceSummarySchema(BaseModel):
    trace_id: str = Field(..., examples=["trace_001"])
    task_run_id: str
    step_count: int
    tool_count: int
    error_flag: bool
    storage_path: str


class ScoreSchema(BaseModel):
    score_id: str = Field(..., examples=["score_001"])
    task_run_id: str
    correctness: float | None = None
    tool_use: float | None = None
    formatting: float | None = None
    pass_fail: bool
    review_needed: bool = False


class ReviewSchema(BaseModel):
    review_id: str = Field(..., examples=["review_001"])
    task_run_id: str
    reviewer_id: str
    verdict: str | None = None
    failure_label: str | None = None
    note: str | None = None


class PhaseContractSnapshot(BaseModel):
    phase: PhaseMarker
    run_statuses: list[RunStatus]
    entities: dict[str, list[str]]

    @classmethod
    def build_default(cls) -> "PhaseContractSnapshot":
        return cls(
            phase=PhaseMarker(
                scope=[
                    "real OpenAI-backed adapter path alongside the deterministic stub harness",
                    "keyword-overlap scoring for natural-language outputs",
                    "benchmark dataset coverage for real compare evidence",
                    "integration smoke gated by explicit provider credentials",
                ],
                non_goals=[
                    "removing the stub adapter",
                    "binding CI or unit tests to external APIs",
                    "LLM-as-judge scoring",
                    "multi-model benchmark platform expansion",
                ],
            ),
            run_statuses=list(RunStatus),
            entities={
                "agent": list(AgentSchema.model_fields.keys()),
                "agent_version": list(AgentVersionSchema.model_fields.keys()),
                "dataset": list(DatasetSchema.model_fields.keys()),
                "dataset_item": list(DatasetItemSchema.model_fields.keys()),
                "scorer_config": list(ScorerConfigSchema.model_fields.keys()),
                "eval_run": list(EvalRunSchema.model_fields.keys()),
                "eval_task_run": list(EvalTaskRunSchema.model_fields.keys()),
                "trace": list(TraceSummarySchema.model_fields.keys()),
                "score": list(ScoreSchema.model_fields.keys()),
                "review": list(ReviewSchema.model_fields.keys()),
            },
        )
