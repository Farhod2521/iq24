"""AI test generator: an LLM writes multiple-choice tests for one topic of a book.

Provider-agnostic: one connection in .env (AI_URL, AI_KEY, AI_MODEL, AI_FORMAT) in OpenAI-style or
Anthropic-style format. The model returns JSON. Figures are *described* by the model and *drawn* by
figures.py, so graphs and shapes come out exact. Everything is validated before the admin sees it, and nothing is
saved automatically — the admin reviews the drafts and saves the ones they keep.
"""

import json
import logging
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

import anthropic
import openai
from pydantic import BaseModel

from .config import get_settings
from .figures import FigureError, render_figure
from .mathtext import escape_json_latex, normalize, normalize_solution
from .solution import Solution, answer_matches, check_math
from .svg import InvalidSvg, sanitize_svg

log = logging.getLogger("qanot.ai")

Difficulty = Literal["easy", "medium", "hard"]
DIFFICULTY_UZ = {"easy": "oson", "medium": "o'rta", "hard": "qiyin"}


class GeneratedQuestion(BaseModel):
    difficulty: Difficulty
    text: str
    options: list[str]
    correct: int
    explanation: str
    figure: dict | None = None  # the model's description of the figure
    figure_svg: str = ""  # sanitized SVG drawn from `figure`, "" for a question without a figure
    solution: dict | None = None  # notebook solution (app/solution.py), checked by code; None if it failed checks


class GenerationError(Exception):
    """A failure worth showing to the admin as-is (already in Uzbek)."""


