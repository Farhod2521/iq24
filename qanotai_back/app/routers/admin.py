import secrets
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import Integer, cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import ai
from ..config import get_settings
from ..db import get_session
from ..models import Book, Question, Subject, Topic, User
from ..security import require_superadmin
from ..mathtext import normalize, normalize_solution
from ..solution import Solution
from ..svg import InvalidSvg, sanitize_svg

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_superadmin)])

TASHKENT = timezone(timedelta(hours=5))  # Uzbekistan has no DST
WEEKDAYS = ["Du", "Se", "Ch", "Pa", "Ju", "Sh", "Ya"]


def _growth(now: int, before: int) -> float | None:
    """Percent change, or None when there is nothing to compare against."""
    return None if before == 0 else round((now - before) * 100 / before, 1)


# ─── overview ────────────────────────────────────────────────────────────────


@router.get("/overview")
async def overview(session: AsyncSession = Depends(get_session)) -> dict:
    today = datetime.now(TASHKENT).replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=6)

    async def count(stmt) -> int:
        return (await session.execute(stmt)).scalar_one()

    users_total = await count(select(func.count(User.id)))
    new_today = await count(select(func.count(User.id)).where(User.created_at >= today))
    new_yesterday = await count(
        select(func.count(User.id)).where(User.created_at >= today - timedelta(days=1), User.created_at < today)
    )
    active_today = await count(select(func.count(User.id)).where(User.last_login_at >= today))
    active_yesterday = await count(
        select(func.count(User.id)).where(
            User.last_login_at >= today - timedelta(days=1), User.last_login_at < today
        )
    )
    new_7d = await count(select(func.count(User.id)).where(User.created_at >= week_ago))
    new_prev_7d = await count(
        select(func.count(User.id)).where(User.created_at >= week_ago - timedelta(days=7), User.created_at < week_ago)
    )

    # per-day registrations / last logins for the past 7 days, in Tashkent time
    def per_day(column):
        day = func.date(func.timezone("Asia/Tashkent", column))
        return select(day, func.count()).where(column >= week_ago).group_by(day)

    new_by_day = dict((await session.execute(per_day(User.created_at))).all())
    active_by_day = dict((await session.execute(per_day(User.last_login_at))).all())
    days = []
    for i in range(7):
        d = (week_ago + timedelta(days=i)).date()
        days.append({"label": WEEKDAYS[d.weekday()], "date": d.isoformat(), "new": new_by_day.get(d, 0), "active": active_by_day.get(d, 0)})

    subjects_total = await count(select(func.count(Subject.id)))
    books_total = await count(select(func.count(Book.id)))
    tests_total = await count(select(func.count(Question.id)))

    bt = _book_tests()
    per_subject = (
        await session.execute(
            select(Subject.id, Subject.name, Subject.color, func.count(Book.id), cast(func.coalesce(func.sum(bt.c.n), 0), Integer))
            .outerjoin(Book, Book.subject_id == Subject.id)
            .outerjoin(bt, bt.c.book_id == Book.id)
            .group_by(Subject.id)
            .order_by(Subject.name)
        )
    ).all()

    recent_users = (await session.execute(select(User).order_by(User.created_at.desc()).limit(6))).scalars().all()
    recent_books = (await session.execute(select(Book).order_by(Book.created_at.desc()).limit(6))).scalars().all()
    activity = [
        {"kind": "user", "title": "Yangi foydalanuvchi ro'yxatdan o'tdi", "detail": u.full_name, "at": u.created_at}
        for u in recent_users
    ] + [
        {"kind": "book", "title": "Kitob qo'shildi", "detail": f"{b.title} · {b.subject.name}", "at": b.created_at}
        for b in recent_books
    ]
    activity.sort(key=lambda a: a["at"], reverse=True)

    return {
        "users": {
            "total": users_total,
            "new_today": new_today,
            "new_today_growth": _growth(new_today, new_yesterday),
            "active_today": active_today,
            "active_today_growth": _growth(active_today, active_yesterday),
            "weekly_growth": _growth(new_7d, new_prev_7d),
        },
        "subjects": subjects_total,
        "books": books_total,
        "tests": tests_total,
        "days": days,
        "per_subject": [
            {"id": sid, "name": name, "color": color, "books": books, "tests": tests}
            for sid, name, color, books, tests in per_subject
        ],
        "activity": activity[:8],
    }


