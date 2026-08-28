from pathlib import Path

from streamlit.testing.v1 import AppTest

from japanese_workplace_tutor.app import PAGE_RENDERERS
from japanese_workplace_tutor.settings import get_settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_all_required_pages_are_registered() -> None:
    assert tuple(PAGE_RENDERERS) == ("Home", "Learn", "Translate", "Progress", "Profile")


def test_app_starts_without_model_configuration(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    for name in (
        "JLT_MODEL_BASE_URL",
        "JLT_MODEL_API_KEY",
        "JLT_PRIMARY_MODEL",
        "JLT_FALLBACK_MODEL",
    ):
        monkeypatch.setenv(name, "")
    get_settings.cache_clear()

    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    assert not app.exception
    assert any(title.value == "Home" for title in app.title)
    assert any("Model features unavailable" in warning.value for warning in app.warning)
    assert any("Database: ready" in success.value for success in app.success)


def test_dummy_model_configuration_changes_status_without_provider_call(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    monkeypatch.setenv("JLT_MODEL_BASE_URL", "https://proxy.invalid/v1")
    monkeypatch.setenv("JLT_MODEL_API_KEY", "dummy-test-value")
    monkeypatch.setenv("JLT_PRIMARY_MODEL", "primary-test-model")
    monkeypatch.setenv("JLT_FALLBACK_MODEL", "fallback-test-model")
    get_settings.cache_clear()

    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    assert not app.exception
    assert any("Model features: configured" in success.value for success in app.success)


def test_each_page_opens_without_exception(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("JLT_DATABASE_URL", f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    get_settings.cache_clear()
    app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()

    for page_name in PAGE_RENDERERS:
        app.sidebar.radio[0].set_value(page_name).run()
        assert not app.exception
        assert any(title.value == page_name for title in app.title)
