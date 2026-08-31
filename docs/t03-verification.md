# T03 Verification Record

Verified on 2026-08-31 against Python 3.14.3 and migration revision `20260831_0003`.

## Automated checks

| Check | Result |
|---|---:|
| Full test suite: `.venv\Scripts\python.exe -m pytest` | 21 passed |
| Profile service: `tests\test_profile.py` | 3 passed |
| Streamlit app flow: `tests\test_app.py` | 6 passed |
| Fresh and T02 upgrade migrations: `tests\test_migrations.py` | 2 passed |
| Repository/notebook secret scan: `tests\test_secret_scan.py` | 1 passed |
| VS Code diagnostics for touched source and tests | No errors |
| `git diff --check` | No errors |

Profile tests cover actionable required-field validation, allowed level values, free-text roles, optional-domain omission, per-user isolation, restart persistence, task normalization, and preservation of estimated-level state when declared level changes. Streamlit tests cover mandatory onboarding, suggested tasks, task removal and supplementation, profile editing, personalized Home, protected navigation, and sign-out/sign-in restoration.

## Migration checks

Both paths reached `20260831_0003 (head)`:

1. An empty SQLite database upgraded directly to head.
2. A database first stopped at `20260831_0002` and then upgraded to head.

Both produced the expected `users` and `learner_profiles` columns. The profile table has one unique, cascading foreign key to `users.id`, allowed-value checks for declared/estimated levels and level source, a 0-1 confidence check, and no foreign-key violations. The workspace database also upgraded from T02 to T03 successfully.

## Live product walkthrough

The application was run at `http://localhost:8502` against the migrated local SQLite database.

1. A new account was registered and routed to **Set up your learner profile** with no protected navigation visible.
2. The searchable role control accepted the unrestricted custom role `Solutions architect`.
3. All suggested tasks were removed and replaced with `Design cloud migration plans` and `Explain architecture decisions`.
4. The optional domain `Azure, enterprise platforms` and declared level `JLPT N4` were saved. Home immediately showed the role, level, tasks, and domain.
5. Profile restored every saved field, displayed the future estimated working level as not set, and showed optional placement as unavailable.
6. Declared level was changed to `JLPT N3`; the profile saved successfully without creating an estimated level.
7. After sign-out and sign-in, Home restored the complete profile at `JLPT N3` without repeating onboarding.
8. After stopping and restarting the full Streamlit process, authentication was cleared. Signing in again returned directly to personalized Home with the same persisted role, tasks, domain, and `JLPT N3` level.

Required-field feedback was exercised by the Streamlit test because the live profile was completed with valid values. A second user with a different free-text role and profile is covered by the isolated service test, which proves reads remain scoped to the requested authenticated user ID.

## Persistence and privacy inspection

The T03 schema stores only account identity/authentication fields and the intended structured learner profile fields. It introduces no lesson, question, translation, uploaded-document, or mastery content storage. The walkthrough account is temporary and was removed after verification; no default or shared credential was added.

## Acceptance result

All T03 acceptance criteria passed. Required profile values gate onboarding with actionable errors; common suggestions and free text both work; tasks can be removed, edited, and supplemented; optional domain data may be omitted; profile editing preserves the declared/estimated level boundary; values survive sign-out and process restart; and all service reads and writes are scoped by user ID.