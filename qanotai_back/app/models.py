from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    avatar_url: Mapped[str | None] = mapped_column(String(1024))

    google_sub: Mapped[str | None] = mapped_column(String(64), unique=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    telegram_username: Mapped[str | None] = mapped_column(String(64))
    language_code: Mapped[str | None] = mapped_column(String(16))

    plan: Mapped[str] = mapped_column(String(20), default="free", server_default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TelegramLogin(Base):
    """One "Telegram orqali kirish" attempt: the site polls it, the bot confirms or rejects it."""

    __tablename__ = "telegram_logins"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    # pending → confirmed | rejected; confirmed → used once the browser has taken the session
    status: Mapped[str] = mapped_column(String(16), default="pending")
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    device: Mapped[str | None] = mapped_column(String(120))  # shown in the bot so people can spot a login they didn't start
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Subject(Base):
    """A school subject (fan): Matematika, Ona tili, ..."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    color: Mapped[str] = mapped_column(String(16), default="blue")  # palette key used by the admin UI
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="RESTRICT"))
    year: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(String(500))
    test_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    subject: Mapped[Subject] = relationship(lazy="joined")


class Topic(Base):
    """One line of a book's table of contents (mavzu)."""

    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)  # order inside the book
    kind: Mapped[str] = mapped_column(String(16), default="lesson")  # lesson | review | answers | section
    number: Mapped[int | None] = mapped_column(Integer)  # printed topic number; lessons only
    title: Mapped[str] = mapped_column(String(300))
    page: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Question(Base):
    """A multiple-choice test inside a topic."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[str] = mapped_column(String(10), default="medium")  # easy | medium | hard
    text: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str]] = mapped_column(JSON)
    correct: Mapped[int] = mapped_column(Integer)  # index into options
    explanation: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))  # figure shown with the question
    figure: Mapped[dict | None] = mapped_column(JSON)  # the figure's description, kept so AI can re-read its data
    solution: Mapped[dict | None] = mapped_column(JSON)  # step-by-step notebook solution (see solution.py)
    explainer: Mapped[dict | None] = mapped_column(JSON)  # detailed illustrated explanation (see solution.Explainer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TestAttempt(Base):
    """One finished run of a topic's test by a student."""

    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    total: Mapped[int] = mapped_column(Integer)
    correct: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    # {question_id: chosen option index, or null when skipped}
    answers: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
