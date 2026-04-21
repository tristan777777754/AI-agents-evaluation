from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.schemas.contracts import AgentVersionSchema, ScorerConfigSchema
from app.schemas.runs import RegistryListSchema

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def _read_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text())


@lru_cache(maxsize=1)
def list_agent_versions() -> list[AgentVersionSchema]:
    return [
        AgentVersionSchema.model_validate(_read_fixture("agent_version_v1.json")),
        AgentVersionSchema.model_validate(_read_fixture("agent_version_v2.json")),
    ]


@lru_cache(maxsize=1)
def list_scorer_configs() -> list[ScorerConfigSchema]:
    return [ScorerConfigSchema.model_validate(_read_fixture("scorer_config.json"))]


def get_agent_version(agent_version_id: str) -> AgentVersionSchema:
    for agent_version in list_agent_versions():
        if agent_version.agent_version_id == agent_version_id:
            return agent_version
    raise LookupError("Agent version not found.")


def get_scorer_config(scorer_config_id: str) -> ScorerConfigSchema:
    for scorer_config in list_scorer_configs():
        if scorer_config.scorer_config_id == scorer_config_id:
            return scorer_config
    raise LookupError("Scorer config not found.")


def get_registry() -> RegistryListSchema:
    return RegistryListSchema(
        agent_versions=list_agent_versions(),
        scorer_configs=list_scorer_configs(),
    )
