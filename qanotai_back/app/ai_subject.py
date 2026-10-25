"""Subject test writer shared by physics, chemistry, planimetry and stereometry: a subject is its prompts; this module is the
pipeline — generate questions (with a figure only where the model decides one is needed), validate and draw them,
blind-verify the answers, and write the two notebook solutions (the short one checked by code, and the detailed,
picture-first one).

The provider plumbing (one URL / key / model from .env, JSON extraction) is shared with app/ai.py.
"""

import json
import logging
import random
from dataclasses import dataclass, field

from pydantic import ValidationError

from .ai import (
    DIFFICULTY_UZ,
    Difficulty,
    GeneratedQuestion,
    GenerationError,
    ProviderFailed,
    _ask_anthropic_format,
    _ask_openai_format,
    _connection,
    _json_object,
)
from .figures import FigureError, render_figure
from .mathtext import normalize, normalize_solution
from .solution import Explainer, Solution, answer_matches, check_math
from .svg import InvalidSvg, sanitize_svg


def _ask(conn: dict):
    return _ask_anthropic_format if conn["format"] == "anthropic" else _ask_openai_format


def _require_connection() -> dict:
    c = _connection()
    if not (c["url"] and c["key"] and c["model"]):
        raise GenerationError("AI sozlanmagan: .env faylida AI_URL, AI_KEY va AI_MODEL ni kiriting.")
    return c


def draw(figure: dict | None) -> str:
    """Sanitized SVG for a figure description ("" for none); raises FigureError / InvalidSvg if unusable."""
    return sanitize_svg(render_figure(figure)) if figure else ""


def solutions_prompt(system: str) -> str:
    """The notebook-solution writer: the generator prompt's style rules and solution section, plus the task."""
    rules = "## The worked solution" + system.split("## The worked solution", 1)[1].split("## Before you answer", 1)[0]
    return system.split("## Every question")[0] + rules + """## Task
You are given finished questions WITH their correct answer. Do not change the questions. For each one write the \
worked solution ("solution") following the rules above. Solve it yourself first; the solution must arrive at the \
given correct answer.

Respond with JSON only: {"solutions": [{"i": 0, "solution": {…}}, …]} — one entry per question, in order. In the \
JSON every backslash is escaped ("\\\\frac")."""


