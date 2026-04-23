from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentRecord(Base):
    __tablename__ = "agents"

    agent_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text(), nullable=True)
    owner_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class AgentVersionRecord(Base):
    __tablename__ = "agent_versions"

    agent_version_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    config_json: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class ScorerConfigRecord(Base):
    __tablename__ = "scorer_configs"

    scorer_config_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(120), nullable=False)
    weights_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    judge_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    judge_provider: Mapped[str | None] = mapped_column(String(120), nullable=True)
    thresholds_json: Mapped[dict[str, float]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class RegistryDefaultsRecord(Base):
    __tablename__ = "registry_defaults"

    defaults_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    default_dataset_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_scorer_config_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
