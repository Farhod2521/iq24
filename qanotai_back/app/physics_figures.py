"""Physics figures: the model describes a schematic as JSON, this module draws it exactly (same idea as figures.py).

Two figure types:
- "plot": a physics graph — axes with quantity names and units (t, s / v, m/s), piecewise-linear series such as a
  v(t) graph, and optional formula curves. Values are read off a grid, so key points must sit on grid lines.
- "scene": a schematic drawing in world coordinates (y up), auto-fitted to the picture: ground and walls with
  hatching, blocks, balls, inclines, ropes, pulleys, springs, levers with a fulcrum, vessels with liquid, force and
  velocity arrows, dimension lines, angle arcs, trajectories and labels.

Everything is computed here (positions, hatching, arrow heads), so the drawing always matches the numbers.
"""

import math

from .figures import INK, FigureError, _compile, _eval, _fmt, _label, _nice_step, _num

W = 480
RED, BLUE, GREEN, GREY = "#e5484d", "#1f55f5", "#0f9d58", "#8a94ad"
WATER, WATER_EDGE = "#cfe6ff", "#5b9be6"
COLORS = {"red": RED, "force": RED, "blue": BLUE, "velocity": BLUE, "green": GREEN, "acceleration": GREEN,
          "black": INK, "grey": GREY, "gray": GREY}
MAX_ITEMS = 40


def _color(name, default=INK) -> str:
    return COLORS.get(str(name or "").lower(), default)


def _svg(body: str, w: int, h: int) -> str:
    markers = "".join(
        f'<marker id="a-{k}" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for k, c in (("ink", INK), ("red", RED), ("blue", BLUE), ("green", GREEN))
    ) + (
        '<marker id="d-ink" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto-start-reverse">'
        f'<path d="M0,0 L8,4 L0,8 z" fill="{INK}"/></marker>'
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><defs>{markers}</defs>'
        f'<rect x="0" y="0" width="{w}" height="{h}" fill="white"/>{body}</svg>'
    )


def _marker(color: str) -> str:
    return {RED: "a-red", BLUE: "a-blue", GREEN: "a-green"}.get(color, "a-ink")


def _pt(v, name: str) -> tuple[float, float]:
    if not isinstance(v, (list, tuple)) or len(v) != 2:
        raise FigureError(f"{name} must be [x, y]")
    return _num(v[0], f"{name}.x"), _num(v[1], f"{name}.y")


# ─── plot (physics graph) ────────────────────────────────────────────────────


