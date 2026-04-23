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
from app.schemas.compare import RunComparisonSchema
from app.schemas.contracts import (
    AgentVersionSchema,
    DatasetLifecycleStatus,
    EvalRunSchema,
    FailureReason,
    RunStatus,
    SamplingMetadataSchema,
    ScorerConfigSchema,
    TraceSummarySchema,
)
from app.schemas.runs import (
    AutoCompareSchema,
    QuickRunRequestSchema,
    QuickRunResponseSchema,
    RunCreateRequestSchema,
    RunDetailSchema,
    RunListPageSchema,
    RunScoreSchema,
    RunSummarySchema,
    RunTaskListSchema,
    RunTaskResultSchema,
    SampledRunCreateRequestSchema,
    SampledRunCreateResponseSchema,
)
from app.services.compare import COMPARABLE_RUN_STATUSES, get_run_comparison
from app.services.registry import get_agent_version, get_registry_defaults, get_scorer_config
from app.services.scoring import (
    build_judge_audit,
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
        judge_audit=record.judge_audit_json,
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


def _sampling_metadata_schema(record: EvalRunRecord) -> SamplingMetadataSchema | None:
    if not record.sample_group_id or not record.sample_index or not record.sample_count:
        return None
    return SamplingMetadataSchema(
        group_id=record.sample_group_id,
        sample_index=record.sample_index,
        sample_count=record.sample_count,
    )


def _task_schema(record: EvalTaskRunRecord) -> RunTaskResultSchema:
    return RunTaskResultSchema(
        task_run_id=record.task_run_id,
        run_id=record.run_id,
        dataset_item_id=record.dataset_item_id,
        dataset_item_tags=list(record.dataset_item_tags_json or []),
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
        dataset_tag_filter=list(record.dataset_tag_filter_json or []),
        scorer_config_id=record.scorer_config_id,
        status=RunStatus(record.status),
        baseline=record.baseline,
        experiment_tag=record.experiment_tag,
        notes=record.notes,
        sampling=_sampling_metadata_schema(record),
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
        agent_version=AgentVersionSchema.model_validate(record.agent_version_snapshot_json),
        scorer_config=ScorerConfigSchema.model_validate(record.scorer_config_snapshot_json),
    )


def list_runs(
    session: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    dataset_id: str | None = None,
    agent_version_id: str | None = None,
) -> RunListPageSchema:
    statement = select(EvalRunRecord).order_by(
        EvalRunRecord.baseline.desc(),
        EvalRunRecord.created_at.desc(),
    )
    if status:
        statement = statement.where(EvalRunRecord.status == status)
    if dataset_id:
        statement = statement.where(EvalRunRecord.dataset_id == dataset_id)
    if agent_version_id:
        statement = statement.where(EvalRunRecord.agent_version_id == agent_version_id)
    runs = session.execute(statement).scalars().all()
    total_count = len(runs)
    start = max(page - 1, 0) * per_page
    end = start + per_page
    paged_runs = runs[start:end]
    return RunListPageSchema(
        items=[_run_summary_schema(run) for run in paged_runs],
        total_count=total_count,
        page=page,
        per_page=per_page,
        has_next_page=end < total_count,
    )


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
    return _create_run(
        session,
        payload,
        sample_group_id=None,
        sample_index=None,
        sample_count=None,
        sampling_config=None,
    )


def _create_run(
    session: Session,
    payload: RunCreateRequestSchema,
    *,
    sample_group_id: str | None,
    sample_index: int | None,
    sample_count: int | None,
    sampling_config: dict[str, object] | None,
) -> EvalRunSchema:
    dataset = session.get(DatasetRecord, payload.dataset_id)
    if dataset is None:
        raise LookupError("Dataset not found.")
    if dataset.lifecycle_status != DatasetLifecycleStatus.published.value:
        raise ValueError("Dataset drafts must be approved before they can be used in a run.")
    if dataset.latest_snapshot_id is None:
        raise LookupError("Dataset has no immutable snapshot yet.")

    dataset_snapshot = session.get(DatasetSnapshotRecord, dataset.latest_snapshot_id)
    if dataset_snapshot is None:
        raise LookupError("Dataset snapshot not found.")

    agent_version = get_agent_version(session, payload.agent_version_id)
    scorer_config = get_scorer_config(payload.scorer_config_id)
    validate_judge_compatibility(
        scorer_type=scorer_config.type,
        judge_provider=scorer_config.judge_provider,
        judge_model=scorer_config.judge_model,
        agent_model=agent_version.model,
        compatibility_policy=(
            scorer_config.governance.compatibility.model_dump(mode="json")
            if scorer_config.governance is not None
            and scorer_config.governance.compatibility is not None
            else None
        ),
    )
    _build_adapter(payload.adapter_type)

    dataset_items = list(
        session.execute(
            select(DatasetItemRecord)
            .where(DatasetItemRecord.dataset_snapshot_id == dataset.latest_snapshot_id)
            .order_by(DatasetItemRecord.sort_index.asc())
        ).scalars()
    )
    if payload.dataset_tag_filter:
        requested_tags = {tag.strip().lower() for tag in payload.dataset_tag_filter if tag.strip()}
        dataset_items = [
            item
            for item in dataset_items
            if requested_tags.intersection({tag.lower() for tag in item.tag_list_json or []})
        ]
        if not dataset_items:
            raise ValueError("No dataset items matched the requested tag filter.")

    run_id = f"run_{uuid4().hex[:12]}"
    run_record = EvalRunRecord(
        run_id=run_id,
        agent_version_id=agent_version.agent_version_id,
        dataset_id=dataset.dataset_id,
        dataset_snapshot_id=dataset_snapshot.dataset_snapshot_id,
        dataset_checksum=dataset_snapshot.checksum,
        sample_group_id=sample_group_id,
        sample_index=sample_index,
        sample_count=sample_count,
        sampling_config_json=sampling_config or {},
        scorer_config_id=scorer_config.scorer_config_id,
        status=RunStatus.pending.value,
        adapter_type=payload.adapter_type,
        agent_version_snapshot_json=agent_version.model_dump(mode="json"),
        scorer_config_snapshot_json=scorer_config.model_dump(mode="json"),
        adapter_config_json=payload.adapter_config,
        dataset_tag_filter_json=payload.dataset_tag_filter,
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
                dataset_item_tags_json=list(item.tag_list_json or []),
                metadata_json={
                    **(item.metadata_json or {}),
                    "rubric_json": item.rubric_json,
                    "dataset_item_tags": list(item.tag_list_json or []),
                },
            )
        )

    session.commit()
    return EvalRunSchema(
        run_id=run_record.run_id,
        agent_version_id=run_record.agent_version_id,
        dataset_id=run_record.dataset_id,
        dataset_snapshot_id=run_record.dataset_snapshot_id,
        dataset_tag_filter=list(run_record.dataset_tag_filter_json or []),
        scorer_config_id=run_record.scorer_config_id,
        status=RunStatus(run_record.status),
        baseline=run_record.baseline,
        experiment_tag=run_record.experiment_tag,
        notes=run_record.notes,
        sampling=_sampling_metadata_schema(run_record),
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
            "sample_group_id": run.sample_group_id,
            "sample_index": run.sample_index,
            "sample_count": run.sample_count,
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
    agent_metadata = run.agent_version_snapshot_json.get("governance")
    scorer_governance = run.scorer_config_snapshot_json.get("governance")
    score.judge_audit_json = build_judge_audit(
        scorer_type=scorer_type,
        agent_metadata=agent_metadata if isinstance(agent_metadata, dict) else None,
        scorer_governance=scorer_governance if isinstance(scorer_governance, dict) else None,
        evidence=evidence,
    )
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


def _update_run_progress_counts(session: Session, run: EvalRunRecord) -> None:
    task_runs = _load_task_runs(session, run.run_id)
    run.total_tasks = len(task_runs)
    run.completed_tasks = sum(
        1 for task_run in task_runs if task_run.status == RunStatus.completed.value
    )
    run.failed_tasks = sum(1 for task_run in task_runs if task_run.status == RunStatus.failed.value)
    pending_tasks = sum(1 for task_run in task_runs if task_run.status == RunStatus.pending.value)
    if pending_tasks > 0:
        run.status = RunStatus.running.value
        run.completed_at = None


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
        _update_run_progress_counts(session, run)
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


def _candidate_agent_id(run: EvalRunRecord) -> str | None:
    raw_agent_id = run.agent_version_snapshot_json.get("agent_id")
    return str(raw_agent_id) if raw_agent_id is not None else None


def get_auto_compare(session: Session, run_id: str) -> AutoCompareSchema:
    candidate_run = session.get(EvalRunRecord, run_id)
    if candidate_run is None:
        raise LookupError("Run not found.")

    candidate_agent_id = _candidate_agent_id(candidate_run)
    baseline_statement = select(EvalRunRecord).where(
        EvalRunRecord.run_id != candidate_run.run_id,
        EvalRunRecord.dataset_id == candidate_run.dataset_id,
        EvalRunRecord.scorer_config_id == candidate_run.scorer_config_id,
    )
    candidate_runs = session.execute(
        baseline_statement.order_by(EvalRunRecord.baseline.desc(), EvalRunRecord.created_at.desc())
    ).scalars().all()

    filtered_runs = [
        run
        for run in candidate_runs
        if run.status in COMPARABLE_RUN_STATUSES
        and (candidate_agent_id is None or _candidate_agent_id(run) == candidate_agent_id)
        and (
            candidate_run.sample_group_id is None
            or run.sample_group_id != candidate_run.sample_group_id
        )
    ]

    selected_run: EvalRunRecord | None = None
    selection_reason: str | None = None

    for run in filtered_runs:
        if run.baseline:
            selected_run = run
            selection_reason = "latest_baseline"
            break
    if selected_run is None and filtered_runs:
        selected_run = filtered_runs[0]
        selection_reason = "latest_comparable_run"

    comparison: RunComparisonSchema | None = None
    if (
        selected_run is not None
        and candidate_run.status in COMPARABLE_RUN_STATUSES
        and selected_run.status in COMPARABLE_RUN_STATUSES
    ):
        comparison = get_run_comparison(session, selected_run.run_id, candidate_run.run_id)

    return AutoCompareSchema(
        baseline_run_id=selected_run.run_id if selected_run is not None else None,
        candidate_run_id=candidate_run.run_id,
        selection_reason=selection_reason,
        comparison=comparison.model_dump(mode="json") if comparison is not None else None,
    )


def create_quick_run(session: Session, payload: QuickRunRequestSchema) -> QuickRunResponseSchema:
    defaults = get_registry_defaults(session)
    if not defaults.default_dataset_id or not defaults.default_scorer_config_id:
        raise ValueError("Quick run defaults must be configured before launching a quick run.")

    run = create_run(
        session,
        RunCreateRequestSchema(
            dataset_id=defaults.default_dataset_id,
            agent_version_id=payload.agent_version_id,
            scorer_config_id=defaults.default_scorer_config_id,
            adapter_type=payload.adapter_type,
            adapter_config=payload.adapter_config,
            experiment_tag=payload.experiment_tag,
            notes=payload.notes,
        ),
    )
    detail = get_run_detail(session, run.run_id)
    return QuickRunResponseSchema(
        run=detail,
        auto_compare=get_auto_compare(session, run.run_id),
    )


def create_sampled_runs(
    session: Session,
    payload: SampledRunCreateRequestSchema,
) -> SampledRunCreateResponseSchema:
    overrides = list(payload.sampling.sample_overrides)
    if len(overrides) > payload.sampling.sample_count:
        raise ValueError("sample_overrides cannot exceed sample_count.")

    group_id = f"sample_group_{uuid4().hex[:12]}"
    created_runs: list[RunDetailSchema] = []

    for sample_index in range(1, payload.sampling.sample_count + 1):
        override = overrides[sample_index - 1] if sample_index - 1 < len(overrides) else {}
        merged_adapter_config = dict(payload.adapter_config)
        merged_adapter_config.update(override)
        run = _create_run(
            session,
            RunCreateRequestSchema(
                dataset_id=payload.dataset_id,
                agent_version_id=payload.agent_version_id,
                scorer_config_id=payload.scorer_config_id,
                dataset_tag_filter=payload.dataset_tag_filter,
                adapter_type=payload.adapter_type,
                adapter_config=merged_adapter_config,
                experiment_tag=payload.experiment_tag,
                notes=payload.notes,
            ),
            sample_group_id=group_id,
            sample_index=sample_index,
            sample_count=payload.sampling.sample_count,
            sampling_config={
                "sample_count": payload.sampling.sample_count,
                "sample_overrides_count": len(overrides),
            },
        )
        created_runs.append(get_run_detail(session, run.run_id))

    return SampledRunCreateResponseSchema(
        group_id=group_id,
        sample_count=payload.sampling.sample_count,
        runs=created_runs,
    )