# ─── users ───────────────────────────────────────────────────────────────────


class AdminUserOut(BaseModel):
    id: int
    full_name: str
    email: str | None
    phone: str | None
    telegram_username: str | None
    avatar_url: str | None
    has_google: bool
    has_telegram: bool
    plan: str
    created_at: datetime
    last_login_at: datetime | None


@router.get("/users")
async def list_users(
    q: str = "",
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> dict:
    stmt = select(User)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(User.full_name.ilike(like), User.email.ilike(like), User.phone.ilike(like), User.telegram_username.ilike(like))
        )
    total = (await session.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = (
        await session.execute(stmt.order_by(User.created_at.desc()).offset((page - 1) * per_page).limit(per_page))
    ).scalars()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            AdminUserOut(
                id=u.id,
                full_name=u.full_name,
                email=u.email,
                phone=u.phone,
                telegram_username=u.telegram_username,
                avatar_url=u.avatar_url,
                has_google=u.google_sub is not None,
                has_telegram=u.telegram_id is not None,
                plan=u.plan,
                created_at=u.created_at,
                last_login_at=u.last_login_at,
            )
            for u in rows
        ],
    }


# ─── subjects ────────────────────────────────────────────────────────────────

COLORS = {"blue", "violet", "emerald", "rose", "amber", "sky", "slate"}


class SubjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    color: str = "blue"


class SubjectOut(BaseModel):
    id: int
    name: str
    color: str
    books: int
    tests: int


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(session: AsyncSession = Depends(get_session)) -> list[SubjectOut]:
    bt = _book_tests()
    rows = (
        await session.execute(
            select(Subject, func.count(Book.id), cast(func.coalesce(func.sum(bt.c.n), 0), Integer))
            .outerjoin(Book, Book.subject_id == Subject.id)
            .outerjoin(bt, bt.c.book_id == Book.id)
            .group_by(Subject.id)
            .order_by(Subject.name)
        )
    ).all()
    return [SubjectOut(id=s.id, name=s.name, color=s.color, books=b, tests=t) for s, b, t in rows]


async def _save_subject(session: AsyncSession, subject: Subject, data: SubjectIn) -> SubjectOut:
    subject.name = data.name.strip()
    subject.color = data.color if data.color in COLORS else "blue"
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bunday fan allaqachon mavjud")
    books = (await session.execute(select(func.count(Book.id)).where(Book.subject_id == subject.id))).scalar_one()
    bt = _book_tests()
    tests = (
        await session.execute(
            select(cast(func.coalesce(func.sum(bt.c.n), 0), Integer)).join(Book, Book.id == bt.c.book_id).where(Book.subject_id == subject.id)
        )
    ).scalar_one()
    return SubjectOut(id=subject.id, name=subject.name, color=subject.color, books=books, tests=tests)


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
async def create_subject(data: SubjectIn, session: AsyncSession = Depends(get_session)) -> SubjectOut:
    subject = Subject()
    session.add(subject)
    return await _save_subject(session, subject, data)


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(subject_id: int, data: SubjectIn, session: AsyncSession = Depends(get_session)) -> SubjectOut:
    subject = await session.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fan topilmadi")
    return await _save_subject(session, subject, data)


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(subject_id: int, session: AsyncSession = Depends(get_session)) -> None:
    subject = await session.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fan topilmadi")
    if (await session.execute(select(func.count(Book.id)).where(Book.subject_id == subject_id))).scalar_one():
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu fanda kitoblar bor — avval ularni o'chiring")
    await session.delete(subject)
    await session.commit()


# ─── books ───────────────────────────────────────────────────────────────────


class BookIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    subject_id: int
    year: int | None = Field(default=None, ge=1900, le=2100)
    description: str | None = Field(default=None, max_length=2000)
    cover_url: str | None = Field(default=None, max_length=500)
    test_count: int = Field(default=0, ge=0, le=100_000)  # ignored: the count comes from the questions themselves


class BookOut(BaseModel):
    id: int
    title: str
    subject_id: int
    subject_name: str
    year: int | None
    description: str | None
    cover_url: str | None
    test_count: int
    topic_count: int = 0
    created_at: datetime

    @classmethod
    def of(cls, b: Book, topic_count: int = 0, test_count: int = 0) -> "BookOut":
        return cls(
            id=b.id,
            title=b.title,
            subject_id=b.subject_id,
            subject_name=b.subject.name,
            year=b.year,
            description=b.description,
            cover_url=b.cover_url,
            test_count=test_count,
            topic_count=topic_count,
            created_at=b.created_at,
        )


async def _topic_counts(session: AsyncSession, book_ids: list[int]) -> dict[int, int]:
    if not book_ids:
        return {}
    rows = await session.execute(
        select(Topic.book_id, func.count(Topic.id)).where(Topic.book_id.in_(book_ids)).group_by(Topic.book_id)
    )
    return dict(rows.all())


def _book_tests():
    """Subquery: book_id → number of questions in that book's topics."""
    return (
        select(Topic.book_id.label("book_id"), func.count(Question.id).label("n"))
        .join(Question, Question.topic_id == Topic.id)
        .group_by(Topic.book_id)
        .subquery()
    )


async def _test_counts(session: AsyncSession, book_ids: list[int]) -> dict[int, int]:
    if not book_ids:
        return {}
    bt = _book_tests()
    rows = await session.execute(select(bt.c.book_id, bt.c.n).where(bt.c.book_id.in_(book_ids)))
    return dict(rows.all())


@router.get("/books", response_model=list[BookOut])
async def list_books(
    subject_id: int | None = None, q: str = "", session: AsyncSession = Depends(get_session)
) -> list[BookOut]:
    stmt = select(Book).order_by(Book.created_at.desc())
    if subject_id:
        stmt = stmt.where(Book.subject_id == subject_id)
    if q.strip():
        stmt = stmt.where(Book.title.ilike(f"%{q.strip()}%"))
    books = (await session.execute(stmt)).scalars().all()
    ids = [b.id for b in books]
    topics, tests = await _topic_counts(session, ids), await _test_counts(session, ids)
    return [BookOut.of(b, topics.get(b.id, 0), tests.get(b.id, 0)) for b in books]


async def _save_book(session: AsyncSession, book: Book, data: BookIn) -> BookOut:
    if await session.get(Subject, data.subject_id) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Fan tanlanmagan")
    book.title = data.title.strip()
    book.subject_id = data.subject_id
    book.year = data.year
    book.description = (data.description or "").strip() or None
    book.cover_url = data.cover_url or None
    session.add(book)  # only now — adding a blank Book earlier would autoflush it on the lookup above
    await session.commit()
    await session.refresh(book, ["subject", "created_at"])
    return BookOut.of(
        book,
        (await _topic_counts(session, [book.id])).get(book.id, 0),
        (await _test_counts(session, [book.id])).get(book.id, 0),
    )


@router.post("/books", response_model=BookOut, status_code=status.HTTP_201_CREATED)
async def create_book(data: BookIn, session: AsyncSession = Depends(get_session)) -> BookOut:
    return await _save_book(session, Book(), data)


