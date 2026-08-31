# Japanese Workplace Learning

T04 provides a safe, local Streamlit application with persistent demo accounts, user-scoped learner profiles, and a deterministic workplace lesson with compact evidence-based progress. Model calls are not implemented yet.

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

Open the URL shown by Streamlit. Register a local demo account without an email address, complete the required learner profile, then open Learn to complete the fixture lesson and Progress to inspect saved evidence. The startup health panel reports only:

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

## Learner profile

- First sign-in requires a role or title, at least one typical task, and a self-reported level before protected navigation is available.
- Role and task suggestions are searchable, editable starting points. Custom roles and tasks are accepted.
- Technologies, tools, or business domain are optional. Romaji support defaults off.
- Profile values are isolated by account and remain in SQLite after sign-out or application restart.
- Declared level remains separate from the future estimated working level. Optional placement is displayed but unavailable until T15.

## Deterministic fixture lesson

- Learn contains one five-item workplace status-update lesson with meaning, reading, and contextual-cloze multiple-choice questions.
- Opening a lesson records exposure for each item but never raises mastery. A correct answer adds `0.10` initial mastery and schedules review one day later; an incorrect answer adds no mastery and schedules review ten minutes later.
- Each question submission is immutable and idempotent for its user and lesson session. Leaving an unfinished lesson retains already submitted compact evidence but writes no completion record.
- Progress shows user-scoped exposure, answer counts, initial mastery, next-review timestamps, and the latest minimal completion metadata.
- Active passage, examples, questions, options, explanations, feedback, and recap exist only in Streamlit session state. SQLite stores canonical item IDs, compact answer evidence, schedule state, and topic/difficulty/item-ID completion metadata. Refresh/process loss removes active content and requires sign-in again.
- T05 will replace the initial schedule with the versioned dimension-aware mastery and simplified SM-2 policy, including corrective delayed retries.

## Test

Run all lesson, profile, authentication, startup, navigation, migration, retention, configuration, database, and secret checks:

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

SQLite files are local and ignored by Git. Every application-created SQLite connection executes `PRAGMA foreign_keys=ON`. Alembic owns the schema, including T02 accounts, T03 learner profiles, and T04 learning items, progress, review attempts, and completion metadata. Run the upgrade command after pulling schema changes and before starting the app.

Useful migration checks:

- Upgrade: `.venv\Scripts\python -m alembic upgrade head`
- Current revision: `.venv\Scripts\python -m alembic current`
- Downgrade baseline: `.venv\Scripts\python -m alembic downgrade base`

## Credential incident action

A prototype credential was removed from the notebook. The credential must still be treated as compromised: its owner must revoke or rotate it in the provider console and clean any version-control history or shared copies containing it. This external action cannot be verified by the application and remains a T01 release blocker until the owner records confirmation.
