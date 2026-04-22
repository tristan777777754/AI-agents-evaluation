from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.compare import TraceComparisonSchema
from app.services.trace_intelligence import get_trace_comparison

router = APIRouter()
CompareSession = Annotated[Session, Depends(get_session)]


@router.get("/traces", response_model=TraceComparisonSchema)
def compare_traces(
    baseline: str,
    candidate: str,
    dataset_item_id: str,
    session: CompareSession,
) -> TraceComparisonSchema:
    try:
        return get_trace_comparison(
            session,
            baseline_run_id=baseline,
            candidate_run_id=candidate,
            dataset_item_id=dataset_item_id,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
