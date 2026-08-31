# Japanese Workplace Learning

T02 provides a safe, local Streamlit foundation with persistent demo accounts for a personalized Japanese workplace learning MVP. Learning logic and model calls are not implemented yet.

## Requirements

- Windows with Python 3.14.3 (pinned in `.python-version`)
- A writable local checkout

## Clean setup

From PowerShell in the project root:

1. Create an isolated environment: `py -3.14 -m venv .venv`
2. Install locked direct and development dependencies: `.venv\Scripts\python -m pip install -r requirements-dev.txt`
3. Establish the migration baseline: `.venv\Scripts\python -m alembic upgrade head`

No model credentials are required. To exercise the configured status only, copy `.env.example` to `.env` and replace every model placeholder with non-production dummy values. Do not commit `.env`.

## Run

Start the app with one command:

`.venv\Scripts\python -m streamlit run app.py`

Open the URL shown by Streamlit. Register a local demo account without an email address, then use Home, Learn, Translate, Progress, and Profile from the sidebar. The startup health panel reports only:

- whether the database is ready;
- whether SQLite foreign-key enforcement is enabled; and
- whether all future model settings are present.

It never displays setting values. If model settings are absent, all non-model pages remain usable after sign-in.

## Demo authentication

- Usernames are Unicode NFKC-normalized and trimmed. Sign-in and uniqueness are case-insensitive, while the normalized display form is preserved.
- Usernames must be 3-64 characters and cannot contain control characters.
- Passwords must be 12-128 characters and are persisted only as Argon2id hashes.
- Accounts remain in SQLite after restart. Authentication is held only in Streamlit session state, so a lost session or application restart requires signing in again.
- This local mechanism is demo authentication, not enterprise identity. It has no shared/default credentials, email, recovery, SSO, or account lockout.

## Test

Run all authentication, startup, navigation, migration, configuration, database, and secret checks:

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

Model status is configured only when all four model variables are present. The current application never contacts a provider.

## Database and migrations

SQLite files are local and ignored by Git. Every application-created SQLite connection executes `PRAGMA foreign_keys=ON`. Alembic owns the schema, including the T02 `users` table. Run the upgrade command after pulling schema changes and before starting the app.

Useful migration checks:

- Upgrade: `.venv\Scripts\python -m alembic upgrade head`
- Current revision: `.venv\Scripts\python -m alembic current`
- Downgrade baseline: `.venv\Scripts\python -m alembic downgrade base`

## Credential incident action

A prototype credential was removed from the notebook. The credential must still be treated as compromised: its owner must revoke or rotate it in the provider console and clean any version-control history or shared copies containing it. This external action cannot be verified by the application and remains a T01 release blocker until the owner records confirmation.
