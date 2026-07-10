from __future__ import annotations

from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.config import Settings
from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    settings = Settings(
        environment="test",
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        write_api_key="test-secret",
        public_reads=True,
        cors_origins=("http://testserver",),
        max_graph_depth=3,
        page_size_max=200,
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def write_headers():
    return {"X-SC-API-Key": "test-secret"}
