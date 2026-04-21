from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.run import EvalTaskRunRecord


class ReviewRecord(Base):
    __tablename__ = "reviews"

    review_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(
        ForeignKey("eval_task_runs.task_run_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    reviewer_id: Mapped[str] = mapped_column(String(120), nullable=False)
    verdict: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    note: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    task_run: Mapped["EvalTaskRunRecord"] = relationship(back_populates="review")
