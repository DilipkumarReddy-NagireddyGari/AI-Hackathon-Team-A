"""Deterministic fixture lesson and compact, user-scoped learning evidence."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Engine, func, select
from sqlalchemy.orm import Session

from .models import (
    CompletedLessonMetadata,
    LearningItem,
    ReviewAttempt,
    UserItemProgress,
)


class ItemCategory(StrEnum):
    KANJI = "kanji"
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"


class QuestionForm(StrEnum):
    MEANING = "meaning"
    READING = "reading"
    CONTEXTUAL_CLOZE = "contextual_cloze"


class FixtureItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_id: str = Field(min_length=1, max_length=128)
    category: ItemCategory
    expression: str
    reading: str
    meaning: str
    example: str
    jlpt_level: str | None
    jlpt_provenance: str
    jlpt_confidence: float = Field(ge=0.0, le=1.0)


class FixtureQuestion(BaseModel):
    model_config = ConfigDict(frozen=True)

    question_id: str = Field(min_length=1, max_length=64)
    item_id: str
    form: QuestionForm
    prompt: str
    options: tuple[str, str, str, str]
    correct_option_index: int = Field(ge=0, le=3)
    explanation: str


class FixtureLesson(BaseModel):
    model_config = ConfigDict(frozen=True)

    topic_id: str
    title: str
    difficulty: str
    passage: str
    items: tuple[FixtureItem, ...]
    questions: tuple[FixtureQuestion, ...]
    recap: str

    @model_validator(mode="after")
    def validate_lesson(self) -> "FixtureLesson":
        item_ids = [item.canonical_id for item in self.items]
        question_ids = [question.question_id for question in self.questions]
        if not 3 <= len(item_ids) <= 7:
            raise ValueError("A lesson must contain 3-7 target items.")
        if not 4 <= len(question_ids) <= 6:
            raise ValueError("A lesson must contain 4-6 questions.")
        if len(item_ids) != len(set(item_ids)):
            raise ValueError("Lesson item IDs must be unique.")
        if len(question_ids) != len(set(question_ids)):
            raise ValueError("Lesson question IDs must be unique.")
        if any(question.item_id not in item_ids for question in self.questions):
            raise ValueError("Every question must reference a lesson item.")
        return self


FIXTURE_LESSON = FixtureLesson(
    topic_id="fixture-status-update-01",
    title="Giving a concise project status update",
    difficulty="JLPT N4-N3 bridge",
    passage=(
        "田中さん、お疲れさまです。開発の進捗を共有します。新しい機能は予定どおり完成しました。"
        "ただ、テストで問題が見つかったので、リリース日を確認してもよろしいでしょうか。"
        "詳しい状況は午後の会議で報告します。"
    ),
    items=(
        FixtureItem(
            canonical_id="kanji:shin-progress",
            category=ItemCategory.KANJI,
            expression="進",
            reading="しん / すすむ",
            meaning="advance; progress",
            example="作業を進めます。",
            jlpt_level="JLPT N3",
            jlpt_provenance="fixture-reference",
            jlpt_confidence=0.9,
        ),
        FixtureItem(
            canonical_id="vocabulary:shinchoku",
            category=ItemCategory.VOCABULARY,
            expression="進捗",
            reading="しんちょく",
            meaning="progress or status of work",
            example="プロジェクトの進捗を共有します。",
            jlpt_level="JLPT N2",
            jlpt_provenance="fixture-reference",
            jlpt_confidence=0.8,
        ),
        FixtureItem(
            canonical_id="vocabulary:kyouyuu",
            category=ItemCategory.VOCABULARY,
            expression="共有",
            reading="きょうゆう",
            meaning="sharing information",
            example="チームに情報を共有します。",
            jlpt_level="JLPT N3",
            jlpt_provenance="fixture-reference",
            jlpt_confidence=0.8,
        ),
        FixtureItem(
            canonical_id="grammar:permission-temo-yoroshii",
            category=ItemCategory.GRAMMAR,
            expression="〜てもよろしいでしょうか",
            reading="〜てもよろしいでしょうか",
            meaning="may I ...?; a polite request for permission",
            example="予定を変更してもよろしいでしょうか。",
            jlpt_level="JLPT N3",
            jlpt_provenance="fixture-reference",
            jlpt_confidence=0.8,
        ),
        FixtureItem(
            canonical_id="vocabulary:houkoku",
            category=ItemCategory.VOCABULARY,
            expression="報告",
            reading="ほうこく",
            meaning="a report; to report",
            example="会議で結果を報告します。",
            jlpt_level="JLPT N3",
            jlpt_provenance="fixture-reference",
            jlpt_confidence=0.9,
        ),
    ),
    questions=(
        FixtureQuestion(
            question_id="meaning-progress",
            item_id="vocabulary:shinchoku",
            form=QuestionForm.MEANING,
            prompt="In a project update, what does 進捗 mean?",
            options=("Progress of work", "Final approval", "Meeting agenda", "Budget"),
            correct_option_index=0,
            explanation="進捗 describes how far work or a project has progressed.",
        ),
        FixtureQuestion(
            question_id="reading-share",
            item_id="vocabulary:kyouyuu",
            form=QuestionForm.READING,
            prompt="How is 共有 read?",
            options=("きょうゆう", "きょうよう", "こうゆう", "こうよう"),
            correct_option_index=0,
            explanation="共有 is read きょうゆう and means sharing information.",
        ),
        FixtureQuestion(
            question_id="cloze-permission",
            item_id="grammar:permission-temo-yoroshii",
            form=QuestionForm.CONTEXTUAL_CLOZE,
            prompt="Choose the polite phrase: リリース日を確認し___。",
            options=("てもよろしいでしょうか", "てはいけません", "たことがあります", "ながら"),
            correct_option_index=0,
            explanation="〜てもよろしいでしょうか politely asks for permission.",
        ),
        FixtureQuestion(
            question_id="meaning-report",
            item_id="vocabulary:houkoku",
            form=QuestionForm.MEANING,
            prompt="Which action is 報告する?",
            options=("To report", "To postpone", "To approve", "To investigate"),
            correct_option_index=0,
            explanation="報告する means to report information or results.",
        ),
        FixtureQuestion(
            question_id="reading-kanji-progress",
            item_id="kanji:shin-progress",
            form=QuestionForm.READING,
            prompt="What is the reading of 進 in 進捗?",
            options=("しん", "じん", "せん", "ぜん"),
            correct_option_index=0,
            explanation="The on-reading of 進 in 進捗 is しん.",
        ),
    ),
    recap=(
        "Use 進捗, 共有, and 報告 to structure a status update. "
        "Use 〜てもよろしいでしょうか when politely checking permission."
    ),
)


class LessonStateError(ValueError):
    pass


@dataclass(frozen=True)
class ActiveLesson:
    lesson_session_id: str
    lesson: FixtureLesson


@dataclass(frozen=True)
class AttemptResult:
    item_id: str
    question_id: str
    is_correct: bool
    mastery_score: float
    next_review_at: datetime
    duplicate: bool


@dataclass(frozen=True)
class ProgressRecord:
    item_id: str
    category: ItemCategory
    exposure_count: int
    correct_count: int
    incorrect_count: int
    mastery_score: float
    last_answered_at: datetime | None
    next_review_at: datetime | None


@dataclass(frozen=True)
class CompletionRecord:
    topic_id: str
    difficulty: str
    studied_item_ids: tuple[str, ...]
    completed_at: datetime


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class LessonService:
    CORRECT_MASTERY_GAIN = 0.10
    CORRECT_REVIEW_DELAY = timedelta(days=1)
    INCORRECT_REVIEW_DELAY = timedelta(minutes=10)

    def __init__(
        self, engine: Engine, clock: Callable[[], datetime] = _utc_now
    ) -> None:
        self._engine = engine
        self._clock = clock

    def start_fixture_lesson(
        self, user_id: int, lesson_session_id: str | None = None
    ) -> ActiveLesson:
        session_id = lesson_session_id or str(uuid4())
        with Session(self._engine) as session:
            for fixture_item in FIXTURE_LESSON.items:
                self._ensure_item(session, fixture_item)
                progress = self._get_progress(
                    session, user_id, fixture_item.canonical_id
                )
                if progress is None:
                    progress = UserItemProgress(
                        user_id=user_id,
                        item_id=fixture_item.canonical_id,
                        exposure_count=1,
                    )
                    session.add(progress)
                else:
                    progress.exposure_count += 1
            session.commit()
        return ActiveLesson(session_id, FIXTURE_LESSON)

    def submit_answer(
        self,
        user_id: int,
        lesson_session_id: str,
        question_id: str,
        selected_option_index: int,
    ) -> AttemptResult:
        question = next(
            (
                candidate
                for candidate in FIXTURE_LESSON.questions
                if candidate.question_id == question_id
            ),
            None,
        )
        if question is None:
            raise LessonStateError("This question is not part of the active lesson.")
        if selected_option_index not in range(len(question.options)):
            raise LessonStateError("Select one of the available answers.")

        now = self._clock()
        idempotency_key = sha256(
            f"{lesson_session_id}:{question_id}".encode("utf-8")
        ).hexdigest()
        with Session(self._engine) as session:
            existing = session.scalar(
                select(ReviewAttempt).where(
                    ReviewAttempt.user_id == user_id,
                    ReviewAttempt.idempotency_key == idempotency_key,
                )
            )
            if existing is not None:
                progress = self._required_progress(session, user_id, existing.item_id)
                return self._attempt_result(existing, question_id, progress, True)

            fixture_item = next(
                item
                for item in FIXTURE_LESSON.items
                if item.canonical_id == question.item_id
            )
            self._ensure_item(session, fixture_item)
            progress = self._get_progress(session, user_id, question.item_id)
            if progress is None:
                progress = UserItemProgress(user_id=user_id, item_id=question.item_id)
                session.add(progress)

            is_correct = selected_option_index == question.correct_option_index
            if is_correct:
                progress.correct_count += 1
                progress.mastery_score = min(
                    1.0, progress.mastery_score + self.CORRECT_MASTERY_GAIN
                )
                review_delay = self.CORRECT_REVIEW_DELAY
            else:
                progress.incorrect_count += 1
                review_delay = self.INCORRECT_REVIEW_DELAY
            progress.last_answered_at = now
            progress.next_review_at = now + review_delay

            attempt = ReviewAttempt(
                user_id=user_id,
                item_id=question.item_id,
                lesson_session_id=lesson_session_id,
                idempotency_key=idempotency_key,
                question_form=question.form.value,
                is_correct=is_correct,
                is_retry=False,
                answered_at=now,
            )
            session.add(attempt)
            session.commit()
            session.refresh(progress)
            return self._attempt_result(attempt, question_id, progress, False)

    def complete_fixture_lesson(
        self, user_id: int, lesson_session_id: str
    ) -> CompletionRecord:
        now = self._clock()
        with Session(self._engine) as session:
            existing = session.scalar(
                select(CompletedLessonMetadata).where(
                    CompletedLessonMetadata.user_id == user_id,
                    CompletedLessonMetadata.lesson_session_id == lesson_session_id,
                )
            )
            if existing is not None:
                return self._completion_record(existing)
            attempt_count = session.scalar(
                select(func.count(ReviewAttempt.id)).where(
                    ReviewAttempt.user_id == user_id,
                    ReviewAttempt.lesson_session_id == lesson_session_id,
                )
            )
            if attempt_count != len(FIXTURE_LESSON.questions):
                raise LessonStateError("Answer every question before completing the lesson.")

            completion = CompletedLessonMetadata(
                user_id=user_id,
                lesson_session_id=lesson_session_id,
                topic_id=FIXTURE_LESSON.topic_id,
                difficulty=FIXTURE_LESSON.difficulty,
                studied_item_ids=[
                    item.canonical_id for item in FIXTURE_LESSON.items
                ],
                completed_at=now,
            )
            session.add(completion)
            session.commit()
            session.refresh(completion)
            return self._completion_record(completion)

    def get_progress(self, user_id: int) -> tuple[ProgressRecord, ...]:
        with Session(self._engine) as session:
            rows = session.execute(
                select(UserItemProgress, LearningItem)
                .join(LearningItem, LearningItem.canonical_id == UserItemProgress.item_id)
                .where(UserItemProgress.user_id == user_id)
                .order_by(UserItemProgress.item_id)
            ).all()
            return tuple(
                ProgressRecord(
                    item_id=progress.item_id,
                    category=ItemCategory(item.category),
                    exposure_count=progress.exposure_count,
                    correct_count=progress.correct_count,
                    incorrect_count=progress.incorrect_count,
                    mastery_score=progress.mastery_score,
                    last_answered_at=progress.last_answered_at,
                    next_review_at=progress.next_review_at,
                )
                for progress, item in rows
            )

    def get_completions(self, user_id: int) -> tuple[CompletionRecord, ...]:
        with Session(self._engine) as session:
            rows = session.scalars(
                select(CompletedLessonMetadata)
                .where(CompletedLessonMetadata.user_id == user_id)
                .order_by(CompletedLessonMetadata.completed_at.desc())
            ).all()
            return tuple(self._completion_record(row) for row in rows)

    @staticmethod
    def _ensure_item(session: Session, fixture_item: FixtureItem) -> None:
        if session.get(LearningItem, fixture_item.canonical_id) is None:
            session.add(
                LearningItem(
                    canonical_id=fixture_item.canonical_id,
                    category=fixture_item.category.value,
                    jlpt_level=fixture_item.jlpt_level,
                    jlpt_provenance=fixture_item.jlpt_provenance,
                    jlpt_confidence=fixture_item.jlpt_confidence,
                )
            )

    @staticmethod
    def _get_progress(
        session: Session, user_id: int, item_id: str
    ) -> UserItemProgress | None:
        return session.scalar(
            select(UserItemProgress).where(
                UserItemProgress.user_id == user_id,
                UserItemProgress.item_id == item_id,
            )
        )

    def _required_progress(
        self, session: Session, user_id: int, item_id: str
    ) -> UserItemProgress:
        progress = self._get_progress(session, user_id, item_id)
        if progress is None:
            raise LessonStateError("Progress for this answer is unavailable.")
        return progress

    @staticmethod
    def _attempt_result(
        attempt: ReviewAttempt,
        question_id: str,
        progress: UserItemProgress,
        duplicate: bool,
    ) -> AttemptResult:
        if progress.next_review_at is None:
            raise LessonStateError("The answer did not produce a review schedule.")
        return AttemptResult(
            item_id=attempt.item_id,
            question_id=question_id,
            is_correct=attempt.is_correct,
            mastery_score=progress.mastery_score,
            next_review_at=progress.next_review_at,
            duplicate=duplicate,
        )

    @staticmethod
    def _completion_record(completion: CompletedLessonMetadata) -> CompletionRecord:
        return CompletionRecord(
            topic_id=completion.topic_id,
            difficulty=completion.difficulty,
            studied_item_ids=tuple(completion.studied_item_ids),
            completed_at=completion.completed_at,
        )