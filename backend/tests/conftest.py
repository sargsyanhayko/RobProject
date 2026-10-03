"""Run API tests in an isolated schema of an explicitly selected PostgreSQL DB."""

import os
from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text

from app import database, main
from app.config import settings
from app.database import Base


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL integration tests")
    schema = f"catalog_test_{uuid4().hex}"
    control_engine = create_engine(url, hide_parameters=True)
    with control_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        url,
        hide_parameters=True,
        connect_args={"options": f"-c search_path={schema}"},
    )
    try:
        yield engine
    finally:
        engine.dispose()
        with control_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control_engine.dispose()


@pytest.fixture
def client(
    test_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    monkeypatch.setattr(main, "engine", test_engine)
    database.SessionLocal.configure(bind=test_engine)
    try:
        with TestClient(main.app) as test_client:
            yield test_client
    finally:
        database.SessionLocal.configure(bind=database.engine)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password.get_secret_value(),
        },
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
