from __future__ import annotations

from pydantic import BaseModel

from app.schemas.contracts import FailureReason, RunStatus


class DashboardCategorySummarySchema(BaseModel):
    category: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    success_rate: float
    average_latency_ms: float | None = None
    total_cost: float = 0.0


class DashboardFailureSummarySchema(BaseModel):
    failure_reason: FailureReason
    count: int


class DashboardFailedCaseSchema(BaseModel):
    task_run_id: str
    run_id: str
    dataset_item_id: str
    category: str
    failure_reason: FailureReason
    error_message: str | None = None
    final_output: str | None = None


class RunDashboardSummarySchema(BaseModel):
    run_id: str
    agent_version_id: str
    dataset_id: str
    scorer_config_id: str
    status: RunStatus
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    review_needed_count: int
    success_rate: float
    average_latency_ms: float | None = None
    total_cost: float = 0.0
    category_breakdown: list[DashboardCategorySummarySchema]
    failure_breakdown: list[DashboardFailureSummarySchema]
    failed_cases: list[DashboardFailedCaseSchema]
