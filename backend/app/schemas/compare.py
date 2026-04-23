from __future__ import annotations

from pydantic import BaseModel

from app.schemas.contracts import FailureReason, RunStatus
from app.schemas.traces import TraceEventSchema


class CompareMetricDeltaSchema(BaseModel):
    baseline: float | None = None
    candidate: float | None = None
    delta: float | None = None


class CompareConfidenceIntervalSchema(BaseModel):
    lower: float | None = None
    upper: float | None = None


class CompareCredibilitySchema(BaseModel):
    label: str
    sample_size: int
    confidence_interval: CompareConfidenceIntervalSchema
    p_value: float | None = None
    is_significant: bool = False


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


class CompareSamplingEvidenceSchema(BaseModel):
    group_id: str | None = None
    representative_run_id: str
    sample_count: int
    completed_sample_count: int
    sample_run_ids: list[str]
    success_rate_mean: float | None = None
    success_rate_stddev: float | None = None
    success_rate_variance: float | None = None
    consistency_rate: float | None = None
    is_stable: bool


class CompareSamplingAssessmentSchema(BaseModel):
    interpretation: str
    baseline: CompareSamplingEvidenceSchema
    candidate: CompareSamplingEvidenceSchema
    notes: str


class RunComparisonSchema(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    baseline_agent_version_id: str
    candidate_agent_version_id: str
    baseline_status: RunStatus
    candidate_status: RunStatus
    compared_task_count: int
    sample_size: int
    improvement_count: int
    regression_count: int
    confidence_interval: CompareConfidenceIntervalSchema
    p_value: float | None = None
    is_significant: bool = False
    success_rate: CompareMetricDeltaSchema
    average_latency_ms: CompareMetricDeltaSchema
    total_cost: CompareMetricDeltaSchema
    review_needed_count: CompareMetricDeltaSchema
    credibility: CompareCredibilitySchema
    lineage: CompareLineageSchema
    sampling: CompareSamplingAssessmentSchema | None = None
    category_deltas: list[CompareCategoryDeltaSchema]
    improvements: list[CompareCaseSchema]
    regressions: list[CompareCaseSchema]


class TraceDerivedMetricsSchema(BaseModel):
    step_count: int
    tool_count: int
    tool_names: list[str]
    final_output_event_count: int
    error_event_count: int
    failure_step_index: int | None = None
    max_steps: int | None = None
    excess_step_count: int | None = None
    efficiency_score: float | None = None


class TraceComparisonEntrySchema(BaseModel):
    run_id: str
    task_run_id: str
    dataset_item_id: str
    category: str
    status: RunStatus
    pass_fail: bool | None = None
    failure_reason: FailureReason | None = None
    input_text: str
    expected_output: str | None = None
    final_output: str | None = None
    error_message: str | None = None
    trace_id: str
    storage_path: str
    derived_metrics: TraceDerivedMetricsSchema
    events: list[TraceEventSchema]


class TraceComparisonSignalSchema(BaseModel):
    signal_key: str
    label: str
    direction: str
    baseline_value: str | int | float | None = None
    candidate_value: str | int | float | None = None
    detail: str | None = None


class TraceComparisonSchema(BaseModel):
    baseline_run_id: str
    candidate_run_id: str
    dataset_item_id: str
    category: str
    input_text: str
    expected_output: str | None = None
    same_final_output: bool
    pass_fail_changed: bool
    overall_label: str
    baseline: TraceComparisonEntrySchema
    candidate: TraceComparisonEntrySchema
    regression_signals: list[TraceComparisonSignalSchema]
    improvement_signals: list[TraceComparisonSignalSchema]
