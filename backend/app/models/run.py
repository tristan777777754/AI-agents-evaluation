from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.review import ReviewRecord
    from app.models.trace import TraceRecord


class EvalRunRecord(Base):
    __tablename__ = "eval_runs"

    run_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    agent_version_id: Mapped[str] = mapped_column(String(120), nullable=False)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.dataset_id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    dataset_snapshot_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    dataset_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scorer_config_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    adapter_type: Mapped[str] = mapped_column(String(64), nullable=False, default="stub")
    agent_version_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    scorer_config_snapshot_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    adapter_config_json: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    total_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    baseline: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    experiment_tag: Mapped[str | None] = mapped_column(String(120), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    task_runs: Mapped[list["EvalTaskRunRecord"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="EvalTaskRunRecord.sort_index",
    )


class EvalTaskRunRecord(Base):
    __tablename__ = "eval_task_runs"

    task_run_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("eval_runs.run_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_item_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    sort_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    input_text: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text(), nullable=True)
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    final_output: Mapped[str | None] = mapped_column(Text(), nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_usage: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float(), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text(), nullable=True)
    trace_preview_json: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped[EvalRunRecord] = relationship(back_populates="task_runs")
    score: Mapped["ScoreRecord | None"] = relationship(
        back_populates="task_run",
        cascade="all, delete-orphan",
        uselist=False,
    )
    trace: Mapped[TraceRecord | None] = relationship(
        back_populates="task_run",
        cascade="all, delete-orphan",
        uselist=False,
    )
    review: Mapped["ReviewRecord | None"] = relationship(
        back_populates="task_run",
        cascade="all, delete-orphan",
        uselist=False,
    )


class ScoreRecord(Base):
    __tablename__ = "scores"

    score_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    task_run_id: Mapped[str] = mapped_column(
        ForeignKey("eval_task_runs.task_run_id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    correctness: Mapped[float | None] = mapped_column(Float(), nullable=True)
    tool_use: Mapped[float | None] = mapped_column(Float(), nullable=True)
    formatting: Mapped[float | None] = mapped_column(Float(), nullable=True)
    pass_fail: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    review_needed: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
    evidence_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)

    task_run: Mapped[EvalTaskRunRecord] = relationship(back_populates="score")
