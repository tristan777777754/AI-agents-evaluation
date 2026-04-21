from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters import OpenAIAgentAdapter, StubAgentAdapter
from app.config import settings
from app.models import DatasetRecord, EvalRunRecord, EvalTaskRunRecord, ScoreRecord, TraceRecord
from app.schemas.contracts import EvalRunSchema, FailureReason, RunStatus, TraceSummarySchema
from app.schemas.runs import (
    RunCreateRequestSchema,
    RunDetailSchema,
    RunScoreSchema,
    RunSummarySchema,
    RunTaskListSchema,
    RunTaskResultSchema,
)
from app.services.registry import get_agent_version, get_scorer_config


def _build_adapter(adapter_type: str) -> StubAgentAdapter | OpenAIAgentAdapter:
    if adapter_type == "stub":
        return StubAgentAdapter()
    if adapter_type == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for adapter_type 'openai'.")
        return OpenAIAgentAdapter()
    raise ValueError(f"Unsupported adapter_type: {adapter_type}")


def _utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def _score_schema(record: ScoreRecord | None) -> RunScoreSchema | None:
    if record is None:
        return None
    return RunScoreSchema(
        correctness=record.correctness,
        tool_use=record.tool_use,
        formatting=record.formatting,
        pass_fail=record.pass_fail,
        review_needed=record.review_needed,
    )


def _trace_summary_schema(record: TraceRecord | None) -> TraceSummarySchema | None:
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


def _task_schema(record: EvalTaskRunRecord) -> RunTaskResultSchema:
    return RunTaskResultSchema(
        task_run_id=record.task_run_id,
        run_id=record.run_id,
        dataset_item_id=record.dataset_item_id,
        status=RunStatus(record.status),
        input_text=record.input_text,
        category=record.category,
        difficulty=record.difficulty,
        expected_output=record.expected_output,
        final_output=record.final_output,
        latency_ms=record.latency_ms,
        token_usage=record.token_usage,
        cost=record.cost,
        termination_reason=record.termination_reason,
        error_message=record.error_message,
        failure_reason=(
            FailureReason(record.trace.failure_reason)
            if record.trace and record.trace.failure_reason
            else None
        ),
        trace_summary=_trace_summary_schema(record.trace),
        score=_score_schema(record.score),
        started_at=_utc_iso(record.started_at),
        completed_at=_utc_iso(record.completed_at),
    )


def _run_summary_schema(record: EvalRunRecord) -> RunSummarySchema:
    return RunSummarySchema(
        run_id=record.run_id,
        agent_version_id=record.agent_version_id,
        dataset_id=record.dataset_id,
        scorer_config_id=record.scorer_config_id,
        status=RunStatus(record.status),
        started_at=_utc_iso(record.started_at),
        completed_at=_utc_iso(record.completed_at),
        adapter_type=record.adapter_type,
        total_tasks=record.total_tasks,
        completed_tasks=record.completed_tasks,
        failed_tasks=record.failed_tasks,
    )


def _run_detail_schema(record: EvalRunRecord) -> RunDetailSchema:
    summary = _run_summary_schema(record)
    return RunDetailSchema(
        **summary.model_dump(),
        agent_version=get_agent_version(record.agent_version_id),
        scorer_config=get_scorer_config(record.scorer_config_id),
    )


def list_runs(session: Session) -> list[RunSummarySchema]:
    statement = select(EvalRunRecord).order_by(EvalRunRecord.created_at.desc())
    runs = session.execute(statement).scalars().all()
    return [_run_summary_schema(run) for run in runs]


def get_run_detail(session: Session, run_id: str) -> RunDetailSchema:
    statement = (
        select(EvalRunRecord)
        .where(EvalRunRecord.run_id == run_id)
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.trace))
    )
    run = session.execute(statement).scalar_one_or_none()
    if run is None:
        raise LookupError("Run not found.")
    return _run_detail_schema(run)


def get_run_tasks(session: Session, run_id: str) -> RunTaskListSchema:
    run = session.get(EvalRunRecord, run_id)
    if run is None:
        raise LookupError("Run not found.")

    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.run_id == run_id)
        .options(selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalTaskRunRecord.trace))
        .order_by(EvalTaskRunRecord.sort_index.asc())
    )
    task_runs = session.execute(statement).scalars().all()
    return RunTaskListSchema(
        run_id=run_id,
        total_count=len(task_runs),
        items=[_task_schema(task_run) for task_run in task_runs],
    )


