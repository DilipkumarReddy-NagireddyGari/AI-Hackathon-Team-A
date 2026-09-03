"""Add the register question form and answer confidence evidence.

Revision ID: 20260903_0006
Revises: 20260831_0005
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260903_0006"
down_revision: str | None = "20260831_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("review_attempts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "answer_confidence",
                sa.String(length=16),
                server_default="sure",
                nullable=False,
            )
        )
        batch_op.drop_constraint("ck_attempt_question_form", type_="check")
        batch_op.create_check_constraint(
            "ck_attempt_question_form",
            "question_form IN ('meaning', 'reading', 'contextual_cloze', 'register')",
        )
        batch_op.create_check_constraint(
            "ck_attempt_answer_confidence",
            "answer_confidence IN ('sure', 'guessed')",
        )


def downgrade() -> None:
    op.execute("DELETE FROM review_attempts WHERE question_form = 'register'")
    with op.batch_alter_table("review_attempts") as batch_op:
        batch_op.drop_constraint("ck_attempt_answer_confidence", type_="check")
        batch_op.drop_constraint("ck_attempt_question_form", type_="check")
        batch_op.create_check_constraint(
            "ck_attempt_question_form",
            "question_form IN ('meaning', 'reading', 'contextual_cloze')",
        )
        batch_op.drop_column("answer_confidence")
