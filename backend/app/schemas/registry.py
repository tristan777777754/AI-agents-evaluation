from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.contracts import AgentSchema, AgentVersionSchema, ScorerConfigSchema


class RegistryDefaultsSchema(BaseModel):
    default_dataset_id: str | None = None
    default_scorer_config_id: str | None = None


class RegistryListSchema(BaseModel):
    agents: list[AgentSchema] = Field(default_factory=list)
    agent_versions: list[AgentVersionSchema] = Field(default_factory=list)
    scorer_configs: list[ScorerConfigSchema] = Field(default_factory=list)
    defaults: RegistryDefaultsSchema = Field(default_factory=RegistryDefaultsSchema)


class AgentCreateRequestSchema(BaseModel):
    agent_id: str
    name: str
    description: str | None = None
    owner_id: str | None = None


class AgentVersionCreateRequestSchema(BaseModel):
    agent_version_id: str
    agent_id: str
    version_name: str
    model: str
    prompt_hash: str
    config_json: dict[str, object] = Field(default_factory=dict)


class RegistryDefaultsUpdateRequestSchema(BaseModel):
    default_dataset_id: str | None = None
    default_scorer_config_id: str | None = None
