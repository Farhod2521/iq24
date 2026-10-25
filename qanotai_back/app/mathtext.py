"""Normalise maths notation in AI-written text to the school form stored in the database.

Models sometimes write powers programmer-style ("8^2025", "x^(n+1)", "2**10"). Students never see that notation in
textbooks, so before anything is saved powers are rewritten with superscript characters ("8²⁰²⁵", "xⁿ⁺¹"); the
frontend then draws superscript runs as real raised text. Exponents that superscript characters can't express are
left as they are (the frontend still raises "^(…)").

Fractions and multi-level expressions are written in LaTeX between $…$ ("$\\frac{5}{18}$") and typeset by the
frontend; that part of the text is left untouched here.
"""

import re

_SUP = {
    **dict(zip("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")),
    "+": "⁺", "-": "⁻", "−": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "i": "ⁱ", "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "k": "ᵏ", "m": "ᵐ", "x": "ˣ", "y": "ʸ",
}

# ^ or ** followed by: (…) | {…} | -?number | a single letter
_POWER = re.compile(r"\s*(?:\^|\*\*)\s*(\([^()]{1,12}\)|\{[^{}]{1,12}\}|[-−]?\d{1,6}|[a-zA-Z])")
_LATEX = re.compile(r"(\$[^$]+\$)")


def _sup(exp: str) -> str | None:
    if exp[0] in "({":
        exp = exp[1:-1]
    exp = exp.replace(" ", "")
    if not exp or any(ch not in _SUP for ch in exp):
        return None
    return "".join(_SUP[ch] for ch in exp)


_SUB = {**dict(zip("0123456789", "₀₁₂₃₄₅₆₇₈₉")), **dict(zip("aehijklmnoprstuvx", "ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ"))}
# stray LaTeX the model leaves in plain text (outside $…$) → the school symbols students read
_STRAY_TEX = {"cdot": "·", "times": "×", "pi": "π", "alpha": "α", "beta": "β", "gamma": "γ", "angle": "∠",
              "parallel": "∥", "perp": "⊥", "triangle": "△", "le": "≤", "leq": "≤", "ge": "≥", "geq": "≥",
              "ne": "≠", "neq": "≠", "approx": "≈", "circ": "°", "degree": "°"}


def _plain(part: str) -> str:
    """S_1 → S₁, a \\cdot b → a · b, \\sqrt{3} → √(3), \\frac{a}{b} → $\\frac{a}{b}$ (typeset by the frontend)."""
    if "\\" not in part and "_" not in part:
        return part
    part = re.sub(r"\\[dt]?frac\s*\{[^{}]*\}\s*\{[^{}]*\}", lambda m: "$" + m.group(0) + "$", part)
    part = re.sub(r"\\sqrt\s*\{([^{}]*)\}", lambda m: "√" + (m.group(1) if re.fullmatch(r"\d+", m.group(1)) else f"({m.group(1)})"), part)
    part = re.sub(r"\\([a-zA-Z]+)(?![a-zA-Z])", lambda m: _STRAY_TEX.get(m.group(1), m.group(0)), part)
    part = re.sub(r"(?<=[A-Za-z])_\{?([0-9aehijklmnoprstuvx]{1,2})\}?(?![A-Za-z0-9_])", lambda m: "".join(_SUB[c] for c in m.group(1)), part)
    return part


def normalize(text: str | None) -> str | None:
    """Rewrites powers and stray LaTeX in plain text; LaTeX between $…$ keeps its own notation."""
    if not text:
        return text

    def repl(m: re.Match) -> str:
        sup = _sup(m.group(1))
        return sup if sup is not None else m.group(0)

    out = []
    for part in _LATEX.split(text):
        if part.startswith("$"):
            out.append(part)
        else:
            out.append("".join(p if p.startswith("$") else _POWER.sub(repl, p) for p in _LATEX.split(_plain(part))))
    return "".join(out)


# ─── LaTeX → plain school notation (for recomputing arithmetic) ──────────────

_CMD = {"cdot": "·", "times": "×", "div": ":", "left": "", "right": ""}
_FRAC = re.compile(r"(\d+)?\s*\\frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}")


def latex_to_plain(text: str) -> str:
    r"""$…$ maths → plain expression: \frac{a}{b} → ((a)/(b)), 3\frac{1}{2} → (3+(1)/(2)), 0{,}7 → 0,7."""

    def conv(tex: str) -> str:
        tex = tex.replace("{,}", ",").replace(r"\dfrac", r"\frac").replace(r"\tfrac", r"\frac")
        tex = re.sub(r"\\[,;! ]", "", tex)
        tex = re.sub(r"\\([a-zA-Z]+)", lambda m: _CMD.get(m.group(1), m.group(0)), tex)
        while True:
            new = _FRAC.sub(
                lambda m: f"({m.group(1)}+({m.group(2)})/({m.group(3)}))" if m.group(1)
                else f"(({m.group(2)})/({m.group(3)}))",
                tex,
            )
            if new == tex:
                break
            tex = new
        tex = re.sub(r"\^\s*\{([^{}]*)\}", r"^(\1)", tex)
        return tex.replace("{", "(").replace("}", ")")

    return re.sub(r"\$([^$]+)\$", lambda m: conv(m.group(1)), text)


# LaTeX commands whose backslash a model may leave unescaped inside JSON ("\frac" would parse as form feed + "rac")
_TEX_WORDS = (
    "frac|dfrac|tfrac|cdot|cdots|ldots|dots|times|div|left|right|sqrt|text|textbf|neq|le|leq|ge|geq|"
    "pi|alpha|beta|gamma|infty|circ|angle|triangle|overline|mathrm|quad|pm|approx|cup|cap|bigl|bigr"
)
_RAW_TEX = re.compile(r"(?<!\\)\\(" + _TEX_WORDS + r")(?![a-zA-Z])")


def escape_json_latex(raw: str) -> str:
    """Doubles single backslashes before LaTeX commands so json.loads keeps them as text."""
    return _RAW_TEX.sub(lambda m: "\\\\" + m.group(1), raw)


def normalize_solution(sol: dict | None) -> dict | None:
    """Same rewrite for every text field of a stored step-by-step solution."""
    if not sol:
        return sol
    out = dict(sol)
    out["steps"] = [
        {**step, "title": normalize(step.get("title")), "lines": [normalize(x) for x in step.get("lines") or []]}
        for step in sol.get("steps") or []
    ]
    out["answer"] = normalize(sol.get("answer"))
    if sol.get("conclusion"):
        out["conclusion"] = normalize(sol["conclusion"])
    if sol.get("check"):
        check = dict(sol["check"])
        check["lines"] = [normalize(x) for x in check.get("lines") or []]
        out["check"] = check
    return out
