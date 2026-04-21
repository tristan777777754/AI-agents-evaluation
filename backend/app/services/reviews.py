from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import EvalTaskRunRecord, ReviewRecord
from app.schemas.contracts import FailureReason
from app.schemas.reviews import (
    ReviewDetailSchema,
    ReviewQueueItemSchema,
    ReviewQueueSchema,
    ReviewUpsertRequestSchema,
)


def _utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def _review_schema(review: ReviewRecord, task_run: EvalTaskRunRecord) -> ReviewDetailSchema:
    return ReviewDetailSchema(
        review_id=review.review_id,
        task_run_id=task_run.task_run_id,
        run_id=task_run.run_id,
        dataset_item_id=task_run.dataset_item_id,
        reviewer_id=review.reviewer_id,
        verdict=review.verdict,
        failure_label=review.failure_label,
        note=review.note,
        created_at=_utc_iso(review.created_at),
        updated_at=_utc_iso(review.updated_at),
    )


def get_task_review(session: Session, task_run_id: str) -> ReviewDetailSchema | None:
    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.task_run_id == task_run_id)
        .options(selectinload(EvalTaskRunRecord.review))
    )
    task_run = session.execute(statement).scalar_one_or_none()
    if task_run is None:
        raise LookupError("Task run not found.")
    if task_run.review is None:
        return None
    return _review_schema(task_run.review, task_run)


def upsert_task_review(
    session: Session,
    task_run_id: str,
    payload: ReviewUpsertRequestSchema,
) -> ReviewDetailSchema:
    statement = (
        select(EvalTaskRunRecord)
        .where(EvalTaskRunRecord.task_run_id == task_run_id)
        .options(selectinload(EvalTaskRunRecord.review))
    )
    task_run = session.execute(statement).scalar_one_or_none()
    if task_run is None:
        raise LookupError("Task run not found.")

    review = task_run.review
    if review is None:
        review = ReviewRecord(
            review_id=f"review_{uuid4().hex[:12]}",
            task_run_id=task_run.task_run_id,
            reviewer_id=payload.reviewer_id,
            verdict=payload.verdict,
            failure_label=payload.failure_label,
            note=payload.note,
        )
        session.add(review)
    else:
        review.reviewer_id = payload.reviewer_id
        review.verdict = payload.verdict
        review.failure_label = payload.failure_label
        review.note = payload.note

    session.commit()
    session.refresh(review)
    return _review_schema(review, task_run)


def list_review_queue(session: Session) -> ReviewQueueSchema:
    statement = (
        select(EvalTaskRunRecord)
        .options(selectinload(EvalTaskRunRecord.score))
        .options(selectinload(EvalTaskRunRecord.trace))
        .options(selectinload(EvalTaskRunRecord.review))
        .where(EvalTaskRunRecord.score.has(review_needed=True))
        .order_by(EvalTaskRunRecord.run_id.desc(), EvalTaskRunRecord.sort_index.asc())
    )
    task_runs = session.execute(statement).scalars().all()

    items: list[ReviewQueueItemSchema] = []
    pending_count = 0
    reviewed_count = 0

    for task_run in task_runs:
        review = task_run.review
        review_status = "reviewed" if review and review.verdict else "pending"
        if review_status == "pending":
            pending_count += 1
        else:
            reviewed_count += 1

        items.append(
            ReviewQueueItemSchema(
                task_run_id=task_run.task_run_id,
                run_id=task_run.run_id,
                dataset_item_id=task_run.dataset_item_id,
                category=task_run.category,
                input_text=task_run.input_text,
                status=task_run.status,
                review_needed=bool(task_run.score and task_run.score.review_needed),
                failure_reason=(
                    FailureReason(task_run.trace.failure_reason)
                    if task_run.trace and task_run.trace.failure_reason
                    else None
                ),
                error_message=task_run.error_message,
                final_output=task_run.final_output,
                review_status=review_status,
                review=_review_schema(review, task_run) if review is not None else None,
            )
        )

    return ReviewQueueSchema(
        total_count=len(items),
        pending_count=pending_count,
        reviewed_count=reviewed_count,
        items=items,
    )
