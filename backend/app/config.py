from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_name: str = "Agent Evaluation Workbench API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    backend_port: int = int(getenv("BACKEND_PORT", "8000"))
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/eval_workbench",
    )
    redis_url: str = getenv("REDIS_URL", "redis://localhost:6379/0")
    storage_endpoint_url: str = getenv("STORAGE_ENDPOINT_URL", "http://localhost:9000")
    storage_bucket: str = getenv("STORAGE_BUCKET", "eval-traces")


settings = Settings()
