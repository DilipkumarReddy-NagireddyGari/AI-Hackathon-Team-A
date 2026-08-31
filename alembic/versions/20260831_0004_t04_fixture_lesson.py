"""Add compact lesson progress and evidence.

Revision ID: 20260831_0004
Revises: 20260831_0003
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260831_0004"
down_revision: str | None = "20260831_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "learning_items",
        sa.Column("canonical_id", sa.String(length=128), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("jlpt_level", sa.String(length=32), nullable=True),
        sa.Column("jlpt_provenance", sa.String(length=32), nullable=False),
        sa.Column("jlpt_confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "category IN ('kanji', 'vocabulary', 'grammar')",
            name="ck_learning_item_category",
        ),
        sa.CheckConstraint(
            "jlpt_confidence >= 0.0 AND jlpt_confidence <= 1.0",
            name="ck_learning_item_jlpt_confidence",
        ),
        sa.PrimaryKeyConstraint("canonical_id"),
    )
    op.create_table(
        "user_item_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("exposure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("correct_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("incorrect_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mastery_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("last_answered_at", sa.DateTime(), nullable=True),
        sa.Column("next_review_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("exposure_count >= 0", name="ck_progress_exposure_count"),
        sa.CheckConstraint("correct_count >= 0", name="ck_progress_correct_count"),
        sa.CheckConstraint("incorrect_count >= 0", name="ck_progress_incorrect_count"),
        sa.CheckConstraint(
            "mastery_score >= 0.0 AND mastery_score <= 1.0",
            name="ck_progress_mastery_score",
        ),
        sa.ForeignKeyConstraint(["item_id"], ["learning_items.canonical_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "item_id", name="uq_progress_user_item"),
    )
    op.create_index(
        op.f("ix_user_item_progress_item_id"),
        "user_item_progress",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_item_progress_user_id"),
        "user_item_progress",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "review_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.String(length=128), nullable=False),
        sa.Column("lesson_session_id", sa.String(length=36), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("question_form", sa.String(length=32), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("is_retry", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("answered_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "question_form IN ('meaning', 'reading', 'contextual_cloze')",
            name="ck_attempt_question_form",
        ),
        sa.ForeignKeyConstraint(["item_id"], ["learning_items.canonical_id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "idempotency_key", name="uq_attempt_user_idempotency"
        ),
    )
    op.create_index(
        op.f("ix_review_attempts_item_id"),
        "review_attempts",
        ["item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_review_attempts_lesson_session_id"),
        "review_attempts",
        ["lesson_session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_review_attempts_user_id"),
        "review_attempts",
        ["user_id"],
        unique=False,
    )
    op.create_table(
        "completed_lesson_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("lesson_session_id", sa.String(length=36), nullable=False),
        sa.Column("topic_id", sa.String(length=128), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("studied_item_ids", sa.JSON(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "lesson_session_id", name="uq_completion_user_session"
        ),
    )
    op.create_index(
        op.f("ix_completed_lesson_metadata_user_id"),
        "completed_lesson_metadata",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_completed_lesson_metadata_user_id"),
        table_name="completed_lesson_metadata",
    )
    op.drop_table("completed_lesson_metadata")
    op.drop_index(op.f("ix_review_attempts_user_id"), table_name="review_attempts")
    op.drop_index(
        op.f("ix_review_attempts_lesson_session_id"), table_name="review_attempts"
    )
    op.drop_index(op.f("ix_review_attempts_item_id"), table_name="review_attempts")
    op.drop_table("review_attempts")
    op.drop_index(
        op.f("ix_user_item_progress_user_id"), table_name="user_item_progress"
    )
    op.drop_index(
        op.f("ix_user_item_progress_item_id"), table_name="user_item_progress"
    )
    op.drop_table("user_item_progress")
    op.drop_table("learning_items")