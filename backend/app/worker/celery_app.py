from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.config import settings

try:
    from celery import Celery  # type: ignore[import-not-found]
except ModuleNotFoundError:
    if not settings.celery_task_always_eager:
        raise RuntimeError(
            "Celery is required when CELERY_TASK_ALWAYS_EAGER=false. "
            "Install backend dependencies with Celery before starting async execution."
        ) from None

    class _LocalTask:
        def __init__(self, func: Callable[..., Any]) -> None:
            self._func = func

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return self._func(*args, **kwargs)

        def delay(self, *args: Any, **kwargs: Any) -> Any:
            return self._func(*args, **kwargs)

    class _LocalCelery:
        def __init__(self) -> None:
            self.conf = type("Conf", (), {})()
            self.conf.task_always_eager = True
            self.conf.task_eager_propagates = True

        def task(self, name: str) -> Callable[[Callable[..., Any]], _LocalTask]:
            _ = name

            def decorator(func: Callable[..., Any]) -> _LocalTask:
                return _LocalTask(func)

            return decorator

    celery_app = _LocalCelery()
else:
    celery_app = Celery(
        "agent_evaluation_workbench",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
    )
    celery_app.conf.task_always_eager = settings.celery_task_always_eager
    celery_app.conf.task_eager_propagates = True
