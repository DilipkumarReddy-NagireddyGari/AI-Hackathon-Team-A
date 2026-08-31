from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from japanese_workplace_tutor.auth import (
    AuthenticationError,
    AuthenticationService,
    INVALID_LOGIN_MESSAGE,
    RegistrationError,
)
from japanese_workplace_tutor.database import create_database_engine
from japanese_workplace_tutor.models import Base, User
from japanese_workplace_tutor.settings import Settings


def create_service(database_path: Path) -> tuple[AuthenticationService, object]:
    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}", _env_file=None
    )
    engine = create_database_engine(settings)
    Base.metadata.create_all(engine)
    return AuthenticationService(engine), engine


def test_registration_stores_argon2id_hash_and_authenticates(tmp_path: Path) -> None:
    password = "correct horse battery staple"
    service, engine = create_service(tmp_path / "auth.db")

    registered = service.register("  Ａlice  ", password)
    authenticated = service.authenticate("alice", password)

    with Session(engine) as session:
        stored = session.scalar(select(User))
    assert stored is not None
    assert stored.username == "Alice"
    assert stored.normalized_username == "alice"
    assert stored.password_hash != password
    assert stored.password_hash.startswith("$argon2id$")
    assert authenticated == registered
    engine.dispose()


def test_duplicate_normalized_username_is_rejected(tmp_path: Path) -> None:
    service, engine = create_service(tmp_path / "auth.db")
    service.register("Alice", "correct horse battery staple")

    with pytest.raises(RegistrationError, match="already registered"):
        service.register("  ALICE ", "another secure password")
    engine.dispose()


@pytest.mark.parametrize(
    ("username", "password"),
    [("unknown", "wrong password"), ("Alice", "wrong password")],
)
def test_invalid_login_uses_one_generic_error(
    tmp_path: Path, username: str, password: str
) -> None:
    service, engine = create_service(tmp_path / "auth.db")
    service.register("Alice", "correct horse battery staple")

    with pytest.raises(AuthenticationError) as error:
        service.authenticate(username, password)
    assert str(error.value) == INVALID_LOGIN_MESSAGE
    engine.dispose()


def test_accounts_are_distinct_and_survive_engine_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "auth.db"
    service, engine = create_service(database_path)
    alice = service.register("Alice", "correct horse battery staple")
    bob = service.register("Bob", "another secure password")
    engine.dispose()

    restarted_service, restarted_engine = create_service(database_path)
    assert restarted_service.authenticate("Alice", "correct horse battery staple") == alice
    assert restarted_service.authenticate("Bob", "another secure password") == bob
    assert alice.id != bob.id
    restarted_engine.dispose()