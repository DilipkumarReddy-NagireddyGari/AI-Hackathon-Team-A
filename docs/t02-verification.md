# T02 Verification Record

Verified on 2026-08-31 against Python 3.14.3 and migration revision `20260831_0002`.

## Automated checks

| Check | Result |
|---|---:|
| Full test suite: `.venv\Scripts\python.exe -m pytest` | 17 passed |
| Authentication service: `tests\test_auth.py` | 5 passed |
| Streamlit app flow: `tests\test_app.py` | 5 passed |
| Fresh and T01 upgrade migrations: `tests\test_migrations.py` | 2 passed |
| Repository/notebook secret scan: `tests\test_secret_scan.py` | 1 passed |
| VS Code diagnostics for source, tests, and migrations | No errors |
| `git diff --check` | No errors |

The authentication tests cover Argon2id storage, normalized duplicate rejection, the same generic error for unknown usernames and incorrect passwords, distinct identities, and login through a recreated engine. Streamlit tests cover the signed-out route guard, registration, logout, later login, all protected pages, and the existing startup-health states.

## Migration checks

Both paths reached `20260831_0002 (head)`:

1. An empty SQLite database upgraded directly to head.
2. A database first stopped at `20260828_0001` and then upgraded to head.

Both produced `id`, `username`, `normalized_username`, `password_hash`, `created_at`, and `updated_at` columns with no foreign-key-check violations. The workspace database was also upgraded from T01 to T02 successfully.

## Live product walkthrough

The application was run at `http://localhost:8502` against the migrated local SQLite database.

1. The signed-out screen showed Demo authentication and no protected navigation.
2. Two different local accounts were registered without email addresses; each reached Home under a distinct displayed identity.
3. Home, Learn, Translate, Progress, and Profile all opened while authenticated.
4. Sign out removed the authenticated identity and returned to the guarded authentication screen.
5. An incorrect password produced only `Invalid username or password.`.
6. The valid password and a different username case signed in successfully.
7. A registration using different case and surrounding whitespace for an existing username produced `That username is already registered.`.
8. After stopping and restarting the full Streamlit process, no authenticated session remained, but the persisted first account signed in successfully.

## Redacted persistence inspection

The two walkthrough rows had distinct integer IDs, normalized usernames matching their login keys, and 97-character password values beginning with `$argon2id$`. No plaintext password column exists. Only these redacted properties were printed; complete hashes were not displayed.

All temporary walkthrough accounts were deleted after verification. No default or shared credential was added.

## Acceptance result

All T02 acceptance criteria passed. Account records persist across application restarts while authentication remains intentionally session-only. There are no user-owned learner records in T02; the app exposes no cross-user read or mutation interface, and the two authenticated identities remained distinct throughout the walkthrough.