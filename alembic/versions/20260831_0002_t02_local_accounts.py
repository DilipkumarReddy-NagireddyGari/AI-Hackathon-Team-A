"""Add local demo accounts.

Revision ID: 20260831_0002
Revises: 20260828_0001
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260831_0002"
down_revision: str | None = "20260828_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("normalized_username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_users_normalized_username"),
        "users",
        ["normalized_username"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_normalized_username"), table_name="users")
    op.drop_table("users")