def create_run(session: Session, payload: RunCreateRequestSchema) -> EvalRunSchema:
    dataset = session.get(DatasetRecord, payload.dataset_id)
    if dataset is None:
        raise LookupError("Dataset not found.")

    agent_version = get_agent_version(payload.agent_version_id)
    scorer_config = get_scorer_config(payload.scorer_config_id)
    _build_adapter(payload.adapter_type)

    dataset_items = list(dataset.items)
    run_id = f"run_{uuid4().hex[:12]}"
    run_record = EvalRunRecord(
        run_id=run_id,
        agent_version_id=agent_version.agent_version_id,
        dataset_id=dataset.dataset_id,
        scorer_config_id=scorer_config.scorer_config_id,
        status=RunStatus.pending.value,
        adapter_type=payload.adapter_type,
        agent_version_snapshot_json=agent_version.model_dump(mode="json"),
        scorer_config_snapshot_json=scorer_config.model_dump(mode="json"),
        adapter_config_json=payload.adapter_config,
        total_tasks=len(dataset_items),
        completed_tasks=0,
        failed_tasks=0,
    )
    session.add(run_record)

    for index, item in enumerate(dataset_items, start=1):
        session.add(
            EvalTaskRunRecord(
                task_run_id=f"{run_id}__task_{index:03d}",
                run_id=run_id,
                dataset_item_id=item.dataset_item_id,
                sort_index=index,
                status=RunStatus.pending.value,
                input_text=item.input_text,
                category=item.category,
                difficulty=item.difficulty,
                expected_output=item.expected_output,
                metadata_json=item.metadata_json,
            )
        )

    session.commit()
    return EvalRunSchema(
        run_id=run_record.run_id,
        agent_version_id=run_record.agent_version_id,
        dataset_id=run_record.dataset_id,
        scorer_config_id=run_record.scorer_config_id,
        status=RunStatus(run_record.status),
        started_at=_utc_iso(run_record.started_at),
        completed_at=_utc_iso(run_record.completed_at),
    )


def _trace_storage_path(run_id: str, task_run_id: str) -> str:
    return f"{settings.storage_bucket}/{run_id}/{task_run_id}.json"


def _normalise_events(raw_events: object) -> list[dict[str, object]]:
    if not isinstance(raw_events, list):
        return []
    normalized: list[dict[str, object]] = []
    for index, entry in enumerate(raw_events):
        if isinstance(entry, dict):
            event = dict(entry)
        else:
            event = {"message": str(entry)}
        event.setdefault("step_index", index)
        event.setdefault("event_type", "event")
        normalized.append(event)
    return normalized


def _classify_failure(
    *,
    task_run: EvalTaskRunRecord,
    error_message: str | None,
    termination_reason: str | None,
    events: list[dict[str, object]],
) -> FailureReason | None:
    if any(
        event.get("event_type") == "tool_call" and str(event.get("status", "")).lower() == "error"
        for event in events
    ):
        return FailureReason.tool_error

    if termination_reason == FailureReason.format_error.value or any(
        event.get("event_type") == "format_error" for event in events
    ):
        return FailureReason.format_error

    if termination_reason == FailureReason.answer_incorrect.value:
        return FailureReason.answer_incorrect

    if error_message:
        return FailureReason.execution_failed

    return None


def _score_for_failure(failure_reason: FailureReason | None) -> tuple[float, float, float, bool]:
    if failure_reason is None:
        return 1.0, 1.0, 1.0, True
    if failure_reason is FailureReason.answer_incorrect:
        return 0.0, 1.0, 1.0, False
    if failure_reason is FailureReason.tool_error:
        return 0.0, 0.0, 1.0, False
    if failure_reason is FailureReason.format_error:
        return 0.0, 1.0, 0.0, False
    return 0.0, 0.0, 0.0, False


def _significant_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 3 or token.isdigit()
    ]


def _keyword_overlap_score(expected_output: str | None, final_output: str | None) -> float:
    if not expected_output or not final_output:
        return 0.0

    expected_tokens = _significant_tokens(expected_output)
    if not expected_tokens:
        return 0.0

    actual_text = final_output.lower()
    matched_tokens = sum(1 for token in expected_tokens if token in actual_text)
    return round(matched_tokens / len(expected_tokens), 2)


def _score_task(
    *,
    scorer_type: str,
    failure_reason: FailureReason | None,
    expected_output: str | None,
    final_output: str | None,
    pass_threshold: float,
) -> tuple[float, float, float, bool]:
    if failure_reason is not None:
        return _score_for_failure(failure_reason)

    if scorer_type == "keyword_overlap":
        correctness = _keyword_overlap_score(expected_output, final_output)
        pass_fail = correctness >= pass_threshold
        return correctness, 1.0, 1.0, pass_fail

    return _score_for_failure(failure_reason)


