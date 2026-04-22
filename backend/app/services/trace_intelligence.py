from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import EvalRunRecord, EvalTaskRunRecord, TraceRecord
from app.schemas.compare import (
    TraceComparisonEntrySchema,
    TraceComparisonSchema,
    TraceComparisonSignalSchema,
    TraceDerivedMetricsSchema,
)
from app.schemas.contracts import FailureReason, RunStatus
from app.schemas.traces import TraceEventSchema

COMPARABLE_RUN_STATUSES = {RunStatus.completed.value, RunStatus.partial_success.value}


def _task_passed(task_run: EvalTaskRunRecord) -> bool | None:
    if task_run.score is None:
        return None
    return task_run.score.pass_fail


def _normalised_events(trace: TraceRecord) -> list[dict[str, object]]:
    return [event for event in trace.events_json if isinstance(event, dict)]


def _failure_step_index(
    failure_reason: FailureReason | None,
    events: list[dict[str, object]],
) -> int | None:
    def step_value(event: dict[str, object], fallback: int) -> int:
        raw_value = event.get("step_index")
        if isinstance(raw_value, int | float):
            return int(raw_value)
        return fallback

    for event in events:
        event_type = str(event.get("event_type", ""))
        status = str(event.get("status", "")).lower()
        if event.get("error") is not None:
            return step_value(event, 0)
        if event_type in {"agent_error", "format_error"}:
            return step_value(event, 0)
        if event_type == "tool_call" and status == "error":
            return step_value(event, 0)
    if failure_reason is not None and events:
        return step_value(events[-1], len(events) - 1)
    return None


def _derive_metrics(
    task_run: EvalTaskRunRecord,
    trace: TraceRecord,
) -> TraceDerivedMetricsSchema:
    events = _normalised_events(trace)
    tool_names = sorted(
        {
            str(event["tool_name"])
            for event in events
            if isinstance(event.get("tool_name"), str) and str(event["tool_name"]).strip()
        }
    )
    final_output_event_count = sum(
        1 for event in events if event.get("event_type") == "final_output"
    )
    error_event_count = sum(
        1
        for event in events
        if event.get("error") is not None
        or str(event.get("status", "")).lower() == "error"
        or str(event.get("event_type", "")).endswith("error")
    )
    rubric_json = (
        task_run.metadata_json.get("rubric_json")
        if isinstance(task_run.metadata_json, dict)
        else None
    )
    max_steps = None
    if isinstance(rubric_json, dict):
        raw_max_steps = rubric_json.get("max_steps")
        if isinstance(raw_max_steps, int | float) and raw_max_steps > 0:
            max_steps = int(raw_max_steps)

    step_count = trace.step_count
    excess_step_count = None if max_steps is None else max(step_count - max_steps, 0)
    efficiency_score = None
    if max_steps is not None and step_count > 0:
        efficiency_score = round(min(max_steps / step_count, 1.0), 4)

    failure_reason = FailureReason(trace.failure_reason) if trace.failure_reason else None
    return TraceDerivedMetricsSchema(
        step_count=step_count,
        tool_count=trace.tool_count,
        tool_names=tool_names,
        final_output_event_count=final_output_event_count,
        error_event_count=error_event_count,
        failure_step_index=_failure_step_index(failure_reason, events),
        max_steps=max_steps,
        excess_step_count=excess_step_count,
        efficiency_score=efficiency_score,
    )


def _trace_entry(task_run: EvalTaskRunRecord) -> TraceComparisonEntrySchema:
    trace = task_run.trace
    if trace is None:
        raise LookupError("Trace not found.")

    return TraceComparisonEntrySchema(
        run_id=task_run.run_id,
        task_run_id=task_run.task_run_id,
        dataset_item_id=task_run.dataset_item_id,
        category=task_run.category,
        status=RunStatus(task_run.status),
        pass_fail=_task_passed(task_run),
        failure_reason=FailureReason(trace.failure_reason) if trace.failure_reason else None,
        input_text=task_run.input_text,
        expected_output=task_run.expected_output,
        final_output=task_run.final_output,
        error_message=task_run.error_message,
        trace_id=trace.trace_id,
        storage_path=trace.storage_path,
        derived_metrics=_derive_metrics(task_run, trace),
        events=[TraceEventSchema.model_validate(event) for event in trace.events_json],
    )


def _string_match(left: str | None, right: str | None) -> bool:
    if left is None or right is None:
        return False
    return left.strip() == right.strip()


def _signal(
    *,
    signal_key: str,
    label: str,
    direction: str,
    baseline_value: str | int | float | None,
    candidate_value: str | int | float | None,
    detail: str | None,
) -> TraceComparisonSignalSchema:
    return TraceComparisonSignalSchema(
        signal_key=signal_key,
        label=label,
        direction=direction,
        baseline_value=baseline_value,
        candidate_value=candidate_value,
        detail=detail,
    )


