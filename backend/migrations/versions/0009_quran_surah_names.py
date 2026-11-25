"""Add optional Arabic and Latin Surah display names."""

from alembic import op
import sqlalchemy as sa


revision = "0009_quran_surah_names"
down_revision = "0008_group_sharing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quran_surahs", sa.Column("name_ar", sa.String(80), nullable=True))
    op.add_column("quran_surahs", sa.Column("name_latin", sa.String(80), nullable=True))


def downgrade() -> None:
    op.drop_column("quran_surahs", "name_latin")
    op.drop_column("quran_surahs", "name_ar")
