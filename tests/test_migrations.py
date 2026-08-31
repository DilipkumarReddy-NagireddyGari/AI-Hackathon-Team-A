from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config

from japanese_workplace_tutor.settings import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def configure_database(monkeypatch, database_path: Path) -> Config:
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    get_settings.cache_clear()
    return Config(str(PROJECT_ROOT / "alembic.ini"))


def assert_t02_schema(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert revision == ("20260831_0002",)
    assert columns == {
        "id",
        "username",
        "normalized_username",
        "password_hash",
        "created_at",
        "updated_at",
    }
    assert violations == []


def test_clean_database_upgrades_to_t02_head(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    config = configure_database(monkeypatch, database_path)

    command.upgrade(config, "head")

    assert_t02_schema(database_path)
    get_settings.cache_clear()


def test_t01_database_upgrades_to_t02_head(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    config = configure_database(monkeypatch, database_path)

    command.upgrade(config, "20260828_0001")
    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        users_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'"
        ).fetchone()

    assert revision == ("20260828_0001",)
    assert users_table is None

    command.upgrade(config, "head")

    assert_t02_schema(database_path)
    get_settings.cache_clear()
