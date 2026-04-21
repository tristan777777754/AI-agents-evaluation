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
def get_review_queue(session: ReviewSession) -> ReviewQueueSchema:
    return list_review_queue(session)
