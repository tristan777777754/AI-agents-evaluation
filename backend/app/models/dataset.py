from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class DatasetRecord(Base):
    __tablename__ = "datasets"

    dataset_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    latest_snapshot_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    snapshots: Mapped[list["DatasetSnapshotRecord"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetSnapshotRecord.version_number",
    )
    items: Mapped[list["DatasetItemRecord"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetItemRecord.sort_index",
    )


class DatasetSnapshotRecord(Base):
    __tablename__ = "dataset_snapshots"

    dataset_snapshot_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.dataset_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    dataset: Mapped[DatasetRecord] = relationship(back_populates="snapshots")
    items: Mapped[list["DatasetItemRecord"]] = relationship(
        back_populates="snapshot",
        cascade="all, delete-orphan",
        order_by="DatasetItemRecord.sort_index",
    )


class DatasetItemRecord(Base):
    __tablename__ = "dataset_items"
    __table_args__ = (
        UniqueConstraint(
            "dataset_snapshot_id",
            "dataset_item_id",
            name="uq_dataset_items_snapshot_and_item_id",
        ),
    )

    dataset_item_record_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    dataset_item_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(
        ForeignKey("datasets.dataset_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_snapshot_id: Mapped[str] = mapped_column(
        ForeignKey("dataset_snapshots.dataset_snapshot_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sort_index: Mapped[int] = mapped_column(Integer, nullable=False)
    input_text: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(64), nullable=True)
    expected_output: Mapped[str | None] = mapped_column(Text(), nullable=True)
    rubric_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    reference_context: Mapped[str | None] = mapped_column(Text(), nullable=True)
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)

    dataset: Mapped[DatasetRecord] = relationship(back_populates="items")
    snapshot: Mapped[DatasetSnapshotRecord] = relationship(back_populates="items")