SYSTEM_PROMPT = """\
You are a senior author of mathematics tests for Uzbekistan's national certificate and university entrance exams \
(DTM / Milliy sertifikat). You write multiple-choice questions for school-leavers ("abituriyentlar"). Teachers \
publish your questions to thousands of students, so a wrong answer key or a confusing question does real harm: \
correctness and clarity matter more than speed or variety.

## Level and style
- Write at the level of real certificate and entrance-exam questions: each question needs genuine mathematical \
work, not just recalling a definition. Avoid questions a student can answer by copying a number from the text.
- Uzbek, Latin script, the clear neutral style of Uzbek textbooks (o', g', ta'lim). School notation: "·" for \
multiplication, ":" for division, "−" for minus, superscripts for powers in plain text (x², 2³, 8²⁰²⁵), "√" for roots, decimal commas (0,7). Never write powers \
programmer-style ("8^2025", "2**10", "x^(n+1)") — students don't read that notation.
- Fractions are typeset exactly as in the printed book, never as "a/b" in a line. Write every fraction, mixed \
number and multi-level expression in LaTeX between $…$ — in the text, in the options and in the solution: \
a fraction $\\frac{a}{b}$, a mixed number $n\\frac{a}{b}$, \
brackets $\\left(…\\right):\\left(…\\right)$, a fraction of fractions $\\frac{p\\cdot\\frac{a}{b}+…}{q\\cdot\\frac{c}{d}}$, \
a series $\\frac{…}{1\\cdot3}+\\frac{…}{3\\cdot5}+\\dots$ (these show the notation only — invent your own numbers). Inside $…$ use \\cdot, \\left( \\right), \
{,} for the decimal comma and ^{…} for powers. Keep words outside $…$. Options that are fractions are $…$ too \
("$\\frac{a}{b}$", "$n\\frac{a}{b}$"). In the JSON output every backslash is escaped ("\\\\frac").
- Stay inside the given topic and the level of the given book; don't need material from later topics.

## Every question
1. Exactly 4 options, exactly one correct; the other three are definitely wrong — check each.
2. Distractors come from real mistakes for this topic: sign errors, wrong order of operations, a forgotten case, \
an off-by-one count, using the wrong formula. No filler distractors.
3. Options share one form (all integers, all fractions in lowest terms, all intervals…) and similar length. Never \
"all of the above", "none of the above", "cannot be determined".
4. Clean numbers: the intended solution comes out neatly; shortcuts that skip the idea lead to a wrong option.
5. Self-contained, one reading only: state units, ranges ("1 dan 100 gacha", inclusive) and conditions.
6. Vary the types: computation, unknown parameter, counting, comparison, short word problem, reasoning about \
properties. Don't repeat questions listed as existing, and don't write near-copies that only change numbers.

## Difficulty
- "easy" (oson): one or two steps, one rule. Under a minute.
- "medium" (o'rta): two or three steps or two rules combined — a typical certificate question.
- "hard" (qiyin): several steps needing an idea (case analysis, a clever substitution, inclusion–exclusion) — the \
hardest entrance-exam level, still solvable by hand in a few minutes.

## Questions with a figure (chizmali savollar)
When asked for questions with a figure, write questions where the figure is essential:
- The figure is the source of data. At least one value needed to solve the question is given ONLY in the figure \
(a graph's roots or vertex, a side length, an angle, an interval) and is NOT repeated in the text. The text points \
to it: "Chizmada…", "Grafikda tasvirlangan…", "Rasmda berilgan…".
- Reading the figure is only the first step: the answer must need a calculation beyond what is drawn. The figure \
must not show the answer itself (never label the unknown with its value).
- Pick the figure the topic naturally uses: graphs for functions, equations and inequalities with a parameter; \
geometry for shapes, lengths, angles, areas; a number line for inequalities and intervals; a table or bar chart \
for data, percentages and word problems. Never a decorative figure.
- Bad: "Grafikda y = x² − 4x + 3 berilgan. Grafik Ox ni qayerda kesadi?" — the formula is in the text, the figure \
adds nothing and shows the answer. Good: "Grafikda y = x² + bx + c parabola tasvirlangan. b · c ni toping." — \
the roots 1 and 3 are read from the graph, then b = −4, c = 3, so b · c = −12.

You do NOT draw the figure. You describe it in "figure" and the system draws it exactly. Use one of these types \
(all coordinates are plain numbers; y points up):
- function_graph: {"type": "function_graph", "functions": [{"expr": "x^2 + b*x + c with real numbers, e.g. x^2-4*x+3", \
"label": "optional, e.g. y = f(x)"}], "x_min": -1, "x_max": 5, "y_min": -2, "y_max": 6, "tick_labels": true, \
"grid": true, "points": [{"x": 1, "y": 0, "label": "A", "dashed_to_axes": false}]}. "expr" is a formula in x with \
+ - * / ^, parentheses, sqrt(), abs(). Choose ranges that show every feature the student must read (roots, vertex, \
intercepts) with some margin, and use integer key points so they can be read from the grid.
- geometry: {"type": "geometry", "points": [{"label": "A", "x": 0, "y": 0}, …], "polygons": [["A", "B", "C"]], \
"segments": [{"from": "B", "to": "H", "dashed": true}], "circles": [{"center": "O", "radius": 5}], \
"labels": [{"from": "A", "to": "B", "text": "25 sm", "unknown": false}], \
"angles": [{"vertex": "C", "from": "A", "to": "B", "text": "60°", "right": false}]}. Give real coordinates that \
match every stated length and angle (a triangle with sides 25, 25, 14: A(0,0), C(14,0), B(7,24)). Mark the asked \
quantity with "unknown": true and a letter (x, h, …), never with its value. Every point used must be in "points".
- number_line: {"type": "number_line", "min": -5, "max": 5, "ticks": [-3, 0, 2], "points": [{"x": 2, "label": "", \
"open": true}], "intervals": [{"from": -3, "to": 2, "from_open": false, "to_open": true}]} (use null for an \
endless side).
- bar_chart: {"type": "bar_chart", "labels": ["Du", "Se", "Ch"], "values": [12, 18, 9], "title": "optional"}.
- table: {"type": "table", "header": ["x", "1", "2", "3"], "rows": [["y", "4", "7", "10"]]}.
For a question without a figure, "figure" is null.

## The worked solution ("solution")
Every question carries a worked solution that students read after the test, drawn as handwriting in a notebook. Write it the way a good teacher writes on the board: short, ordered steps a student can follow and repeat.
- 2–5 steps. Each step has a short "title" (what we do: "Berilgan ma'lumotlarni qo'yamiz", "Hisoblaymiz", "Qoldiqni topamiz") and 1–3 "lines" of mathematics — one equality or expression per line, not prose.
- Start with a formula or rule ONLY when the problem actually rests on one: the division-with-remainder identity, the number-of-divisors formula (a+1)(b+1)…, a divisibility rule, Viète's formulas, the discriminant, a short multiplication formula, a percentage formula, an area formula, Legendre's formula, and so on. Then the first step is titled "Formula" (or "Qoida") and has "boxed": true, written in words or symbols, e.g. "Bo'linuvchi = bo'luvchi × bo'linma + qoldiq".
- When the problem is plain calculation (312 · 352, 2345 + 6789, an order-of-operations expression), do NOT invent a formula. Show the calculation itself: for multiplying or adding or subtracting multi-digit whole numbers add a "column" to the step — {"a": "312", "b": "352", "op": "×", "result": "109824", "partials": ["624", "1560", "936"]} (op is one of + − ×; "partials" only for multiplication: a × each digit of b from the right, without trailing zeros) — or show a convenient regrouping (125 · 8 · 37 = 1000 · 37 = 37000) when that is the smart way.
- Every numeric equality you write must be exactly true; the system recomputes them and rejects any slip. Use the notation "·" or "×", "−", ":", superscripts (2³), decimal commas as in Uzbek schools, and fractions in $…$ LaTeX ($\\frac{a}{b}\\cdot\\frac{c}{d}=\\frac{ac}{bd}$ with real numbers).
- "answer": the circled final line, short and containing the correct option exactly: "Qoldiq = 7", "Javob: 24", "x = 5".
- "check" (optional): a quick verification when it is natural — for division with remainder a long division {"title": "Tekshirish", "division": {"dividend": "247", "divisor": "15", "quotient": "16", "product": "240", "remainder": "7"}}, for an equation the substitution in "lines" ("2 · 5 + 3 = 13 ✓"). Omit it when it adds nothing.
- "conclusion" (optional): one sentence in Uzbek restating the result ("Demak, …").

## Before you answer
Solve every question yourself from scratch after writing it and recompute the arithmetic. Confirm the option \
marked correct equals your result and the other three differ from it. For a figure, check that every number in it \
matches the question and your solution, that the needed data really is in the figure, and that the figure alone \
doesn't give the answer away. If a question is ambiguous or has two defensible answers, replace it.

## Output — JSON only
{"questions": [{"difficulty": "easy | medium | hard", "text": "…", "options": ["…", "…", "…", "…"], "correct": 0, \
"explanation": "…", "figure": null, "solution": {"steps": [{"title": "…", "lines": ["…"], "boxed": false}], "answer": "…", "check": null, "conclusion": "…"}}]}
- "options": plain strings without "A)" prefixes; "correct": 0-based index, at a varied position;
- "explanation": a short step-by-step solution in Uzbek (1–4 sentences) ending with the answer; you may name the \
common mistake behind one distractor in a short clause;
- "figure": the figure description, or null;
- "solution": the worked solution described above (required for every question).
"""


