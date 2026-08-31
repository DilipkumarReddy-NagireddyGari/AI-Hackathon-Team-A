from pathlib import Path

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from japanese_workplace_tutor.auth import AuthenticationService
from japanese_workplace_tutor.database import create_database_engine
from japanese_workplace_tutor.models import Base, LearnerProfile
from japanese_workplace_tutor.profile import (
    JapaneseLevel,
    LevelSource,
    ProfileService,
    ProfileValidationError,
)
from japanese_workplace_tutor.settings import Settings


def create_services(database_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}", _env_file=None
    )
    engine = create_database_engine(settings)
    Base.metadata.create_all(engine)
    return AuthenticationService(engine), ProfileService(engine), engine


def test_profile_requires_role_tasks_and_valid_level(tmp_path: Path) -> None:
    auth, profiles, engine = create_services(tmp_path / "profiles.db")
    user = auth.register("Alice", "correct horse battery staple")

    with pytest.raises(ProfileValidationError, match="Role or title is required"):
        profiles.create_profile(
            user.id, role="  ", tasks=["Meet customers"], declared_level="JLPT N5"
        )
    with pytest.raises(ProfileValidationError, match="at least one typical task"):
        profiles.create_profile(
            user.id, role="Sales", tasks=["  "], declared_level="JLPT N5"
        )
    with pytest.raises(ProfileValidationError, match="Input should be"):
        profiles.create_profile(
            user.id, role="Sales", tasks=["Meet customers"], declared_level="Expert"
        )

    assert profiles.get_profile(user.id) is None
    engine.dispose()


def test_profiles_are_isolated_and_persist_across_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "profiles.db"
    auth, profiles, engine = create_services(database_path)
    alice = auth.register("Alice", "correct horse battery staple")
    bob = auth.register("Bob", "another secure password")

    profiles.create_profile(
        alice.id,
        role="Software engineer",
        tasks=["Discuss requirements", "  Give status updates  "],
        declared_level=JapaneseLevel.N4,
        tools_domain="Cloud services",
    )
    profiles.create_profile(
        bob.id,
        role="Patent attorney",
        tasks=["Review applications"],
        declared_level=JapaneseLevel.UNSURE,
    )
    engine.dispose()

    _, restarted_profiles, restarted_engine = create_services(database_path)
    alice_profile = restarted_profiles.get_profile(alice.id)
    bob_profile = restarted_profiles.get_profile(bob.id)

    assert alice_profile is not None
    assert alice_profile.role == "Software engineer"
    assert alice_profile.tasks == ("Discuss requirements", "Give status updates")
    assert alice_profile.tools_domain == "Cloud services"
    assert bob_profile is not None
    assert bob_profile.role == "Patent attorney"
    assert bob_profile.tools_domain is None
    restarted_engine.dispose()


def test_declared_level_update_preserves_estimated_level_state(tmp_path: Path) -> None:
    auth, profiles, engine = create_services(tmp_path / "profiles.db")
    user = auth.register("Alice", "correct horse battery staple")
    profiles.create_profile(
        user.id,
        role="Researcher",
        tasks=["Present findings"],
        declared_level=JapaneseLevel.N5,
        romaji_preference=True,
    )
    with Session(engine) as session:
        session.execute(
            update(LearnerProfile)
            .where(LearnerProfile.user_id == user.id)
            .values(
                estimated_working_level=JapaneseLevel.N4.value,
                level_source=LevelSource.PLACEMENT_ESTIMATED.value,
                level_confidence=0.6,
            )
        )
        session.commit()

    updated = profiles.update_profile(
        user.id,
        role="Researcher",
        tasks=["Present findings", "Plan experiments"],
        declared_level=JapaneseLevel.N3,
        romaji_preference=False,
    )

    assert updated.declared_level is JapaneseLevel.N3
    assert updated.estimated_working_level is JapaneseLevel.N4
    assert updated.level_source is LevelSource.PLACEMENT_ESTIMATED
    assert updated.level_confidence == 0.6
    assert updated.romaji_preference is False
    engine.dispose()