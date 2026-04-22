from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.adapters import OpenAIAgentAdapter, StubAgentAdapter
from app.config import settings
from app.models import (
    DatasetItemRecord,
    DatasetRecord,
    DatasetSnapshotRecord,
    EvalRunRecord,
    EvalTaskRunRecord,
    ScoreRecord,
    TraceRecord,
)
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
from app.services.scoring import (
    keyword_overlap_score,
    llm_judge_score,
    rubric_based_score,
    score_for_failure,
    validate_judge_compatibility,
)

logger = logging.getLogger(__name__)


class InvalidStateTransitionError(ValueError):
    pass


_RUN_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.pending: {RunStatus.running, RunStatus.cancelled},
    RunStatus.running: {
        RunStatus.completed,
        RunStatus.failed,
        RunStatus.partial_success,
        RunStatus.cancelled,
    },
    RunStatus.completed: set(),
    RunStatus.failed: set(),
    RunStatus.cancelled: set(),
    RunStatus.partial_success: set(),
}

_TASK_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.pending: {
        RunStatus.running,
        RunStatus.completed,
        RunStatus.failed,
        RunStatus.cancelled,
    },
    RunStatus.running: {RunStatus.completed, RunStatus.failed, RunStatus.cancelled},
    RunStatus.completed: set(),
    RunStatus.failed: {RunStatus.running},
    RunStatus.cancelled: set(),
    RunStatus.partial_success: set(),
}


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
        evidence_json=record.evidence_json,
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
        dataset_snapshot_id=record.dataset_snapshot_id,
        scorer_config_id=record.scorer_config_id,
        status=RunStatus(record.status),
        baseline=record.baseline,
        experiment_tag=record.experiment_tag,
        notes=record.notes,
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
    statement = select(EvalRunRecord).order_by(
        EvalRunRecord.baseline.desc(),
        EvalRunRecord.created_at.desc(),
    )
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
    if dataset.latest_snapshot_id is None:
        raise LookupError("Dataset has no immutable snapshot yet.")

    dataset_snapshot = session.get(DatasetSnapshotRecord, dataset.latest_snapshot_id)
    if dataset_snapshot is None:
        raise LookupError("Dataset snapshot not found.")

    agent_version = get_agent_version(payload.agent_version_id)
    scorer_config = get_scorer_config(payload.scorer_config_id)
    validate_judge_compatibility(
        scorer_type=scorer_config.type,
        judge_provider=scorer_config.judge_provider,
        agent_model=agent_version.model,
    )
    _build_adapter(payload.adapter_type)

    dataset_items = list(
        session.execute(
            select(DatasetItemRecord)
            .where(DatasetItemRecord.dataset_snapshot_id == dataset.latest_snapshot_id)
            .order_by(DatasetItemRecord.sort_index.asc())
        ).scalars()
    )
    run_id = f"run_{uuid4().hex[:12]}"
    run_record = EvalRunRecord(
        run_id=run_id,
        agent_version_id=agent_version.agent_version_id,
        dataset_id=dataset.dataset_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
        dataset_checksum=dataset_snapshot.checksum,
        scorer_config_id=scorer_config.scorer_config_id,
        status=RunStatus.pending.value,
        adapter_type=payload.adapter_type,
        agent_version_snapshot_json=agent_version.model_dump(mode="json"),
        scorer_config_snapshot_json=scorer_config.model_dump(mode="json"),
        adapter_config_json=payload.adapter_config,
        baseline=False,
        experiment_tag=payload.experiment_tag,
        notes=payload.notes,
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
                metadata_json={
                    **(item.metadata_json or {}),
                    "rubric_json": item.rubric_json,
                },
            )
        )

    session.commit()
    return EvalRunSchema(
        run_id=run_record.run_id,
        agent_version_id=run_record.agent_version_id,
        dataset_id=run_record.dataset_id,
        dataset_snapshot_id=run_record.dataset_snapshot_id,
        scorer_config_id=run_record.scorer_config_id,
        status=RunStatus(run_record.status),
        baseline=run_record.baseline,
        experiment_tag=run_record.experiment_tag,
        notes=run_record.notes,
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


def _score_task(
    *,
    scorer_type: str,
    failure_reason: FailureReason | None,
    expected_output: str | None,
    final_output: str | None,
    rubric_json: dict[str, object] | None,
    trace_events: list[dict[str, object]],
    pass_threshold: float,
    judge_model: str | None,
    judge_provider: str | None,
) -> tuple[float, float, float, bool, dict[str, object] | None]:
    if failure_reason is not None:
        return *score_for_failure(failure_reason), {
            "score_method": "failure_short_circuit",
            "failure_reason": failure_reason.value,
        }

    if scorer_type == "keyword_overlap":
        correctness = keyword_overlap_score(expected_output, final_output)
        pass_fail = correctness >= pass_threshold
        return correctness, 1.0, 1.0, pass_fail, {
            "score_method": "keyword_overlap",
            "matched_token_ratio": correctness,
        }

    if scorer_type == "llm_judge":
        correctness, pass_fail, evidence = llm_judge_score(
            expected_output=expected_output,
            final_output=final_output,
            pass_threshold=pass_threshold,
            judge_model=judge_model,
            judge_provider=judge_provider,
        )
        return correctness, 1.0, 1.0, pass_fail, evidence

    if scorer_type == "rubric_based":
        correctness, pass_fail, evidence = rubric_based_score(
            rubric_json=rubric_json,
            expected_output=expected_output,
            final_output=final_output,
            trace_events=trace_events,
            pass_threshold=pass_threshold,
        )
        return correctness, 1.0, 1.0, pass_fail, evidence

    return *score_for_failure(failure_reason), {
        "score_method": scorer_type,
    }


def _set_run_status(
    run: EvalRunRecord,
    target_status: RunStatus,
    *,
    allow_restart: bool = False,
) -> None:
    current_status = RunStatus(run.status)
    if current_status == target_status:
        return

    allowed_targets = set(_RUN_TRANSITIONS[current_status])
    if allow_restart and target_status is RunStatus.running:
        allowed_targets.add(RunStatus.running)

    if target_status not in allowed_targets:
        logger.warning(
            "Rejected invalid run status transition run_id=%s from=%s to=%s",
            run.run_id,
            current_status.value,
            target_status.value,
        )
        raise InvalidStateTransitionError(
            f"Invalid run status transition: {current_status.value} -> {target_status.value}"
        )

    run.status = target_status.value


def _set_task_status(task_run: EvalTaskRunRecord, target_status: RunStatus) -> None:
    current_status = RunStatus(task_run.status)
    if current_status == target_status:
        return
    if target_status not in _TASK_TRANSITIONS[current_status]:
        logger.warning(
            "Rejected invalid task status transition task_run_id=%s from=%s to=%s",
            task_run.task_run_id,
            current_status.value,
            target_status.value,
        )
        raise InvalidStateTransitionError(
            f"Invalid task status transition: {current_status.value} -> {target_status.value}"
        )
    task_run.status = target_status.value


def _load_task_runs(session: Session, run_id: str) -> list[EvalTaskRunRecord]:
    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.run_id == run_id)
        .options(selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalTaskRunRecord.trace))
        .order_by(EvalTaskRunRecord.sort_index.asc())
    )
    return list(session.execute(statement).scalars().all())


