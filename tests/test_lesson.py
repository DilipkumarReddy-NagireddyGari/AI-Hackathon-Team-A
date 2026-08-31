from datetime import datetime
from pathlib import Path
import sqlite3

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from japanese_workplace_tutor.auth import AuthenticationService
from japanese_workplace_tutor.database import create_database_engine
from japanese_workplace_tutor.lesson import FIXTURE_LESSON, LessonService, LessonStateError
from japanese_workplace_tutor.models import (
    Base,
    CompletedLessonMetadata,
    ReviewAttempt,
)
from japanese_workplace_tutor.settings import Settings


NOW = datetime(2026, 8, 31, 12, 0, 0)


def create_services(database_path: Path):
    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}", _env_file=None
    )
    engine = create_database_engine(settings)
    Base.metadata.create_all(engine)
    auth = AuthenticationService(engine)
    return auth, LessonService(engine, clock=lambda: NOW), engine


def test_exposure_does_not_raise_mastery_and_answers_are_idempotent(
    tmp_path: Path,
) -> None:
    auth, lessons, engine = create_services(tmp_path / "lesson.db")
    user = auth.register("Alice", "correct horse battery staple")

    active = lessons.start_fixture_lesson(user.id, "11111111-1111-1111-1111-111111111111")
    before = lessons.get_progress(user.id)
    assert len(before) == 5
    assert all(record.exposure_count == 1 for record in before)
    assert all(record.mastery_score == 0.0 for record in before)

    question = FIXTURE_LESSON.questions[0]
    first = lessons.submit_answer(
        user.id,
        active.lesson_session_id,
        question.question_id,
        question.correct_option_index,
    )
    duplicate = lessons.submit_answer(
        user.id,
        active.lesson_session_id,
        question.question_id,
        question.correct_option_index + 1,
    )

    assert first.is_correct is True
    assert first.mastery_score == 0.1
    assert duplicate.is_correct is True
    assert duplicate.mastery_score == 0.1
    assert duplicate.duplicate is True
    lessons.start_fixture_lesson(user.id)
    reopened_progress = lessons.get_progress(user.id)
    assert all(record.exposure_count == 2 for record in reopened_progress)
    answered_item = next(
        record for record in reopened_progress if record.item_id == question.item_id
    )
    assert answered_item.mastery_score == 0.1
    with Session(engine) as session:
        assert session.scalar(select(func.count(ReviewAttempt.id))) == 1
    engine.dispose()


def test_mixed_answers_create_compact_progress_and_one_completion(
    tmp_path: Path,
) -> None:
    auth, lessons, engine = create_services(tmp_path / "lesson.db")
    user = auth.register("Alice", "correct horse battery staple")
    active = lessons.start_fixture_lesson(user.id)

    with pytest.raises(LessonStateError, match="Answer every question"):
        lessons.complete_fixture_lesson(user.id, active.lesson_session_id)
    assert lessons.get_completions(user.id) == ()

    for index, question in enumerate(FIXTURE_LESSON.questions):
        selected = question.correct_option_index if index % 2 == 0 else 3
        lessons.submit_answer(
            user.id, active.lesson_session_id, question.question_id, selected
        )

    completion = lessons.complete_fixture_lesson(user.id, active.lesson_session_id)
    duplicate = lessons.complete_fixture_lesson(user.id, active.lesson_session_id)
    progress = lessons.get_progress(user.id)

    assert completion == duplicate
    assert completion.topic_id == FIXTURE_LESSON.topic_id
    assert completion.difficulty == FIXTURE_LESSON.difficulty
    assert completion.studied_item_ids == tuple(
        item.canonical_id for item in FIXTURE_LESSON.items
    )
    assert sum(record.correct_count for record in progress) == 3
    assert sum(record.incorrect_count for record in progress) == 2
    with Session(engine) as session:
        assert session.scalar(select(func.count(ReviewAttempt.id))) == 5
        assert session.scalar(select(func.count(CompletedLessonMetadata.id))) == 1
    engine.dispose()

    _, restarted_lessons, restarted_engine = create_services(tmp_path / "lesson.db")
    assert restarted_lessons.get_completions(user.id) == (completion,)
    restarted_engine.dispose()


def test_progress_is_user_scoped_and_survives_engine_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "lesson.db"
    auth, lessons, engine = create_services(database_path)
    alice = auth.register("Alice", "correct horse battery staple")
    bob = auth.register("Bob", "another secure password")
    active = lessons.start_fixture_lesson(alice.id)
    question = FIXTURE_LESSON.questions[0]
    lessons.submit_answer(
        alice.id,
        active.lesson_session_id,
        question.question_id,
        question.correct_option_index,
    )
    assert lessons.get_progress(bob.id) == ()
    engine.dispose()

    _, restarted_lessons, restarted_engine = create_services(database_path)
    restored = restarted_lessons.get_progress(alice.id)
    assert len(restored) == 5
    assert sum(record.correct_count for record in restored) == 1
    assert restarted_lessons.get_completions(alice.id) == ()
    restarted_engine.dispose()


def test_database_excludes_replayable_fixture_content(tmp_path: Path) -> None:
    database_path = tmp_path / "lesson.db"
    auth, lessons, engine = create_services(database_path)
    user = auth.register("Alice", "correct horse battery staple")
    active = lessons.start_fixture_lesson(user.id)
    for question in FIXTURE_LESSON.questions:
        lessons.submit_answer(
            user.id,
            active.lesson_session_id,
            question.question_id,
            question.correct_option_index,
        )
    lessons.complete_fixture_lesson(user.id, active.lesson_session_id)
    engine.dispose()

    with sqlite3.connect(database_path) as connection:
        database_dump = "\n".join(connection.iterdump())

    prohibited_content = [FIXTURE_LESSON.passage, FIXTURE_LESSON.recap]
    prohibited_content.extend(item.example for item in FIXTURE_LESSON.items)
    for question in FIXTURE_LESSON.questions:
        prohibited_content.extend((question.prompt, question.explanation))
        prohibited_content.extend(question.options)

    leaked_content = [
        content for content in prohibited_content if content in database_dump
    ]
    assert leaked_content == []