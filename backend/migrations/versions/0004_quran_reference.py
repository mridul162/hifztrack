"""Create empty Quran reference coordinate and mapping tables.

Revision ID: 0004_quran_reference
Revises: 0003_groups
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0004_quran_reference"
down_revision: str | None = "0003_groups"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "quran_surahs",
        sa.Column("surah_number", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_quran_surahs_number"),
        sa.PrimaryKeyConstraint("surah_number"),
    )
    op.create_table(
        "quran_ayahs",
        sa.Column("surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("ayah_number", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_quran_ayahs_surah_number"),
        sa.CheckConstraint("ayah_number > 0", name="ck_quran_ayahs_number_positive"),
        sa.ForeignKeyConstraint(["surah_number"], ["quran_surahs.surah_number"],
                                name="fk_quran_ayahs_surah", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("surah_number", "ayah_number"),
    )
    op.create_table(
        "quran_juzs",
        sa.Column("juz_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_ayah_number", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("juz_number BETWEEN 1 AND 30", name="ck_quran_juzs_number"),
        sa.ForeignKeyConstraint(["start_surah_number", "start_ayah_number"],
                                ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
                                name="fk_quran_juzs_start_ayah", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("juz_number"),
        sa.UniqueConstraint("start_surah_number", "start_ayah_number",
                            name="uq_quran_juzs_start_ayah"),
    )
    op.create_table(
        "quran_pages",
        sa.Column("page_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_surah_number", sa.SmallInteger(), nullable=False),
        sa.Column("start_ayah_number", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("page_number BETWEEN 1 AND 604", name="ck_quran_pages_number"),
        sa.ForeignKeyConstraint(["start_surah_number", "start_ayah_number"],
                                ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
                                name="fk_quran_pages_start_ayah", ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("page_number"),
        sa.UniqueConstraint("start_surah_number", "start_ayah_number",
                            name="uq_quran_pages_start_ayah"),
    )


def downgrade() -> None:
    op.drop_table("quran_pages")
    op.drop_table("quran_juzs")
    op.drop_table("quran_ayahs")
    op.drop_table("quran_surahs")
