"""Initialize migration tracking without application tables.

Revision ID: 0001_foundation
Revises:
Create Date: 2026-11-23
"""

from typing import Sequence

from alembic import op

revision: str = "0001_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
