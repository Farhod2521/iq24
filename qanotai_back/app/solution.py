"""Step-by-step ("handwritten notebook") solution of a test question.

Stored as JSON on Question.solution and drawn by the frontend as notebook-style handwriting. Keeping it as data
(not an image) means numbers stay exact, can be edited, and can be checked by code — check_math() recomputes
every purely numeric equality, column operation and long division, so a solution with an arithmetic slip is
rejected instead of shown to students.
"""

import math
import re
from fractions import Fraction
from typing import Literal

from pydantic import BaseModel, Field

from .mathtext import latex_to_plain


class ColumnOp(BaseModel):
    """Column (vertical) addition, subtraction or multiplication of two whole numbers."""

    a: str = Field(max_length=20)
    b: str = Field(max_length=20)
    op: str = Field(pattern=r"^[+−×-]$")
    result: str = Field(max_length=24)
    partials: list[str] = Field(default_factory=list, max_length=6)  # partial products of a column multiplication


class SolutionStep(BaseModel):
    title: str = Field(max_length=120)  # "Formula", "Berilgan ma'lumotlarni qo'yamiz", …
    lines: list[str] = Field(default_factory=list, max_length=8)  # one line of math/text each
    boxed: bool = False  # draw the lines inside a frame (key formula)
    column: ColumnOp | None = None  # a written column calculation under the lines


class LongDivision(BaseModel):
    """Column division drawn as in a school notebook: dividend | divisor, product under it, remainder."""

    dividend: str = Field(max_length=20)
    divisor: str = Field(max_length=20)
    quotient: str = Field(max_length=20)
    product: str = Field(max_length=20)
    remainder: str = Field(max_length=20)


class SolutionCheck(BaseModel):
    title: str = Field(default="Tekshirish", max_length=60)
    lines: list[str] = Field(default_factory=list, max_length=6)
    division: LongDivision | None = None


class Solution(BaseModel):
    # physics notebook header: "Berilgan" values, their SI conversion, and what is asked ("F — ?")
    given: list[str] = Field(default_factory=list, max_length=10)
    si: list[str] = Field(default_factory=list, max_length=8)
    find: list[str] = Field(default_factory=list, max_length=4)
    steps: list[SolutionStep] = Field(min_length=1, max_length=8)
    answer: str = Field(max_length=80)  # circled at the end: "Qoldiq = 7"
    check: SolutionCheck | None = None
    conclusion: str | None = Field(default=None, max_length=300)


class ExplainerBlock(BaseModel):
    """One piece of the illustrated explanation: a paragraph, a formula, a picture, a numbered step or a tip."""

    type: Literal["text", "formula", "figure", "step", "tip"]
    title: str | None = Field(default=None, max_length=120)
    text: str | None = Field(default=None, max_length=900)
    tex: str | None = Field(default=None, max_length=400)  # formula block: LaTeX, shown large and framed
    where: list[str] = Field(default_factory=list, max_length=8)  # formula block: what each letter means
    figure: dict | None = None  # figure block: description (figures.py / physics_figures.py)
    svg: str | None = Field(default=None, max_length=60_000)  # figure block: the sanitized drawing, shown inline


class Explainer(BaseModel):
    """Second notebook solution: the same handwritten page, but slow and picture-first — sketches drawn in the
    notebook, every formula taken apart — for a student who did not follow the short one."""

    blocks: list[ExplainerBlock] = Field(min_length=2, max_length=16)


# ─── arithmetic check ────────────────────────────────────────────────────────

_SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")
_NUMERIC = re.compile(r"^[\d\s.,+\-−×·*:/()^⁰¹²³⁴⁵⁶⁷⁸⁹⁻√π]+$")
# a unit written after a number: "6 N", "20 m/s", "9,8 m/s²", "300 K", "5 kJ", "2 km/soat"
_UNIT = re.compile(r"(?<=[\d)⁰¹²³⁴⁵⁶⁷⁸⁹])\s+(?:[A-Za-zμΩ°%][A-Za-zμΩ°]*(?:[/·][A-Za-zμΩ°]+)*[²³⁻¹]*)+(?=$|[\s)+\-−×·*:=])")


