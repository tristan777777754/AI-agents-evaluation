from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.contracts import FailureReason


class ReviewUpsertRequestSchema(BaseModel):
    reviewer_id: str = Field(..., examples=["reviewer_demo"])
    verdict: str | None = Field(default=None, examples=["confirmed_issue"])
    failure_label: str | None = Field(default=None, examples=["tool_error"])
    note: str | None = None


class ReviewDetailSchema(BaseModel):
    review_id: str = Field(..., examples=["review_001"])
    task_run_id: str
    run_id: str
    dataset_item_id: str
    reviewer_id: str
    verdict: str | None = None
    failure_label: str | None = None
    note: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ReviewQueueItemSchema(BaseModel):
    task_run_id: str
    run_id: str
    dataset_item_id: str
    category: str
    input_text: str
    status: str
    review_needed: bool
    failure_reason: FailureReason | None = None
    error_message: str | None = None
    final_output: str | None = None
    review_status: str
    review: ReviewDetailSchema | None = None


class ReviewQueueSchema(BaseModel):
    total_count: int
    pending_count: int
    reviewed_count: int
    page: int = 1
    per_page: int
    has_next_page: bool = False
    items: list[ReviewQueueItemSchema]
