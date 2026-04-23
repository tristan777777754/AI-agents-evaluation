from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.reviews import ReviewQueueSchema
from app.services.reviews import list_review_queue

router = APIRouter()
ReviewSession = Annotated[Session, Depends(get_session)]


@router.get("/queue", response_model=ReviewQueueSchema)
def get_review_queue(
    session: ReviewSession,
    page: int = 1,
    per_page: int = 25,
    review_status: str | None = None,
    failure_reason: str | None = None,
) -> ReviewQueueSchema:
    return list_review_queue(
        session,
        page=max(page, 1),
        per_page=min(max(per_page, 1), 100),
        review_status=review_status,
        failure_reason=failure_reason,
    )