@dataclass
class SubjectAI:
    subject: str  # "Fizika", "Geometriya", …
    system: str  # generator prompt (must contain "## Every question", "## The worked solution", "## Before you answer")
    verify_prompt: str
    explainer_prompt: str
    units: bool = False  # ignore units after numbers when recomputing the notebook arithmetic
    figure_hint: str = "Add a figure only to those that need one."
    log: logging.Logger = field(default_factory=lambda: logging.getLogger("qanot.ai.subject"))

    @property
    def solutions_prompt(self) -> str:
        return solutions_prompt(self.system)

    # ─── checks ──────────────────────────────────────────────────────────────

    def clean_solution(self, raw, correct_option: str) -> dict | None:
        """Notebook solution, validated: shape, every numeric equality recomputed, the circled answer stated."""
        if not raw:
            return None
        try:
            sol = Solution.model_validate(normalize_solution(raw) if isinstance(raw, dict) else raw)
        except ValueError:
            return None
        sol.given = [normalize(x) for x in sol.given]
        sol.si = [normalize(x) for x in sol.si]
        sol.find = [normalize(x) for x in sol.find]
        problem = check_math(sol, units=self.units)
        if problem:
            self.log.info("dropping a solution: %s", problem)
            return None
        if not answer_matches(sol, correct_option):
            self.log.info("dropping a solution whose answer %r doesn't state %r", sol.answer, correct_option)
            return None
        return sol.model_dump(exclude_none=True)

    def clean_explainer(self, raw) -> dict | None:
        """Validated detailed solution with every figure drawn (sanitized SVG under "svg", shown inline on the
        notebook page); blocks whose figure can't be drawn are dropped; at least one picture is required."""
        if not isinstance(raw, dict):
            return None
        blocks = []
        for b in raw.get("blocks") or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "figure":
                try:
                    svg = draw(b.get("figure"))
                except (FigureError, InvalidSvg) as e:
                    self.log.info("dropping an explainer figure: %s", e)
                    continue
                if not svg:
                    continue
                b = {**b, "svg": svg}
            for key in ("text", "title"):
                if b.get(key):
                    b[key] = normalize(str(b[key]))
            b["where"] = [normalize(str(w)) for w in b.get("where") or []]
            blocks.append(b)
        try:
            explainer = Explainer.model_validate({"blocks": blocks})
        except ValidationError as e:
            self.log.info("dropping an explainer: %s", e.errors()[0].get("msg"))
            return None
        if not any(b.type == "figure" for b in explainer.blocks):
            self.log.info("dropping an explainer without a picture")
            return None
        return explainer.model_dump(exclude_none=True)

    def _clean(self, raw: list[dict], difficulty: Difficulty) -> list[GeneratedQuestion]:
        out: list[GeneratedQuestion] = []
        for item in raw:
            try:
                q = GeneratedQuestion.model_validate({**item, "difficulty": difficulty})
            except ValueError:
                continue
            options = [normalize(str(o).strip()) for o in q.options]
            if len(options) != 4 or any(not o for o in options) or len(set(options)) != 4:
                continue
            if not 0 <= q.correct < 4 or len(q.text.strip()) < 5:
                continue
            try:
                svg = draw(q.figure)
            except (FigureError, InvalidSvg) as e:
                self.log.info("dropping a question whose figure can't be drawn: %s", e)
                continue
            solution = self.clean_solution(item.get("solution"), options[q.correct])
            order = list(range(4))
            random.shuffle(order)
            out.append(
                GeneratedQuestion(
                    difficulty=difficulty,
                    text=normalize(q.text.strip()),
                    options=[options[i] for i in order],
                    correct=order.index(q.correct),
                    explanation=normalize(q.explanation.strip()),
                    figure=q.figure if svg else None,
                    figure_svg=svg,
                    solution=solution,
                )
            )
        return out

    # ─── calls ───────────────────────────────────────────────────────────────

    def _user_prompt(self, *, book: str, topic: str, topic_number: int | None, difficulty: Difficulty, count: int,
                     existing: list[str], notes: str | None) -> str:
        existing_block = "\n".join(f"- {t}" for t in existing) if existing else "(none yet)"
        parts = [
            f"Subject: {self.subject}",
            f"Book: {book}",
            f"Topic{f' {topic_number}' if topic_number else ''}: {topic}",
            f'Difficulty: "{difficulty}" ({DIFFICULTY_UZ[difficulty]}) — every question at this level',
            "",
            "Questions already in this topic (do not repeat them or write near-copies):",
            existing_block,
        ]
        if notes:
            parts += ["", f"Additional instructions from the teacher: {notes}"]
        parts += ["", f"Write exactly {count} questions. {self.figure_hint}"]
        return "\n".join(parts)

    async def generate_questions(self, *, book: str, topic: str, topic_number: int | None, difficulty: Difficulty,
                                 count: int, existing: list[str], notes: str | None = None) -> tuple[list[GeneratedQuestion], dict]:
        c = _require_connection()
        prompt = self._user_prompt(book=book, topic=topic, topic_number=topic_number, difficulty=difficulty,
                                   count=count, existing=existing, notes=notes)
        try:
            text, tokens_in, tokens_out = await _ask(c)(c, self.system, prompt)
            questions = self._clean(_json_object(text, "questions")["questions"], difficulty)
        except ProviderFailed as e:
            raise GenerationError(f"AI ishlamadi: {e}.")
        except (ValueError, KeyError, TypeError, IndexError):
            raise GenerationError("AI javobini o'qib bo'lmadi. Qayta urinib ko'ring.")
        if not questions:
            raise GenerationError("AI yaroqli test qaytarmadi. Qayta urinib ko'ring.")
        return questions[:count], {"input_tokens": tokens_in, "output_tokens": tokens_out}

    async def verify(self, questions: list[GeneratedQuestion]) -> list[bool]:
        """Second, blind solve of each question; True where it agrees with the stored answer."""
        if not questions:
            return []
        c = _require_connection()
        items = [
            {"i": i, "text": q.text, "options": q.options, **({"figure": q.figure} if q.figure else {})}
            for i, q in enumerate(questions)
        ]
        text, _, _ = await _ask(c)(c, self.verify_prompt, json.dumps({"questions": items}, ensure_ascii=False))
        got = {int(a["i"]): int(a["answer"]) for a in _json_object(text, "answers").get("answers", []) if "i" in a and "answer" in a}
        return [got.get(i) == q.correct for i, q in enumerate(questions)]

    async def explain(self, questions: list[dict], topic: str) -> list[dict | None]:
        """Detailed notebook solutions for finished questions: [{"text", "options", "correct", "figure"?, "solution"?}]."""
        if not questions:
            return []
        c = _require_connection()
        items = [
            {
                "i": i,
                "text": q["text"],
                "options": q["options"],
                "correct_answer": q["options"][q["correct"]],
                **({"figure": q["figure"]} if q.get("figure") else {}),
                **({"notebook_solution": q["solution"]} if q.get("solution") else {}),
            }
            for i, q in enumerate(questions)
        ]
        text, _, _ = await _ask(c)(c, self.explainer_prompt, json.dumps({"topic": topic, "questions": items}, ensure_ascii=False))
        got = {int(e["i"]): e for e in _json_object(text, "explainers").get("explainers", []) if "i" in e}
        return [self.clean_explainer(got.get(i)) for i in range(len(questions))]

    async def write_solutions(self, questions: list[dict], topic: str) -> list[dict | None]:
        """Short notebook solutions for existing questions: [{"text", "options", "correct", "figure"?}]."""
        if not questions:
            return []
        c = _require_connection()
        items = [
            {"i": i, "text": q["text"], "options": q["options"], "correct_answer": q["options"][q["correct"]],
             **({"figure": q["figure"]} if q.get("figure") else {})}
            for i, q in enumerate(questions)
        ]
        text, _, _ = await _ask(c)(c, self.solutions_prompt, json.dumps({"topic": topic, "questions": items}, ensure_ascii=False))
        got = {int(e["i"]): e.get("solution") for e in _json_object(text, "solutions").get("solutions", []) if "i" in e}
        return [self.clean_solution(got.get(i), q["options"][q["correct"]]) for i, q in enumerate(questions)]