def _value(expr: str) -> Fraction | float | None:
    """Value of a purely numeric school expression, or None if it isn't one (letters, words, …): exact (Fraction)
    when rational, a float when it has roots or π ("4√3", "12π", "√(9 + 16)")."""
    expr = expr.strip()
    if not expr or not _NUMERIC.match(expr) or not re.search(r"\d", expr):
        return None
    # 2³ → 2**3 ; 1,5 / 1.5 → 1.5 ; school operators → python ones
    expr = re.sub(r"(⁻?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)", lambda m: "**(" + m.group(1).translate(_SUP) + ")", expr)
    expr = expr.replace("^", "**").replace("×", "*").replace("·", "*").replace("−", "-").replace(":", "/")
    expr = re.sub(r"(\d),(\d)", r"\1.\2", expr)
    if re.search(r"\d\s+\d", expr):  # "1 000" thousands separators
        expr = re.sub(r"(?<=\d)\s+(?=\d{3}\b)", "", expr)
    irrational = "√" in expr or "π" in expr
    if irrational:
        # √3 → sqrt(3), √(…) → sqrt(…); 4√3 → 4*sqrt(3), 2π → 2*pi
        expr = re.sub(r"√\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", expr).replace("√", "sqrt").replace("π", "pi")
        expr = re.sub(r"(?<=[\d)])\s*(?=sqrt|pi|\()", "*", expr)
    expr = re.sub(r"(\d+(?:\.\d+)?)", r"Fraction('\1')", expr)
    if "**" in expr and re.search(r"\*\*\s*Fraction\('(\d{3,})", expr):
        return None  # absurd exponents
    names = {"Fraction": Fraction, "sqrt": lambda x: math.sqrt(x), "pi": math.pi}
    try:
        v = eval(expr, {"__builtins__": {}}, names)  # noqa: S307 — input is digits/operators/sqrt/pi only
    except Exception:
        return None
    if isinstance(v, complex):
        return None
    if irrational or isinstance(v, float):
        return float(v)
    return v if isinstance(v, Fraction) else Fraction(v)


def _same(a, b) -> bool:
    if isinstance(a, Fraction) and isinstance(b, Fraction):
        return a == b
    return math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=1e-9)


def _num(text: str) -> int | None:
    t = re.sub(r"\s", "", text)
    return int(t) if re.fullmatch(r"-?\d+", t) else None


def strip_units(expr: str) -> str:
    """'4200 J/(kg·K)' stays unchecked, but '2 · 3 = 6 N' → '2 · 3 = 6' so physics arithmetic is recomputed too."""
    return _UNIT.sub("", expr)


def check_math(sol: Solution, units: bool = False) -> str | None:
    """None when every checkable calculation is right, else a short description of the first mistake.

    units=True (physics): a unit written after a number is ignored, so "F = 2 · 5 = 10 N" is checked as 2 · 5 = 10.
    """
    lines = [line for s in sol.steps for line in s.lines] + (sol.check.lines if sol.check else [])
    for line in lines:
        plain = latex_to_plain(line)
        if units:
            # a unit conversion ("5 kJ = 5000 J", "36 km/soat = 10 m/s") is not an arithmetic equality
            if len({u.strip() for side in plain.split("=") for u in _UNIT.findall(side)}) > 1:
                continue
            plain = strip_units(plain)
        sides = re.split(r"=", plain)
        values = [_value(s) for s in sides]
        known = [v for v in values if v is not None]
        if len(known) >= 2 and any(not _same(v, known[0]) for v in known):
            return f"noto'g'ri hisob: {line}"
    for s in sol.steps:
        c = s.column
        if c is None:
            continue
        a, b, r = _num(c.a), _num(c.b), _num(c.result)
        if None in (a, b, r):
            return "ustun amalda son emas"
        expected = {"+": a + b, "−": a - b, "-": a - b, "×": a * b}[c.op]
        if expected != r:
            return f"ustun amal xato: {c.a} {c.op} {c.b} = {c.result}"
    if sol.check and sol.check.division:
        d = sol.check.division
        n, q, p, dd, rem = (_num(x) for x in (d.dividend, d.quotient, d.product, d.divisor, d.remainder))
        if None in (n, q, p, dd, rem) or dd * q != p or n - p != rem or not 0 <= rem < dd:
            return "ustun bo'lish xato"
    return None


def answer_matches(sol: Solution, correct_option: str) -> bool:
    """The circled answer must state the correct option (ignoring spaces and case)."""
    squash = lambda s: re.sub(r"\s+|\$|(?<=\\)[dt](?=frac)", "", s).lower().replace("−", "-")  # noqa: E731
    return squash(correct_option) in squash(sol.answer)
