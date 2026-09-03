# T07 Verification - Validated generated scenario lessons

**Execution date:** 2026-09-01  
**Status:** Executed

## Delivered checkpoint

T07 adds the first LLM-assisted learning slice. A signed-in learner can enter an English or Japanese workplace scenario, confirm the detected mode, and request a profile-adapted lesson. Validated lesson content renders first while a separate grounded quiz is generated in memory. Only a promoted content-plus-quiz package can enter the existing deterministic scoring, retry, mastery, scheduling, and completion path. The UI identifies the successful route separately for lesson content and quiz generation.

## Automated verification

Commands run from the project root with the pinned virtual environment:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m pytest tests\test_generation.py
.venv\Scripts\python.exe -m pytest tests\test_secret_scan.py
git diff --check
```

Results:

- Full suite: **54 passed**.
- Focused generation suite: **20 passed**.
- Streamlit integration suite: **11 passed**.
- VS Code diagnostics: no errors in the touched service, UI, and test files.
- Whitespace validation: passed with no output.

## Provider and validation matrix

Fake transports verified these deterministic paths:

1. Valid first Tsuzumi response returns a lesson labeled **Tsuzumi 2** with one call.
2. Tsuzumi timeout followed by valid repair returns **Tsuzumi 2** without GPT fallback.
3. Malformed and schema-invalid Tsuzumi responses trigger exactly two primary calls, then a valid GPT response returns a lesson labeled **GPT-5 nano**.
4. A schema-invalid first GPT response receives one repair attempt with sanitized validation feedback.
5. Four failed attempts return one safe error, preserve the scenario, and create no progress.
6. Valid but stylistically unevaluated output does not trigger fallback.
7. Out-of-range answer keys, missing canonical references, duplicate IDs, wrong counts, and unvaried retries fail schema validation before rendering or scoring.
8. Passage lines and line explanations must match exactly and in order; each quiz target must be a Japanese kanji, vocabulary, or grammar item included in those explanations.
9. Explain mode rejects rewritten or additional Japanese text and requires each target-item example to reuse an exact source line.
10. Scenario prompts explicitly give technical, general, or social scenario intent priority over role context. Blank prompts request a varied topic and include recent topic IDs to reduce repetition.
11. Compact item mastery and exposure evidence is supplied with the learner's working JLPT level for quiz and difficulty personalization.
12. Lesson content and quizzes use independent strict schemas, so content can render before quiz generation completes.
13. Technical Tsuzumi failures skip a redundant same-route retry and fall back immediately; schema failures retain one repair attempt.
14. Quiz questions and retries are rejected unless every item ID belongs to the validated lesson content.
15. GPT-5 requests use low reasoning effort and strict JSON Schema output; the Tsuzumi payload remains compatible with JSON-object mode.
16. Generated dialogue is canonicalized from its validated explanation lines, while Explain mode retains exact source text and line order.
17. Target items must be atomic Japanese expressions copied from line explanations rather than whole utterances.

Operational records include provider, configured model ID, attempt number, status, latency, and fallback reason. They exclude scenario/profile content, prompts, responses, lesson content, exception details, endpoint, and credential.

## Deterministic learning loop

- Validated generated questions are resolved from the promoted active session lesson, not fixture globals or model-provided state mutations.
- Opening validated content creates exposure only. Promoting its background quiz does not create duplicate exposure.
- Objective answers use application-owned correctness, evidence dimensions, `t05-v1` mastery, and SM-2 calculations.
- Incorrect answers require the package's separately validated varied retry.
- Completion stores only topic ID, difficulty, canonical studied item IDs, user/session identity, and timestamp.
- A SQLite dump after generated lesson completion contained no passage, examples, prompts, options, explanations, retry content, or recap.

## Live product walkthrough

The existing app at [http://localhost:8502/](http://localhost:8502/) reloaded with T07 while signed in to the local verification profile.

Observed sequence:

1. Startup health reported **Model features: configured** without exposing values.
2. Learn displayed the scenario text area, both explicit modes, detected/default mode text, generated lesson action, and offline fixture fallback.
3. An English software-requirement scenario defaulted to **Generate a lesson from this scenario**.
4. Proxy diagnostics identified HTTP 500 upstream connection failures from `tsuzumi2` and HTTP 200 responses from `gpt-5-nano`.
5. A full GPT-5 nano lesson response took 56.8 seconds, exceeding the original 45-second transport timeout.
6. After raising the configurable timeout to 90 seconds, the complete application policy returned a validated fallback lesson with 4 items, 4 questions, and 4 retries.
7. The shared Streamlit page then generated the learner's nomikai scenario as a 5-item, 5-question lesson and displayed **Generated with GPT-5 nano**.
8. After adding exhaustive line explanations, a live GPT-5 nano probe exceeded 90 seconds before returning content. The configurable default was raised to 180 seconds for the larger response contract.
9. After splitting generation, enabling low GPT-5 reasoning, and using structured output, a live nomikai content phase validated in **50.4 seconds** with 5 dialogue lines, 5 matching line explanations, and 5 target items.
10. The live nomikai passage contained social-topic language and no detected requirements, design, coding, development, specification, or software topic terms despite the Software engineer profile.
11. A separate live quiz response validated with 4 questions and 4 varied retries, all grounded in the supplied lesson item IDs. Quiz work is outside the content-render critical path.

The successful content fallback is labeled **Lesson generated with GPT-5 nano**. Lesson and quiz routes are attributed independently. Streamlit and transport tests verify both phase labels. The live server remains available on port `8502`.

## Persistence and migration

- T07 adds no database table or column. Alembic head remains `20260831_0005`.
- Generated scenario and lesson content live only in Streamlit session state and are cleared on leave or sign-out.
- Total generation failure occurs before lesson start and therefore cannot create exposure, evidence, or completion rows.
- Existing fresh/populated migration, foreign-key, cross-user, retention, and secret-scan checks remain in the full suite.

## Acceptance result

- [x] English and Japanese scenarios have an explicit confirmable mode.
- [x] Strictly valid output completes through deterministic scoring and persistence.
- [x] Invalid or partial output cannot render or score.
- [x] Tsuzumi receives one repair/retry before GPT fallback.
- [x] Structurally valid output does not fall back for subjective style.
- [x] Total failure preserves scenario input and changes no progress.
- [x] Generated lesson content displays the successful LLM provider as requested.
- [x] Scenario subject outranks role context, so general and social situations do not inherit unrelated technical topics.
- [x] Generated lessons are multi-turn conversations rather than lesson descriptions.
- [x] Explain mode preserves the submitted Japanese text and adds no Japanese sentences.
- [x] Every passage line includes visible kanji, vocabulary, and grammar explanations.
- [x] Quizzes target Japanese language points from the passage and receive compact prior-learning context.
- [x] Validated content renders before quiz generation and exposes a **Go to quiz** transition.
- [x] Quiz generation runs in a background I/O worker and remains hidden until requested.
- [x] Lesson and quiz providers are attributed separately.

## Residual scope

Provider route availability remains external to the application. T08 should reuse the generation boundary for application-selected topics. Every later LLM-generated content surface must carry the successful provider name into its UI while continuing to hide endpoint, model ID, prompt, response, and credential details.