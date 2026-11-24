"""Add per-category Quran source provenance and Ayah counts.

Revision ID: 0005_quran_reference_sources
Revises: 0004_quran_reference
"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0005_quran_reference_sources"
down_revision: str | None = "0004_quran_reference"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("quran_surahs", sa.Column("ayah_count", sa.SmallInteger(), nullable=True))
    op.execute(
        "UPDATE quran_surahs SET ayah_count = "
        "(SELECT count(*) FROM quran_ayahs "
        "WHERE quran_ayahs.surah_number = quran_surahs.surah_number)"
    )
    with op.batch_alter_table("quran_surahs") as batch_op:
        batch_op.alter_column("ayah_count", nullable=False)
        batch_op.create_check_constraint(
            "ck_quran_surahs_ayah_count", "ayah_count BETWEEN 1 AND 286"
        )
    op.create_table(
        "quran_reference_sources",
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=200), nullable=False),
        sa.Column("source_version", sa.String(length=100), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("usage_conditions", sa.Text(), nullable=False),
        sa.Column("verification_method", sa.Text(), nullable=False),
        sa.CheckConstraint("length(source_sha256) = 64", name="ck_quran_source_sha256_length"),
        sa.PrimaryKeyConstraint("category"),
    )


def downgrade() -> None:
    op.drop_table("quran_reference_sources")
    with op.batch_alter_table("quran_surahs") as batch_op:
        batch_op.drop_constraint("ck_quran_surahs_ayah_count", type_="check")
        batch_op.drop_column("ayah_count")