def _build_adapter_config(
    run: EvalRunRecord,
    task_run: EvalTaskRunRecord,
) -> dict[str, object]:
    agent_version_config = run.agent_version_snapshot_json.get("config_json", {})
    adapter_config = dict(agent_version_config) if isinstance(agent_version_config, dict) else {}
    adapter_config.update(run.adapter_config_json)
    adapter_config.update(
        {
            "dataset_item_id": task_run.dataset_item_id,
            "expected_output": task_run.expected_output,
            "model": run.agent_version_snapshot_json.get("model"),
        }
    )
    return adapter_config


def _run_task_with_adapter(
    adapter: StubAgentAdapter | OpenAIAgentAdapter,
    task_run: EvalTaskRunRecord,
    adapter_config: dict[str, object],
) -> dict[str, object]:
    try:
        return adapter.run_task(task_run.input_text, adapter_config)
    except Exception as exc:
        logger.exception(
            "Task execution failed run_id=%s task_run_id=%s",
            task_run.run_id,
            task_run.task_run_id,
        )
        return {
            "final_output": None,
            "latency_ms": None,
            "token_usage": None,
            "cost": None,
            "termination_reason": "failed",
            "error": str(exc),
            "trace_events": [
                {"step_index": 0, "event_type": "agent_start", "input": task_run.input_text},
                {"step_index": 1, "event_type": "agent_error", "error": str(exc)},
            ],
        }


def _apply_task_result(
    session: Session,
    run: EvalRunRecord,
    task_run: EvalTaskRunRecord,
    result: dict[str, object],
) -> None:
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
    rubric_json = None
    if isinstance(task_run.metadata_json, dict):
        raw_rubric = task_run.metadata_json.get("rubric_json")
        rubric_json = raw_rubric if isinstance(raw_rubric, dict) else None
    correctness, tool_use, formatting, pass_fail, evidence = _score_task(
        scorer_type=scorer_type,
        failure_reason=failure_reason,
        expected_output=task_run.expected_output,
        final_output=task_run.final_output,
        rubric_json=rubric_json,
        trace_events=trace_events,
        pass_threshold=pass_threshold,
        judge_model=(
            str(run.scorer_config_snapshot_json.get("judge_model"))
            if run.scorer_config_snapshot_json.get("judge_model") is not None
            else None
        ),
        judge_provider=(
            str(run.scorer_config_snapshot_json.get("judge_provider"))
            if run.scorer_config_snapshot_json.get("judge_provider") is not None
            else None
        ),
    )
    if failure_reason is None and not pass_fail:
        failure_reason = FailureReason.answer_incorrect
    task_succeeded = failure_reason is None
    _set_task_status(task_run, RunStatus.completed if task_succeeded else RunStatus.failed)
    score.correctness = correctness
    score.tool_use = tool_use
    score.formatting = formatting
    score.pass_fail = pass_fail
    score.review_needed = failure_reason is not None or not pass_fail
    score.evidence_json = evidence
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


