from __future__ import annotations

from app.db import SessionLocal
from app.services.runs import execute_run
from app.worker.celery_app import celery_app


@celery_app.task(name="eval_runs.execute")
def execute_run_task(run_id: str) -> dict[str, object]:
    with SessionLocal() as session:
        detail = execute_run(session, run_id)
    return detail.model_dump(mode="json")
