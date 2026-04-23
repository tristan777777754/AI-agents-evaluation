from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.calibration import CalibrationReportSchema, JudgeConsistencyReportSchema
from app.services.calibration import get_judge_consistency_report, get_latest_calibration_report

router = APIRouter()


@router.get("/latest", response_model=CalibrationReportSchema, status_code=status.HTTP_200_OK)
def get_latest_calibration() -> CalibrationReportSchema:
    try:
        return get_latest_calibration_report()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Golden set fixture not found.",
        ) from exc
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Calibration fixture is invalid: {exc}",
        ) from exc


@router.get(
    "/judge-consistency",
    response_model=JudgeConsistencyReportSchema,
    status_code=status.HTTP_200_OK,
)
def get_judge_consistency(
    baseline_run_id: Annotated[str, Query(...)],
    candidate_run_id: Annotated[str, Query(...)],
    session: Annotated[Session, Depends(get_session)],
) -> JudgeConsistencyReportSchema:
    try:
        return get_judge_consistency_report(
            session,
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