def _prepare_task_for_execution(session: Session, task_run: EvalTaskRunRecord) -> None:
    _set_task_status(task_run, RunStatus.running)
    task_run.started_at = datetime.now(UTC)
    task_run.completed_at = None
    task_run.final_output = None
    task_run.latency_ms = None
    task_run.token_usage = None
    task_run.cost = None
    task_run.termination_reason = None
    task_run.error_message = None
    task_run.trace_preview_json = None
    if task_run.review is not None:
        session.delete(task_run.review)


def _recompute_run_aggregation(
    session: Session,
    run: EvalRunRecord,
    *,
    allow_restart: bool,
) -> None:
    task_runs = _load_task_runs(session, run.run_id)
    run.total_tasks = len(task_runs)
    run.completed_tasks = sum(
        1 for task_run in task_runs if task_run.status == RunStatus.completed.value
    )
    run.failed_tasks = sum(1 for task_run in task_runs if task_run.status == RunStatus.failed.value)
    running_tasks = sum(1 for task_run in task_runs if task_run.status == RunStatus.running.value)
    pending_tasks = sum(1 for task_run in task_runs if task_run.status == RunStatus.pending.value)

    if running_tasks > 0:
        target_status = RunStatus.running
        run.completed_at = None
    elif run.completed_tasks == run.total_tasks and run.total_tasks > 0:
        target_status = RunStatus.completed
        run.completed_at = datetime.now(UTC)
    elif run.failed_tasks == run.total_tasks and run.total_tasks > 0:
        target_status = RunStatus.failed
        run.completed_at = datetime.now(UTC)
    elif pending_tasks == run.total_tasks:
        target_status = RunStatus.pending
        run.completed_at = None
    else:
        target_status = RunStatus.partial_success
        run.completed_at = datetime.now(UTC)

    _set_run_status(run, target_status, allow_restart=allow_restart)


def execute_run(
    session: Session,
    run_id: str,
    *,
    eligible_statuses: set[RunStatus] | None = None,
    allow_restart: bool = False,
) -> RunDetailSchema:
    run = session.get(EvalRunRecord, run_id)
    if run is None:
        raise LookupError("Run not found.")

    adapter = _build_adapter(run.adapter_type)
    all_task_runs = _load_task_runs(session, run_id)
    selected_statuses = eligible_statuses or {RunStatus.pending}
    task_runs = [
        task_run
        for task_run in all_task_runs
        if RunStatus(task_run.status) in selected_statuses
    ]
    if not task_runs:
        return _run_detail_schema(run)

    _set_run_status(run, RunStatus.running, allow_restart=allow_restart)
    if run.started_at is None:
        run.started_at = datetime.now(UTC)
    run.completed_at = None
    session.commit()

    for task_run in task_runs:
        _prepare_task_for_execution(session, task_run)
        session.commit()

        adapter_config = _build_adapter_config(run, task_run)
        result = _run_task_with_adapter(adapter, task_run, adapter_config)
        _apply_task_result(session, run, task_run, result)
        session.commit()

    _recompute_run_aggregation(session, run, allow_restart=True)
    session.commit()
    session.refresh(run)
    return _run_detail_schema(run)


def rerun_run(session: Session, run_id: str) -> RunDetailSchema:
    return execute_run(
        session,
        run_id,
        eligible_statuses={RunStatus.pending, RunStatus.failed},
        allow_restart=True,
    )


def repair_run_aggregation(session: Session, run_id: str) -> RunDetailSchema:
    run = session.get(EvalRunRecord, run_id)
    if run is None:
        raise LookupError("Run not found.")
    _recompute_run_aggregation(session, run, allow_restart=True)
    session.commit()
    session.refresh(run)
    return _run_detail_schema(run)


def update_run_status(session: Session, run_id: str, target_status: str) -> RunDetailSchema:
    run = session.get(EvalRunRecord, run_id)
    if run is None:
        raise LookupError("Run not found.")

    try:
        parsed_status = RunStatus(target_status)
    except ValueError as exc:
        raise ValueError(f"Unsupported run status: {target_status}") from exc

    _set_run_status(run, parsed_status, allow_restart=False)
    if parsed_status in {RunStatus.pending, RunStatus.running}:
        run.completed_at = None
    elif run.completed_at is None:
        run.completed_at = datetime.now(UTC)
    session.commit()
    session.refresh(run)
    return _run_detail_schema(run)


def update_run_baseline(session: Session, run_id: str, baseline: bool) -> RunDetailSchema:
    run = session.get(EvalRunRecord, run_id)
    if run is None:
        raise LookupError("Run not found.")

    run.baseline = baseline
    session.commit()
    session.refresh(run)
    return _run_detail_schema(run)
