# T06 Verification - Due-item review experience

**Execution date:** 2026-09-01  
**Status:** Executed

## Delivered checkpoint

T06 turns T05 schedules into a user-facing Home review without changing the database schema. The signed-in learner sees a due count, can start an ordered review of at most five items, skip without mutation, submit objective answers through the existing `t05-v1` policy, and return Home to see refreshed due work and the earliest remaining schedule. Starting a new lesson remains available throughout.

## Automated verification

Commands run from the project root with the pinned virtual environment:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m pytest tests\test_secret_scan.py -q
.venv\Scripts\python.exe -m pytest tests\test_migrations.py -q
git diff --check
```

Results:

- Full suite: **32 passed in 32.20s**.
- Focused secret scan: **1 passed**.
- Migration checks: **2 passed**.
- Whitespace validation: passed with no output.
- Focused lesson and app suites: **17 passed** before final validation.
- Pylance and VS Code diagnostics: no errors in the changed service, UI, and test files.

## Deterministic service checks

A controlled clock fixed the current time at `2026-08-31 12:00:00` and seeded seven due items.

Verified behavior:

1. Due counts are scoped by authenticated user.
2. Selection uses `next_review_at <= now`.
3. Ordering is earliest due date, lowest mastery, then canonical ID.
4. A review contains exactly the first five records when seven are due.
5. Question selection targets the lowest-scored available skill dimension with a stable question-ID tie-breaker.
6. Starting a review leaves every progress row unchanged.
7. One correct review submission creates one immutable evidence row and moves the item out of the due set.
8. Repeating the same submission returns the original result and leaves the evidence-row count at one.

## Live product walkthrough

The app was started at [http://localhost:8502/](http://localhost:8502/) and a temporary local verification account was given seven overdue schedules.

Observed sequence:

1. Home displayed **7 items due**.
2. **Review due items** was the primary button and **Start a lesson** remained visible.
3. Starting review rendered **5 items in this review**, ordered deterministically.
4. **Skip review** returned Home with **7 items due**, proving no schedule mutation.
5. A second review was completed with one incorrect and four correct first attempts.
6. Home displayed **Review complete: 4 of 5 correct**.
7. Home then displayed **2 items due**, representing the two items outside the five-item session.
8. **Start a lesson** remained available after completion.

The live verification server remains available on port `8502` for inspection.
The temporary verification account and its cascaded progress/evidence rows were removed after sign-out.

## Persistence and privacy

- T06 adds no table or column. Alembic head remains `20260831_0005`.
- Clean migration and populated T04-to-T05 migration checks still pass.
- The retention test submitted both fixture-lesson and due-review answers, dumped SQLite, and found no fixture/review passage, prompt, option, explanation, example, or recap content.
- Persisted review data remains limited to canonical item IDs, question form, skill dimension, result/outcome, policy version, timestamps, and progress/schedule fields.
- The tracked-source and notebook-output secret scan passed.

## Acceptance result

- [x] No-due Home uses **Continue learning** as its primary action.
- [x] Due Home uses **Review due items** as its primary action and displays the due count.
- [x] Review sessions contain no more than five items.
- [x] Skip leaves schedules unchanged and lesson access visible.
- [x] Review answers update evidence, mastery, and schedules exactly once.
- [x] Completion refreshes Home due state and schedule summary consistently.

## Residual scope

Generated questions, reminders, and review-gated lessons remain out of scope. The current review bank is deterministic and local. Future generated review content must pass structural validation and must continue using the application-owned evidence and SM-2 policy.
