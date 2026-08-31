# T04 Verification Record

**Task:** Deterministic first lesson loop  
**Status:** Executed and accepted  
**Date:** 2026-08-31  
**Migration head:** `20260831_0004`

## Product Checkpoint

The local Streamlit application ran at `http://localhost:8502/` with the existing authenticated demo user. The Learn page rendered a deterministic workplace status-update lesson containing five target items and five questions across meaning, reading, and contextual-cloze forms.

The live walkthrough submitted three correct and two incorrect answers. Immediate feedback appeared after every immutable submission, the recap appeared only after all five answers, and completion returned the user to a fresh Learn start state. Progress displayed:

| Result group | Items | Mastery | Next review |
|---|---:|---:|---|
| Correct | 3 | `0.10` each | One day after submission |
| Incorrect | 2 | `0.00` each | Ten minutes after submission |

Each item showed one exposure. The completion summary retained only topic ID `fixture-status-update-01`, difficulty, studied item IDs, and timestamp.

A browser refresh cleared authentication and the active session content. Before refresh, Progress showed the persisted results; after the walkthrough, direct SQLite inspection confirmed the compact rows remained.

## Automated Verification

- Full suite: **26 passed**.
- Lesson service and retention suite: **4 passed**.
- Streamlit application suite: **7 passed**.
- Migration suite: **2 passed**.
- Pylance and VS Code diagnostics: no errors in any touched Python file.
- Fresh database and T03-state database both upgraded to `20260831_0004 (head)`.

The lesson tests verify:

- exposure does not raise mastery;
- correct and incorrect answers update deterministic progress and schedules;
- a duplicate submission cannot add another attempt or mastery gain;
- incomplete lessons cannot create completion metadata;
- completion is idempotent;
- progress and completion metadata survive engine restart;
- progress queries are scoped by authenticated user;
- passage, examples, prompts, options, explanations, feedback source text, and recap are absent from SQLite.

## Live Persistence Audit

The post-walkthrough database contained:

```text
learning_items: 5
user_item_progress: 5
review_attempts: 5
completed_lesson_metadata: 1
prohibited content matches: 0
foreign-key violations: 0
```

Canonical item IDs are stable ASCII semantic slugs, so persisted identity fields do not duplicate Japanese lesson or option text. Review attempts retain only user/item IDs, a random lesson-session ID, a hashed idempotency key, question form, correctness, retry marker, and timestamp.

## Initial T04 Policy

T04 deliberately uses a small provisional policy to prove the evidence and retention boundary independently of model behavior:

- exposure: increment exposure count only;
- correct answer: mastery `+0.10`, capped at `1.00`, next review in one day;
- incorrect answer: no mastery gain, next review in ten minutes;
- no retry/outcome/SM-2 claim is made in T04.

T05 owns the versioned dimension-aware mastery policy, corrective delayed retry, Again/Hard/Good/Easy mapping, consecutive-review guards, ease, and interval behavior.

## Handoff To T05

- Extend compact attempt evidence with skill dimension, first/retry marker semantics, mapped outcome, and policy version; do not add question text.
- Extend progress with dimension scores, consecutive-review state, SM-2 interval/ease, and deterministic UTC scheduling.
- Preserve the unique user/idempotency boundary and immutable original failed attempts.
- Reuse `LessonService` as the application-owned scoring boundary; model output must never write mastery or schedules.
- Add a varied delayed question for failed items and golden clock-controlled vectors before changing the provisional T04 constants.