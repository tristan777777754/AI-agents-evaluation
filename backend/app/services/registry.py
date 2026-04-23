from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AgentRecord,
    AgentVersionRecord,
    DatasetRecord,
    RegistryDefaultsRecord,
    ScorerConfigRecord,
)
from app.schemas.contracts import (
    AgentSchema,
    AgentVersionSchema,
    GovernedModelRoleSchema,
    ScorerConfigSchema,
    ScorerGovernanceSchema,
)
from app.schemas.registry import (
    AgentCreateRequestSchema,
    AgentVersionCreateRequestSchema,
    RegistryDefaultsSchema,
    RegistryDefaultsUpdateRequestSchema,
    RegistryListSchema,
)
from app.services.scoring import provider_from_model_name

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
DEFAULTS_ROW_ID = "default"


def _read_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _utc_iso(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _humanize_agent_name(agent_id: str) -> str:
    parts = [part for part in agent_id.replace("-", "_").split("_") if part and part != "agent"]
    if not parts:
        return agent_id
    return " ".join(part.capitalize() for part in parts)


def _agent_schema(record: AgentRecord) -> AgentSchema:
    return AgentSchema(
        agent_id=record.agent_id,
        name=record.name,
        description=record.description,
        owner_id=record.owner_id,
        created_at=_utc_iso(record.created_at),
    )


def _agent_version_schema(record: AgentVersionRecord) -> AgentVersionSchema:
    prompt_id_raw = None
    prompt_version_raw = None
    if isinstance(record.config_json, dict):
        prompt_id_raw = record.config_json.get("prompt_id")
        prompt_version_raw = record.config_json.get("prompt_version")
    provider = provider_from_model_name(record.model)
    governance = {
        "role": "agent",
        "provider": provider,
        "model": record.model,
        "prompt_id": (
            str(prompt_id_raw) if prompt_id_raw is not None else record.agent_version_id
        ),
        "prompt_version": (
            str(prompt_version_raw) if prompt_version_raw is not None else record.version_name
        ),
        "prompt_hash": record.prompt_hash,
        "credential_mode": "platform_managed",
        "reasoning_available": None,
    }
    return AgentVersionSchema(
        agent_version_id=record.agent_version_id,
        agent_id=record.agent_id,
        version_name=record.version_name,
        model=record.model,
        provider=provider,
        prompt_hash=record.prompt_hash,
        config_json=dict(record.config_json or {}),
        created_at=_utc_iso(record.created_at),
        governance=GovernedModelRoleSchema.model_validate(governance),
    )


def _scorer_config_schema(record: ScorerConfigRecord) -> ScorerConfigSchema:
    return ScorerConfigSchema(
        scorer_config_id=record.scorer_config_id,
        name=record.name,
        type=record.type,
        weights_json=dict(record.weights_json or {}),
        judge_model=record.judge_model,
        judge_provider=record.judge_provider,
        thresholds_json=dict(record.thresholds_json or {}),
        governance=(
            ScorerGovernanceSchema.model_validate(record.governance_json)
            if record.governance_json
            else None
        ),
    )


def ensure_registry_seeded(session: Session) -> None:
    if session.get(RegistryDefaultsRecord, DEFAULTS_ROW_ID) is None:
        session.add(RegistryDefaultsRecord(defaults_id=DEFAULTS_ROW_ID))

    existing_agent_ids = {
        agent_id
        for agent_id in session.execute(select(AgentRecord.agent_id)).scalars().all()
    }
    existing_agent_version_ids = {
        agent_version_id
        for agent_version_id in session.execute(
            select(AgentVersionRecord.agent_version_id)
        ).scalars().all()
    }
    existing_scorer_ids = {
        scorer_config_id
        for scorer_config_id in session.execute(
            select(ScorerConfigRecord.scorer_config_id)
        ).scalars().all()
    }

    fixture_agent_versions = [
        AgentVersionSchema.model_validate(_read_fixture("agent_version_v1.json")),
        AgentVersionSchema.model_validate(_read_fixture("agent_version_v2.json")),
    ]
    for fixture_version in fixture_agent_versions:
        if fixture_version.agent_id not in existing_agent_ids:
            session.add(
                AgentRecord(
                    agent_id=fixture_version.agent_id,
                    name=_humanize_agent_name(fixture_version.agent_id),
                )
            )
            existing_agent_ids.add(fixture_version.agent_id)
        if fixture_version.agent_version_id not in existing_agent_version_ids:
            session.add(
                AgentVersionRecord(
                    agent_version_id=fixture_version.agent_version_id,
                    agent_id=fixture_version.agent_id,
                    version_name=fixture_version.version_name,
                    model=fixture_version.model,
                    prompt_hash=fixture_version.prompt_hash,
                    config_json=fixture_version.config_json,
                )
            )
            existing_agent_version_ids.add(fixture_version.agent_version_id)

    for fixture_name in (
        "scorer_config.json",
        "scorer_config_keyword_overlap.json",
        "scorer_config_llm_judge.json",
        "scorer_config_rubric_based.json",
    ):
        fixture_scorer = ScorerConfigSchema.model_validate(_read_fixture(fixture_name))
        if fixture_scorer.scorer_config_id not in existing_scorer_ids:
            session.add(
                ScorerConfigRecord(
                    scorer_config_id=fixture_scorer.scorer_config_id,
                    name=fixture_scorer.name,
                    type=fixture_scorer.type,
                    weights_json=fixture_scorer.weights_json,
                    judge_model=fixture_scorer.judge_model,
                    judge_provider=fixture_scorer.judge_provider,
                    thresholds_json=fixture_scorer.thresholds_json,
                    governance_json=(
                        fixture_scorer.governance.model_dump(mode="json")
                        if fixture_scorer.governance is not None
                        else {}
                    ),
                )
            )
            existing_scorer_ids.add(fixture_scorer.scorer_config_id)

    session.commit()

    defaults = session.get(RegistryDefaultsRecord, DEFAULTS_ROW_ID)
    if defaults is None:
        raise LookupError("Registry defaults could not be initialized.")
    if defaults.default_dataset_id is None:
        defaults.default_dataset_id = session.scalar(
            select(DatasetRecord.dataset_id)
            .where(DatasetRecord.lifecycle_status == "published")
            .order_by(DatasetRecord.created_at.asc())
            .limit(1)
        )
    if defaults.default_scorer_config_id is None:
        defaults.default_scorer_config_id = session.scalar(
            select(ScorerConfigRecord.scorer_config_id)
            .order_by(ScorerConfigRecord.created_at.asc())
            .limit(1)
        )
    session.commit()


def list_agents(session: Session) -> list[AgentSchema]:
    ensure_registry_seeded(session)
    agents = session.execute(
        select(AgentRecord).order_by(AgentRecord.created_at.asc())
    ).scalars().all()
    return [_agent_schema(agent) for agent in agents]


def list_agent_versions(
    session: Session,
    *,
    agent_id: str | None = None,
) -> list[AgentVersionSchema]:
    ensure_registry_seeded(session)
    statement = select(AgentVersionRecord)
    if agent_id:
        statement = statement.where(AgentVersionRecord.agent_id == agent_id)
    versions = session.execute(
        statement.order_by(
            AgentVersionRecord.created_at.desc(),
            AgentVersionRecord.agent_version_id.asc(),
        )
    ).scalars().all()
    return [_agent_version_schema(version) for version in versions]


def list_scorer_configs(session: Session) -> list[ScorerConfigSchema]:
    ensure_registry_seeded(session)
    scorers = session.execute(
        select(ScorerConfigRecord).order_by(ScorerConfigRecord.created_at.asc())
    ).scalars().all()
    return [_scorer_config_schema(scorer) for scorer in scorers]


def get_registry_defaults(session: Session) -> RegistryDefaultsSchema:
    ensure_registry_seeded(session)
    defaults = session.get(RegistryDefaultsRecord, DEFAULTS_ROW_ID)
    if defaults is None:
        raise LookupError("Registry defaults not found.")
    return RegistryDefaultsSchema(
        default_dataset_id=defaults.default_dataset_id,
        default_scorer_config_id=defaults.default_scorer_config_id,
    )


def update_registry_defaults(
    session: Session,
    payload: RegistryDefaultsUpdateRequestSchema,
) -> RegistryDefaultsSchema:
    ensure_registry_seeded(session)
    defaults = session.get(RegistryDefaultsRecord, DEFAULTS_ROW_ID)
    if defaults is None:
        raise LookupError("Registry defaults not found.")

    if (
        payload.default_dataset_id is not None
        and session.get(DatasetRecord, payload.default_dataset_id) is None
    ):
        raise LookupError("Default dataset not found.")
    if (
        payload.default_scorer_config_id is not None
        and session.get(ScorerConfigRecord, payload.default_scorer_config_id) is None
    ):
        raise LookupError("Default scorer config not found.")

    defaults.default_dataset_id = payload.default_dataset_id
    defaults.default_scorer_config_id = payload.default_scorer_config_id
    session.commit()
    session.refresh(defaults)
    return RegistryDefaultsSchema(
        default_dataset_id=defaults.default_dataset_id,
        default_scorer_config_id=defaults.default_scorer_config_id,
    )


def create_agent(session: Session, payload: AgentCreateRequestSchema) -> AgentSchema:
    ensure_registry_seeded(session)
    if session.get(AgentRecord, payload.agent_id) is not None:
        raise ValueError("Agent already exists.")

    record = AgentRecord(
        agent_id=payload.agent_id,
        name=payload.name,
        description=payload.description,
        owner_id=payload.owner_id,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _agent_schema(record)


def create_agent_version(
    session: Session,
    payload: AgentVersionCreateRequestSchema,
) -> AgentVersionSchema:
    ensure_registry_seeded(session)
    if session.get(AgentVersionRecord, payload.agent_version_id) is not None:
        raise ValueError("Agent version already exists.")
    if session.get(AgentRecord, payload.agent_id) is None:
        raise LookupError("Agent not found.")

    record = AgentVersionRecord(
        agent_version_id=payload.agent_version_id,
        agent_id=payload.agent_id,
        version_name=payload.version_name,
        model=payload.model,
        prompt_hash=payload.prompt_hash,
        config_json=payload.config_json,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return _agent_version_schema(record)


def get_agent_version(session: Session, agent_version_id: str) -> AgentVersionSchema:
    ensure_registry_seeded(session)
    record = session.get(AgentVersionRecord, agent_version_id)
    if record is None:
        raise LookupError("Agent version not found.")
    return _agent_version_schema(record)


def get_scorer_config(scorer_config_id: str) -> ScorerConfigSchema:
    for fixture_name in (
        "scorer_config.json",
        "scorer_config_keyword_overlap.json",
        "scorer_config_llm_judge.json",
        "scorer_config_rubric_based.json",
    ):
        scorer_config = ScorerConfigSchema.model_validate(_read_fixture(fixture_name))
        if scorer_config.scorer_config_id == scorer_config_id:
            return scorer_config
    raise LookupError("Scorer config not found.")


def get_registry(session: Session) -> RegistryListSchema:
    return RegistryListSchema(
        agents=list_agents(session),
        agent_versions=list_agent_versions(session),
        scorer_configs=list_scorer_configs(session),
        defaults=get_registry_defaults(session),
    )