def _user_prompt(
    *,
    subject: str,
    book: str,
    topic: str,
    topic_number: int | None,
    difficulty: Difficulty | Literal["mixed"],
    count: int,
    figure_count: int,
    existing: list[str],
    notes: str | None,
) -> str:
    total = count + figure_count
    if difficulty == "mixed":
        level = (
            f"a mixed set: about a third each of easy, medium and hard (for {total} questions, split as evenly as "
            "possible, starting from easy)"
        )
    else:
        level = f'"{difficulty}" ({DIFFICULTY_UZ[difficulty]}) — every question at this level'

    existing_block = "\n".join(f"- {t}" for t in existing) if existing else "(none yet)"
    if figure_count and count:
        what = (
            f"exactly {total} questions: {count} WITHOUT a figure (\"figure\": null), then {figure_count} WITH a "
            "figure. Every one of those last questions must have a non-null \"figure\" that the question depends on."
        )
    elif figure_count:
        what = (
            f"exactly {figure_count} questions, ALL WITH a figure. Every question must have a non-null \"figure\" "
            "that the question depends on."
        )
    else:
        what = f'exactly {count} questions without a figure ("figure": null).'
    parts = [
        f"Subject: {subject}",
        f"Book: {book}",
        f"Topic{f' {topic_number}' if topic_number else ''}: {topic}",
        f"Difficulty: {level}",
        "",
        "Questions already in this topic (do not repeat them or write near-copies):",
        existing_block,
    ]
    if notes:
        parts += ["", f"Additional instructions from the teacher: {notes}"]
    parts += ["", f"Write {what}"]
    return "\n".join(parts)


def clean_solution(raw, correct_option: str) -> dict | None:
    """A model-written solution, validated: right shape, every calculation recomputed, circled answer matches."""
    if not raw:
        return None
    try:
        sol = Solution.model_validate(normalize_solution(raw) if isinstance(raw, dict) else raw)
    except ValueError:
        return None
    problem = check_math(sol)
    if problem:
        log.info("dropping a solution: %s", problem)
        return None
    if not answer_matches(sol, correct_option):
        log.info("dropping a solution whose answer %r doesn't state %r", sol.answer, correct_option)
        return None
    return sol.model_dump(exclude_none=True)


