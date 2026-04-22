from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.datasets import DatasetPromotionRequestSchema, DatasetPromotionResultSchema
from app.schemas.reviews import ReviewDetailSchema, ReviewUpsertRequestSchema
from app.schemas.traces import TaskRunDetailSchema, TraceDetailSchema
from app.services.datasets import promote_failed_case
from app.services.reviews import upsert_task_review
from app.services.traces import get_task_run_detail, get_trace_detail

router = APIRouter()
TaskRunSession = Annotated[Session, Depends(get_session)]


@router.get("/{task_run_id}", response_model=TaskRunDetailSchema)
def get_task_run(task_run_id: str, session: TaskRunSession) -> TaskRunDetailSchema:
    try:
        return get_task_run_detail(session, task_run_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task run not found.",
        ) from exc


@router.get("/{task_run_id}/trace", response_model=TraceDetailSchema)
def get_task_trace(task_run_id: str, session: TaskRunSession) -> TraceDetailSchema:
    try:
        return get_trace_detail(session, task_run_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found.",
        ) from exc


@router.put("/{task_run_id}/review", response_model=ReviewDetailSchema)
def put_task_review(
    task_run_id: str,
    payload: ReviewUpsertRequestSchema,
    session: TaskRunSession,
) -> ReviewDetailSchema:
    try:
        return upsert_task_review(session, task_run_id, payload)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task run not found.",
        ) from exc


@router.post("/{task_run_id}/promote", response_model=DatasetPromotionResultSchema)
def promote_task_run_to_dataset(
    task_run_id: str,
    payload: DatasetPromotionRequestSchema,
    session: TaskRunSession,
) -> DatasetPromotionResultSchema:
    try:
        return promote_failed_case(session, task_run_id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
