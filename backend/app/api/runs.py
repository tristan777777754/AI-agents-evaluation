from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
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
from app.services.runs import (
    InvalidStateTransitionError,
    create_run,
    get_run_detail,
    get_run_tasks,
    list_runs,
    repair_run_aggregation,
    rerun_run,
    update_run_status,
)
from app.services.summary import get_run_dashboard_summary
from app.worker.tasks import execute_run_task

router = APIRouter()
RunSession = Annotated[Session, Depends(get_session)]
StatusPayload = Annotated[dict[str, str], Body(...)]


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


@router.post("/{run_id}/rerun", response_model=RunDetailSchema)
def rerun_eval_run(run_id: str, session: RunSession) -> RunDetailSchema:
    try:
        return rerun_run(session, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{run_id}/repair", response_model=RunDetailSchema)
def repair_eval_run(run_id: str, session: RunSession) -> RunDetailSchema:
    try:
        return repair_run_aggregation(session, run_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/{run_id}/status", response_model=RunDetailSchema)
def update_eval_run_status(
    run_id: str,
    payload: StatusPayload,
    session: RunSession,
) -> RunDetailSchema:
    target_status = payload.get("status", "")
    try:
        return update_run_status(session, run_id, target_status)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found.") from exc
    except InvalidStateTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


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