def execute_run(session: Session, run_id: str) -> RunDetailSchema:
    run = session.get(EvalRunRecord, run_id)
    if run is None:
        raise LookupError("Run not found.")

    adapter = _build_adapter(run.adapter_type)
    started_at = datetime.now(UTC)
    run.status = RunStatus.running.value
    run.started_at = started_at
    session.commit()

    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.run_id == run_id)
        .options(selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalTaskRunRecord.trace))
        .order_by(EvalTaskRunRecord.sort_index.asc())
    )
    task_runs = session.execute(statement).scalars().all()

    completed_tasks = 0
    failed_tasks = 0
    for task_run in task_runs:
        task_run.status = RunStatus.running.value
        task_run.started_at = datetime.now(UTC)
        session.commit()

        agent_version_config = run.agent_version_snapshot_json.get("config_json", {})
        adapter_config = (
            dict(agent_version_config) if isinstance(agent_version_config, dict) else {}
        )
        adapter_config.update(run.adapter_config_json)
        adapter_config.update(
            {
                "dataset_item_id": task_run.dataset_item_id,
                "expected_output": task_run.expected_output,
                "model": run.agent_version_snapshot_json.get("model"),
            }
        )
        result = adapter.run_task(task_run.input_text, adapter_config)

        error = result.get("error")
        final_output = result.get("final_output")
        task_run.final_output = final_output if isinstance(final_output, str) else None
        latency_value = result.get("latency_ms")
        task_run.latency_ms = int(latency_value) if isinstance(latency_value, int | float) else None
        token_usage = result.get("token_usage")
        task_run.token_usage = token_usage if isinstance(token_usage, dict) else None
        cost_value = result.get("cost")
        task_run.cost = float(cost_value) if isinstance(cost_value, int | float) else None
        termination_reason = result.get("termination_reason")
        task_run.termination_reason = (
            str(termination_reason) if termination_reason is not None else None
        )
        task_run.error_message = str(error) if error is not None else None
        trace_events = _normalise_events(result.get("trace_events"))
        task_run.trace_preview_json = trace_events[:3]
        task_run.completed_at = datetime.now(UTC)

        failure_reason = _classify_failure(
            task_run=task_run,
            error_message=task_run.error_message,
            termination_reason=task_run.termination_reason,
            events=trace_events,
        )
        score = task_run.score or ScoreRecord(
            score_id=f"score_{task_run.task_run_id}",
            task_run_id=task_run.task_run_id,
        )
        scorer_type = str(run.scorer_config_snapshot_json.get("type", "rule_based"))
        threshold_config = run.scorer_config_snapshot_json.get("thresholds_json", {})
        pass_threshold_raw = (
            threshold_config.get("pass_fail") if isinstance(threshold_config, dict) else 0.7
        )
        pass_threshold = (
            float(pass_threshold_raw) if isinstance(pass_threshold_raw, int | float) else 0.7
        )
        correctness, tool_use, formatting, pass_fail = _score_task(
            scorer_type=scorer_type,
            failure_reason=failure_reason,
            expected_output=task_run.expected_output,
            final_output=task_run.final_output,
            pass_threshold=pass_threshold,
        )
        if failure_reason is None and not pass_fail:
            failure_reason = FailureReason.answer_incorrect
        task_succeeded = failure_reason is None
        task_run.status = RunStatus.completed.value if task_succeeded else RunStatus.failed.value
        score.correctness = correctness
        score.tool_use = tool_use
        score.formatting = formatting
        score.pass_fail = pass_fail
        score.review_needed = failure_reason is not None or not pass_fail
        session.add(score)

        trace_record = task_run.trace or TraceRecord(
            trace_id=f"trace_{task_run.task_run_id}",
            task_run_id=task_run.task_run_id,
            run_id=task_run.run_id,
            storage_path=_trace_storage_path(task_run.run_id, task_run.task_run_id),
        )
        trace_record.step_count = len(trace_events)
        trace_record.tool_count = sum(
            1 for event in trace_events if event.get("event_type") == "tool_call"
        )
        trace_record.error_flag = failure_reason is not None
        trace_record.failure_reason = failure_reason.value if failure_reason is not None else None
        trace_record.events_json = trace_events
        session.add(trace_record)

        if task_succeeded:
            completed_tasks += 1
        else:
            failed_tasks += 1
        session.commit()

    run.completed_tasks = completed_tasks
    run.failed_tasks = failed_tasks
    run.completed_at = datetime.now(UTC)
    if completed_tasks == run.total_tasks:
        run.status = RunStatus.completed.value
    elif completed_tasks > 0:
        run.status = RunStatus.partial_success.value
    else:
        run.status = RunStatus.failed.value
    session.commit()
    session.refresh(run)
    return _run_detail_schema(run)
