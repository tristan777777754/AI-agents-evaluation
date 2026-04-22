from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import EvalRunRecord, EvalTaskRunRecord
from app.schemas.compare import (
    CompareCaseSchema,
    CompareCategoryDeltaSchema,
    CompareConfidenceIntervalSchema,
    CompareCredibilitySchema,
    CompareLineageSchema,
    CompareMetricDeltaSchema,
    CompareRunLineageSchema,
    RunComparisonSchema,
)
from app.schemas.contracts import FailureReason, RunStatus
from app.services.scoring import normal_cdf
from app.services.summary import get_run_dashboard_summary

COMPARABLE_RUN_STATUSES = {RunStatus.completed.value, RunStatus.partial_success.value}


def _round_metric(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 2)


def _metric_delta(
    baseline: float | int | None,
    candidate: float | int | None,
) -> CompareMetricDeltaSchema:
    baseline_value = float(baseline) if baseline is not None else None
    candidate_value = float(candidate) if candidate is not None else None
    delta = None
    if baseline_value is not None and candidate_value is not None:
        delta = round(candidate_value - baseline_value, 2)
    return CompareMetricDeltaSchema(
        baseline=baseline_value,
        candidate=candidate_value,
        delta=delta,
    )


def _task_passed(task_run: EvalTaskRunRecord) -> bool:
    if task_run.score is not None:
        return task_run.score.pass_fail
    return task_run.status == RunStatus.completed.value


def _failure_reason(task_run: EvalTaskRunRecord) -> FailureReason | None:
    if task_run.trace is None or task_run.trace.failure_reason is None:
        return None
    return FailureReason(task_run.trace.failure_reason)


def _snapshot_hash(payload: dict[str, object]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:12]


def _run_lineage_schema(run: EvalRunRecord) -> CompareRunLineageSchema:
    return CompareRunLineageSchema(
        run_id=run.run_id,
        dataset_id=run.dataset_id,
        dataset_snapshot_id=run.dataset_snapshot_id,
        agent_version_id=run.agent_version_id,
        agent_version_snapshot_hash=_snapshot_hash(run.agent_version_snapshot_json),
        scorer_config_id=run.scorer_config_id,
        scorer_snapshot_hash=_snapshot_hash(run.scorer_config_snapshot_json),
        baseline=run.baseline,
        experiment_tag=run.experiment_tag,
    )


def _case_schema(
    baseline_task: EvalTaskRunRecord,
    candidate_task: EvalTaskRunRecord,
) -> CompareCaseSchema:
    return CompareCaseSchema(
        dataset_item_id=baseline_task.dataset_item_id,
        category=baseline_task.category,
        baseline_task_run_id=baseline_task.task_run_id,
        candidate_task_run_id=candidate_task.task_run_id,
        baseline_status=RunStatus(baseline_task.status),
        candidate_status=RunStatus(candidate_task.status),
        baseline_failure_reason=_failure_reason(baseline_task),
        candidate_failure_reason=_failure_reason(candidate_task),
        baseline_final_output=baseline_task.final_output,
        candidate_final_output=candidate_task.final_output,
    )


def _paired_binary_credibility(
    baseline_tasks: list[EvalTaskRunRecord],
    candidate_tasks: list[EvalTaskRunRecord],
) -> CompareCredibilitySchema:
    sample_size = min(len(baseline_tasks), len(candidate_tasks))
    if sample_size == 0:
        return CompareCredibilitySchema(
            label="inconclusive",
            sample_size=0,
            confidence_interval=CompareConfidenceIntervalSchema(lower=None, upper=None),
            p_value=None,
            is_significant=False,
        )

    deltas = [
        float(_task_passed(candidate_task)) - float(_task_passed(baseline_task))
        for baseline_task, candidate_task in zip(baseline_tasks, candidate_tasks, strict=True)
    ]
    mean = sum(deltas) / sample_size
    if sample_size > 1:
        variance = sum((delta - mean) ** 2 for delta in deltas) / (sample_size - 1)
        std_error = math.sqrt(variance / sample_size)
    else:
        std_error = 0.0

    margin = 1.96 * std_error * 100
    mean_percentage = mean * 100
    if std_error == 0.0:
        p_value = 0.0 if mean != 0 else 1.0
    else:
        z_score = mean / std_error
        p_value = round(max(0.0, min(1.0, 2 * (1 - normal_cdf(abs(z_score))))), 4)

    is_significant = bool(p_value < 0.05)
    if is_significant and mean_percentage > 0:
        label = "statistically_significant_improvement"
    elif is_significant and mean_percentage < 0:
        label = "statistically_significant_regression"
    elif mean_percentage > 0:
        label = "directional_improvement"
    elif mean_percentage < 0:
        label = "directional_regression"
    else:
        label = "inconclusive"

    return CompareCredibilitySchema(
        label=label,
        sample_size=sample_size,
        confidence_interval=CompareConfidenceIntervalSchema(
            lower=round(mean_percentage - margin, 2),
            upper=round(mean_percentage + margin, 2),
        ),
        p_value=p_value,
        is_significant=is_significant,
    )


