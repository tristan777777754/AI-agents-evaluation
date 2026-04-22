from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.calibration import router as calibration_router
from app.api.compare import router as compare_router
from app.api.datasets import router as dataset_router
from app.api.registry import router as registry_router
from app.api.reviews import router as review_router
from app.api.routes import router as meta_router
from app.api.runs import router as run_router
from app.api.task_runs import router as task_run_router
from app.config import settings
from app.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(meta_router, prefix=f"{settings.api_prefix}/meta", tags=["meta"])
app.include_router(compare_router, prefix=f"{settings.api_prefix}/compare", tags=["compare"])
app.include_router(registry_router, prefix=f"{settings.api_prefix}/registry", tags=["registry"])
app.include_router(dataset_router, prefix=f"{settings.api_prefix}/datasets", tags=["datasets"])
app.include_router(run_router, prefix=f"{settings.api_prefix}/runs", tags=["runs"])
app.include_router(task_run_router, prefix=f"{settings.api_prefix}/task-runs", tags=["task-runs"])
app.include_router(review_router, prefix=f"{settings.api_prefix}/reviews", tags=["reviews"])
app.include_router(
    calibration_router,
    prefix=f"{settings.api_prefix}/calibration",
    tags=["calibration"],
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "phase": settings.current_phase,
        "docs_path": "/docs",
    }
