"""What students see: books, their topics, and the topic tests (signed-in users).

Correct answers never leave the server before submission: the test endpoint sends questions without them, and
grading happens in /submit.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..models import Book, Question, Subject, TestAttempt, Topic, User
from ..security import current_user

router = APIRouter(prefix="/api/catalog", tags=["catalog"], dependencies=[Depends(current_user)])

DIFFICULTY_ORDER = {"easy": 0, "medium": 1, "hard": 2}


class BookCard(BaseModel):
    id: int
    title: str
    subject: str
    year: int | None
    cover_url: str | None
    topics: int
    tests: int  # questions actually written in this book's topics


async def _question_counts(session: AsyncSession, topic_ids: list[int]) -> dict[int, int]:
    if not topic_ids:
        return {}
    rows = await session.execute(
        select(Question.topic_id, func.count(Question.id)).where(Question.topic_id.in_(topic_ids)).group_by(Question.topic_id)
    )
    return dict(rows.all())


@router.get("/books", response_model=list[BookCard])
async def books(session: AsyncSession = Depends(get_session)) -> list[BookCard]:
    rows = (
        await session.execute(
            select(Book, Subject.name).join(Subject, Subject.id == Book.subject_id).order_by(Subject.name, Book.title)
        )
    ).all()
    topics = dict((await session.execute(select(Topic.book_id, func.count(Topic.id)).group_by(Topic.book_id))).all())
    tests = dict(
        (
            await session.execute(
                select(Topic.book_id, func.count(Question.id)).join(Question, Question.topic_id == Topic.id).group_by(Topic.book_id)
            )
        ).all()
    )
    return [
        BookCard(
            id=b.id,
            title=b.title,
            subject=subject,
            year=b.year,
            cover_url=b.cover_url,
            topics=topics.get(b.id, 0),
            tests=tests.get(b.id, 0),
        )
        for b, subject in rows
    ]


# ─── a book and its topics ───────────────────────────────────────────────────


class TopicRow(BaseModel):
    id: int
    kind: str
    number: int | None
    title: str
    tests: int
    best_percent: int | None  # this student's best result, or None if never taken
    attempts: int


class BookPage(BookCard):
    description: str | None
    topic_list: list[TopicRow]


@router.get("/books/{book_id}", response_model=BookPage)
async def book(book_id: int, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)) -> BookPage:
    b = await session.get(Book, book_id)
    if b is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kitob topilmadi")
    topics = list((await session.execute(select(Topic).where(Topic.book_id == book_id).order_by(Topic.position, Topic.id))).scalars())
    ids = [t.id for t in topics]
    counts = await _question_counts(session, ids)
    stats = {}
    if ids:
        rows = await session.execute(
            select(TestAttempt.topic_id, func.max(TestAttempt.correct * 100 / func.nullif(TestAttempt.total, 0)), func.count(TestAttempt.id))
            .where(TestAttempt.user_id == user.id, TestAttempt.topic_id.in_(ids))
            .group_by(TestAttempt.topic_id)
        )
        stats = {tid: (best, n) for tid, best, n in rows.all()}
    return BookPage(
        id=b.id,
        title=b.title,
        subject=b.subject.name,
        year=b.year,
        cover_url=b.cover_url,
        description=b.description,
        topics=len(topics),
        tests=sum(counts.values()),
        topic_list=[
            TopicRow(
                id=t.id,
                kind=t.kind,
                number=t.number,
                title=t.title,
                tests=counts.get(t.id, 0),
                best_percent=int(stats[t.id][0]) if t.id in stats and stats[t.id][0] is not None else None,
                attempts=stats[t.id][1] if t.id in stats else 0,
            )
            for t in topics
        ],
    )


# ─── taking a test ───────────────────────────────────────────────────────────


class TestQuestion(BaseModel):
    id: int
    difficulty: str
    text: str
    options: list[str]
    image_url: str | None


class TestOut(BaseModel):
    topic_id: int
    topic_title: str
    topic_number: int | None
    book_id: int
    book_title: str
    questions: list[TestQuestion]


async def _topic_with_questions(session: AsyncSession, topic_id: int) -> tuple[Topic, Book, list[Question]]:
    topic = await session.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mavzu topilmadi")
    book_ = await session.get(Book, topic.book_id)
    questions = list(
        (await session.execute(select(Question).where(Question.topic_id == topic_id).order_by(Question.position, Question.id))).scalars()
    )
    return topic, book_, questions


@router.get("/topics/{topic_id}/test", response_model=TestOut)
async def test(topic_id: int, session: AsyncSession = Depends(get_session)) -> TestOut:
    topic, book_, questions = await _topic_with_questions(session, topic_id)
    if not questions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bu mavzuda hali test yo'q")
    # easy → hard, keeping the authored order inside each level
    questions.sort(key=lambda q: (DIFFICULTY_ORDER.get(q.difficulty, 1), q.position, q.id))
    return TestOut(
        topic_id=topic.id,
        topic_title=topic.title,
        topic_number=topic.number,
        book_id=book_.id,
        book_title=book_.title,
        questions=[TestQuestion(id=q.id, difficulty=q.difficulty, text=q.text, options=q.options, image_url=q.image_url) for q in questions],
    )


class SubmitIn(BaseModel):
    answers: dict[int, int | None]  # question id → chosen option index (None = skipped)
    duration_seconds: int = Field(default=0, ge=0, le=24 * 3600)


class ReviewItem(BaseModel):
    id: int
    difficulty: str
    text: str
    options: list[str]
    image_url: str | None
    chosen: int | None
    correct: int
    is_correct: bool
    explanation: str | None
    solution: dict | None = None
    explainer: dict | None = None  # detailed illustrated notebook solution (physics)


class LevelStat(BaseModel):
    difficulty: str
    total: int
    correct: int


class ResultOut(BaseModel):
    attempt_id: int
    total: int
    correct: int
    wrong: int
    skipped: int
    percent: int
    duration_seconds: int
    best_percent: int  # best result on this topic including this one
    previous_percent: int | None  # last result before this one
    by_level: list[LevelStat]
    review: list[ReviewItem]


@router.post("/topics/{topic_id}/submit", response_model=ResultOut)
async def submit(
    topic_id: int, data: SubmitIn, user: User = Depends(current_user), session: AsyncSession = Depends(get_session)
) -> ResultOut:
    topic, _, questions = await _topic_with_questions(session, topic_id)
    if not questions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bu mavzuda hali test yo'q")
    questions.sort(key=lambda q: (DIFFICULTY_ORDER.get(q.difficulty, 1), q.position, q.id))

    review, levels = [], {}
    for q in questions:
        chosen = data.answers.get(q.id)
        if chosen is not None and not 0 <= chosen < len(q.options):
            chosen = None
        ok = chosen == q.correct
        review.append(
            ReviewItem(
                id=q.id, difficulty=q.difficulty, text=q.text, options=q.options, image_url=q.image_url,
                chosen=chosen, correct=q.correct, is_correct=ok, explanation=q.explanation, solution=q.solution, explainer=q.explainer,
            )
        )
        lv = levels.setdefault(q.difficulty, [0, 0])
        lv[0] += 1
        lv[1] += ok

    total = len(questions)
    correct = sum(r.is_correct for r in review)
    skipped = sum(r.chosen is None for r in review)
    percent = round(correct * 100 / total)

    previous = (
        await session.execute(
            select(TestAttempt).where(TestAttempt.user_id == user.id, TestAttempt.topic_id == topic_id).order_by(TestAttempt.created_at.desc()).limit(1)
        )
    ).scalar_one_or_none()
    best_before = (
        await session.execute(
            select(func.max(TestAttempt.correct * 100 / func.nullif(TestAttempt.total, 0))).where(
                TestAttempt.user_id == user.id, TestAttempt.topic_id == topic_id
            )
        )
    ).scalar_one()

    attempt = TestAttempt(
        user_id=user.id,
        topic_id=topic_id,
        total=total,
        correct=correct,
        duration_seconds=data.duration_seconds,
        answers={str(r.id): r.chosen for r in review},
    )
    session.add(attempt)
    await session.commit()

    return ResultOut(
        attempt_id=attempt.id,
        total=total,
        correct=correct,
        wrong=total - correct - skipped,
        skipped=skipped,
        percent=percent,
        duration_seconds=data.duration_seconds,
        best_percent=max(percent, int(best_before or 0)),
        previous_percent=round(previous.correct * 100 / previous.total) if previous and previous.total else None,
        by_level=[
            LevelStat(difficulty=d, total=v[0], correct=v[1])
            for d, v in sorted(levels.items(), key=lambda kv: DIFFICULTY_ORDER.get(kv[0], 1))
        ],
        review=review,
    )
