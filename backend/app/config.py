from __future__ import annotations

from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_name: str = "Agent Evaluation Workbench API"
    app_version: str = "0.1.0"
    current_phase: str = "phase7"
    api_prefix: str = "/api/v1"
    backend_port: int = int(getenv("BACKEND_PORT", "8000"))
    frontend_origin: str = getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    database_url: str = getenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/eval_workbench",
    )
    redis_url: str = getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = getenv("CELERY_BROKER_URL", getenv("REDIS_URL", "redis://localhost:6379/0"))
    celery_result_backend: str = getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/1"
    )
    celery_task_always_eager: bool = getenv("CELERY_TASK_ALWAYS_EAGER", "true").lower() in {
        "1",
        "true",
        "yes",
    }
    storage_endpoint_url: str = getenv("STORAGE_ENDPOINT_URL", "http://localhost:9000")
    storage_bucket: str = getenv("STORAGE_BUCKET", "eval-traces")
    openai_api_key: str = getenv("OPENAI_API_KEY", "")


settings = Settings()
