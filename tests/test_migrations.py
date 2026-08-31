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


def assert_t03_schema(database_path: Path) -> None:
    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        user_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        profile_columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(learner_profiles)"
            ).fetchall()
        }
        profile_foreign_keys = connection.execute(
            "PRAGMA foreign_key_list(learner_profiles)"
        ).fetchall()
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    assert revision == ("20260831_0003",)
    assert user_columns == {
        "id",
        "username",
        "normalized_username",
        "password_hash",
        "created_at",
        "updated_at",
    }
    assert profile_columns == {
        "id",
        "user_id",
        "role",
        "tasks",
        "tools_domain",
        "declared_level",
        "estimated_working_level",
        "level_source",
        "level_confidence",
        "romaji_preference",
        "created_at",
        "updated_at",
    }
    assert len(profile_foreign_keys) == 1
    assert profile_foreign_keys[0][2:5] == ("users", "user_id", "id")
    assert profile_foreign_keys[0][6] == "CASCADE"
    assert violations == []


def test_clean_database_upgrades_to_t03_head(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    config = configure_database(monkeypatch, database_path)

    command.upgrade(config, "head")

    assert_t03_schema(database_path)
    get_settings.cache_clear()


def test_t02_database_upgrades_to_t03_head(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    config = configure_database(monkeypatch, database_path)

    command.upgrade(config, "20260831_0002")
    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        profiles_table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'learner_profiles'"
        ).fetchone()

    assert revision == ("20260831_0002",)
    assert profiles_table is None

    command.upgrade(config, "head")

    assert_t03_schema(database_path)
    get_settings.cache_clear()
