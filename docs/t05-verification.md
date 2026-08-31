# T05 Verification Record

Verified on 2026-08-31.

## Result

T05 is executed. The application provides deterministic dimension-aware mastery, immutable failure and recovery evidence, alternate-form delayed retries, guarded Easy/mastery outcomes, and simplified SM-2 scheduling under policy `t05-v1`.

## Automated Verification

- Full suite: `29 passed` with `.venv\Scripts\python.exe -m pytest`.
- Focused lesson suite: `6 passed` with `.venv\Scripts\python.exe -m pytest tests\test_lesson.py -q`.
- Migration suite: `2 passed` with `.venv\Scripts\python.exe -m pytest tests\test_migrations.py -q`.
- Streamlit acceptance coverage verifies immediate correction, alternate retry form/item identity, Hard recovery feedback, and completion availability.
- `git diff --check` completed without errors.
- Language-service diagnostics reported no errors in the changed application, model, migration-test, lesson-test, or app-test files.

## Golden Policy Traces

Initial state is mastery `0.00`, ease `2.50`, interval `0`.

| Evidence | Mastery | Ease | Interval | Next review |
|---|---:|---:|---:|---|
| Incorrect first attempt: Again | `0.00` | `2.30` | `0` | 10 minutes |
| Correct alternate retry: Hard | `0.08` | `2.15` | `1` | 1 day |
| Next separate first-try success: Good | `0.26` | `2.20` | `3` | 3 days |
| Next separate first-try success: Good | `0.44` | `2.25` | `7` | 7 days |
| Eligible varied first-try success: Easy | `0.74` | `2.40` | `22` | 22 days |
| Eligible varied first-try success: Easy | `1.00` | `2.55` | `73` | 73 days |

Easy requires at least two preceding consecutive first-try successes from separate sessions and successful evidence across at least two forms. Non-Easy and single-form evidence cannot exceed mastery `0.79`, below the `0.80` mastery threshold.

## Migration Verification

- Clean database upgrade reached `20260831_0005 (head)`.
- A populated T04 database upgraded from `20260831_0004` to head.
- Existing contextual grammar evidence backfilled to dimension `grammar_application`, outcome `again`, and policy `t04-provisional`.
- Existing progress retained its counters/mastery while new dimensions, consecutive successes, interval, and ease received conservative defaults.
- Foreign-key checks returned no violations.

## Live Product Walkthrough

The app was started at `http://localhost:8502/` after upgrading the local database to head.

1. Registered a temporary local account and completed onboarding.
2. Started the fixture lesson and deliberately answered all five first-pass questions incorrectly.
3. Confirmed each answer immediately displayed the correct option and explanation.
4. Confirmed five corrective questions appeared only after first-pass practice and each used a different form/content for the same canonical item.
5. Answered every retry correctly and confirmed each was labeled as Hard recovery rather than first-try success.
6. Confirmed completion stayed unavailable until all retries were attempted, then completed the lesson.
7. Opened Progress and confirmed five items each showed one incorrect attempt and one correct recovery.
8. Inspected SQLite: five Again rows and five separate Hard retry rows used `t05-v1`; recovered progress was mastery `0.08`, ease `2.15`, interval `1` for each item.
9. Removed the temporary verification account after recording the trace.

## Retention and Isolation

- SQLite stores canonical item IDs, question form/dimension, correctness, retry marker, mapped outcome, policy version, timestamps, and schedule state.
- The retention canary covers all fixture and retry prompts, options, explanations, examples, passage, and recap; none appeared in the database dump.
- Attempt and progress queries remain user-scoped, submissions remain idempotent, and exposure alone does not increase mastery.

## Deferred Work

- T06 owns due-item selection and the skippable review experience of up to five items.
- Generated lesson/retry content and model failure handling remain T07 work.
- T10 owns richer progress/weakness visualization.