"""Figure renderer: the model *describes* a figure as JSON, this module *draws* it as SVG.

Language models are poor at hand-drawing curves and keeping a drawing to scale, but good at saying what should
be drawn. So a function graph is sampled from its formula, a triangle is drawn from its coordinates, and so on —
the picture is exactly what the description says. The output only uses elements the SVG sanitizer allows.

Supported figure types: function_graph, geometry, number_line, bar_chart, table, the physics types plot and scene
(physics_figures.py), and raw "svg" as a last resort.
"""

import ast
import math
import operator
import re
from xml.sax.saxutils import escape

W, H = 480, 320
PAD = 36
INK = "#0b1533"
ACCENT = "#1f55f5"
GRID = "#e3e9f6"
FONT = 'font-family="Arial, sans-serif"'


class FigureError(ValueError):
    pass


def _num(v, name: str) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise FigureError(f"{name} is not a number")
    if not math.isfinite(f):
        raise FigureError(f"{name} is not finite")
    return f


def _fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def _label(x: float, y: float, text: str, *, size=15, anchor="middle", color=INK, weight="normal") -> str:
    return (
        f'<text x="{_fmt(x)}" y="{_fmt(y)}" {FONT} font-size="{size}" font-weight="{weight}" '
        f'text-anchor="{anchor}" dominant-baseline="middle" fill="{color}">{escape(str(text))}</text>'
    )


