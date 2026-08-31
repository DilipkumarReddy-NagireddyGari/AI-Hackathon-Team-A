from pathlib import Path

from alembic import command
from alembic.config import Config
from streamlit.testing.v1 import AppTest

from japanese_workplace_tutor.app import PAGE_RENDERERS
from japanese_workplace_tutor.settings import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def prepare_database(monkeypatch, database_path: Path) -> None:
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{database_path.as_posix()}")
    get_settings.cache_clear()
    command.upgrade(Config(str(PROJECT_ROOT / "alembic.ini")), "head")
    get_settings.cache_clear()


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
    prepare_database(monkeypatch, tmp_path / "app.db")
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
    app.session_state["authenticated_user_id"] = 1
    app.session_state["authenticated_username"] = "Alice"
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

    assert any(title.value == "Home" for title in app.title)
    assert app.session_state["authenticated_username"] == "Alice"

    app.sidebar.button[0].click().run()
    assert any(title.value == "Demo authentication" for title in app.title)
    assert "authenticated_user_id" not in app.session_state

    app.text_input(key="sign_in_username").input("alice")
    app.text_input(key="sign_in_password").input("correct horse battery staple")
    app.button(key="FormSubmitter:sign_in_form-Sign in").click().run()

    assert any(title.value == "Home" for title in app.title)
    assert app.session_state["authenticated_username"] == "Alice"
