from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.contracts import FailureReason, TraceSummarySchema
from app.schemas.reviews import ReviewDetailSchema
from app.schemas.runs import RunTaskResultSchema


class TraceEventSchema(BaseModel):
    step_index: int
    event_type: str
    message: str | None = None
    tool_name: str | None = None
    input: object | None = None
    output: object | None = None
    latency_ms: int | None = None
    status: str | None = None
    error: str | None = None


class TaskRunDetailSchema(RunTaskResultSchema):
    failure_reason: FailureReason | None = None
    trace_summary: TraceSummarySchema | None = None
    review: ReviewDetailSchema | None = None


class TraceDetailSchema(BaseModel):
    trace_id: str = Field(..., examples=["trace_001"])
    task_run_id: str
    run_id: str
    failure_reason: FailureReason | None = None
    input_text: str
    expected_output: str | None = None
    final_output: str | None = None
    error_message: str | None = None
    summary: TraceSummarySchema
    events: list[TraceEventSchema]
