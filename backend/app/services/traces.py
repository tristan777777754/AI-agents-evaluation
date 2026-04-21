from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import EvalTaskRunRecord, TraceRecord
from app.schemas.contracts import FailureReason, TraceSummarySchema
from app.schemas.traces import TaskRunDetailSchema, TraceDetailSchema, TraceEventSchema
from app.services.reviews import _review_schema
from app.services.runs import _task_schema


def _trace_summary(record: TraceRecord | None) -> TraceSummarySchema | None:
    if record is None:
        return None
    return TraceSummarySchema(
        trace_id=record.trace_id,
        task_run_id=record.task_run_id,
        step_count=record.step_count,
        tool_count=record.tool_count,
        error_flag=record.error_flag,
        storage_path=record.storage_path,
    )


def get_task_run_detail(session: Session, task_run_id: str) -> TaskRunDetailSchema:
    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.task_run_id == task_run_id)
        .options(selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalTaskRunRecord.trace))
        .options(selectinload(EvalTaskRunRecord.review))
    )
    task_run = session.execute(statement).scalar_one_or_none()
    if task_run is None:
        raise LookupError("Task run not found.")

    task_schema = _task_schema(task_run)
    return TaskRunDetailSchema(
        **task_schema.model_dump(),
        review=_review_schema(task_run.review, task_run) if task_run.review is not None else None,
    )


def get_trace_detail(session: Session, task_run_id: str) -> TraceDetailSchema:
    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.task_run_id == task_run_id)
        .options(selectinload(EvalTaskRunRecord.trace))
    )
    task_run = session.execute(statement).scalar_one_or_none()
    if task_run is None or task_run.trace is None:
        raise LookupError("Trace not found.")

    trace = task_run.trace
    summary = _trace_summary(trace)
    if summary is None:
        raise LookupError("Trace not found.")
    return TraceDetailSchema(
        trace_id=trace.trace_id,
        task_run_id=task_run.task_run_id,
        run_id=task_run.run_id,
        failure_reason=FailureReason(trace.failure_reason) if trace.failure_reason else None,
        input_text=task_run.input_text,
        expected_output=task_run.expected_output,
        final_output=task_run.final_output,
        error_message=task_run.error_message,
        summary=summary,
        events=[TraceEventSchema.model_validate(event) for event in trace.events_json],
    )
