"""Live T07 probe: exercises the real two-phase content + quiz generation path."""

import logging
import sys
from time import monotonic

from japanese_workplace_tutor.generation import (
    GenerationError,
    LessonGenerationService,
    OpenAICompatibleTransport,
    ScenarioMode,
    detect_scenario_mode,
)
from japanese_workplace_tutor.profile import JapaneseLevel, LevelSource, ProfileRecord
from japanese_workplace_tutor.settings import get_settings


logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

PROFILE = ProfileRecord(
    user_id=1,
    role="Software engineer",
    tasks=("Daily standup", "Code review"),
    tools_domain="Python, Azure",
    declared_level=JapaneseLevel.N4,
    estimated_working_level=None,
    level_source=LevelSource.SELF_REPORTED,
    level_confidence=0.5,
    romaji_preference=False,
)


def main() -> int:
    scenario = " ".join(sys.argv[1:]) or "Asking a teammate to review my pull request"
    settings = get_settings()
    print(f"Model features: {settings.model_status}")
    if not settings.model_configured:
        print("Aborting: model settings are incomplete.")
        return 2

    assert settings.model_base_url and settings.model_api_key
    assert settings.primary_model and settings.fallback_model
    service = LessonGenerationService(
        OpenAICompatibleTransport(
            settings.model_base_url,
            settings.model_api_key.get_secret_value(),
            settings.model_timeout_seconds,
        ),
        settings.primary_model,
        settings.fallback_model,
        primary_timeout_seconds=settings.primary_model_timeout_seconds,
    )

    mode = detect_scenario_mode(scenario)
    print(f"Scenario: {scenario!r}\nDetected mode: {mode.value}\n")

    started = monotonic()
    try:
        draft = service.generate_lesson_content(scenario, mode, PROFILE)
    except GenerationError as error:
        print(f"CONTENT PHASE FAILED after {monotonic() - started:.1f}s: {error}")
        return 1
    print(
        f"\nCONTENT OK in {monotonic() - started:.1f}s via {draft.provider_name}\n"
        f"  title={draft.content.title}\n"
        f"  difficulty={draft.content.difficulty}\n"
        f"  passage_lines={len(draft.content.passage.splitlines())}\n"
        f"  explanations={len(draft.line_explanations)}\n"
        f"  items={len(draft.content.items)}\n"
    )
    print(draft.content.passage)

    started = monotonic()
    try:
        quiz = service.generate_quiz(draft.content)
    except GenerationError as error:
        print(f"\nQUIZ PHASE FAILED after {monotonic() - started:.1f}s: {error}")
        return 1
    print(
        f"\nQUIZ OK in {monotonic() - started:.1f}s via {quiz.provider_name}\n"
        f"  questions={len(quiz.questions)} retries={len(quiz.retry_questions)}"
    )
    for question in quiz.questions:
        print(f"  - [{question.form.value}] {question.prompt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
