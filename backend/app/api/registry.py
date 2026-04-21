from __future__ import annotations

from fastapi import APIRouter

from app.schemas.runs import RegistryListSchema
from app.services.registry import get_registry

router = APIRouter()


@router.get("", response_model=RegistryListSchema)
def list_registry() -> RegistryListSchema:
    return get_registry()
