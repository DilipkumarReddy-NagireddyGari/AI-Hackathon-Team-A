"""SQLAlchemy engine creation and database readiness checks."""

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text

from .settings import Settings


@dataclass(frozen=True)
class DatabaseHealth:
    ready: bool
    foreign_keys_enabled: bool
    message: str


def create_database_engine(settings: Settings, project_root: Path | None = None) -> Engine:
    """Create an engine and enforce SQLite foreign keys on every connection."""

    settings.ensure_local_directories(project_root)
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    engine = create_engine(settings.database_url, connect_args=connect_args)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
            finally:
                cursor.close()

    return engine


def check_database(engine: Engine) -> DatabaseHealth:
    """Check connectivity and confirm SQLite foreign-key enforcement."""

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            if engine.dialect.name != "sqlite":
                return DatabaseHealth(True, True, "Database ready")
            enabled = connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
            if not enabled:
                return DatabaseHealth(False, False, "Database foreign-key enforcement is disabled")
            return DatabaseHealth(True, True, "Database ready")
    except Exception:
        return DatabaseHealth(False, False, "Database unavailable")