def _plot(f: dict) -> str:
    H = 320
    pad_l, pad_r, pad_t, pad_b = 52, 30, 30, 40
    x0, x1 = _num(f.get("x_min", 0), "x_min"), _num(f.get("x_max", 10), "x_max")
    y0, y1 = _num(f.get("y_min", 0), "y_min"), _num(f.get("y_max", 10), "y_max")
    if not (x1 > x0 and y1 > y0):
        raise FigureError("empty range")
    px = lambda x: pad_l + (x - x0) * (W - pad_l - pad_r) / (x1 - x0)  # noqa: E731
    py = lambda y: H - pad_b - (y - y0) * (H - pad_t - pad_b) / (y1 - y0)  # noqa: E731
    sx = _num(f["x_step"], "x_step") if f.get("x_step") else _nice_step(x1 - x0, 8)
    sy = _num(f["y_step"], "y_step") if f.get("y_step") else _nice_step(y1 - y0, 6)
    if (x1 - x0) / sx > 40 or (y1 - y0) / sy > 40:
        raise FigureError("too many grid lines")
    parts = []

    k = math.ceil(x0 / sx) * sx
    while k <= x1 + 1e-9:
        parts.append(f'<line x1="{_fmt(px(k))}" y1="{_fmt(py(y0))}" x2="{_fmt(px(k))}" y2="{_fmt(py(y1))}" stroke="#e3e9f6" stroke-width="1"/>')
        if abs(k) > 1e-9 or not (y0 <= 0 <= y1):
            parts.append(_label(px(k), (py(0) if y0 <= 0 <= y1 else py(y0)) + 15, _fmt(k), size=12))
        k += sx
    k = math.ceil(y0 / sy) * sy
    while k <= y1 + 1e-9:
        parts.append(f'<line x1="{_fmt(px(x0))}" y1="{_fmt(py(k))}" x2="{_fmt(px(x1))}" y2="{_fmt(py(k))}" stroke="#e3e9f6" stroke-width="1"/>')
        if abs(k) > 1e-9:
            parts.append(_label(px(x0) - 8, py(k), _fmt(k), size=12, anchor="end"))
        k += sy

    ax_y = py(0) if y0 <= 0 <= y1 else py(y0)
    parts.append(f'<line x1="{_fmt(px(x0))}" y1="{_fmt(ax_y)}" x2="{_fmt(px(x1) + 18)}" y2="{_fmt(ax_y)}" stroke="{INK}" stroke-width="1.6" marker-end="url(#a-ink)"/>')
    parts.append(f'<line x1="{_fmt(px(x0))}" y1="{_fmt(py(y0))}" x2="{_fmt(px(x0))}" y2="{_fmt(py(y1) - 16)}" stroke="{INK}" stroke-width="1.6" marker-end="url(#a-ink)"/>')
    parts.append(_label(px(x0) - 8, ax_y + 15, "0", size=12, anchor="end"))
    parts.append(_label(W - 6, ax_y - 14, str(f.get("x_label", "t, s")), size=14, anchor="end", weight="bold"))
    parts.append(_label(px(x0) + 8, 14, str(f.get("y_label", "v, m/s")), size=14, anchor="start", weight="bold"))

    palette = [BLUE, RED, GREEN]
    series = (f.get("series") or [])[:3]
    functions = (f.get("functions") or [])[:3]
    if not series and not functions:
        raise FigureError("plot without data")
    for i, s in enumerate(series):
        pts = [_pt(p, "series point") for p in (s.get("points") or [])][:30]
        if len(pts) < 2:
            raise FigureError("series needs at least two points")
        color = palette[i % 3]
        d = "M" + " L".join(f"{_fmt(px(x))},{_fmt(py(y))}" for x, y in pts)
        parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.6" stroke-linejoin="round"/>')
        for x, y in pts:
            if s.get("dashed_to_axes"):
                parts.append(f'<path d="M{_fmt(px(x))},{_fmt(ax_y)} L{_fmt(px(x))},{_fmt(py(y))} L{_fmt(px(x0))},{_fmt(py(y))}" fill="none" stroke="{GREY}" stroke-width="1" stroke-dasharray="4 4"/>')
        if s.get("label"):
            lx, ly = pts[-1]
            parts.append(_label(px(lx) + 6, py(ly) - 12, s["label"], size=14, anchor="start", color=color, weight="bold"))
    for i, fn in enumerate(functions):
        node = _compile(fn.get("expr", ""))
        color = palette[(len(series) + i) % 3]
        a = _num(fn.get("x_from", x0), "x_from")
        b = _num(fn.get("x_to", x1), "x_to")
        pts = []
        for j in range(301):
            x = a + (b - a) * j / 300
            try:
                y = _eval(node, x)
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            if math.isfinite(y) and y0 - 1e-9 <= y <= y1 + 1e-9:
                pts.append((px(x), py(y)))
        if len(pts) < 2:
            raise FigureError("curve not visible")
        parts.append(f'<path d="M{" L".join(f"{_fmt(a)},{_fmt(b)}" for a, b in pts)}" fill="none" stroke="{color}" stroke-width="2.6"/>')
        if fn.get("label"):
            parts.append(_label(pts[-1][0] + 6, pts[-1][1] - 12, fn["label"], size=14, anchor="start", color=color, weight="bold"))
    for p in (f.get("points") or [])[:10]:
        x, y = _pt([p.get("x"), p.get("y")], "point")
        parts.append(f'<circle cx="{_fmt(px(x))}" cy="{_fmt(py(y))}" r="4" fill="{INK}"/>')
        if p.get("label"):
            parts.append(_label(px(x) + 8, py(y) - 12, p["label"], size=14, anchor="start", weight="bold"))
    return _svg("".join(parts), W, H)


# ─── scene (schematic) ───────────────────────────────────────────────────────


