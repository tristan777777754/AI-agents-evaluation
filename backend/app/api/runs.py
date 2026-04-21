from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.compare import RunComparisonSchema
from app.schemas.runs import (
    RunCreateRequestSchema,
    RunDetailSchema,
    RunSummarySchema,
    RunTaskListSchema,
)
from app.schemas.summary import RunDashboardSummarySchema
from app.services.compare import get_run_comparison
from app.services.runs import create_run, get_run_detail, get_run_tasks, list_runs
from app.services.summary import get_run_dashboard_summary
from app.worker.tasks import execute_run_task

router = APIRouter()
RunSession = Annotated[Session, Depends(get_session)]


@router.post("", response_model=RunDetailSchema, status_code=status.HTTP_201_CREATED)
def create_eval_run(payload: RunCreateRequestSchema, session: RunSession) -> RunDetailSchema:
    try:
        run = create_run(session, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        execute_run_task.delay(run.run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return get_run_detail(session, run.run_id)


@router.get("", response_model=list[RunSummarySchema])
def get_runs(session: RunSession) -> list[RunSummarySchema]:
    return list_runs(session)


@router.get("/compare", response_model=RunComparisonSchema)
def compare_runs(
    baseline_run_id: str,
    candidate_run_id: str,
    session: RunSession,
) -> RunComparisonSchema:
    try:
        return get_run_comparison(session, baseline_run_id, candidate_run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{run_id}", response_model=RunDetailSchema)
def get_run(run_id: str, session: RunSession) -> RunDetailSchema:
    try:
        return get_run_detail(session, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc


@router.get("/{run_id}/tasks", response_model=RunTaskListSchema)
def get_run_task_list(run_id: str, session: RunSession) -> RunTaskListSchema:
    try:
        return get_run_tasks(session, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc


@router.get("/{run_id}/summary", response_model=RunDashboardSummarySchema)
def get_run_summary(run_id: str, session: RunSession) -> RunDashboardSummarySchema:
    try:
        return get_run_dashboard_summary(session, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
