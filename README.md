# Japanese Workplace Learning

T01 provides a safe, local Streamlit foundation for a personalized Japanese workplace learning MVP. It intentionally contains no authentication, learning logic, or model calls yet.

## Requirements

- Windows with Python 3.14.3 (pinned in `.python-version`)
- A writable local checkout

## Clean setup

From PowerShell in the project root:

1. Create an isolated environment: `py -3.14 -m venv .venv`
2. Install locked direct and development dependencies: `.venv\Scripts\python -m pip install -r requirements-dev.txt`
3. Establish the migration baseline: `.venv\Scripts\python -m alembic upgrade head`

No model credentials are required for T01. To exercise the configured status only, copy `.env.example` to `.env` and replace every model placeholder with non-production dummy values. Do not commit `.env`.

## Run

Start the app with one command:

`.venv\Scripts\python -m streamlit run app.py`

Open the URL shown by Streamlit. Home, Learn, Translate, Progress, and Profile are available from the sidebar. The startup health panel reports only:

- whether the database is ready;
- whether SQLite foreign-key enforcement is enabled; and
- whether all future model settings are present.

It never displays setting values. If model settings are absent, all non-model pages remain usable.

## Test

Run all startup, navigation, configuration, database, and secret checks:

`.venv\Scripts\python -m pytest`

Run only the repository secret scan:

`.venv\Scripts\python -m pytest tests/test_secret_scan.py`

The scan includes notebook source/output JSON. Before sharing, also inspect version-control history with an approved secret-scanning tool because deleting a credential from the current tree does not remove historical commits.

## Configuration

All settings use the `JLT_` environment prefix:

| Variable | Required now | Purpose |
|---|---:|---|
| `JLT_DATABASE_URL` | No | SQLAlchemy URL; defaults to `sqlite:///data/app.db` |
| `JLT_MODEL_BASE_URL` | No | Future OpenAI-compatible endpoint |
| `JLT_MODEL_API_KEY` | No | Future model credential |
| `JLT_PRIMARY_MODEL` | No | Future primary model ID |
| `JLT_FALLBACK_MODEL` | No | Future fallback model ID |

Model status is configured only when all four model variables are present. T01 never contacts a provider.

## Database and migrations

SQLite files are local and ignored by Git. Every application-created SQLite connection executes `PRAGMA foreign_keys=ON`. Alembic owns the schema baseline and will be extended by subsequent tasks.

Useful migration checks:

- Upgrade: `.venv\Scripts\python -m alembic upgrade head`
- Current revision: `.venv\Scripts\python -m alembic current`
- Downgrade baseline: `.venv\Scripts\python -m alembic downgrade base`

## Credential incident action

A prototype credential was removed from the notebook. The credential must still be treated as compromised: its owner must revoke or rotate it in the provider console and clean any version-control history or shared copies containing it. This external action cannot be verified by the application and remains a T01 release blocker until the owner records confirmation.
