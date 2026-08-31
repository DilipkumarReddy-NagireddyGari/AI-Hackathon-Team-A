"""Add learner profiles.

Revision ID: 20260831_0003
Revises: 20260831_0002
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260831_0003"
down_revision: str | None = "20260831_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEVEL_VALUES = "'Complete beginner', 'JLPT N5', 'JLPT N4', 'JLPT N3', 'JLPT N2', 'JLPT N1', 'Unsure'"
SOURCE_VALUES = "'self-reported', 'placement-estimated', 'performance-estimated'"


def upgrade() -> None:
    op.create_table(
        "learner_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=256), nullable=False),
        sa.Column("tasks", sa.JSON(), nullable=False),
        sa.Column("tools_domain", sa.Text(), nullable=True),
        sa.Column("declared_level", sa.String(length=32), nullable=False),
        sa.Column("estimated_working_level", sa.String(length=32), nullable=True),
        sa.Column(
            "level_source",
            sa.String(length=32),
            server_default="self-reported",
            nullable=False,
        ),
        sa.Column(
            "level_confidence", sa.Float(), server_default="1.0", nullable=False
        ),
        sa.Column(
            "romaji_preference", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            f"declared_level IN ({LEVEL_VALUES})", name="ck_profile_declared_level"
        ),
        sa.CheckConstraint(
            f"estimated_working_level IS NULL OR estimated_working_level IN ({LEVEL_VALUES})",
            name="ck_profile_estimated_level",
        ),
        sa.CheckConstraint(
            f"level_source IN ({SOURCE_VALUES})", name="ck_profile_level_source"
        ),
        sa.CheckConstraint(
            "level_confidence >= 0.0 AND level_confidence <= 1.0",
            name="ck_profile_level_confidence",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_learner_profiles_user_id"),
        "learner_profiles",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_learner_profiles_user_id"), table_name="learner_profiles")
    op.drop_table("learner_profiles")