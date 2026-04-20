from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.schemas.contracts import PhaseContractSnapshot

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name, "phase": "phase1"}


@router.get("/contracts", response_model=PhaseContractSnapshot)
def get_contracts() -> PhaseContractSnapshot:
    return PhaseContractSnapshot.build_default()
