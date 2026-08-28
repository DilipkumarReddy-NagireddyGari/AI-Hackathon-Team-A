from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config

from japanese_workplace_tutor.settings import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_clean_database_upgrades_to_t01_head(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    get_settings.cache_clear()
    config = Config(str(PROJECT_ROOT / "alembic.ini"))

    command.upgrade(config, "head")

    with sqlite3.connect(database_path) as connection:
        revision = connection.execute("SELECT version_num FROM alembic_version").fetchone()
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()

    get_settings.cache_clear()
    assert revision == ("20260828_0001",)
    assert violations == []