def _clean(raw: list[dict], difficulty: Difficulty | Literal["mixed"]) -> list[GeneratedQuestion]:
    """Validate the model's JSON and normalise it; drop anything malformed rather than show a broken test."""
    out: list[GeneratedQuestion] = []
    for item in raw:
        try:
            q = GeneratedQuestion.model_validate(item)
        except ValueError:
            continue
        options = [normalize(str(o).strip()) for o in q.options]
        if len(options) != 4 or any(not o for o in options) or len(set(options)) != 4:
            continue
        if not 0 <= q.correct < len(options) or len(q.text.strip()) < 5:
            continue
        figure = ""
        if q.figure:
            try:
                figure = sanitize_svg(render_figure(q.figure))
            except (FigureError, InvalidSvg) as e:
                log.info("dropping a question whose figure can't be drawn: %s", e)
                continue  # the question depends on a figure we can't show
        solution = clean_solution(item.get("solution"), options[q.correct])
        # reshuffle so the answer position never follows a pattern
        order = list(range(4))
        random.shuffle(order)
        out.append(
            GeneratedQuestion(
                difficulty=q.difficulty if difficulty == "mixed" else difficulty,
                text=normalize(q.text.strip()),
                options=[options[i] for i in order],
                correct=order.index(q.correct),
                explanation=normalize(q.explanation.strip()),
                figure=q.figure if figure else None,
                figure_svg=figure,
                solution=solution,
            )
        )
    return out


# ─── provider call (URL + key + model) ───────────────────────────────────────


class ProviderFailed(Exception):
    """The AI call failed in a way worth telling the admin about."""


def _host(url: str) -> str:
    return urlparse(url).hostname or url


def _connection() -> dict:
    s = get_settings()
    return {"url": s.ai_url.strip(), "key": s.ai_key.strip(), "model": s.ai_model.strip(), "format": s.ai_format.strip().lower() or "openai"}


def ai_status() -> dict:
    """What the admin UI shows: is AI set up, and with which host and model."""
    c = _connection()
    return {"configured": bool(c["url"] and c["key"] and c["model"]), "host": _host(c["url"]) if c["url"] else "", "model": c["model"]}


def _status_reason(status_code: int) -> str:
    return {
        401: "API kaliti noto'g'ri",
        402: "balans tugagan",
        403: "kalitga ruxsat yo'q",
        404: "URL yoki model topilmadi",
        429: "limit yoki balans tugagan",
    }.get(status_code, "server xatosi" if status_code >= 500 else f"so'rov qabul qilinmadi ({status_code})")