def _points_of(item: dict) -> list[tuple[float, float]]:
    """World points an item occupies — used to fit the scene into the picture."""
    k = item.get("kind")
    out = []
    for key in ("from", "to", "at", "center", "vertex"):
        if key in item and isinstance(item[key], (list, tuple)):
            out.append(_pt(item[key], key))
    if k == "dimension" and item.get("offset"):  # the dimension line sits beside the object
        (ax, ay), (bx, by) = _pt(item["from"], "from"), _pt(item["to"], "to")
        ln = math.hypot(bx - ax, by - ay) or 1
        off = _num(item["offset"], "offset")
        nx, ny = -(by - ay) / ln * off, (bx - ax) / ln * off
        out += [(ax + nx * 1.25, ay + ny * 1.25), (bx + nx * 1.25, by + ny * 1.25)]
    if k in ("polygon", "liquid", "path", "incline"):
        out += [_pt(p, "point") for p in item.get("points") or []]
    if k == "block":
        if item.get("on"):
            cx, cy, _, w, h = _resting(item)
        else:
            cx, cy = _pt(item.get("center"), "center")
            w, h = _num(item.get("w", 1), "w"), _num(item.get("h", 1), "h")
        r = math.hypot(w, h) / 2
        out += [(cx - r, cy - r), (cx + r, cy + r)]
    if k in ("ball", "pulley"):
        cx, cy = _pt(item.get("center"), "center")
        r = _num(item.get("r", 0.5), "r")
        out += [(cx - r, cy - r), (cx + r, cy + r)]
    if k == "vessel":
        x, y = _num(item.get("x"), "x"), _num(item.get("y"), "y")
        out += [(x, y), (x + _num(item.get("w"), "w"), y + _num(item.get("h"), "h"))]
    return out


def _resting(item: dict) -> tuple[float, float, float, float, float]:
    """World centre, angle, width and height of a block that rests on its "on" surface [[x1, y1], [x2, y2]]."""
    (x1, y1), (x2, y2) = (_pt(p, "on") for p in item["on"][:2])
    if x2 < x1:
        x1, y1, x2, y2 = x2, y2, x1, y1
    t = min(max(_num(item.get("t", 0.5), "t"), 0), 1)
    w, h = _num(item.get("w", 1), "w"), _num(item.get("h", 1), "h")
    ln = math.hypot(x2 - x1, y2 - y1) or 1
    nx, ny = -(y2 - y1) / ln, (x2 - x1) / ln  # world normal pointing up from the surface
    cx, cy = x1 + (x2 - x1) * t + nx * h / 2, y1 + (y2 - y1) * t + ny * h / 2
    return cx, cy, math.atan2(y2 - y1, x2 - x1), w, h


def _on_surface(item: dict, P) -> tuple[float, tuple[float, float]]:
    cx, cy, angle, _, _ = _resting(item)
    return angle, P((cx, cy))


