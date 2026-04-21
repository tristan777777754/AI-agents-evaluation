from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DATABASE_PATH = Path(__file__).resolve().parent / "test_phase2.db"


def pytest_configure() -> None:
    os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DATABASE_PATH}"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    from app.db import reset_db
    from app.main import app

    reset_db()
    with TestClient(app) as test_client:
        yield test_client