def _compare_entries(
    baseline: TraceComparisonEntrySchema,
    candidate: TraceComparisonEntrySchema,
) -> tuple[list[TraceComparisonSignalSchema], list[TraceComparisonSignalSchema]]:
    regressions: list[TraceComparisonSignalSchema] = []
    improvements: list[TraceComparisonSignalSchema] = []

    baseline_metrics = baseline.derived_metrics
    candidate_metrics = candidate.derived_metrics
    same_final_output = _string_match(baseline.final_output, candidate.final_output)

    if candidate_metrics.step_count > baseline_metrics.step_count:
        detail = "Candidate used a longer path."
        if same_final_output:
            detail = "Candidate reached the same final answer with more steps."
        regressions.append(
            _signal(
                signal_key="more_steps",
                label="More steps",
                direction="regression",
                baseline_value=baseline_metrics.step_count,
                candidate_value=candidate_metrics.step_count,
                detail=detail,
            )
        )
    elif candidate_metrics.step_count < baseline_metrics.step_count:
        improvements.append(
            _signal(
                signal_key="fewer_steps",
                label="Fewer steps",
                direction="improvement",
                baseline_value=baseline_metrics.step_count,
                candidate_value=candidate_metrics.step_count,
                detail="Candidate finished in fewer steps.",
            )
        )

    if candidate_metrics.tool_count > baseline_metrics.tool_count:
        regressions.append(
            _signal(
                signal_key="more_tool_calls",
                label="More tool calls",
                direction="regression",
                baseline_value=baseline_metrics.tool_count,
                candidate_value=candidate_metrics.tool_count,
                detail="Candidate depended on more tool calls.",
            )
        )
    elif candidate_metrics.tool_count < baseline_metrics.tool_count:
        improvements.append(
            _signal(
                signal_key="fewer_tool_calls",
                label="Fewer tool calls",
                direction="improvement",
                baseline_value=baseline_metrics.tool_count,
                candidate_value=candidate_metrics.tool_count,
                detail="Candidate solved the item with fewer tool calls.",
            )
        )

    if (
        baseline_metrics.efficiency_score is not None
        and candidate_metrics.efficiency_score is not None
        and candidate_metrics.efficiency_score != baseline_metrics.efficiency_score
    ):
        direction = (
            "regression"
            if candidate_metrics.efficiency_score < baseline_metrics.efficiency_score
            else "improvement"
        )
        target = regressions if direction == "regression" else improvements
        target.append(
            _signal(
                signal_key="efficiency_score",
                label="Efficiency score",
                direction=direction,
                baseline_value=baseline_metrics.efficiency_score,
                candidate_value=candidate_metrics.efficiency_score,
                detail="Derived from rubric max_steps versus actual trace step count.",
            )
        )

    if baseline.failure_reason != candidate.failure_reason:
        direction = "regression" if candidate.failure_reason is not None else "improvement"
        target = regressions if direction == "regression" else improvements
        target.append(
            _signal(
                signal_key="failure_reason_changed",
                label="Failure mode changed",
                direction=direction,
                baseline_value=baseline.failure_reason.value if baseline.failure_reason else "none",
                candidate_value=(
                    candidate.failure_reason.value if candidate.failure_reason else "none"
                ),
                detail="Trace-level failure classification changed between runs.",
            )
        )

    if (
        baseline_metrics.failure_step_index is not None
        and candidate_metrics.failure_step_index is not None
        and baseline_metrics.failure_step_index != candidate_metrics.failure_step_index
    ):
        direction = (
            "regression"
            if candidate_metrics.failure_step_index < baseline_metrics.failure_step_index
            else "improvement"
        )
        target = regressions if direction == "regression" else improvements
        target.append(
            _signal(
                signal_key="failure_step_shift",
                label="Failure step moved",
                direction=direction,
                baseline_value=baseline_metrics.failure_step_index,
                candidate_value=candidate_metrics.failure_step_index,
                detail="Later failures preserve more useful work before the breakage.",
            )
        )

    return regressions, improvements


def get_trace_comparison(
    session: Session,
    *,
    baseline_run_id: str,
    candidate_run_id: str,
    dataset_item_id: str,
) -> TraceComparisonSchema:
    if baseline_run_id == candidate_run_id:
        raise ValueError("Baseline and candidate runs must be different.")

    statement = (
        select(EvalRunRecord)
        .where(EvalRunRecord.run_id.in_([baseline_run_id, candidate_run_id]))
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.trace))
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.score))
    )
    runs = session.execute(statement).scalars().all()
    run_by_id = {run.run_id: run for run in runs}

    baseline_run = run_by_id.get(baseline_run_id)
    candidate_run = run_by_id.get(candidate_run_id)
    if baseline_run is None or candidate_run is None:
        raise LookupError("Run not found.")
    if baseline_run.dataset_id != candidate_run.dataset_id:
        raise ValueError("Runs must use the same dataset for trace comparison.")
    if (
        baseline_run.status not in COMPARABLE_RUN_STATUSES
        or candidate_run.status not in COMPARABLE_RUN_STATUSES
    ):
        raise ValueError("Only completed or partial-success runs can be compared.")

    baseline_task = next(
        (task for task in baseline_run.task_runs if task.dataset_item_id == dataset_item_id),
        None,
    )
    candidate_task = next(
        (task for task in candidate_run.task_runs if task.dataset_item_id == dataset_item_id),
        None,
    )
    if baseline_task is None or candidate_task is None:
        raise LookupError("Comparable task run not found.")
    if baseline_task.trace is None or candidate_task.trace is None:
        raise LookupError("Trace not found.")

    baseline_entry = _trace_entry(baseline_task)
    candidate_entry = _trace_entry(candidate_task)
    regression_signals, improvement_signals = _compare_entries(baseline_entry, candidate_entry)

    if regression_signals:
        overall_label = "regression"
    elif improvement_signals:
        overall_label = "improvement"
    else:
        overall_label = "neutral"

    return TraceComparisonSchema(
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        dataset_item_id=dataset_item_id,
        category=baseline_task.category,
        input_text=baseline_task.input_text,
        expected_output=baseline_task.expected_output,
        same_final_output=_string_match(baseline_task.final_output, candidate_task.final_output),
        pass_fail_changed=_task_passed(baseline_task) != _task_passed(candidate_task),
        overall_label=overall_label,
        baseline=baseline_entry,
        candidate=candidate_entry,
        regression_signals=regression_signals,
        improvement_signals=improvement_signals,
    )
