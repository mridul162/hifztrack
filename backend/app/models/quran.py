from sqlalchemy import (
    CheckConstraint,
    ForeignKeyConstraint,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QuranSurah(Base):
    __tablename__ = "quran_surahs"
    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_quran_surahs_number"),
        CheckConstraint("ayah_count BETWEEN 1 AND 286", name="ck_quran_surahs_ayah_count"),
    )

    surah_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    ayah_count: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name_latin: Mapped[str | None] = mapped_column(String(80), nullable=True)


class QuranAyah(Base):
    __tablename__ = "quran_ayahs"
    __table_args__ = (
        CheckConstraint("surah_number BETWEEN 1 AND 114", name="ck_quran_ayahs_surah_number"),
        CheckConstraint("ayah_number > 0", name="ck_quran_ayahs_number_positive"),
        ForeignKeyConstraint(
            ["surah_number"],
            ["quran_surahs.surah_number"],
            name="fk_quran_ayahs_surah",
            ondelete="RESTRICT",
        ),
    )

    surah_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    ayah_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)


class QuranJuz(Base):
    __tablename__ = "quran_juzs"
    __table_args__ = (
        CheckConstraint("juz_number BETWEEN 1 AND 30", name="ck_quran_juzs_number"),
        UniqueConstraint(
            "start_surah_number", "start_ayah_number", name="uq_quran_juzs_start_ayah"
        ),
        ForeignKeyConstraint(
            ["start_surah_number", "start_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            name="fk_quran_juzs_start_ayah",
            ondelete="RESTRICT",
        ),
    )

    juz_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    start_surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class QuranPage(Base):
    __tablename__ = "quran_pages"
    __table_args__ = (
        CheckConstraint("page_number BETWEEN 1 AND 604", name="ck_quran_pages_number"),
        UniqueConstraint(
            "start_surah_number", "start_ayah_number", name="uq_quran_pages_start_ayah"
        ),
        ForeignKeyConstraint(
            ["start_surah_number", "start_ayah_number"],
            ["quran_ayahs.surah_number", "quran_ayahs.ayah_number"],
            name="fk_quran_pages_start_ayah",
            ondelete="RESTRICT",
        ),
    )

    page_number: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    start_surah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    start_ayah_number: Mapped[int] = mapped_column(SmallInteger, nullable=False)


class QuranReferenceSource(Base):
    __tablename__ = "quran_reference_sources"
    __table_args__ = (
        CheckConstraint("length(source_sha256) = 64", name="ck_quran_source_sha256_length"),
    )

    category: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    source_version: Mapped[str] = mapped_column(String(100), nullable=False)
    source_path: Mapped[str] = mapped_column(String(500), nullable=False)
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    usage_conditions: Mapped[str] = mapped_column(Text, nullable=False)
    verification_method: Mapped[str] = mapped_column(Text, nullable=False)
