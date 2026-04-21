from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import EvalRunRecord, EvalTaskRunRecord
from app.schemas.contracts import FailureReason, RunStatus
from app.schemas.summary import (
    DashboardCategorySummarySchema,
    DashboardFailedCaseSchema,
    DashboardFailureSummarySchema,
    RunDashboardSummarySchema,
)


def _round_metric(value: float) -> float:
    return round(value, 2)


def _round_cost(value: float) -> float:
    return round(value, 4)


def get_run_dashboard_summary(session: Session, run_id: str) -> RunDashboardSummarySchema:
    statement = (
        select(EvalRunRecord)
        .where(EvalRunRecord.run_id == run_id)
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalRunRecord.task_runs).selectinload(EvalTaskRunRecord.trace))
    )
    run = session.execute(statement).scalar_one_or_none()
    if run is None:
        raise LookupError("Run not found.")

    task_runs = sorted(run.task_runs, key=lambda task_run: task_run.sort_index)
    total_tasks = len(task_runs)
    successful_tasks = sum(
        1 for task_run in task_runs if task_run.status == RunStatus.completed.value
    )
    failed_tasks = total_tasks - successful_tasks
    review_needed_count = sum(
        1 for task_run in task_runs if task_run.score is not None and task_run.score.review_needed
    )

    latency_values = [
        float(task_run.latency_ms) for task_run in task_runs if task_run.latency_ms is not None
    ]
    average_latency_ms = (
        _round_metric(sum(latency_values) / len(latency_values)) if latency_values else None
    )
    total_cost = _round_cost(sum(float(task_run.cost or 0.0) for task_run in task_runs))
    success_rate = _round_metric((successful_tasks / total_tasks) * 100) if total_tasks else 0.0

    category_buckets: dict[str, list[EvalTaskRunRecord]] = defaultdict(list)
    failure_counts: dict[FailureReason, int] = defaultdict(int)
    failed_cases: list[DashboardFailedCaseSchema] = []

    for task_run in task_runs:
        category_buckets[task_run.category].append(task_run)
        failure_reason_value = task_run.trace.failure_reason if task_run.trace else None
        if not failure_reason_value:
            continue

        failure_reason = FailureReason(failure_reason_value)
        failure_counts[failure_reason] += 1
        failed_cases.append(
            DashboardFailedCaseSchema(
                task_run_id=task_run.task_run_id,
                run_id=task_run.run_id,
                dataset_item_id=task_run.dataset_item_id,
                category=task_run.category,
                failure_reason=failure_reason,
                error_message=task_run.error_message,
                final_output=task_run.final_output,
            )
        )

    category_breakdown = []
    for category, category_tasks in sorted(category_buckets.items()):
        category_total = len(category_tasks)
        category_successful = sum(
            1 for task_run in category_tasks if task_run.status == RunStatus.completed.value
        )
        category_latency_values = [
            float(task_run.latency_ms)
            for task_run in category_tasks
            if task_run.latency_ms is not None
        ]
        category_average_latency = (
            _round_metric(sum(category_latency_values) / len(category_latency_values))
            if category_latency_values
            else None
        )
        category_breakdown.append(
            DashboardCategorySummarySchema(
                category=category,
                total_tasks=category_total,
                successful_tasks=category_successful,
                failed_tasks=category_total - category_successful,
                success_rate=_round_metric((category_successful / category_total) * 100)
                if category_total
                else 0.0,
                average_latency_ms=category_average_latency,
                total_cost=_round_cost(
                    sum(float(task_run.cost or 0.0) for task_run in category_tasks)
                ),
            )
        )

    failure_breakdown = [
        DashboardFailureSummarySchema(failure_reason=failure_reason, count=count)
        for failure_reason, count in sorted(
            failure_counts.items(), key=lambda item: (-item[1], item[0].value)
        )
    ]

    return RunDashboardSummarySchema(
        run_id=run.run_id,
        agent_version_id=run.agent_version_id,
        dataset_id=run.dataset_id,
        scorer_config_id=run.scorer_config_id,
        status=RunStatus(run.status),
        total_tasks=total_tasks,
        successful_tasks=successful_tasks,
        failed_tasks=failed_tasks,
        review_needed_count=review_needed_count,
        success_rate=success_rate,
        average_latency_ms=average_latency_ms,
        total_cost=total_cost,
        category_breakdown=category_breakdown,
        failure_breakdown=failure_breakdown,
        failed_cases=failed_cases,
    )
