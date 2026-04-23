from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas.contracts import AgentSchema, AgentVersionSchema
from app.schemas.registry import (
    AgentCreateRequestSchema,
    AgentVersionCreateRequestSchema,
    RegistryDefaultsSchema,
    RegistryDefaultsUpdateRequestSchema,
    RegistryListSchema,
)
from app.services.registry import (
    create_agent,
    create_agent_version,
    get_registry,
    update_registry_defaults,
)

router = APIRouter()
RegistrySession = Annotated[Session, Depends(get_session)]


@router.get("", response_model=RegistryListSchema)
def list_registry(session: RegistrySession) -> RegistryListSchema:
    return get_registry(session)


@router.post("/agents", response_model=AgentSchema, status_code=status.HTTP_201_CREATED)
def create_registry_agent(
    payload: AgentCreateRequestSchema,
    session: RegistrySession,
) -> AgentSchema:
    try:
        return create_agent(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/agent-versions",
    response_model=AgentVersionSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_registry_agent_version(
    payload: AgentVersionCreateRequestSchema,
    session: RegistrySession,
) -> AgentVersionSchema:
    try:
        return create_agent_version(session, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.put("/defaults", response_model=RegistryDefaultsSchema)
def update_registry_default_selection(
    payload: RegistryDefaultsUpdateRequestSchema,
    session: RegistrySession,
) -> RegistryDefaultsSchema:
    try:
        return update_registry_defaults(session, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
