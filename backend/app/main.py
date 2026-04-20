from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router as meta_router
from app.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
app.include_router(meta_router, prefix=f"{settings.api_prefix}/meta", tags=["meta"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "phase": "phase1",
        "docs_path": "/docs",
    }
