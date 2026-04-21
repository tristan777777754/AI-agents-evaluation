from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.calibration import CalibrationReportSchema
from app.services.calibration import get_latest_calibration_report

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