def get_run_comparison(
    session: Session,
    baseline_run_id: str,
    candidate_run_id: str,
) -> RunComparisonSchema:
    if baseline_run_id == candidate_run_id:
        raise ValueError("Baseline and candidate runs must be different.")

    statement = (
        select(EvalRunRecord)
        .where(EvalRunRecord.run_id.in_([baseline_run_id, candidate_run_id]))
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.trace))
    )
    runs = session.execute(statement).scalars().all()
    run_by_id = {run.run_id: run for run in runs}

    baseline_run = run_by_id.get(baseline_run_id)
    candidate_run = run_by_id.get(candidate_run_id)
    if baseline_run is None or candidate_run is None:
        raise LookupError("Run not found.")

    if baseline_run.dataset_id != candidate_run.dataset_id:
        raise ValueError("Runs must use the same dataset for comparison.")

    if (
        baseline_run.status not in COMPARABLE_RUN_STATUSES
        or candidate_run.status not in COMPARABLE_RUN_STATUSES
    ):
        raise ValueError("Only completed or partial-success runs can be compared.")

    baseline_summary = get_run_dashboard_summary(session, baseline_run_id)
    candidate_summary = get_run_dashboard_summary(session, candidate_run_id)

    baseline_tasks = {task.dataset_item_id: task for task in baseline_run.task_runs}
    candidate_tasks = {task.dataset_item_id: task for task in candidate_run.task_runs}
    common_ids = sorted(set(baseline_tasks) & set(candidate_tasks))
    if not common_ids:
        raise ValueError("Runs do not share comparable dataset items.")

    improvements: list[CompareCaseSchema] = []
    regressions: list[CompareCaseSchema] = []
    category_pairs: dict[str, list[tuple[EvalTaskRunRecord, EvalTaskRunRecord]]] = defaultdict(list)
    paired_tasks: list[tuple[EvalTaskRunRecord, EvalTaskRunRecord]] = []

    for dataset_item_id in common_ids:
        baseline_task = baseline_tasks[dataset_item_id]
        candidate_task = candidate_tasks[dataset_item_id]
        category_pairs[baseline_task.category].append((baseline_task, candidate_task))
        paired_tasks.append((baseline_task, candidate_task))

        baseline_passed = _task_passed(baseline_task)
        candidate_passed = _task_passed(candidate_task)
        if not baseline_passed and candidate_passed:
            improvements.append(_case_schema(baseline_task, candidate_task))
        elif baseline_passed and not candidate_passed:
            regressions.append(_case_schema(baseline_task, candidate_task))

    category_deltas = []
    for category, pairs in sorted(category_pairs.items()):
        baseline_total = len(pairs)
        candidate_total = len(pairs)
        baseline_successful = sum(1 for baseline_task, _ in pairs if _task_passed(baseline_task))
        candidate_successful = sum(1 for _, candidate_task in pairs if _task_passed(candidate_task))
        baseline_success_rate = round((baseline_successful / baseline_total) * 100, 2)
        candidate_success_rate = round((candidate_successful / candidate_total) * 100, 2)
        category_deltas.append(
            CompareCategoryDeltaSchema(
                category=category,
                baseline_total_tasks=baseline_total,
                candidate_total_tasks=candidate_total,
                baseline_success_rate=baseline_success_rate,
                candidate_success_rate=candidate_success_rate,
                success_rate_delta=round(candidate_success_rate - baseline_success_rate, 2),
                baseline_failed_tasks=baseline_total - baseline_successful,
                candidate_failed_tasks=candidate_total - candidate_successful,
            )
        )

    credibility = _paired_binary_credibility(
        [baseline_task for baseline_task, _ in paired_tasks],
        [candidate_task for _, candidate_task in paired_tasks],
    )

    return RunComparisonSchema(
        baseline_run_id=baseline_run.run_id,
        candidate_run_id=candidate_run.run_id,
        baseline_agent_version_id=baseline_run.agent_version_id,
        candidate_agent_version_id=candidate_run.agent_version_id,
        baseline_status=RunStatus(baseline_run.status),
        candidate_status=RunStatus(candidate_run.status),
        compared_task_count=len(common_ids),
        sample_size=credibility.sample_size,
        improvement_count=len(improvements),
        regression_count=len(regressions),
        confidence_interval=credibility.confidence_interval,
        p_value=credibility.p_value,
        is_significant=credibility.is_significant,
        success_rate=_metric_delta(baseline_summary.success_rate, candidate_summary.success_rate),
        average_latency_ms=_metric_delta(
            baseline_summary.average_latency_ms,
            candidate_summary.average_latency_ms,
        ),
        total_cost=_metric_delta(baseline_summary.total_cost, candidate_summary.total_cost),
        review_needed_count=_metric_delta(
            baseline_summary.review_needed_count,
            candidate_summary.review_needed_count,
        ),
        credibility=credibility,
        lineage=CompareLineageSchema(
            baseline=_run_lineage_schema(baseline_run),
            candidate=_run_lineage_schema(candidate_run),
        ),
        category_deltas=category_deltas,
        improvements=improvements,
        regressions=regressions,
    )
