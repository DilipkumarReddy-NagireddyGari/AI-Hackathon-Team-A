from pathlib import Path

from alembic import command
from alembic.config import Config
from streamlit.testing.v1 import AppTest

from japanese_workplace_tutor.auth import AuthenticationService
from japanese_workplace_tutor.app import PAGE_RENDERERS
from japanese_workplace_tutor.database import create_database_engine
from japanese_workplace_tutor.lesson import FIXTURE_LESSON, LessonService
from japanese_workplace_tutor.profile import JapaneseLevel, ProfileService
from japanese_workplace_tutor.settings import Settings, get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def prepare_database(monkeypatch, database_path: Path) -> None:
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    get_settings.cache_clear()
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    get_settings.cache_clear()


def create_completed_user(database_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}", _env_file=None
    )
    engine = create_database_engine(settings)
    user = AuthenticationService(engine).register(
        "Alice", "correct horse battery staple"
    )
    ProfileService(engine).create_profile(
        user.id,
        role="Software engineer",
        tasks=["Discuss requirements", "Give status updates"],
        declared_level=JapaneseLevel.N4,
    )
    engine.dispose()
    return user


def test_all_required_pages_are_registered() -> None:
    assert tuple(PAGE_RENDERERS) == ("Home", "Learn", "Translate", "Progress", "Profile")


def test_app_starts_without_model_configuration(monkeypatch, tmp_path: Path) -> None:
    prepare_database(monkeypatch, tmp_path / "app.db")
    for name in (
        "JLT_MODEL_BASE_URL",
        "JLT_MODEL_API_KEY",
        "JLT_PRIMARY_MODEL",
        "JLT_FALLBACK_MODEL",
    ):
        monkeypatch.setenv(name, "")

    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    assert not app.exception
    assert any(title.value == "Demo authentication" for title in app.title)
    assert not app.sidebar.radio
    assert any("Model features unavailable" in warning.value for warning in app.warning)
    assert any("Database: ready" in success.value for success in app.success)


def test_dummy_model_configuration_changes_status_without_provider_call(monkeypatch, tmp_path: Path) -> None:
    prepare_database(monkeypatch, tmp_path / "app.db")
    monkeypatch.setenv("JLT_MODEL_BASE_URL", "https://proxy.invalid/v1")
    monkeypatch.setenv("JLT_MODEL_API_KEY", "dummy-test-value")
    monkeypatch.setenv("JLT_PRIMARY_MODEL", "primary-test-model")
    monkeypatch.setenv("JLT_FALLBACK_MODEL", "fallback-test-model")
    get_settings.cache_clear()

    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    assert not app.exception
    assert any("Model features: configured" in success.value for success in app.success)


def test_each_page_opens_without_exception(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "app.db"
    prepare_database(monkeypatch, database_path)
    user = create_completed_user(database_path)
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.session_state["authenticated_user_id"] = user.id
    app.session_state["authenticated_username"] = user.username
    app.run()

    for page_name in PAGE_RENDERERS:
        app.sidebar.radio[0].set_value(page_name).run()
        assert not app.exception
        assert any(title.value == page_name for title in app.title)


def test_register_logout_and_login_flow(monkeypatch, tmp_path: Path) -> None:
    prepare_database(monkeypatch, tmp_path / "app.db")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    app.text_input(key="registration_username").input("Alice")
    app.text_input(key="registration_password").input("correct horse battery staple")
    app.button(key="FormSubmitter:registration_form-Create account").click().run()

    assert any(title.value == "Set up your learner profile" for title in app.title)
    assert not app.sidebar.radio

    app.button(key="onboarding_1_submit").click().run()
    assert any(title.value == "Home" for title in app.title)
    assert app.session_state["authenticated_username"] == "Alice"
    assert any("Software engineer" in subheader.value for subheader in app.subheader)

    app.sidebar.button[0].click().run()
    assert any(title.value == "Demo authentication" for title in app.title)
    assert "authenticated_user_id" not in app.session_state

    app.text_input(key="sign_in_username").input("alice")
    app.text_input(key="sign_in_password").input("correct horse battery staple")
    app.button(key="FormSubmitter:sign_in_form-Sign in").click().run()

    assert any(title.value == "Home" for title in app.title)
    assert app.session_state["authenticated_username"] == "Alice"


def test_onboarding_validates_tasks_and_profile_can_be_edited(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "app.db"
    prepare_database(monkeypatch, database_path)
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    app.text_input(key="registration_username").input("Alice")
    app.text_input(key="registration_password").input("correct horse battery staple")
    app.button(key="FormSubmitter:registration_form-Create account").click().run()

    app.multiselect(key="onboarding_1_tasks").set_value([])
    app.button(key="onboarding_1_submit").click().run()
    assert any("at least one typical task" in error.value for error in app.error)

    app.selectbox(key="onboarding_1_role").set_value("Researcher").run()
    app.multiselect(key="onboarding_1_tasks").set_value(
        ["Review applications", "Meet inventors"]
    )
    app.selectbox(key="onboarding_1_declared_level").set_value("JLPT N5")
    app.button(key="onboarding_1_submit").click().run()

    assert any(title.value == "Home" for title in app.title)
    assert any("Researcher" in subheader.value for subheader in app.subheader)

    app.sidebar.radio[0].set_value("Profile").run()
    app.selectbox(key="profile_1_declared_level").set_value("JLPT N3")
    app.text_area(key="profile_1_tools_domain").input("Intellectual property")
    app.button(key="profile_1_submit").click().run()

    assert any(success.value == "Profile saved." for success in app.success)
    stored = ProfileService(
        create_database_engine(
            Settings(
                database_url=f"sqlite:///{database_path.as_posix()}", _env_file=None
            )
        )
    ).get_profile(1)
    assert stored is not None
    assert stored.declared_level is JapaneseLevel.N3
    assert stored.tools_domain == "Intellectual property"


def test_fixture_lesson_can_be_answered_completed_and_viewed_in_progress(
    monkeypatch, tmp_path: Path
) -> None:
    database_path = tmp_path / "app.db"
    prepare_database(monkeypatch, database_path)
    user = create_completed_user(database_path)
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.session_state["authenticated_user_id"] = user.id
    app.session_state["authenticated_username"] = user.username
    app.run()

    app.sidebar.radio[0].set_value("Learn").run()
    app.button(key="start_fixture_lesson").click().run()
    active = app.session_state["active_fixture_lesson"]

    for question in FIXTURE_LESSON.questions:
        answer_key = (
            f"fixture_answer_{active.lesson_session_id}_{question.question_id}"
        )
        submit_key = f"submit_{active.lesson_session_id}_{question.question_id}"
        app.radio(key=answer_key).set_value(
            question.options[question.correct_option_index]
        )
        app.button(key=submit_key).click().run()

    app.button(key="complete_fixture_lesson").click().run()
    assert any("Lesson completed" in success.value for success in app.success)
    assert "active_fixture_lesson" not in app.session_state

    app.sidebar.radio[0].set_value("Progress").run(timeout=10)
    assert not app.exception
    assert app.dataframe

    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}", _env_file=None
    )
    engine = create_database_engine(settings)
    lessons = LessonService(engine)
    assert len(lessons.get_progress(user.id)) == 5
    assert sum(record.correct_count for record in lessons.get_progress(user.id)) == 5
    assert len(lessons.get_completions(user.id)) == 1
    engine.dispose()
