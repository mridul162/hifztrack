from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.api import health
from app.main import app

client = TestClient(app)


def test_application_imports_and_liveness_responds() -> None:
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_succeeds_when_database_query_succeeds(monkeypatch) -> None:
    sqlite_engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr(health, "engine", sqlite_engine)

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    sqlite_engine.dispose()


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    class UnavailableEngine:
        def connect(self):
            raise OperationalError("SELECT 1", {}, OSError("connection refused"))

    monkeypatch.setattr(health, "engine", UnavailableEngine())

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}


def test_database_engine_uses_configured_postgresql_url() -> None:
    from app.core.config import settings
    from app.db.session import engine

    assert engine.url.render_as_string(hide_password=False) == settings.database_url
    assert engine.url.get_backend_name() == "postgresql"
    assert engine.url.get_driver_name() == "psycopg"