@router.put("/books/{book_id}", response_model=BookOut)
async def update_book(book_id: int, data: BookIn, session: AsyncSession = Depends(get_session)) -> BookOut:
    book = await session.get(Book, book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kitob topilmadi")
    return await _save_book(session, book, data)


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, session: AsyncSession = Depends(get_session)) -> None:
    book = await session.get(Book, book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kitob topilmadi")
    await session.delete(book)
    await session.commit()


# ─── topics (a book's table of contents) ─────────────────────────────────────

TopicKind = Literal["lesson", "review", "answers", "section"]  # section: a chapter heading (Kinematika …)


class TopicIn(BaseModel):
    kind: TopicKind = "lesson"
    number: int | None = Field(default=None, ge=1, le=10_000)
    title: str = Field(min_length=2, max_length=300)
    page: int | None = Field(default=None, ge=1, le=100_000)


class TopicOut(BaseModel):
    id: int
    position: int
    kind: str
    number: int | None
    title: str
    page: int | None
    question_count: int = 0


class BookDetailOut(BookOut):
    topics: list[TopicOut]


def _topic_out(t: Topic, question_count: int = 0) -> TopicOut:
    return TopicOut(
        id=t.id, position=t.position, kind=t.kind, number=t.number, title=t.title, page=t.page, question_count=question_count
    )


async def _question_counts(session: AsyncSession, topic_ids: list[int]) -> dict[int, int]:
    if not topic_ids:
        return {}
    rows = await session.execute(
        select(Question.topic_id, func.count(Question.id)).where(Question.topic_id.in_(topic_ids)).group_by(Question.topic_id)
    )
    return dict(rows.all())


async def _book_or_404(session: AsyncSession, book_id: int) -> Book:
    book = await session.get(Book, book_id)
    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kitob topilmadi")
    return book


async def _topics(session: AsyncSession, book_id: int) -> list[Topic]:
    stmt = select(Topic).where(Topic.book_id == book_id).order_by(Topic.position, Topic.id)
    return list((await session.execute(stmt)).scalars())


@router.get("/books/{book_id}", response_model=BookDetailOut)
async def get_book(book_id: int, session: AsyncSession = Depends(get_session)) -> BookDetailOut:
    book = await _book_or_404(session, book_id)
    topics = await _topics(session, book_id)
    counts = await _question_counts(session, [t.id for t in topics])
    return BookDetailOut(
        **BookOut.of(book, len(topics), sum(counts.values())).model_dump(), topics=[_topic_out(t, counts.get(t.id, 0)) for t in topics]
    )


def _apply_topic(topic: Topic, data: TopicIn) -> None:
    topic.kind = data.kind
    topic.number = data.number if data.kind == "lesson" else None  # only lessons carry a printed number
    topic.title = data.title.strip()
    if "page" in data.model_fields_set:  # the admin form no longer edits pages; don't wipe the stored one
        topic.page = data.page


@router.post("/books/{book_id}/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED)
async def create_topic(book_id: int, data: TopicIn, session: AsyncSession = Depends(get_session)) -> TopicOut:
    await _book_or_404(session, book_id)
    last = (
        await session.execute(select(func.coalesce(func.max(Topic.position), 0)).where(Topic.book_id == book_id))
    ).scalar_one()
    topic = Topic(book_id=book_id, position=last + 1)
    _apply_topic(topic, data)
    session.add(topic)
    await session.commit()
    return _topic_out(topic)


@router.put("/topics/{topic_id}", response_model=TopicOut)
async def update_topic(topic_id: int, data: TopicIn, session: AsyncSession = Depends(get_session)) -> TopicOut:
    topic = await session.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mavzu topilmadi")
    _apply_topic(topic, data)
    await session.commit()
    return _topic_out(topic, (await _question_counts(session, [topic.id])).get(topic.id, 0))


@router.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(topic_id: int, session: AsyncSession = Depends(get_session)) -> None:
    topic = await session.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mavzu topilmadi")
    await session.delete(topic)
    await session.commit()


class ReorderIn(BaseModel):
    ids: list[int]


@router.put("/books/{book_id}/topics/order", response_model=list[TopicOut])
async def reorder_topics(book_id: int, data: ReorderIn, session: AsyncSession = Depends(get_session)) -> list[TopicOut]:
    topics = {t.id: t for t in await _topics(session, book_id)}
    if sorted(data.ids) != sorted(topics):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Mavzular ro'yxati mos kelmadi")
    for position, topic_id in enumerate(data.ids, start=1):
        topics[topic_id].position = position
    await session.commit()
    counts = await _question_counts(session, data.ids)
    return [_topic_out(topics[i], counts.get(i, 0)) for i in data.ids]


# ─── questions (tests inside a topic) ────────────────────────────────────────

Difficulty = Literal["easy", "medium", "hard"]


class QuestionIn(BaseModel):
    difficulty: Difficulty = "medium"
    text: str = Field(min_length=2, max_length=5000)
    options: list[str] = Field(min_length=2, max_length=6)
    correct: int = Field(ge=0)
    explanation: str | None = Field(default=None, max_length=5000)
    # an uploaded image (/api/media/...), or None
    image_url: str | None = Field(default=None, max_length=500)
    # AI drafts carry their figure as SVG markup; it is sanitized and written to /api/media on save
    figure_svg: str | None = Field(default=None, max_length=40_000)
    solution: Solution | None = None


class QuestionOut(BaseModel):
    id: int
    position: int
    difficulty: str
    text: str
    options: list[str]
    correct: int
    explanation: str | None
    image_url: str | None
    solution: dict | None = None
    explainer: dict | None = None


class TopicDetailOut(TopicOut):
    book_id: int
    book_title: str
    questions: list[QuestionOut]


def _question_out(q: Question) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        position=q.position,
        difficulty=q.difficulty,
        text=q.text,
        options=q.options,
        correct=q.correct,
        explanation=q.explanation,
        image_url=q.image_url,
        solution=q.solution,
        explainer=q.explainer,
    )


def _apply_question(q: Question, data: QuestionIn) -> None:
    options = [normalize(o.strip()) for o in data.options]
    if any(not o for o in options):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Barcha variantlarni to'ldiring")
    if data.correct >= len(options):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "To'g'ri javobni belgilang")
    q.difficulty = data.difficulty
    q.text = normalize(data.text.strip())
    q.options = options
    q.correct = data.correct
    q.explanation = normalize((data.explanation or "").strip()) or None
    if "solution" in data.model_fields_set:
        q.solution = normalize_solution(data.solution.model_dump(exclude_none=True)) if data.solution else None
    if data.figure_svg:
        q.image_url = _save_figure(data.figure_svg)
    elif data.image_url and data.image_url.startswith("/api/media/"):
        q.image_url = data.image_url
    else:
        q.image_url = None


