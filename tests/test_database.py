from pathlib import Path

from sqlalchemy import text

from japanese_workplace_tutor.database import check_database, create_database_engine
from japanese_workplace_tutor.settings import Settings


def sqlite_url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def test_database_is_ready_with_foreign_keys_enabled(tmp_path: Path) -> None:
    settings = Settings(database_url=sqlite_url(tmp_path / "app.db"), _env_file=None)
    engine = create_database_engine(settings)

    health = check_database(engine)
    with engine.connect() as connection:
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
    engine.dispose()

    assert health.ready is True
    assert health.foreign_keys_enabled is True
    assert foreign_keys == 1


def test_foreign_keys_are_enabled_on_each_connection(tmp_path: Path) -> None:
    settings = Settings(database_url=sqlite_url(tmp_path / "app.db"), _env_file=None)
    engine = create_database_engine(settings)

    with engine.connect() as first:
        assert first.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    engine.dispose()

    engine = create_database_engine(settings)
    with engine.connect() as second:
        assert second.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
    engine.dispose()
