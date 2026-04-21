from __future__ import annotations

from pydantic import BaseModel

from app.schemas.contracts import FailureReason, RunStatus


class CompareMetricDeltaSchema(BaseModel):
    baseline: float | None = None
    candidate: float | None = None
    delta: float | None = None


class CompareCategoryDeltaSchema(BaseModel):
    category: str
    baseline_total_tasks: int
    candidate_total_tasks: int
    baseline_success_rate: float
    candidate_success_rate: float
    success_rate_delta: float
    baseline_failed_tasks: int
    candidate_failed_tasks: int


class CompareCaseSchema(BaseModel):
    dataset_item_id: str
    category: str
    baseline_task_run_id: str
    candidate_task_run_id: str
    baseline_status: RunStatus
    candidate_status: RunStatus
    baseline_failure_reason: FailureReason | None = None
    candidate_failure_reason: FailureReason | None = None
    baseline_final_output: str | None = None
    candidate_final_output: str | None = None


class CompareRunLineageSchema(BaseModel):
    run_id: str
    dataset_id: str
    dataset_snapshot_id: str | None = None
    agent_version_id: str
    agent_version_snapshot_hash: str
    scorer_config_id: str
    scorer_snapshot_hash: str
    baseline: bool = False
    experiment_tag: str | None = None


class CompareLineageSchema(BaseModel):
    baseline: CompareRunLineageSchema
    candidate: CompareRunLineageSchema


class RunComparisonSchema(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    baseline_agent_version_id: str
    candidate_agent_version_id: str
    baseline_status: RunStatus
    candidate_status: RunStatus
    compared_task_count: int
    improvement_count: int
    regression_count: int
    success_rate: CompareMetricDeltaSchema
    average_latency_ms: CompareMetricDeltaSchema
    total_cost: CompareMetricDeltaSchema
    review_needed_count: CompareMetricDeltaSchema
    lineage: CompareLineageSchema
    category_deltas: list[CompareCategoryDeltaSchema]
    improvements: list[CompareCaseSchema]
    regressions: list[CompareCaseSchema]
