# T01 verification checkpoint

Date: 2026-08-28

## Automated evidence

- Full test suite: **10 passed**.
- Covered: safe missing/complete model configuration, secret masking, Streamlit startup, all five navigation states, SQLite readiness, foreign-key enforcement on repeated connections, clean Alembic upgrade, and repository/notebook secret patterns.
- Fresh migration reached revision `20260828_0001 (head)`.
- SQLite `PRAGMA foreign_key_check` returned no violations.

## Manual product smoke test

The application was started without model environment variables and checked in a browser.

- Home opened successfully.
- Learn opened successfully.
- Translate opened successfully.
- Progress opened successfully.
- Profile opened successfully.
- Startup health displayed `Database: ready`.
- Startup health displayed `SQLite foreign keys: enabled`.
- Startup health displayed the safe missing-configuration state.
- No configuration value was displayed.

Automated application testing also confirmed that dummy model variables change the health state to configured without making a provider call.

## Credential and retention audit

- The embedded prototype credential and credential-shaped placeholder were removed from notebook source.
- The secret-pattern test scans notebook JSON, including stored outputs.
- No Git repository is currently initialized, so Git history scanning is not applicable to this workspace at this checkpoint.
- Local `.env`, SQLite files, virtual environments, caches, and editor state are ignored.
- Streamlit usage-statistics collection is disabled in repository configuration.

## Credential-rotation confirmation

**Complete:** on 2026-08-28, the owner confirmed that the API key previously embedded in the prototype notebook was replaced. The same replacement proxy credential is configured for both model routes; no secret value is recorded here.

GPT access is currently available while the Tsuzumi 2 model route is unavailable. This is a provider/model-availability condition rather than a T01 credential-management blocker. T01 is accepted; later model-gateway work must handle Tsuzumi failure and GPT fallback without exposing the shared proxy credential.