def _save_figure(markup: str) -> str:
    """Sanitize an SVG figure and store it like an upload; returns its /api/media URL."""
    try:
        clean = sanitize_svg(markup)
    except InvalidSvg:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Rasm (SVG) yaroqsiz")
    folder = Path(get_settings().media_dir) / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(8)}.svg"
    (folder / name).write_text(clean, encoding="utf-8")
    return f"/api/media/figures/{name}"


async def _topic_or_404(session: AsyncSession, topic_id: int) -> Topic:
    topic = await session.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mavzu topilmadi")
    return topic


@router.get("/topics/{topic_id}", response_model=TopicDetailOut)
async def get_topic(topic_id: int, session: AsyncSession = Depends(get_session)) -> TopicDetailOut:
    topic = await _topic_or_404(session, topic_id)
    book = await session.get(Book, topic.book_id)
    questions = list(
        (await session.execute(select(Question).where(Question.topic_id == topic_id).order_by(Question.position, Question.id))).scalars()
    )
    return TopicDetailOut(
        **_topic_out(topic, len(questions)).model_dump(),
        book_id=book.id,
        book_title=book.title,
        questions=[_question_out(q) for q in questions],
    )


@router.post("/topics/{topic_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(topic_id: int, data: QuestionIn, session: AsyncSession = Depends(get_session)) -> QuestionOut:
    await _topic_or_404(session, topic_id)
    last = (
        await session.execute(select(func.coalesce(func.max(Question.position), 0)).where(Question.topic_id == topic_id))
    ).scalar_one()
    question = Question(topic_id=topic_id, position=last + 1)
    _apply_question(question, data)
    session.add(question)
    await session.commit()
    return _question_out(question)


@router.put("/questions/{question_id}", response_model=QuestionOut)
async def update_question(question_id: int, data: QuestionIn, session: AsyncSession = Depends(get_session)) -> QuestionOut:
    question = await session.get(Question, question_id)
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test topilmadi")
    _apply_question(question, data)
    await session.commit()
    return _question_out(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(question_id: int, session: AsyncSession = Depends(get_session)) -> None:
    question = await session.get(Question, question_id)
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test topilmadi")
    await session.delete(question)
    await session.commit()


# ─── AI test generator ───────────────────────────────────────────────────────


class GenerateIn(BaseModel):
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "medium"
    count: int = Field(default=5, ge=0, le=20)  # questions without a figure
    figure_count: int = Field(default=0, ge=0, le=10)  # questions with an SVG figure
    notes: str | None = Field(default=None, max_length=1000)


class GenerateOut(BaseModel):
    questions: list[QuestionIn]
    host: str
    model: str
    input_tokens: int
    output_tokens: int
    warning: str = ""  # e.g. fewer questions with a figure came back than were asked for


class AiStatusOut(BaseModel):
    configured: bool
    host: str
    model: str


@router.get("/ai/status", response_model=AiStatusOut)
async def ai_status() -> AiStatusOut:
    """Whether AI_URL / AI_KEY / AI_MODEL are set in .env (the key itself is never returned)."""
    return AiStatusOut(**ai.ai_status())


@router.post("/topics/{topic_id}/questions/generate", response_model=GenerateOut)
async def generate_topic_questions(topic_id: int, data: GenerateIn, session: AsyncSession = Depends(get_session)) -> GenerateOut:
    """Drafts only — nothing is stored until the admin saves the ones they keep (see /questions/bulk)."""
    if not 1 <= data.count + data.figure_count <= 20:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Jami 1 tadan 20 tagacha test so'rang")
    topic = await _topic_or_404(session, topic_id)
    book = await session.get(Book, topic.book_id)
    existing = list(
        (await session.execute(select(Question.text).where(Question.topic_id == topic_id).order_by(Question.position))).scalars()
    )
    try:
        drafts, usage = await ai.generate_questions(
            subject=book.subject.name,
            book=book.title,
            topic=topic.title,
            topic_number=topic.number,
            difficulty=data.difficulty,
            count=data.count,
            figure_count=data.figure_count,
            existing=existing,
            notes=(data.notes or "").strip() or None,
        )
    except ai.GenerationError as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))
    return GenerateOut(questions=[QuestionIn(**d.model_dump()) for d in drafts], **usage)