def _svg(body: str, w: int = W, h: int = H) -> str:
    defs = (
        '<defs><marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>'
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">{defs}<rect x="0" y="0" width="{w}" height="{h}" fill="white"/>{body}</svg>'


def _nice_step(span: float, target: int = 10) -> float:
    raw = span / target
    mag = 10 ** math.floor(math.log10(raw)) if raw > 0 else 1
    for m in (1, 2, 5, 10):
        if raw <= m * mag:
            return m * mag
    return 10 * mag


# ─── safe formula evaluation ─────────────────────────────────────────────────

_FUNCS = {
    "sqrt": math.sqrt, "abs": abs, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "ln": math.log, "lg": math.log10, "log10": math.log10, "log2": math.log2, "exp": math.exp,
}
_CONSTS = {"pi": math.pi, "e": math.e}
_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}
_UN = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _compile(expr: str):
    """Parse "x^2 - 4x + 3" style formulas into an AST that only allows arithmetic on x."""
    src = str(expr).replace("^", "**").replace("·", "*").replace("−", "-").replace("×", "*")
    # 4x → 4*x, 2(x+1) → 2*(x+1) — but leave digits that are part of a name, like log10(
    src = re.sub(r"(?<![a-z_\d.])(\d+(?:\.\d+)?)\s*([a-z(])", r"\1*\2", src)
    src = re.sub(r"\)\s*([a-z0-9(])", r")*\1", src)  # (x+1)(x-1) → (x+1)*(x-1)
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError:
        raise FigureError(f"bad formula: {expr}")

    def check(node):
        if isinstance(node, ast.Expression):
            return check(node.body)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            return check(node.left) and check(node.right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
            return check(node.operand)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return True
        if isinstance(node, ast.Name) and (node.id == "x" or node.id in _CONSTS):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS and len(node.args) == 1:
            return check(node.args[0])
        raise FigureError(f"unsupported formula: {expr}")

    check(tree)
    return tree.body


def _eval(node, x: float) -> float:
    if isinstance(node, ast.BinOp):
        a, b = _eval(node.left, x), _eval(node.right, x)
        if isinstance(node.op, ast.Pow) and abs(b) > 50:
            raise OverflowError
        return _BIN[type(node.op)](a, b)
    if isinstance(node, ast.UnaryOp):
        return _UN[type(node.op)](_eval(node.operand, x))
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        return x if node.id == "x" else _CONSTS[node.id]
    return float(_FUNCS[node.func.id](_eval(node.args[0], x)))


# ─── function graph ──────────────────────────────────────────────────────────


def _function_graph(f: dict) -> str:
    x0, x1 = _num(f.get("x_min", -5), "x_min"), _num(f.get("x_max", 5), "x_max")
    y0, y1 = _num(f.get("y_min", -5), "y_min"), _num(f.get("y_max", 5), "y_max")
    if not (x1 > x0 and y1 > y0):
        raise FigureError("empty range")
    sx = (W - 2 * PAD) / (x1 - x0)
    sy = (H - 2 * PAD) / (y1 - y0)
    px = lambda x: PAD + (x - x0) * sx  # noqa: E731
    py = lambda y: H - PAD - (y - y0) * sy  # noqa: E731
    parts = []

    step = _nice_step(max(x1 - x0, y1 - y0))
    show_numbers = bool(f.get("tick_labels", True))
    if f.get("grid", True):
        g = []
        k = math.ceil(x0 / step) * step
        while k <= x1 + 1e-9:
            g.append(f'<line x1="{_fmt(px(k))}" y1="{_fmt(py(y0))}" x2="{_fmt(px(k))}" y2="{_fmt(py(y1))}" stroke="{GRID}" stroke-width="1"/>')
            k += step
        k = math.ceil(y0 / step) * step
        while k <= y1 + 1e-9:
            g.append(f'<line x1="{_fmt(px(x0))}" y1="{_fmt(py(k))}" x2="{_fmt(px(x1))}" y2="{_fmt(py(k))}" stroke="{GRID}" stroke-width="1"/>')
            k += step
        parts.append("".join(g))

    # axes through the origin when it is in view, otherwise along the edge
    ax_y = py(0) if y0 <= 0 <= y1 else py(y0)
    ax_x = px(0) if x0 <= 0 <= x1 else px(x0)
    parts.append(f'<line x1="{_fmt(px(x0) - 6)}" y1="{_fmt(ax_y)}" x2="{_fmt(px(x1) + 14)}" y2="{_fmt(ax_y)}" stroke="{INK}" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(f'<line x1="{_fmt(ax_x)}" y1="{_fmt(py(y0) + 6)}" x2="{_fmt(ax_x)}" y2="{_fmt(py(y1) - 14)}" stroke="{INK}" stroke-width="1.5" marker-end="url(#arr)"/>')
    parts.append(_label(px(x1) + 16, ax_y + 14, "x", size=14))
    parts.append(_label(ax_x - 12, py(y1) - 16, "y", size=14))
    if x0 <= 0 <= x1 and y0 <= 0 <= y1:
        parts.append(_label(ax_x - 9, ax_y + 13, "0", size=12))

    if show_numbers:
        k = math.ceil(x0 / step) * step
        while k <= x1 + 1e-9:
            if abs(k) > 1e-9:
                parts.append(f'<line x1="{_fmt(px(k))}" y1="{_fmt(ax_y - 4)}" x2="{_fmt(px(k))}" y2="{_fmt(ax_y + 4)}" stroke="{INK}" stroke-width="1.2"/>')
                parts.append(_label(px(k), ax_y + 15, _fmt(k), size=12))
            k += step
        k = math.ceil(y0 / step) * step
        while k <= y1 + 1e-9:
            if abs(k) > 1e-9:
                parts.append(f'<line x1="{_fmt(ax_x - 4)}" y1="{_fmt(py(k))}" x2="{_fmt(ax_x + 4)}" y2="{_fmt(py(k))}" stroke="{INK}" stroke-width="1.2"/>')
                parts.append(_label(ax_x - 8, py(k), _fmt(k), size=12, anchor="end"))
            k += step

    colors = [ACCENT, "#e5484d", "#0f9d58"]
    functions = f.get("functions") or []
    if not functions:
        raise FigureError("no functions")
    for i, fn in enumerate(functions[:3]):
        node = _compile(fn.get("expr", ""))
        color = colors[i % len(colors)]
        # sample the formula and cut the curve exactly where it leaves the y-range (no clamping onto the edge)
        n = 800
        samples = []
        for j in range(n + 1):
            x = x0 + (x1 - x0) * j / n
            try:
                y = _eval(node, x)
                y = y if math.isfinite(y) else None
            except (ValueError, ZeroDivisionError, OverflowError):
                y = None
            samples.append((x, y))

        def inside(y):
            return y is not None and y0 <= y <= y1

        def edge_point(xa, ya, xb, yb):
            """Where the segment a→b crosses the y-range boundary."""
            edge = y1 if max(ya, yb) > y1 else y0
            t = (edge - ya) / (yb - ya) if yb != ya else 0
            return (px(xa + (xb - xa) * t), py(edge))

        segs, cur = [], []
        for (xa, ya), (xb, yb) in zip(samples, samples[1:]):
            if ya is None or yb is None or abs(yb - ya) > 2 * (y1 - y0):  # undefined or an asymptote jump
                if len(cur) > 1:
                    segs.append(cur)
                cur = []
                continue
            a_in, b_in = inside(ya), inside(yb)
            if a_in and not cur:
                cur = [(px(xa), py(ya))]
            if a_in and b_in:
                cur.append((px(xb), py(yb)))
            elif a_in and not b_in:  # leaving the plot
                cur.append(edge_point(xa, ya, xb, yb))
                segs.append(cur)
                cur = []
            elif not a_in and b_in:  # entering the plot
                cur = [edge_point(xa, ya, xb, yb), (px(xb), py(yb))]
        if len(cur) > 1:
            segs.append(cur)
        if not segs:
            raise FigureError("graph not visible in the given range")
        for seg in segs:
            d = "M" + " L".join(f"{_fmt(a)},{_fmt(b)}" for a, b in seg)
            parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>')
        if fn.get("label"):
            # top-right corner of the plot, one line per function, so it never runs off the figure
            text = str(fn["label"])
            tw = len(text) * 8 + 10  # rough width of a 14px label
            ty = PAD + 4 + 22 * i
            parts.append(f'<rect x="{_fmt(W - PAD - tw)}" y="{_fmt(ty - 11)}" width="{tw}" height="22" rx="4" fill="white" fill-opacity="0.92"/>')
            parts.append(_label(W - PAD - 5, ty, text, size=14, color=color, anchor="end", weight="bold"))

    for p in (f.get("points") or [])[:12]:
        x, y = _num(p.get("x"), "point x"), _num(p.get("y"), "point y")
        if p.get("dashed_to_axes"):
            parts.append(f'<path d="M{_fmt(px(x))},{_fmt(ax_y)} L{_fmt(px(x))},{_fmt(py(y))} L{_fmt(ax_x)},{_fmt(py(y))}" fill="none" stroke="{INK}" stroke-width="1" stroke-dasharray="4 4"/>')
        parts.append(f'<circle cx="{_fmt(px(x))}" cy="{_fmt(py(y))}" r="4" fill="{INK}"/>')
        if p.get("label"):
            parts.append(_label(px(x) + 8, py(y) - 12, p["label"], size=14, anchor="start"))
    return _svg("".join(parts))


# ─── geometry ────────────────────────────────────────────────────────────────


def _geometry(f: dict) -> str:
    raw = {}
    for p in f.get("points") or []:
        name = str(p.get("label", "")).strip()
        if not name:
            raise FigureError("point without label")
        raw[name] = (_num(p.get("x"), f"{name}.x"), _num(p.get("y"), f"{name}.y"))
    circles = f.get("circles") or []
    if not raw:
        raise FigureError("no points")

    # fit everything (points and circle extents) into the viewBox with one scale, y pointing up
    xs = [v[0] for v in raw.values()]
    ys = [v[1] for v in raw.values()]
    for c in circles:
        cx, cy = raw[c["center"]]
        r = _num(c.get("radius"), "radius")
        xs += [cx - r, cx + r]
        ys += [cy - r, cy + r]
    bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
    span = max(bx1 - bx0, by1 - by0, 1e-6)
    s = min((W - 2 * PAD - 20) / max(bx1 - bx0, span * 0.2), (H - 2 * PAD - 10) / max(by1 - by0, span * 0.2))
    ox = (W - (bx1 - bx0) * s) / 2
    oy = (H - (by1 - by0) * s) / 2
    P = {k: (ox + (x - bx0) * s, H - oy - (y - by0) * s) for k, (x, y) in raw.items()}
    cx_all = sum(v[0] for v in P.values()) / len(P)
    cy_all = sum(v[1] for v in P.values()) / len(P)

    def get(name):
        if name not in P:
            raise FigureError(f"unknown point {name}")
        return P[name]

    parts = []
    shades = {"blue": ("#1f55f5", 0.18), "green": ("#22c55e", 0.3), "red": ("#e5484d", 0.25), "orange": ("#f59e0b", 0.3)}
    for poly in f.get("polygons") or []:
        # a polygon is a list of point names, or {"points": [...], "fill": "green"} for a shaded region
        names = poly.get("points") if isinstance(poly, dict) else poly
        pts = " ".join(f"{_fmt(get(n)[0])},{_fmt(get(n)[1])}" for n in names or [])
        if isinstance(poly, dict) and poly.get("fill") in shades:
            color, alpha = shades[poly["fill"]]
            parts.append(f'<polygon points="{pts}" fill="{color}" fill-opacity="{alpha}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
        else:
            parts.append(f'<polygon points="{pts}" fill="#eef4ff" fill-opacity="0.6" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>')
    for c in circles:
        ccx, ccy = get(c["center"])
        parts.append(f'<circle cx="{_fmt(ccx)}" cy="{_fmt(ccy)}" r="{_fmt(_num(c["radius"], "radius") * s)}" fill="none" stroke="{INK}" stroke-width="2"/>')

    for seg in f.get("segments") or []:
        (ax, ay), (bx, by) = get(seg["from"]), get(seg["to"])
        dash = ' stroke-dasharray="6 5"' if seg.get("dashed") else ""
        color = ACCENT if seg.get("dashed") else INK
        parts.append(f'<line x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke="{color}" stroke-width="2"{dash}/>')

    # equal-length marks: 1–3 short strokes across the middle of a side ("ticks" on a segment or a label)
    for item in [*(f.get("segments") or []), *(f.get("labels") or []), *(f.get("ticks") or [])]:
        n = int(min(max(_num(item.get("ticks", 0) or 0, "ticks"), 0), 3))
        if not n:
            continue
        (ax, ay), (bx, by) = get(item["from"]), get(item["to"])
        ln = math.hypot(bx - ax, by - ay) or 1
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        mx, my = (ax + bx) / 2, (ay + by) / 2
        for k in range(n):
            off = (k - (n - 1) / 2) * 5
            cx, cy = mx + ux * off, my + uy * off
            parts.append(f'<line x1="{_fmt(cx - uy * 6)}" y1="{_fmt(cy + ux * 6)}" x2="{_fmt(cx + uy * 6)}" y2="{_fmt(cy - ux * 6)}" stroke="{INK}" stroke-width="1.8"/>')

    # point names sit outside the figure (away from its centre); everything placed is remembered so later
    # labels can step aside instead of landing on top of it
    names = {}
    for name, (x, y) in P.items():
        dx, dy = x - cx_all, y - cy_all
        ln = math.hypot(dx, dy) or 1
        names[name] = (x + dx / ln * 17, y + dy / ln * 17)
    taken = list(names.values()) + list(P.values())

    def free(x: float, y: float) -> bool:
        return all(math.hypot(x - a, y - b) > 22 for a, b in taken)

    # side / segment labels: on the outer side of the segment, aligned away from it, sliding along the segment
    # when the midpoint is already occupied (e.g. by the foot of a height)
    for seg in f.get("labels") or []:
        (ax, ay), (bx, by) = get(seg["from"]), get(seg["to"])
        nx, ny = -(by - ay), bx - ax
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if (mx + nx - cx_all) ** 2 + (my + ny - cy_all) ** 2 < (mx - cx_all) ** 2 + (my - cy_all) ** 2:
            nx, ny = -nx, -ny
        anchor = "start" if nx > 0.35 else "end" if nx < -0.35 else "middle"
        pos = None
        for t in (0.5, 0.35, 0.65, 0.22, 0.78):
            cand = (ax + (bx - ax) * t + nx * 12, ay + (by - ay) * t + ny * 14)
            if free(*cand):
                pos = cand
                break
        pos = pos or (mx + nx * 12, my + ny * 14)
        taken.append(pos)
        unknown = bool(seg.get("unknown"))
        parts.append(_label(*pos, seg.get("text", ""), size=15, anchor=anchor, color=ACCENT if unknown else INK, weight="bold" if unknown else "normal"))

    for ang in f.get("angles") or []:
        vx, vy = get(ang["vertex"])
        (ax, ay), (bx, by) = get(ang["from"]), get(ang["to"])
        a1, a2 = math.atan2(ay - vy, ax - vx), math.atan2(by - vy, bx - vx)
        if ang.get("right"):
            u1 = (math.cos(a1) * 14, math.sin(a1) * 14)
            u2 = (math.cos(a2) * 14, math.sin(a2) * 14)
            parts.append(
                f'<path d="M{_fmt(vx + u1[0])},{_fmt(vy + u1[1])} L{_fmt(vx + u1[0] + u2[0])},{_fmt(vy + u1[1] + u2[1])} '
                f'L{_fmt(vx + u2[0])},{_fmt(vy + u2[1])}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
            )
            continue
        d = (a2 - a1) % (2 * math.pi)
        if d > math.pi:
            a1, a2, d = a2, a1, 2 * math.pi - d
        r = 24
        sx_, sy_ = vx + r * math.cos(a1), vy + r * math.sin(a1)
        ex_, ey_ = vx + r * math.cos(a2), vy + r * math.sin(a2)
        parts.append(f'<path d="M{_fmt(sx_)},{_fmt(sy_)} A{r},{r} 0 0 1 {_fmt(ex_)},{_fmt(ey_)}" fill="none" stroke="{ACCENT}" stroke-width="1.8"/>')
        if ang.get("text"):
            mid = a1 + d / 2
            parts.append(_label(vx + 42 * math.cos(mid), vy + 42 * math.sin(mid), ang["text"], size=14, color=ACCENT))

    for name, (x, y) in P.items():
        parts.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="3" fill="{INK}"/>')
        parts.append(_label(*names[name], name, size=16, weight="bold"))
    return _svg("".join(parts))


# ─── number line ─────────────────────────────────────────────────────────────


def _number_line(f: dict) -> str:
    lo, hi = _num(f.get("min"), "min"), _num(f.get("max"), "max")
    if hi <= lo:
        raise FigureError("empty range")
    h = 130
    y = 70
    px = lambda v: PAD + (v - lo) * (W - 2 * PAD) / (hi - lo)  # noqa: E731
    parts = [f'<line x1="{PAD - 14}" y1="{y}" x2="{W - PAD + 18}" y2="{y}" stroke="{INK}" stroke-width="2" marker-end="url(#arr)"/>']
    for t in (f.get("ticks") or [])[:20]:
        t = _num(t, "tick")
        parts.append(f'<line x1="{_fmt(px(t))}" y1="{y - 6}" x2="{_fmt(px(t))}" y2="{y + 6}" stroke="{INK}" stroke-width="1.5"/>')
        parts.append(_label(px(t), y + 22, _fmt(t), size=14))
    for iv in (f.get("intervals") or [])[:4]:
        a = lo if iv.get("from") is None else _num(iv["from"], "from")
        b = hi if iv.get("to") is None else _num(iv["to"], "to")
        parts.append(f'<line x1="{_fmt(px(a))}" y1="{y - 16}" x2="{_fmt(px(b))}" y2="{y - 16}" stroke="{ACCENT}" stroke-width="5" stroke-linecap="round"/>')
        for v, opened, given in ((a, iv.get("from_open", True), iv.get("from") is not None), (b, iv.get("to_open", True), iv.get("to") is not None)):
            if given:
                fill = "white" if opened else ACCENT
                parts.append(f'<circle cx="{_fmt(px(v))}" cy="{y - 16}" r="5.5" fill="{fill}" stroke="{ACCENT}" stroke-width="2"/>')
    for p in (f.get("points") or [])[:10]:
        v = _num(p.get("x"), "point")
        fill = "white" if p.get("open") else INK
        parts.append(f'<circle cx="{_fmt(px(v))}" cy="{y}" r="5" fill="{fill}" stroke="{INK}" stroke-width="2"/>')
        if p.get("label"):
            parts.append(_label(px(v), y - 36, p["label"], size=15, weight="bold"))
    return _svg("".join(parts), W, h)


# ─── bar chart & table ───────────────────────────────────────────────────────


def _bar_chart(f: dict) -> str:
    labels = [str(v) for v in (f.get("labels") or [])][:10]
    values = [_num(v, "value") for v in (f.get("values") or [])][: len(labels)]
    if not labels or len(values) != len(labels) or min(values) < 0:
        raise FigureError("labels and values must match")
    top = max(values) or 1
    step = _nice_step(top, 5)
    top = math.ceil(top / step) * step
    x0, y0, w, h = PAD + 20, H - PAD, W - 2 * PAD - 20, H - 2 * PAD - 10
    parts = []
    k = 0.0
    while k <= top + 1e-9:
        yy = y0 - k / top * h
        parts.append(f'<line x1="{x0}" y1="{_fmt(yy)}" x2="{x0 + w}" y2="{_fmt(yy)}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(_label(x0 - 8, yy, _fmt(k), size=12, anchor="end"))
        k += step
    bw = w / len(labels)
    for i, (lab, v) in enumerate(zip(labels, values)):
        bh = v / top * h
        parts.append(f'<rect x="{_fmt(x0 + i * bw + bw * 0.2)}" y="{_fmt(y0 - bh)}" width="{_fmt(bw * 0.6)}" height="{_fmt(bh)}" fill="{ACCENT}" rx="3"/>')
        parts.append(_label(x0 + i * bw + bw / 2, y0 + 16, lab, size=13))
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0 + w}" y2="{y0}" stroke="{INK}" stroke-width="1.5"/>')
    if f.get("title"):
        parts.append(_label(W / 2, 16, f["title"], size=14, weight="bold"))
    return _svg("".join(parts))


def _table(f: dict) -> str:
    header = [str(v) for v in (f.get("header") or [])][:8]
    rows = [[str(c) for c in r][: len(header)] for r in (f.get("rows") or [])][:8]
    if not header or not rows:
        raise FigureError("empty table")
    cw = min(110, (W - 20) / len(header))
    rh = 34
    tw, th = cw * len(header), rh * (len(rows) + 1)
    x0, y0 = (W - tw) / 2, 10
    parts = [f'<rect x="{_fmt(x0)}" y="{y0}" width="{_fmt(tw)}" height="{rh}" fill="#eef4ff"/>']
    for r, row in enumerate([header] + rows):
        for c, cell in enumerate(row):
            parts.append(_label(x0 + c * cw + cw / 2, y0 + r * rh + rh / 2, cell, size=14, weight="bold" if r == 0 else "normal"))
    for r in range(len(rows) + 2):
        parts.append(f'<line x1="{_fmt(x0)}" y1="{y0 + r * rh}" x2="{_fmt(x0 + tw)}" y2="{y0 + r * rh}" stroke="{INK}" stroke-width="1.2"/>')
    for c in range(len(header) + 1):
        parts.append(f'<line x1="{_fmt(x0 + c * cw)}" y1="{y0}" x2="{_fmt(x0 + c * cw)}" y2="{y0 + th}" stroke="{INK}" stroke-width="1.2"/>')
    return _svg("".join(parts), W, int(th + 20))


RENDERERS = {
    "function_graph": _function_graph,
    "geometry": _geometry,
    "number_line": _number_line,
    "bar_chart": _bar_chart,
    "table": _table,
}


def render_figure(figure: dict | None) -> str:
    """SVG markup for a figure description; "" for no figure. Raises FigureError for an unusable description."""
    if not figure or not isinstance(figure, dict):
        return ""
    kind = str(figure.get("type", "")).strip()
    if not kind:  # the model sometimes leaves "type" out; the keys say which figure it is
        kind = next((k for keys, k in ((("bodies",), "solid"), (("items",), "scene"), (("series",), "plot"),
                                      (("functions",), "function_graph"), (("polygons", "circles"), "geometry"),
                                      (("header", "rows"), "table")) if any(x in figure for x in keys)), "")
        if kind == "function_graph" and "x_label" in figure:
            kind = "plot"
    if kind in ("", "none"):
        return ""
    if kind == "svg":
        return str(figure.get("svg", ""))
    # physics schematics and 3D solids; imported here to avoid a cycle
    from .physics_figures import RENDERERS as PHYSICS
    from .solid_figures import RENDERERS as SOLIDS

    renderers = {**RENDERERS, **PHYSICS, **SOLIDS}
    if kind not in renderers:
        raise FigureError(f"unknown figure type {kind}")
    try:
        return renderers[kind](figure)
    except FigureError:
        raise
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as e:
        raise FigureError(str(e))