def _scene(f: dict) -> str:
    items = [i for i in (f.get("items") or []) if isinstance(i, dict)][:MAX_ITEMS]
    if not items:
        raise FigureError("empty scene")
    pts = [p for i in items for p in _points_of(i)]
    if not pts:
        raise FigureError("scene without coordinates")
    bx0, bx1 = min(p[0] for p in pts), max(p[0] for p in pts)
    by0, by1 = min(p[1] for p in pts), max(p[1] for p in pts)
    span_x, span_y = max(bx1 - bx0, 1e-6), max(by1 - by0, 1e-6)
    margin = 42
    s = (W - 2 * margin) / span_x
    H = int(min(400, max(170, span_y * s + 2 * margin)))
    s = min(s, (H - 2 * margin) / span_y)
    ox = (W - span_x * s) / 2
    oy = (H - span_y * s) / 2

    def P(p) -> tuple[float, float]:
        x, y = _pt(p, "point") if not isinstance(p, tuple) else p
        return ox + (x - bx0) * s, H - oy - (y - by0) * s

    def L(v, name="length") -> float:
        return _num(v, name) * s

    back, mid, front = [], [], []  # liquids/hatching first, bodies, then arrows and labels on top
    for it in items:
        k = str(it.get("kind", ""))
        label = str(it.get("label", "") or "")
        dashed = ' stroke-dasharray="6 5"' if it.get("dashed") else ""

        if k == "grid":  # background squares, e.g. a trajectory drawn on a grid
            step = _num(it.get("step", 1), "step")
            if span_x / step > 40 or span_y / step > 40:
                raise FigureError("grid too dense")
            g = []
            x = math.floor(bx0 / step) * step
            while x <= bx1 + 1e-9:
                g.append(f"M{_fmt(P((x, by0))[0])},{_fmt(P((x, by0))[1])} V{_fmt(P((x, by1))[1])}")
                x += step
            y = math.floor(by0 / step) * step
            while y <= by1 + 1e-9:
                g.append(f"M{_fmt(P((bx0, y))[0])},{_fmt(P((bx0, y))[1])} H{_fmt(P((bx1, y))[0])}")
                y += step
            back.append(f'<path d="{" ".join(g)}" stroke="#e3e9f6" stroke-width="1" fill="none"/>')

        elif k in ("ground", "wall"):  # a surface with hatching on its "outside" (right of the from→to direction)
            (ax, ay), (bx, by) = P(it["from"]), P(it["to"])
            ln = math.hypot(bx - ax, by - ay) or 1
            ux, uy = (bx - ax) / ln, (by - ay) / ln
            nx, ny = uy, -ux  # screen-right of the direction; for ground drawn left→right this points down
            if it.get("flip"):
                nx, ny = -nx, -ny
            hatch = []
            n = max(3, int(ln / 14))
            for j in range(n + 1):
                hx, hy = ax + ux * ln * j / n, ay + uy * ln * j / n
                hatch.append(f"M{_fmt(hx)},{_fmt(hy)} l{_fmt(nx * 9 - ux * 9)},{_fmt(ny * 9 - uy * 9)}")
            back.append(f'<path d="{" ".join(hatch)}" stroke="{GREY}" stroke-width="1.2" fill="none"/>')
            back.append(f'<line x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke="{INK}" stroke-width="2.2"/>')

        elif k in ("polygon", "incline"):
            ps = [P(p) for p in it.get("points") or []]
            if len(ps) < 3:
                raise FigureError("polygon needs 3 points")
            fill = "#eef1f7" if it.get("fill", True) else "none"
            back.append(f'<polygon points="{" ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in ps)}" fill="{fill}" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')

        elif k == "liquid":
            ps = [P(p) for p in it.get("points") or []]
            if len(ps) < 3:
                raise FigureError("liquid needs 3 points")
            back.append(f'<polygon points="{" ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in ps)}" fill="{WATER}" stroke="{WATER_EDGE}" stroke-width="1.2"/>')

        elif k == "vessel":  # open container, optionally filled to "level" (height of liquid from its bottom)
            x, y, w, h = (_num(it.get(n), n) for n in ("x", "y", "w", "h"))
            (lx, ty), (rx, by_) = P((x, y + h)), P((x + w, y))
            if it.get("level") is not None:
                lv = min(_num(it["level"], "level"), h)
                _, ly = P((x, y + lv))
                back.append(f'<rect x="{_fmt(lx)}" y="{_fmt(ly)}" width="{_fmt(rx - lx)}" height="{_fmt(by_ - ly)}" fill="{WATER}"/>')
                back.append(f'<line x1="{_fmt(lx)}" y1="{_fmt(ly)}" x2="{_fmt(rx)}" y2="{_fmt(ly)}" stroke="{WATER_EDGE}" stroke-width="1.5"/>')
            mid.append(f'<path d="M{_fmt(lx)},{_fmt(ty)} V{_fmt(by_)} H{_fmt(rx)} V{_fmt(ty)}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>')
            if label:
                front.append(_label((lx + rx) / 2, by_ + 16, label, size=14))

        elif k == "block":
            cx, cy = P(it["center"]) if not it.get("on") else (0.0, 0.0)
            w, h = L(it.get("w", 1), "w"), L(it.get("h", 1), "h")
            a = math.radians(_num(it.get("angle", 0), "angle"))
            if it.get("on"):  # resting on a surface: lies along it, centre half a height above it
                a, (cx, cy) = _on_surface(it, P)
            corners = []
            for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
                # screen y points down, so a positive (counter-clockwise) world angle is a negative screen angle
                corners.append((cx + dx * math.cos(a) + dy * math.sin(a), cy - dx * math.sin(a) + dy * math.cos(a)))
            mid.append(f'<polygon points="{" ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in corners)}" fill="#dfe8ff" stroke="{INK}" stroke-width="2" stroke-linejoin="round"/>')
            if label:
                front.append(_label(cx, cy, label, size=15, weight="bold"))

        elif k == "ball":
            cx, cy = P(it["center"])
            r = max(L(it.get("r", 0.3), "r"), 5)
            mid.append(f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(r)}" fill="#dfe8ff" stroke="{INK}" stroke-width="2"/>')
            if label:
                front.append(_label(cx, cy, label, size=14, weight="bold") if r > 12 else _label(cx + r + 4, cy - r - 4, label, size=14, anchor="start", weight="bold"))

        elif k == "pulley":
            cx, cy = P(it["center"])
            r = max(L(it.get("r", 0.4), "r"), 8)
            mid.append(f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(r)}" fill="white" stroke="{INK}" stroke-width="2.2"/>')
            mid.append(f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="3" fill="{INK}"/>')

        elif k in ("line", "rope", "rod", "lever"):
            (ax, ay), (bx, by) = P(it["from"]), P(it["to"])
            width = {"rod": 4, "lever": 5}.get(k, 1.8)
            mid.append(f'<line x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke="{_color(it.get("color"))}" stroke-width="{width}" stroke-linecap="round"{dashed}/>')
            if label:
                front.append(_label((ax + bx) / 2, (ay + by) / 2 - 12, label, size=14))

        elif k == "spring":
            (ax, ay), (bx, by) = P(it["from"]), P(it["to"])
            ln = math.hypot(bx - ax, by - ay) or 1
            ux, uy = (bx - ax) / ln, (by - ay) / ln
            nx, ny = -uy, ux
            coils = int(min(max(_num(it.get("coils", 8), "coils"), 3), 20))
            lead = min(10, ln * 0.12)
            d = [f"M{_fmt(ax)},{_fmt(ay)}", f"L{_fmt(ax + ux * lead)},{_fmt(ay + uy * lead)}"]
            body = ln - 2 * lead
            for j in range(1, 2 * coils):
                t = lead + body * j / (2 * coils)
                side = 7 if j % 2 else -7
                d.append(f"L{_fmt(ax + ux * t + nx * side)},{_fmt(ay + uy * t + ny * side)}")
            d += [f"L{_fmt(bx - ux * lead)},{_fmt(by - uy * lead)}", f"L{_fmt(bx)},{_fmt(by)}"]
            mid.append(f'<path d="{" ".join(d)}" fill="none" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>')
            if label:
                if ny > 0:
                    nx, ny = -nx, -ny
                front.append(_label((ax + bx) / 2 + nx * 20, (ay + by) / 2 + ny * 20, label, size=14))

        elif k in ("support", "fulcrum"):  # triangle under a lever, apex at the point
            x, y = P(it["at"])
            mid.append(f'<polygon points="{_fmt(x)},{_fmt(y)} {_fmt(x - 11)},{_fmt(y + 18)} {_fmt(x + 11)},{_fmt(y + 18)}" fill="{INK}"/>')
            if label:
                front.append(_label(x, y + 30, label, size=14, weight="bold"))

        elif k in ("arrow", "force", "velocity"):
            (ax, ay), (bx, by) = P(it["from"]), P(it["to"])
            color = _color(it.get("color") or ("force" if k == "force" else "velocity" if k == "velocity" else "black"))
            front.append(f'<line x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke="{color}" stroke-width="2.4" marker-end="url(#{_marker(color)})"{dashed}/>')
            if label:
                ln = math.hypot(bx - ax, by - ay) or 1
                nx, ny = -(by - ay) / ln, (bx - ax) / ln
                if ny > 0:  # put the label above / to the left of the arrow
                    nx, ny = -nx, -ny
                anchor = "start" if nx > 0.4 else "end" if nx < -0.4 else "middle"
                front.append(_label(bx + nx * 10 + (bx - ax) / ln * 8, by + ny * 10 + (by - ay) / ln * 8, label, size=15, anchor=anchor, color=color, weight="bold"))

        elif k == "dimension":  # measured distance with end ticks and its value, offset from the object
            (ax, ay), (bx, by) = P(it["from"]), P(it["to"])
            ln = math.hypot(bx - ax, by - ay) or 1
            nx, ny = (by - ay) / ln, -(bx - ax) / ln  # screen normal pointing to world-left of from→to
            off = _num(it.get("offset", 0), "offset") * s
            if off:  # thin extension lines from the object to the dimension line
                front.append(
                    f'<path d="M{_fmt(ax)},{_fmt(ay)} l{_fmt(nx * off)},{_fmt(ny * off)} M{_fmt(bx)},{_fmt(by)} l{_fmt(nx * off)},{_fmt(ny * off)}" '
                    f'stroke="{GREY}" stroke-width="1" stroke-dasharray="3 3" fill="none"/>'
                )
            ax, ay, bx, by = ax + nx * off, ay + ny * off, bx + nx * off, by + ny * off
            front.append(f'<line x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke="{INK}" stroke-width="1.3" marker-start="url(#d-ink)" marker-end="url(#d-ink)"/>')
            if ny > 0:
                nx, ny = -nx, -ny
            front.append(_label((ax + bx) / 2 + nx * 12, (ay + by) / 2 + ny * 12, it.get("text", ""), size=14, weight="bold"))

        elif k == "angle":
            vx, vy = P(it["vertex"])
            (ax, ay), (bx, by) = P(it["from"]), P(it["to"])
            a1, a2 = math.atan2(ay - vy, ax - vx), math.atan2(by - vy, bx - vx)
            d = (a2 - a1) % (2 * math.pi)
            if d > math.pi:
                a1, a2, d = a2, a1, 2 * math.pi - d
            r = 26
            front.append(f'<path d="M{_fmt(vx + r * math.cos(a1))},{_fmt(vy + r * math.sin(a1))} A{r},{r} 0 0 1 {_fmt(vx + r * math.cos(a2))},{_fmt(vy + r * math.sin(a2))}" fill="none" stroke="{BLUE}" stroke-width="1.8"/>')
            if label or it.get("text"):
                m = a1 + d / 2
                front.append(_label(vx + 42 * math.cos(m), vy + 42 * math.sin(m), label or it.get("text"), size=14, color=BLUE))

        elif k == "path":  # trajectory through points; "smooth" draws a curve through them
            ps = [P(p) for p in it.get("points") or []][:40]
            if len(ps) < 2:
                raise FigureError("path needs 2 points")
            if it.get("smooth") and len(ps) > 2:
                d = [f"M{_fmt(ps[0][0])},{_fmt(ps[0][1])}"]
                for j in range(len(ps) - 1):  # Catmull-Rom → cubic Bézier
                    p0, p1, p2 = ps[max(j - 1, 0)], ps[j], ps[j + 1]
                    p3 = ps[min(j + 2, len(ps) - 1)]
                    c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
                    c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
                    d.append(f"C{_fmt(c1[0])},{_fmt(c1[1])} {_fmt(c2[0])},{_fmt(c2[1])} {_fmt(p2[0])},{_fmt(p2[1])}")
                path = " ".join(d)
            else:
                path = "M" + " L".join(f"{_fmt(x)},{_fmt(y)}" for x, y in ps)
            color = _color(it.get("color"), BLUE)
            end = f' marker-end="url(#{_marker(color)})"' if it.get("arrow") else ""
            mid.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round"{dashed}{end}/>')
            if label:
                front.append(_label(ps[-1][0] + 8, ps[-1][1] - 12, label, size=14, anchor="start", color=color, weight="bold"))

        elif k == "point":
            x, y = P(it["at"])
            front.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="4" fill="{INK}"/>')
            if label:
                front.append(_label(x + 8, y - 12, label, size=15, anchor="start", weight="bold"))

        elif k == "text":
            x, y = P(it["at"])
            front.append(_label(x, y, it.get("text", label), size=_num(it.get("size", 15), "size"), weight="bold" if it.get("bold") else "normal"))

        else:
            raise FigureError(f"unknown scene item {k}")

    return _svg("".join(back + mid + front), W, H)


RENDERERS = {"plot": _plot, "scene": _scene}
