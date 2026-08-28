"""Establish the T01 migration baseline.

Revision ID: 20260828_0001
Revises: None
"""

from collections.abc import Sequence

revision: str = "20260828_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """T01 has no domain tables; Alembic records the baseline revision."""


def downgrade() -> None:
    """Remove no domain tables."""
