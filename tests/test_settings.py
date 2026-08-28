from pydantic import SecretStr

from japanese_workplace_tutor.settings import Settings


MODEL_ENV_NAMES = (
    "JLT_MODEL_BASE_URL",
    "JLT_MODEL_API_KEY",
    "JLT_PRIMARY_MODEL",
    "JLT_FALLBACK_MODEL",
)


def test_missing_model_settings_are_safe(monkeypatch) -> None:
    for name in MODEL_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    settings = Settings(_env_file=None)

    assert settings.model_configured is False
    assert settings.model_status == "Not configured"


def test_complete_model_settings_report_presence_without_secret(monkeypatch) -> None:
    values = {
        "JLT_MODEL_BASE_URL": "https://proxy.example/v1",
        "JLT_MODEL_API_KEY": "unit-test-sensitive-value",
        "JLT_PRIMARY_MODEL": "primary-id",
        "JLT_FALLBACK_MODEL": "fallback-id",
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)

    settings = Settings(_env_file=None)

    assert settings.model_configured is True
    assert settings.model_status == "Configured"
    assert isinstance(settings.model_api_key, SecretStr)
    assert "unit-test-sensitive-value" not in repr(settings)