class BulkIn(BaseModel):
    questions: list[QuestionIn] = Field(min_length=1, max_length=50)


@router.post("/topics/{topic_id}/questions/bulk", response_model=list[QuestionOut], status_code=status.HTTP_201_CREATED)
async def bulk_create_questions(topic_id: int, data: BulkIn, session: AsyncSession = Depends(get_session)) -> list[QuestionOut]:
    await _topic_or_404(session, topic_id)
    last = (
        await session.execute(select(func.coalesce(func.max(Question.position), 0)).where(Question.topic_id == topic_id))
    ).scalar_one()
    created = []
    for i, item in enumerate(data.questions, start=1):
        question = Question(topic_id=topic_id, position=last + i)
        _apply_question(question, item)  # same validation as a single save
        session.add(question)
        created.append(question)
    await session.commit()
    return [_question_out(q) for q in created]


# ─── uploads ─────────────────────────────────────────────────────────────────

IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_UPLOAD = 5 * 1024 * 1024


@router.post("/uploads")
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    ext = IMAGE_TYPES.get(file.content_type or "")
    if ext is None:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Faqat JPG, PNG yoki WEBP rasm")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Rasm 5 MB dan oshmasin")
    # cheap sanity check that the bytes really are that image type
    magic = {".jpg": (b"\xff\xd8\xff",), ".png": (b"\x89PNG",), ".webp": (b"RIFF",)}[ext]
    if not data.startswith(magic):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Rasm fayli buzilgan")

    folder = Path(get_settings().media_dir) / "covers"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{datetime.now(UTC):%Y%m%d}-{secrets.token_hex(8)}{ext}"
    (folder / name).write_bytes(data)
    return {"url": f"/api/media/covers/{name}"}
