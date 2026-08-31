"""Add versioned mastery, dimension, and SM-2 evidence.

Revision ID: 20260831_0005
Revises: 20260831_0004
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260831_0005"
down_revision: str | None = "20260831_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("user_item_progress") as batch_op:
        batch_op.add_column(
            sa.Column(
                "dimension_scores", sa.JSON(), server_default=sa.text("'{}'"), nullable=False
            )
        )
        batch_op.add_column(
            sa.Column(
                "consecutive_successful_reviews",
                sa.Integer(),
                server_default="0",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column("sm2_interval_days", sa.Integer(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column("sm2_ease", sa.Float(), server_default="2.5", nullable=False)
        )
        batch_op.add_column(sa.Column("last_outcome", sa.String(length=16), nullable=True))
        batch_op.create_check_constraint(
            "ck_progress_sm2_ease", "sm2_ease >= 1.3 AND sm2_ease <= 3.0"
        )
        batch_op.create_check_constraint(
            "ck_progress_sm2_interval_days", "sm2_interval_days >= 0"
        )
        batch_op.create_check_constraint(
            "ck_progress_consecutive_successful_reviews",
            "consecutive_successful_reviews >= 0",
        )

    with op.batch_alter_table("review_attempts") as batch_op:
        batch_op.add_column(sa.Column("skill_dimension", sa.String(length=32)))
        batch_op.add_column(sa.Column("outcome", sa.String(length=16)))
        batch_op.add_column(sa.Column("policy_version", sa.String(length=16)))

    op.execute(
        """
        UPDATE review_attempts
        SET skill_dimension = CASE
                WHEN question_form = 'reading' THEN 'reading'
                WHEN question_form = 'contextual_cloze' AND item_id LIKE 'grammar:%'
                    THEN 'grammar_application'
                WHEN question_form = 'contextual_cloze' THEN 'contextual_use'
                ELSE 'recognition'
            END,
            outcome = CASE
                WHEN is_correct = 0 THEN 'again'
                WHEN is_retry = 1 THEN 'hard'
                ELSE 'good'
            END,
            policy_version = 't04-provisional'
        """
    )

    with op.batch_alter_table("review_attempts") as batch_op:
        batch_op.alter_column("skill_dimension", existing_type=sa.String(length=32), nullable=False)
        batch_op.alter_column("outcome", existing_type=sa.String(length=16), nullable=False)
        batch_op.alter_column("policy_version", existing_type=sa.String(length=16), nullable=False)
        batch_op.create_check_constraint(
            "ck_attempt_skill_dimension",
            "skill_dimension IN ('recognition', 'reading', 'contextual_use', "
            "'grammar_application')",
        )
        batch_op.create_check_constraint(
            "ck_attempt_outcome", "outcome IN ('again', 'hard', 'good', 'easy')"
        )


def downgrade() -> None:
    with op.batch_alter_table("review_attempts") as batch_op:
        batch_op.drop_constraint("ck_attempt_outcome", type_="check")
        batch_op.drop_constraint("ck_attempt_skill_dimension", type_="check")
        batch_op.drop_column("policy_version")
        batch_op.drop_column("outcome")
        batch_op.drop_column("skill_dimension")

    with op.batch_alter_table("user_item_progress") as batch_op:
        batch_op.drop_constraint(
            "ck_progress_consecutive_successful_reviews", type_="check"
        )
        batch_op.drop_constraint("ck_progress_sm2_interval_days", type_="check")
        batch_op.drop_constraint("ck_progress_sm2_ease", type_="check")
        batch_op.drop_column("last_outcome")
        batch_op.drop_column("sm2_ease")
        batch_op.drop_column("sm2_interval_days")
        batch_op.drop_column("consecutive_successful_reviews")
        batch_op.drop_column("dimension_scores")