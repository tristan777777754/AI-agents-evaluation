from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.run import EvalRunRecord, EvalTaskRunRecord


class TraceRecord(Base):
    __tablename__ = "traces"

    trace_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(
        ForeignKey("eval_task_runs.task_run_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    run_id: Mapped[str] = mapped_column(
        ForeignKey("eval_runs.run_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    step_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tool_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    storage_path: Mapped[str] = mapped_column(Text(), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    events_json: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    task_run: Mapped[EvalTaskRunRecord] = relationship(back_populates="trace")
    run: Mapped[EvalRunRecord] = relationship()
