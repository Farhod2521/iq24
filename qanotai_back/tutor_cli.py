"""tutor_cli.py — the shared engine of the subject test writers (test_tuz_fizika.py, test_tuz_geo.py, test_tuz_kimyo.py,
test_tuz_stereometriya.py): fill each topic of a book up to its plan (easy / medium / hard), with a figure where the
AI decides one is needed and two notebook solutions per test — the short one (formulas, checked by code) and the
detailed, picture-first one; plus --fill (add only what is missing), --status, --solutions, --explainers and a menu.

A subject script only gives a Config (book, prompts, topic guide) and calls cli(config).
"""

import argparse
import asyncio
import sys
import time
from dataclasses import dataclass, field

from sqlalchemy import delete, func, select

from app import ai
from app.ai_subject import SubjectAI
from app.db import SessionLocal, init_db
from app.models import Book, Question, TestAttempt, Topic
from test_tuz import Stats, ask, ask_topics, fatal, norm, parse_topics, remove_figure, report, save_figure, say



@dataclass
class Config:
    """One subject's test writer: which book, which AI prompts, what each topic needs."""

    label: str  # "Fizika" — shown in the menu
    book_title: str  # found in the database with ILIKE
    ai: SubjectAI
    guide: dict[int, list[str]]  # topic number → exercise families, pointed at in turn
    style_note: str  # appended to every batch's notes ("Kitob uslubida: …")
    # (difficulty, how many, batch size)
    plan: list[tuple[str, int, int]] = field(default_factory=lambda: [("easy", 25, 5), ("medium", 15, 5), ("hard", 10, 4)])


CFG: Config  # set by cli()


def per_topic() -> int:
    return sum(p[1] for p in CFG.plan)

MAX_ROUNDS = 3  # extra attempts per level when the AI returns fewer usable tests than asked
MAX_FAILS = 2  # consecutive failed AI calls after which a level is skipped (each failure costs tokens)
EXPLAIN_BATCH = 3  # questions per "write the detailed explanation" request (they are long)
SOLUTION_BATCH = 6

# ─── database helpers ────────────────────────────────────────────────────────


async def topic_questions(topic_id: int) -> list[Question]:
    async with SessionLocal() as s:
        return list((await s.execute(select(Question).where(Question.topic_id == topic_id).order_by(Question.position, Question.id))).scalars())


async def counts_for(topic_id: int) -> dict[str, int]:
    c = {"easy": 0, "medium": 0, "hard": 0, "figure": 0, "solved": 0, "explained": 0}
    for q in await topic_questions(topic_id):
        c[q.difficulty] = c.get(q.difficulty, 0) + 1
        c["figure"] += bool(q.image_url)
        c["solved"] += bool(q.solution)
        c["explained"] += bool(q.explainer)
    return c


async def store(topic_id: int, items: list[tuple[ai.GeneratedQuestion, dict | None]]) -> int:
    async with SessionLocal() as s:
        last = (await s.execute(select(func.coalesce(func.max(Question.position), 0)).where(Question.topic_id == topic_id))).scalar_one()
        for i, (q, explainer) in enumerate(items, start=1):
            s.add(
                Question(
                    topic_id=topic_id,
                    position=last + i,
                    difficulty=q.difficulty,
                    text=q.text,
                    options=q.options,
                    correct=q.correct,
                    explanation=q.explanation or None,
                    image_url=save_figure(q.figure_svg) if q.figure_svg else None,
                    figure=q.figure,
                    solution=q.solution,
                    explainer=explainer,
                )
            )
        await s.commit()
    return len(items)


def payload(q) -> dict:
    """What the AI is told about a finished question (stored row or fresh draft)."""
    return {"text": q.text, "options": q.options, "correct": q.correct, "figure": q.figure, "solution": q.solution}


# ─── generating tests ────────────────────────────────────────────────────────


async def explain_drafts(drafts: list, topic: Topic, stats: Stats) -> list[dict | None]:
    """Detailed notebook explanations for fresh drafts; None where it failed (filled later with --explainers)."""
    out: list[dict | None] = []
    for i in range(0, len(drafts), EXPLAIN_BATCH):
        chunk = drafts[i : i + EXPLAIN_BATCH]
        try:
            stats.calls += 1
            out += await CFG.ai.explain([payload(d) for d in chunk], f"{topic.number}. {topic.title}")
        except Exception as e:  # the tests are still worth keeping; the explanation can be added later
            stats.errors += 1
            say(f"  {topic.number}-mavzu: batafsil yechim yozilmadi — {e}")
            out += [None] * len(chunk)
    return out


