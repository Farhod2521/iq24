"""Starter catalogue so a fresh install isn't empty: the six core subjects and one book each.

Runs only while the subjects table is empty, so anything an admin edits or deletes stays that way.
Covers point at images bundled with the frontend (public/images/books).
"""

import random

from sqlalchemy import func, select

from .db import SessionLocal
from .models import Book, Question, Subject, Topic
from .questions_data import BOLINISH_BELGILARI, NATURAL_SONLAR
from .topics_data import MATEMATIKA_1_QISM

CATALOG = [
    ("Matematika", "blue", "Matematika 1-qism", "math", 250),
    ("Ona tili", "rose", "Ona tili va adabiyot", "onatili", 198),
    ("Tarix", "amber", "O'zbekiston tarixi", "tarix", 180),
    ("Ingliz tili", "violet", "Ingliz tili", "ingliz", 220),
    ("Kimyo", "emerald", "Kimyo", "kimyo", 150),
    ("Fizika", "sky", "Fizika", "fizika", 175),
]


async def seed_catalog() -> None:
    async with SessionLocal() as session:
        if (await session.execute(select(func.count(Subject.id)))).scalar_one():
            return
        for name, color, title, cover, tests in CATALOG:
            subject = Subject(name=name, color=color)
            session.add(subject)
            await session.flush()
            book = Book(title=title, subject_id=subject.id, year=2026, cover_url=f"/images/books/{cover}.webp", test_count=tests)
            session.add(book)
            if cover == "math":
                await session.flush()
                topics = add_topics(session, book.id, MATEMATIKA_1_QISM)
                await session.flush()
                add_questions(session, topics[0].id, NATURAL_SONLAR)
                add_questions(session, topics[1].id, BOLINISH_BELGILARI)
        await session.commit()


def add_topics(session, book_id: int, rows) -> list[Topic]:
    topics = [
        Topic(book_id=book_id, position=position, kind=kind, number=number, title=title, page=page)
        for position, (kind, number, title, page) in enumerate(rows, start=1)
    ]
    session.add_all(topics)
    return topics


def add_questions(session, topic_id: int, rows) -> None:
    """The data lists the right answer first; shuffle each question's options (deterministically, so a
    re-seed gives the same test) so the answer isn't always A."""
    for position, (difficulty, text, options, correct, explanation) in enumerate(rows, start=1):
        order = list(range(len(options)))
        random.Random(f"{topic_id}:{position}").shuffle(order)
        session.add(
            Question(
                topic_id=topic_id,
                position=position,
                difficulty=difficulty,
                text=text,
                options=[options[i] for i in order],
                correct=order.index(correct),
                explanation=explanation,
            )
        )