async def _ask_anthropic_format(conn: dict, system: str, user: str) -> tuple[str, int, int]:
    client = anthropic.AsyncAnthropic(api_key=conn["key"], base_url=conn["url"])
    params: dict = {
        "model": conn["model"],
        "max_tokens": 32000,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    official = _host(conn["url"]) == "api.anthropic.com"
    try:
        if official:
            # Claude API extras: effort, and a server-side fallback model when a safety classifier declines
            async with client.beta.messages.stream(
                **params,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={"effort": "medium"},
            ) as stream:
                message = await stream.get_final_message()
        else:
            async with client.messages.stream(**params) as stream:
                message = await stream.get_final_message()
    except anthropic.APIStatusError as e:
        raise ProviderFailed(_status_reason(e.status_code))
    except anthropic.APIConnectionError:
        raise ProviderFailed("serverga ulanib bo'lmadi")

    if message.stop_reason == "refusal":
        raise ProviderFailed("so'rovni bajarmadi")
    if message.stop_reason == "max_tokens":
        raise ProviderFailed("javob juda uzun bo'lib ketdi")
    text = next((b.text for b in message.content if b.type == "text"), "")
    return text, message.usage.input_tokens, message.usage.output_tokens


async def _ask_openai_format(conn: dict, system: str, user: str) -> tuple[str, int, int]:
    client = openai.AsyncOpenAI(api_key=conn["key"], base_url=conn["url"], timeout=300)
    params: dict = {
        "model": conn["model"],
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_object"},
    }
    try:
        try:
            response = await client.chat.completions.create(**params)
        except openai.BadRequestError:
            # some OpenAI-style endpoints don't accept response_format; the prompt already asks for JSON
            params.pop("response_format")
            response = await client.chat.completions.create(**params)
    except openai.APIStatusError as e:
        raise ProviderFailed(_status_reason(e.status_code))
    except openai.APIConnectionError:
        raise ProviderFailed("serverga ulanib bo'lmadi")

    if not response.choices:
        raise ProviderFailed("bo'sh javob qaytardi")
    choice = response.choices[0]
    if choice.finish_reason == "length":
        raise ProviderFailed("javob juda uzun bo'lib ketdi")
    usage = response.usage
    return choice.message.content or "", usage.prompt_tokens if usage else 0, usage.completion_tokens if usage else 0


_FAILED_DIR = Path(get_settings().media_dir) / "ai_failures"


def _json_object(text: str, key: str) -> dict:
    """The JSON object holding `key` inside the model's text.

    Tolerates a ```json fence and prose around it — including prose with LaTeX braces ("0{,}7", "\\frac{1}{2}"),
    so the object is found by trying to decode at every "{" that opens a JSON key, not by the first "{".
    When nothing decodes, the raw text is kept in media/ai_failures/ for inspection and ValueError is raised.
    """
    fixed = escape_json_latex(text)
    decoder = json.JSONDecoder()
    for m in re.finditer(r'\{\s*"', fixed):
        try:
            obj, _ = decoder.raw_decode(fixed, m.start())
        except ValueError:
            continue
        if isinstance(obj, dict) and key in obj:
            return obj
    repaired = _drop_stray_closers(fixed, key)
    if repaired is not None:
        return repaired
    try:
        _FAILED_DIR.mkdir(parents=True, exist_ok=True)
        path = _FAILED_DIR / f"{datetime.now():%Y%m%d-%H%M%S}-{key}.txt"
        path.write_text(text, encoding="utf-8")
        log.warning("AI output without a %r object (%d chars) saved to %s", key, len(text), path)
    except OSError:
        pass
    if not text.strip():
        raise ValueError("empty AI output")
    raise ValueError(f"no {key!r} object in AI output")


def _drop_stray_closers(text: str, key: str, tries: int = 5) -> dict | None:
    """Long nested replies sometimes close an object once too often ('…]]}}},{"type"…'); delete the "}" / "]" the
    decoder trips over and decode again."""
    start = text.find('{"' + key + '"')
    if start < 0:
        start = text.find("{")
    if start < 0:
        return None
    text = text[start:]
    for _ in range(tries):
        try:
            obj, _ = json.JSONDecoder().raw_decode(text)
        except json.JSONDecodeError as e:
            if e.pos >= len(text) or text[e.pos] not in "}]":
                return None
            text = text[: e.pos] + text[e.pos + 1 :]
            continue
        return obj if isinstance(obj, dict) and key in obj else None
    return None


def _parse_json(text: str) -> list:
    """Questions out of the model's text."""
    return _json_object(text, "questions")["questions"]


async def _ask(conn: dict, prompt: str) -> tuple[list[GeneratedQuestion], int, int, str]:
    """One model call → raw questions (not yet cleaned) + token usage."""
    ask = _ask_anthropic_format if conn["format"] == "anthropic" else _ask_openai_format
    text, tokens_in, tokens_out = await ask(conn, SYSTEM_PROMPT, prompt)
    return _parse_json(text), tokens_in, tokens_out, text


async def generate_questions(
    *,
    subject: str,
    book: str,
    topic: str,
    topic_number: int | None,
    difficulty: Difficulty | Literal["mixed"],
    count: int,
    figure_count: int = 0,
    existing: list[str],
    notes: str | None = None,
) -> tuple[list[GeneratedQuestion], dict]:
    c = _connection()
    if not (c["url"] and c["key"] and c["model"]):
        raise GenerationError("AI sozlanmagan: .env faylida AI_URL, AI_KEY va AI_MODEL ni kiriting.")

    base = dict(subject=subject, book=book, topic=topic, topic_number=topic_number, difficulty=difficulty, notes=notes)
    tokens_in = tokens_out = 0
    try:
        raw, ti, to, _ = await _ask(c, _user_prompt(**base, count=count, figure_count=figure_count, existing=existing))
        tokens_in, tokens_out = ti, to
        cleaned = _clean(raw, difficulty)
        plain = [q for q in cleaned if not q.figure_svg][:count]
        figured = [q for q in cleaned if q.figure_svg][:figure_count]

        # models sometimes skip or botch figures; ask once more just for the missing ones
        missing = figure_count - len(figured)
        if missing > 0:
            seen = existing + [q.text for q in plain + figured]
            raw2, ti, to, _ = await _ask(c, _user_prompt(**base, count=0, figure_count=missing, existing=seen))
            tokens_in, tokens_out = tokens_in + ti, tokens_out + to
            figured += [q for q in _clean(raw2, difficulty) if q.figure_svg][:missing]
    except ProviderFailed as e:
        log.warning("AI call failed: %s", e)
        raise GenerationError(f"AI ishlamadi: {e}.")
    except (ValueError, KeyError, TypeError, IndexError):
        log.warning("AI returned unparseable output")
        raise GenerationError("AI javobini o'qib bo'lmadi. Qayta urinib ko'ring.")

    questions = plain + figured
    if not questions:
        raise GenerationError("AI yaroqli test qaytarmadi. Qayta urinib ko'ring.")

    warnings = []
    if len(plain) < count:
        warnings.append(f"oddiy testlardan {count - len(plain)} tasi chiqmadi")
    if len(figured) < figure_count:
        warnings.append(f"rasmli testlardan {figure_count - len(figured)} tasi chiqmadi")
    usage = {
        "host": _host(c["url"]),
        "model": c["model"],
        "input_tokens": tokens_in,
        "output_tokens": tokens_out,
        "warning": ("Diqqat: " + ", ".join(warnings) + ". «Qayta yaratish» bilan yana urinib ko'ring.") if warnings else "",
    }
    return questions, usage


# ─── independent answer check ────────────────────────────────────────────────

VERIFY_PROMPT = """\
You check multiple-choice mathematics questions before they are published to students. You are given questions \
without their answer key. Solve each one yourself, carefully and from scratch, and report the index (0-based) of \
the single correct option. If no option is correct, more than one option is correct, or the question is ambiguous \
or unsolvable as written (including a figure that contradicts the text), report -1.
A question may come with "figure": a JSON description of the drawing the student sees (graph formula and ranges, \
point coordinates, side labels, …). Use it exactly as given.

Respond with JSON only: {"answers": [{"i": 0, "answer": 2}, …]} — one entry per question, in order."""


async def verify(questions: list[GeneratedQuestion]) -> list[bool]:
    """Second, blind solve of each question; True where it agrees with the stored answer."""
    if not questions:
        return []
    c = _connection()
    items = [
        {"i": i, "text": q.text, "options": q.options, **({"figure": q.figure} if q.figure else {})}
        for i, q in enumerate(questions)
    ]
    ask = _ask_anthropic_format if c["format"] == "anthropic" else _ask_openai_format
    text, _, _ = await ask(c, VERIFY_PROMPT, json.dumps({"questions": items}, ensure_ascii=False))
    data = _json_object(text, "answers")
    got = {int(a["i"]): int(a["answer"]) for a in data.get("answers", []) if "i" in a and "answer" in a}
    return [got.get(i) == q.correct for i, q in enumerate(questions)]


# ─── worked solutions for existing questions ─────────────────────────────────

# the solution-writing rules are the same section of the generator prompt
SOLUTION_RULES = "## The worked solution" + SYSTEM_PROMPT.split("## The worked solution", 1)[1].split("## Before you answer", 1)[0]
EXPLAIN_PROMPT = SYSTEM_PROMPT.split("## Every question")[0] + SOLUTION_RULES + """## Task
You are given finished questions WITH their correct answer. Do not change the questions. For each one write the worked solution ("solution") following the rules above, for the topic the question belongs to. Solve it yourself first; the solution must arrive at the given correct answer.

Respond with JSON only: {"solutions": [{"i": 0, "solution": {…}}, …]} — one entry per question, in order."""


async def explain(questions: list[dict], topic: str) -> list[dict | None]:
    """Worked solutions for existing questions: [{"text", "options", "correct", "figure"?}] → solution or None each."""
    if not questions:
        return []
    c = _connection()
    items = [
        {"i": i, "text": q["text"], "options": q["options"], "correct_answer": q["options"][q["correct"]],
         **({"figure": q["figure"]} if q.get("figure") else {})}
        for i, q in enumerate(questions)
    ]
    ask = _ask_anthropic_format if c["format"] == "anthropic" else _ask_openai_format
    text, _, _ = await ask(c, EXPLAIN_PROMPT, json.dumps({"topic": topic, "questions": items}, ensure_ascii=False))
    data = _json_object(text, "solutions")
    got = {int(e["i"]): e.get("solution") for e in data.get("solutions", []) if "i" in e}
    return [clean_solution(got.get(i), q["options"][q["correct"]]) for i, q in enumerate(questions)]
