import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


EXPECTED_TABLES = {
    "organizations", "groups", "group_memberships", "group_invitations",
    "group_membership_events", "group_rate_limits", "quran_surahs", "quran_ayahs",
    "quran_juzs", "quran_pages", "quran_reference_sources", "user_ayah_progress",
    "revision_sessions",
    "memorization_entries",
}
APPLICATION_TABLES = (
    "organizations", "groups", "group_memberships", "group_invitations",
    "group_membership_events", "group_rate_limits", "auth_rate_limits",
    "user_sessions", "users", "quran_surahs", "quran_ayahs", "quran_juzs",
    "quran_pages", "quran_reference_sources", "user_ayah_progress", "memorization_entries",
    "revision_sessions",
)
RESET_SQL = text("""
    TRUNCATE TABLE revision_sessions, memorization_entries, user_ayah_progress, quran_pages, quran_juzs,
        quran_ayahs, quran_surahs, quran_reference_sources, group_membership_events,
        group_rate_limits, group_invitations, group_memberships, groups, organizations,
        auth_rate_limits, user_sessions, users
    RESTART IDENTITY CASCADE
""")


@pytest.fixture(scope="session")
def postgres_engine():
    database_url = os.environ.get("TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("Set TEST_POSTGRES_URL to the disposable HifzTrack verification database")
    if os.environ.get("HIFZTRACK_ALLOW_DESTRUCTIVE_PG_TESTS") != "1":
        pytest.fail(
            "PostgreSQL integration tests truncate application tables; set "
            "HIFZTRACK_ALLOW_DESTRUCTIVE_PG_TESTS=1 to opt in"
        )
    engine = create_engine(database_url, pool_pre_ping=True, pool_size=12, max_overflow=12,
        connect_args={"application_name": "hifztrack-postgres-tests"})
    try:
        with engine.connect() as connection:
            database_name, database_user, version = connection.execute(text(
                "SELECT current_database(), current_user, version()"
            )).one()
            if not database_name.startswith("hifztrack_verify_") or not database_user.startswith("htverify_"):
                pytest.fail("PostgreSQL tests require the dedicated hifztrack_verify_ database and htverify_ user")
            if not version.startswith("PostgreSQL "):
                pytest.fail("PostgreSQL integration suite requires PostgreSQL")
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0007_revision_tracking":
                pytest.fail("PostgreSQL integration suite requires migration revision 0007_revision_tracking")
            existing_tables = set(connection.scalars(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )).all())
            if not EXPECTED_TABLES.issubset(existing_tables):
                pytest.fail("PostgreSQL verification schema is missing required Phase 2 tables")
            existing_data = sum(
                connection.scalar(text(f"SELECT count(*) FROM {table}"))
                for table in APPLICATION_TABLES
            )
            if existing_data:
                pytest.fail("Disposable PostgreSQL database must be empty before integration tests")
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def pg_sessions(postgres_engine):
    factory = sessionmaker(bind=postgres_engine, autoflush=False, expire_on_commit=False)
    with postgres_engine.begin() as connection:
        connection.execute(RESET_SQL)
    try:
        yield factory
    finally:
        with postgres_engine.begin() as connection:
            connection.execute(RESET_SQL)
