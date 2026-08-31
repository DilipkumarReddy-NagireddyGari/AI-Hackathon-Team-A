"""Shared SQLAlchemy models for persistent application data."""

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64))
    normalized_username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now(), onupdate=func.now()
    )


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    role: Mapped[str] = mapped_column(String(256))
    tasks: Mapped[list[str]] = mapped_column(JSON)
    tools_domain: Mapped[str | None] = mapped_column(Text(), nullable=True)
    declared_level: Mapped[str] = mapped_column(String(32))
    estimated_working_level: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )
    level_source: Mapped[str] = mapped_column(String(32), default="self-reported")
    level_confidence: Mapped[float] = mapped_column(Float(), default=1.0)
    romaji_preference: Mapped[bool] = mapped_column(Boolean(), default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(), server_default=func.now(), onupdate=func.now()
    )