async def fill_topic(topic: Topic, book: Book, verify: bool, stats: Stats, sem: asyncio.Semaphore) -> None:
    families = CFG.guide.get(topic.number or 0, [])
    label = f"{topic.number}-mavzu"
    batch_no = 0
    for difficulty, target, size in CFG.plan:
        fails = 0
        for _ in range(MAX_ROUNDS + target // size):
            if fails >= MAX_FAILS:
                say(f"  {label} {difficulty}: {fails} marta ketma-ket xato — token behuda ketmasligi uchun keyingi darajaga o'tildi")
                break
            have = (await counts_for(topic.id))[difficulty]
            need = target - have
            if need <= 0:
                break
            n = min(size, need)
            focus = [families[(batch_no + k) % len(families)] for k in range(2)] if families else []
            batch_no += 1
            notes = ("Bu to'plamda asosan quyidagi turdagi masalalar bo'lsin: " + "; ".join(focus) + ". ") if focus else ""
            notes += CFG.style_note
            seen = [q.text for q in await topic_questions(topic.id)]
            async with sem:
                try:
                    stats.calls += 1
                    drafts, usage = await CFG.ai.generate_questions(
                        book=book.title, topic=topic.title, topic_number=topic.number, difficulty=difficulty,
                        count=n, existing=[t[:140] for t in seen[-50:]], notes=notes,
                    )
                    stats.tokens_in += usage["input_tokens"]
                    stats.tokens_out += usage["output_tokens"]
                    known = {norm(t) for t in seen}
                    unique = []
                    for d in drafts:
                        if norm(d.text) not in known:
                            known.add(norm(d.text))
                            unique.append(d)
                    drafts = unique[:n]
                    if verify and drafts:
                        stats.calls += 1
                        try:
                            ok = await CFG.ai.verify(drafts)
                        except Exception:  # don't throw away a paid generation over one bad verifier reply
                            stats.calls += 1
                            ok = await CFG.ai.verify(drafts)
                        kept = [d for d, good in zip(drafts, ok) if good]
                        stats.rejected += len(drafts) - len(kept)
                        drafts = kept
                    explainers = await explain_drafts(drafts, topic, stats) if drafts else []
                except ai.GenerationError as e:
                    stats.errors += 1
                    say(f"  {label} {difficulty}: xato — {e}")
                    if fatal(e):
                        raise
                    fails += 1
                    await asyncio.sleep(5)
                    continue
                except Exception as e:  # network hiccup, bad JSON from the verifier, …
                    stats.errors += 1
                    say(f"  {label} {difficulty}: kutilmagan xato — {e!r}")
                    fails += 1
                    await asyncio.sleep(5)
                    continue
            fails = 0
            saved = await store(topic.id, list(zip(drafts, explainers)))
            stats.saved += saved
            with_sol = sum(d.solution is not None for d in drafts)
            with_fig = sum(bool(d.figure_svg) for d in drafts)
            with_exp = sum(e is not None for e in explainers)
            stats.solutions += with_sol
            say(f"  {label} {difficulty}: +{saved} (jami {have + saved}/{target}; rasmli {with_fig}, yechim {with_sol}, batafsil {with_exp})")
    # tests whose notebook solution or detailed explanation failed get one more chance
    await solve_topic(topic, missing_only=True, stats=stats, sem=sem, quiet=True)
    await explain_topic(topic, missing_only=True, stats=stats, sem=sem, quiet=True)
    c = await counts_for(topic.id)
    total = c["easy"] + c["medium"] + c["hard"]
    say(
        f"✓ {label} «{topic.title}»: oson {c['easy']}, o'rta {c['medium']}, qiyin {c['hard']} (rasmli {c['figure']}) "
        f"· yechim {c['solved']}/{total} · batafsil {c['explained']}/{total}"
    )


async def solve_topic(topic: Topic, missing_only: bool, stats: Stats, sem: asyncio.Semaphore, quiet: bool = False) -> None:
    """(Re)write the short notebook solution."""
    label = f"{topic.number}-mavzu"
    questions = [q for q in await topic_questions(topic.id) if not (missing_only and q.solution)]
    if not questions:
        if not quiet:
            say(f"✓ {label}: qisqa yechim yozadigan test yo'q")
        return
    done = failed = 0
    for i in range(0, len(questions), SOLUTION_BATCH):
        chunk = questions[i : i + SOLUTION_BATCH]
        async with sem:
            try:
                stats.calls += 1
                solutions = await CFG.ai.write_solutions([payload(q) for q in chunk], f"{topic.number}. {topic.title}")
            except ai.GenerationError as e:
                stats.errors += 1
                say(f"  {label} yechim: xato — {e}")
                if fatal(e):
                    raise
                continue
            except Exception as e:
                stats.errors += 1
                say(f"  {label} yechim: kutilmagan xato — {e!r}")
                continue
        async with SessionLocal() as s:
            for q, sol in zip(chunk, solutions):
                row = await s.get(Question, q.id)
                if sol is None or row is None:
                    failed += 1
                    continue
                row.solution = sol
                done += 1
            await s.commit()
    stats.solutions += done
    stats.no_solution += failed
    if not quiet or done or failed:
        say(f"✓ {label}: {done} ta qisqa yechim yozildi" + (f", {failed} tasi tekshiruvdan o'tmadi" if failed else ""))


async def explain_topic(topic: Topic, missing_only: bool, stats: Stats, sem: asyncio.Semaphore, quiet: bool = False) -> None:
    """(Re)write the detailed illustrated notebook explanation."""
    label = f"{topic.number}-mavzu"
    questions = [q for q in await topic_questions(topic.id) if not (missing_only and q.explainer)]
    if not questions:
        if not quiet:
            say(f"✓ {label}: batafsil yechim yozadigan test yo'q")
        return
    done = failed = 0
    for i in range(0, len(questions), EXPLAIN_BATCH):
        chunk = questions[i : i + EXPLAIN_BATCH]
        async with sem:
            try:
                stats.calls += 1
                explainers = await CFG.ai.explain([payload(q) for q in chunk], f"{topic.number}. {topic.title}")
            except ai.GenerationError as e:
                stats.errors += 1
                say(f"  {label} batafsil: xato — {e}")
                if fatal(e):
                    raise
                continue
            except Exception as e:
                stats.errors += 1
                say(f"  {label} batafsil: kutilmagan xato — {e!r}")
                continue
        async with SessionLocal() as s:
            for q, exp in zip(chunk, explainers):
                row = await s.get(Question, q.id)
                if exp is None or row is None:
                    failed += 1
                    continue
                row.explainer = exp
                done += 1
            await s.commit()
    if not quiet or done or failed:
        say(f"✓ {label}: {done} ta batafsil yechim yozildi" + (f", {failed} tasi o'tmadi" if failed else ""))


# ─── entry points ────────────────────────────────────────────────────────────


async def load(topic_numbers: list[int] | None) -> tuple[Book, list[Topic]]:
    async with SessionLocal() as s:
        book = (await s.execute(select(Book).where(Book.title.ilike(f"%{CFG.book_title}%")).order_by(Book.id))).scalars().first()
        if book is None:
            raise SystemExit(f"«{CFG.book_title}» kitobi bazada topilmadi.")
        topics = list(
            (await s.execute(select(Topic).where(Topic.book_id == book.id, Topic.kind == "lesson").order_by(Topic.position))).scalars()
        )
    if topic_numbers:
        missing = sorted(set(topic_numbers) - {t.number for t in topics})
        if missing:
            print(f"Ogohlantirish: kitobda bunday mavzu yo'q: {missing}")
        topics = [t for t in topics if t.number in topic_numbers]
    return book, topics


async def reset_topics(topics: list[Topic]) -> None:
    ids = [t.id for t in topics]
    async with SessionLocal() as s:
        for q in (await s.execute(select(Question).where(Question.topic_id.in_(ids)))).scalars():
            remove_figure(q.image_url)
        n_q = (await s.execute(delete(Question).where(Question.topic_id.in_(ids)))).rowcount
        n_a = (await s.execute(delete(TestAttempt).where(TestAttempt.topic_id.in_(ids)))).rowcount
        await s.commit()
    say(f"Tozalandi: {n_q} ta test va {n_a} ta natija ({len(topics)} ta mavzu).")


async def show_status(topics: list[Topic]) -> None:
    print(f"{'':>4} {'Mavzu':<52} {'oson':>5} {'o‘rta':>5} {'qiyin':>5} {'jami':>7} {'rasmli':>6} {'yechim':>6} {'batafsil':>8}")
    for t in topics:
        c = await counts_for(t.id)
        total = c["easy"] + c["medium"] + c["hard"]
        print(f"{t.number:>3}. {t.title[:52]:<52} {c['easy']:>5} {c['medium']:>5} {c['hard']:>5} {total:>4}/{per_topic()} "
              f"{c['figure']:>6} {c['solved']:>6} {c['explained']:>8}")


async def run(kind: str, topic_numbers: list[int], *, reset: bool = False, verify: bool = True, missing_only: bool = False,
              parallel: int = 2) -> None:
    book, topics = await load(topic_numbers)
    if not topics:
        print("Mavzu tanlanmadi.")
        return
    names = ", ".join(str(t.number) for t in topics)
    stats = Stats()
    sem = asyncio.Semaphore(max(1, parallel))
    started = time.monotonic()
    try:
        if kind == "tests":
            say(f"Test tuzish: {book.title}, {names}-mavzular · har biriga {per_topic()} ta · AI: {ai.ai_status()['model']}")
            if reset:
                await reset_topics(topics)
            await asyncio.gather(*(fill_topic(t, book, verify, stats, sem) for t in topics))
        elif kind == "solutions":
            say(f"{book.title}: qisqa yechimlarni {'to‘ldirish' if missing_only else 'qayta yozish'} — {names}-mavzular")
            await asyncio.gather(*(solve_topic(t, missing_only, stats, sem) for t in topics))
        else:
            say(f"{book.title}: batafsil yechimlarni {'to‘ldirish' if missing_only else 'qayta yozish'} — {names}-mavzular")
            await asyncio.gather(*(explain_topic(t, missing_only, stats, sem) for t in topics))
    except ai.GenerationError as e:
        say(f"To'xtatildi: {e}")
    report(stats, started)


async def gaps(topic: Topic) -> dict:
    """What a topic is missing: tests per level (to reach PLAN), short solutions and detailed explanations."""
    c = await counts_for(topic.id)
    total = c["easy"] + c["medium"] + c["hard"]
    need = {d: max(0, target - c[d]) for d, target, _ in CFG.plan}
    return {"have": c, "total": total, "need": need, "tests": sum(need.values()),
            "solutions": total - c["solved"], "explainers": total - c["explained"]}


async def run_fill(topic_numbers: list[int] | None, *, include_empty: bool, verify: bool = True, parallel: int = 2) -> None:
    """Check every topic from the start and add only what is missing: tests of each level up to 25/15/10, then the
    short and the detailed solutions of tests that lack them. Without topic numbers, topics with no tests yet are
    skipped unless include_empty (each of those costs a full 50-test run)."""
    book, topics = await load(topic_numbers)
    plan = []
    for t in topics:
        g = await gaps(t)
        if g["total"] == 0 and not (include_empty or topic_numbers):
            continue
        if g["tests"] or g["solutions"] or g["explainers"]:
            plan.append((t, g))
    if not plan:
        say("Hamma mavzular to'liq: to'ldiradigan narsa yo'q.")
        return

    print(f"{'':>4} {'Mavzu':<44} {'bor':>7}  {'qo‘shiladi: oson':>17} {'o‘rta':>6} {'qiyin':>6}  {'yechim':>7} {'batafsil':>9}")
    for t, g in plan:
        n = g["need"]
        print(f"{t.number:>3}. {t.title[:44]:<44} {g['total']:>3}/{per_topic()}  {n['easy']:>17} {n['medium']:>6} {n['hard']:>6}  "
              f"{g['solutions']:>7} {g['explainers']:>9}")
    print(f"Jami: {sum(g['tests'] for _, g in plan)} ta yangi test, {sum(g['solutions'] for _, g in plan)} ta qisqa yechim, "
          f"{sum(g['explainers'] for _, g in plan)} ta batafsil yechim ({len(plan)} ta mavzu).")

    stats = Stats()
    sem = asyncio.Semaphore(max(1, parallel))
    started = time.monotonic()
    say(f"To'ldirish boshlandi · AI: {ai.ai_status()['model']}")
    try:
        # fill_topic only asks for the missing tests of each level, then fills missing solutions and explanations
        await asyncio.gather(*(fill_topic(t, book, verify, stats, sem) for t, _ in plan))
    except ai.GenerationError as e:
        say(f"To'xtatildi: {e}")
    report(stats, started)
    left = [(t, g) for t, _ in plan if (g := await gaps(t))["tests"] or g["solutions"] or g["explainers"]]
    if left:
        say("Hali to'lmagan mavzular (qayta «To'ldirish» ni ishga tushiring): "
            + ", ".join(f"{t.number} (−{g['tests']} test)" if g["tests"] else f"{t.number} (yechim)" for t, g in left))


async def menu(parallel: int) -> None:
    while True:
        print()
        print(f"══════════ QANOT.AI · {CFG.label} test tuzish ({CFG.book_title}) ══════════")
        print("  1. Test tuzish                 — mavzular oralig'ini kiriting (masalan 1-5)")
        print("  2. Qisqa yechimni qayta yozish — mavzularni kiriting (masalan 3,4)")
        print("  3. Batafsil (rasmli) yechim    — yo'qlarini to'ldirish yoki qayta yozish")
        print("  4. Holatni ko'rish")
        print("  5. To'ldirish                  — har bir mavzuni tekshirib, kam test va yechimlarni qo'shish")
        print("  0. Chiqish")
        choice = ask("Tanlang: ")
        if choice in ("0", "", "q"):
            return
        if choice == "1":
            topics = ask_topics("Qaysi mavzular? (masalan 1-5 yoki 1,3,7): ")
            if topics:
                reset = ask("Shu mavzulardagi bor testlarni o'chirib, boshidan tuzaymi? [h = ha / Enter = yo'q, to'ldirish]: ").lower() in ("h", "ha")
                await run("tests", topics, reset=reset, parallel=parallel)
        elif choice in ("2", "3"):
            topics = ask_topics("Qaysi mavzular? (masalan 3,4 yoki 1-5): ")
            if topics:
                only = ask("Faqat yo'qlariga yozaymi? [Enter = ha / q = hammasiga qayta]: ").lower() not in ("q",)
                await run("solutions" if choice == "2" else "explainers", topics, missing_only=only, parallel=parallel)
        elif choice == "4":
            _, topics = await load(None)
            await show_status(topics)
        elif choice == "5":
            topics = ask_topics("Qaysi mavzular? [Enter = hammasi]: ")
            empty = False
            if not topics:
                empty = ask("Hali umuman testi yo'q mavzular ham to'ldirilsinmi? (har biri 50 ta test) [h = ha / Enter = yo'q]: ").lower() in ("h", "ha")
            await run_fill(topics or None, include_empty=empty, parallel=parallel)
        else:
            print("  1, 2, 3, 4, 5 yoki 0 ni tanlang.")


async def main() -> int:
    p = argparse.ArgumentParser(description=f"{CFG.book_title}: AI bilan test va ikki xil daftar yechimi tuzish")
    p.add_argument("--topics", nargs="*", default=[], help="test tuzish uchun mavzular: 1-5 yoki 1,3,7")
    p.add_argument("--reset", action="store_true", help="--topics dagi mavzular testlarini o'chirib, boshidan tuzish")
    p.add_argument("--solutions", nargs="*", default=[], help="qisqa daftar yechimini qayta yozish: 3,4")
    p.add_argument("--explainers", nargs="*", default=[], help="batafsil (rasmli) daftar yechimini yozish: 3,4")
    p.add_argument("--missing-only", action="store_true", help="--solutions / --explainers bilan: faqat yo'qlariga")
    p.add_argument("--status", action="store_true", help="mavzular bo'yicha holatni ko'rsatish")
    p.add_argument("--fill", nargs="*", default=None, help="to'ldirish: kam test va yechimlarni qo'shish (mavzusiz = boshlangan hamma mavzular)")
    p.add_argument("--with-empty", action="store_true", help="--fill bilan: testi yo'q mavzularni ham to'ldirish")
    p.add_argument("--parallel", type=int, default=2, help="bir vaqtda nechta mavzu ustida ishlash (standart 2)")
    p.add_argument("--no-verify", dest="verify", action="store_false", help="test javoblarini ikkinchi marta tekshirmaslik")
    args = p.parse_args()

    await init_db()
    if args.status:
        _, topics = await load(None)
        await show_status(topics)
        return 0
    status = ai.ai_status()
    if not status["configured"]:
        print("AI sozlanmagan: .env faylida AI_URL, AI_KEY va AI_MODEL ni kiriting, so'ng `docker compose up -d backend`.")
        return 1
    try:
        if args.fill is not None:
            numbers = parse_topics(" ".join(args.fill)) if args.fill else None
            await run_fill(numbers, include_empty=args.with_empty, verify=args.verify, parallel=args.parallel)
        elif args.topics:
            await run("tests", parse_topics(" ".join(args.topics)), reset=args.reset, verify=args.verify, parallel=args.parallel)
        elif args.solutions:
            await run("solutions", parse_topics(" ".join(args.solutions)), missing_only=args.missing_only, parallel=args.parallel)
        elif args.explainers:
            await run("explainers", parse_topics(" ".join(args.explainers)), missing_only=args.missing_only, parallel=args.parallel)
        else:
            print(f"AI: {status['model']} ({status['host']})")
            await menu(args.parallel)
    except ValueError as e:
        print(e)
        return 1
    return 0


def cli(config: Config) -> None:
    """Entry point of a subject script: test_tuz_fizika.py, test_tuz_geo.py, …"""
    global CFG
    CFG = config
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        print("\nTo'xtatildi. Qayta ishga tushirsangiz, qolgan joyidan davom etadi.")
