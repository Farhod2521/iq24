"""Solid-geometry figures (stereometry): the model describes the solid in 3D, this module draws it as a textbook does.

The view is a fixed axonometric (orthographic) projection — turned a little and seen from slightly above — so cubes
look like the book's and horizontal circles stay level ellipses. Visibility is computed, never guessed: every edge
and segment is sampled along its length and each sample is tested against the faces in front of it, so the hidden
parts come out dashed even for stacked or non-convex solids.

Figure type "solid":
  points    {"A": [x, y, z], …}            z is up, y goes away from the viewer
  bodies    box | prism | pyramid | polyhedron (faces of named points) | cylinder | cone | frustum | sphere | circle
  segments  extra lines between points (diagonals, heights, radii); dashed where hidden unless "dashed" is given
  polygons  highlighted sections / faces ("color": green | red | blue)
  labels    lengths written beside a segment;  angles  arcs or right-angle marks
"""

import math

from .figures import INK, FigureError, _fmt, _label, _num, _svg

W = 480
BLUE, GREEN, RED, GREY = "#1f55f5", "#16a34a", "#e5484d", "#8a94ad"
FILL = {"blue": ("#1f55f5", 0.16), "green": ("#22c55e", 0.3), "red": ("#e5484d", 0.25), "orange": ("#f59e0b", 0.28)}
SAMPLES = 36
MAX_POINTS, MAX_BODIES = 40, 6


# ─── vectors ─────────────────────────────────────────────────────────────────


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


class View:
    """Orthographic view: turned `yaw` about the vertical axis, looking down `elev` degrees."""

    def __init__(self, yaw: float, elev: float):
        self.cy, self.sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        self.ce, self.se = math.cos(math.radians(elev)), math.sin(math.radians(elev))
        # direction the viewer looks in (into the scene), world coordinates
        self.d = (self.ce * -self.sy, self.ce * self.cy, -self.se)

    def screen(self, p):
        """→ (X right, Y up, depth: larger = farther)."""
        xr = p[0] * self.cy + p[1] * self.sy
        yr = -p[0] * self.sy + p[1] * self.cy
        return xr, p[2] * self.ce + yr * self.se, yr * self.ce - p[2] * self.se


# ─── faces and occlusion ─────────────────────────────────────────────────────


class Face:
    def __init__(self, pts):
        if len(pts) < 3:
            raise FigureError("face needs 3 points")
        self.pts = pts
        c = mul(pts[0], 0)
        for p in pts:
            c = add(c, p)
        self.c = mul(c, 1 / len(pts))
        n = (0.0, 0.0, 0.0)
        for i in range(len(pts)):  # Newell's method: robust normal for any planar polygon
            a, b = pts[i], pts[(i + 1) % len(pts)]
            n = add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
        ln = norm(n)
        if ln < 1e-12:
            raise FigureError("degenerate face")
        self.n = mul(n, 1 / ln)
        self.k = dot(self.n, self.c)
        ax = max(range(3), key=lambda i: abs(self.n[i]))
        self.ij = [i for i in range(3) if i != ax]
        self.poly2 = [(p[self.ij[0]], p[self.ij[1]]) for p in pts]

    def contains(self, q, tol) -> bool:
        x, y = q[self.ij[0]], q[self.ij[1]]
        inside = False
        poly = self.poly2
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            if (y1 > y) != (y2 > y):
                xi = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xi > x:
                    inside = not inside
        if inside:
            # points on the outline count as outside (an edge must not hide itself on its own face)
            for i in range(len(poly)):
                (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
                ex, ey = x2 - x1, y2 - y1
                ln = math.hypot(ex, ey) or 1
                if abs((x - x1) * ey - (y - y1) * ex) / ln < tol:
                    t = ((x - x1) * ex + (y - y1) * ey) / (ln * ln)
                    if -0.01 <= t <= 1.01:
                        return False
        return inside

    def hides(self, p, view_d, tol) -> bool:
        """Is this face between the viewer and point p?"""
        nd = dot(self.n, view_d)
        if abs(nd) < 1e-9:
            return False
        t = (dot(self.n, p) - self.k) / nd  # p − t·d lies on the plane; t > 0 means toward the viewer
        if t <= tol:
            return False
        return self.contains(sub(p, mul(view_d, t)), tol)


class Body:
    def __init__(self, faces, transparent=False, fill="blue"):
        self.faces = faces
        self.transparent = transparent
        self.fill = fill
        c = (0.0, 0.0, 0.0)
        for f in faces:
            c = add(c, f.c)
        self.c = mul(c, 1 / len(faces))
        for f in faces:  # outward normals
            if dot(f.n, sub(f.c, self.c)) < 0:
                f.n = mul(f.n, -1)
                f.k = -f.k
        self.edges = []
        seen = set()
        for f in faces:
            for i in range(len(f.pts)):
                a, b = f.pts[i], f.pts[(i + 1) % len(f.pts)]
                key = tuple(sorted((tuple(round(v, 6) for v in a), tuple(round(v, 6) for v in b))))
                if key not in seen:
                    seen.add(key)
                    self.edges.append((a, b))


def runs(a, b, hidden_at):
    """Split segment a→b into (start, end, hidden) pieces by sampling."""
    flags = [hidden_at(lerp3(a, b, (i + 0.5) / SAMPLES)) for i in range(SAMPLES)]
    out = []
    start = 0
    for i in range(1, SAMPLES + 1):
        if i == SAMPLES or flags[i] != flags[start]:
            out.append((lerp3(a, b, start / SAMPLES), lerp3(a, b, i / SAMPLES), flags[start]))
            start = i
    return out


# ─── renderer ────────────────────────────────────────────────────────────────


def _solid(f: dict) -> str:
    view_cfg = f.get("view") or {}
    view = View(_num(view_cfg.get("yaw", -24), "yaw"), _num(view_cfg.get("elevation", 20), "elevation"))
    points: dict[str, tuple] = {}
    for name, v in list((f.get("points") or {}).items())[:MAX_POINTS]:
        if not isinstance(v, (list, tuple)) or len(v) != 3:
            raise FigureError(f"point {name} must be [x, y, z]")
        points[str(name)] = tuple(_num(c, f"{name}") for c in v)
    named = set(points)  # points whose names are drawn

    def P(ref):
        if isinstance(ref, str):
            if ref not in points:
                raise FigureError(f"unknown point {ref}")
            return points[ref]
        if isinstance(ref, (list, tuple)) and len(ref) == 3:
            return tuple(_num(c, "coordinate") for c in ref)
        raise FigureError("bad point reference")

    bodies: list[Body] = []
    rounds = []
    for b in (f.get("bodies") or [])[:MAX_BODIES]:
        kind = str(b.get("kind", ""))
        transparent = bool(b.get("transparent"))
        fill = str(b.get("fill", "blue"))
        if kind == "box":
            x, y, z = P(b.get("at", [0, 0, 0]))
            a, bb, c = (_num(v, "size") for v in b.get("size", [1, 1, 1]))
            names = list(b.get("names") or ["A", "B", "C", "D", "A1", "B1", "C1", "D1"])[:8]
            if len(names) != 8:
                raise FigureError("box needs 8 names")
            corners = [(x, y, z), (x + a, y, z), (x + a, y + bb, z), (x, y + bb, z)]
            corners += [(p[0], p[1], p[2] + c) for p in corners]
            for nm, p in zip(names, corners):
                points[nm] = p
                if not b.get("hide_names"):
                    named.add(nm)
            A, B, C, D, A1, B1, C1, D1 = names
            faces = [[A, B, C, D], [A1, B1, C1, D1], [A, B, B1, A1], [B, C, C1, B1], [C, D, D1, C1], [D, A, A1, D1]]
            bodies.append(Body([Face([P(n) for n in fc]) for fc in faces], transparent, fill))
        elif kind == "prism":
            base, top = list(b.get("base") or []), list(b.get("top") or [])
            if len(base) < 3 or len(base) != len(top):
                raise FigureError("prism needs base and top of the same size")
            n = len(base)
            faces = [base, top] + [[base[i], base[(i + 1) % n], top[(i + 1) % n], top[i]] for i in range(n)]
            bodies.append(Body([Face([P(x) for x in fc]) for fc in faces], transparent, fill))
        elif kind == "pyramid":
            base, apex = list(b.get("base") or []), b.get("apex")
            if len(base) < 3 or not apex:
                raise FigureError("pyramid needs a base and an apex")
            n = len(base)
            faces = [base] + [[base[i], base[(i + 1) % n], apex] for i in range(n)]
            bodies.append(Body([Face([P(x) for x in fc]) for fc in faces], transparent, fill))
        elif kind == "polyhedron":
            faces = b.get("faces") or []
            if len(faces) < 4:
                raise FigureError("polyhedron needs at least 4 faces")
            bodies.append(Body([Face([P(x) for x in fc]) for fc in faces], transparent, fill))
        elif kind in ("cylinder", "cone", "frustum", "sphere", "circle"):
            rounds.append(b)
        else:
            raise FigureError(f"unknown body {kind}")
    if not bodies and not rounds:
        raise FigureError("no bodies")

    # extent of everything on screen → scale into the picture
    scr = [view.screen(p) for p in points.values()]
    for b in rounds:
        c = P(b.get("center", [0, 0, 0]))
        r = max(_num(b.get("r", b.get("r1", 1)), "r"), _num(b.get("r2", 0), "r2"))
        h = _num(b.get("h", 0), "h")
        for dz in (0, h) if b["kind"] != "sphere" else (-r, r):
            for dx in (-r, r):
                for dy in (-r, r):
                    scr.append(view.screen((c[0] + dx, c[1] + dy, c[2] + dz)))
        if b["kind"] == "sphere":
            sx, sy, _ = view.screen(c)
            scr += [(sx - r, sy - r, 0), (sx + r, sy + r, 0)]
    if not scr:
        raise FigureError("nothing to draw")
    x0, x1 = min(p[0] for p in scr), max(p[0] for p in scr)
    y0, y1 = min(p[1] for p in scr), max(p[1] for p in scr)
    span = max(x1 - x0, y1 - y0, 1e-6)
    m = 40
    s = (W - 2 * m) / max(x1 - x0, span * 0.35)
    H = int(min(400, max(220, (y1 - y0) * s + 2 * m)))
    s = min(s, (H - 2 * m) / max(y1 - y0, span * 0.35))
    ox = (W - (x1 - x0) * s) / 2
    oy = (H - (y1 - y0) * s) / 2
    tol = span * 1e-4

    def S(p):
        X, Y, _ = view.screen(p)
        return ox + (X - x0) * s, H - oy - (Y - y0) * s

    occluders = [fc for bd in bodies if not bd.transparent for fc in bd.faces]

    def hidden_by(faces):
        return lambda p: any(fc.hides(p, view.d, tol) for fc in faces)

    def line(a, b, color=INK, width=2.0, dashed=False):
        (ax, ay), (bx, by) = S(a), S(b)
        dash = ' stroke-dasharray="6 5"' if dashed else ""
        return f'<line x1="{_fmt(ax)}" y1="{_fmt(ay)}" x2="{_fmt(bx)}" y2="{_fmt(by)}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"{dash}/>'

    back, mid, front = [], [], []

    # polyhedra: front faces lightly filled (top lighter), edges solid where seen, dashed where hidden
    for bd in bodies:
        color, alpha = FILL.get(bd.fill, FILL["blue"]) if bd.fill != "none" else (None, 0)
        if color:
            for fc in sorted(bd.faces, key=lambda fc: -view.screen(fc.c)[2]):
                if dot(fc.n, view.d) < 0:
                    a = alpha * (0.55 if fc.n[2] > 0.5 else 1.0)
                    pts = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in (S(p) for p in fc.pts))
                    back.append(f'<polygon points="{pts}" fill="{color}" fill-opacity="{a:.2f}" stroke="none"/>')
        own = [fc for fc in bd.faces] + [fc for other in bodies if other is not bd and not other.transparent for fc in other.faces]
        for a, b in bd.edges:
            for p, q, hid in runs(a, b, hidden_by(own)):
                (mid if not hid else back).append(line(p, q, BLUE if not hid else BLUE, 2.2 if not hid else 1.5, hid))

    # round solids (transparent: they never hide anything)
    for b in rounds:
        kind = b["kind"]
        c = P(b.get("center", [0, 0, 0]))
        color = BLUE

        def ellipse(center, r, back_dashed=True, solid_all=False, stroke=color):
            cx, cy = S(center)
            rx, ry = r * s, r * s * view.se
            if solid_all:
                return [f'<ellipse cx="{_fmt(cx)}" cy="{_fmt(cy)}" rx="{_fmt(rx)}" ry="{_fmt(ry)}" fill="none" stroke="{stroke}" stroke-width="2"/>']
            # screen y grows downward: the front half of a level circle is the lower half on screen
            fr = f'<path d="M{_fmt(cx - rx)},{_fmt(cy)} A{_fmt(rx)},{_fmt(ry)} 0 0 0 {_fmt(cx + rx)},{_fmt(cy)}" fill="none" stroke="{stroke}" stroke-width="2"/>'
            dash = ' stroke-dasharray="6 5"' if back_dashed else ""
            bk = f'<path d="M{_fmt(cx - rx)},{_fmt(cy)} A{_fmt(rx)},{_fmt(ry)} 0 0 1 {_fmt(cx + rx)},{_fmt(cy)}" fill="none" stroke="{stroke}" stroke-width="1.5"{dash}/>'
            return [fr, bk]

        if kind == "sphere":
            r = _num(b.get("r", 1), "r")
            cx, cy = S(c)
            fc, fa = FILL.get(str(b.get("fill", "red")), FILL["red"])
            back.append(f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(r * s)}" fill="{fc}" fill-opacity="{fa:.2f}" stroke="{RED}" stroke-width="2"/>')
            if b.get("equator", True):
                mid.extend(ellipse(c, r, stroke=RED))
        elif kind == "circle":  # a level circle, e.g. inscribed in a base
            mid.extend(ellipse(c, _num(b.get("r", 1), "r"), back_dashed=bool(b.get("dashed_back", True)), stroke=RED if b.get("color") == "red" else BLUE))
        elif kind in ("cylinder", "frustum"):
            r1 = _num(b.get("r", b.get("r1", 1)), "r")
            r2 = _num(b.get("r2", r1), "r2") if kind == "frustum" else r1
            h = _num(b.get("h", 1), "h")
            top = (c[0], c[1], c[2] + h)
            (bx, by), (tx, ty) = S(c), S(top)
            fc, fa = FILL.get(str(b.get("fill", "blue")), FILL["blue"])
            ry1, ry2 = r1 * s * view.se, r2 * s * view.se
            # silhouette: front half of the bottom ellipse, the sides, the far half of the top ellipse
            back.append(
                f'<path d="M{_fmt(bx - r1 * s)},{_fmt(by)} A{_fmt(r1 * s)},{_fmt(ry1)} 0 0 0 {_fmt(bx + r1 * s)},{_fmt(by)} '
                f'L{_fmt(tx + r2 * s)},{_fmt(ty)} A{_fmt(r2 * s)},{_fmt(ry2)} 0 0 0 {_fmt(tx - r2 * s)},{_fmt(ty)} Z" '
                f'fill="{fc}" fill-opacity="{fa * 0.7:.2f}" stroke="none"/>'
            )
            mid.append(f'<line x1="{_fmt(bx - r1 * s)}" y1="{_fmt(by)}" x2="{_fmt(tx - r2 * s)}" y2="{_fmt(ty)}" stroke="{color}" stroke-width="2.2"/>')
            mid.append(f'<line x1="{_fmt(bx + r1 * s)}" y1="{_fmt(by)}" x2="{_fmt(tx + r2 * s)}" y2="{_fmt(ty)}" stroke="{color}" stroke-width="2.2"/>')
            mid.extend(ellipse(c, r1))
            mid.extend(ellipse(top, r2, solid_all=True))
        elif kind == "cone":
            r = _num(b.get("r", 1), "r")
            h = _num(b.get("h", 1), "h")
            apex = (c[0], c[1], c[2] + h)
            (bx, by), (axp, ayp) = S(c), S(apex)
            rx, ry = r * s, r * s * view.se
            fc, fa = FILL.get(str(b.get("fill", "blue")), FILL["blue"])
            # tangent points from the apex to the base ellipse: where (P − A) is parallel to the tangent P'
            tang = []
            prev = None
            for i in range(721):
                t = 2 * math.pi * i / 720
                px, py = bx + rx * math.cos(t), by + ry * math.sin(t)
                dx, dy = -rx * math.sin(t), ry * math.cos(t)
                val = (px - axp) * dy - (py - ayp) * dx
                if prev is not None and (val > 0) != (prev[1] > 0):
                    tang.append(t)
                prev = (t, val)
            if len(tang) >= 2:
                ta, tb = tang[0], tang[1]
                pa = (bx + rx * math.cos(ta), by + ry * math.sin(ta))
                pb = (bx + rx * math.cos(tb), by + ry * math.sin(tb))
                # the arc on the viewer's side (lower on screen) is the visible one
                mid_t = (ta + tb) / 2
                lower_is_mid = math.sin(mid_t) > 0  # screen y down: sin > 0 → lower half
                def arc(t0, t1, dashed):
                    pts = " ".join(
                        f"{_fmt(bx + rx * math.cos(t0 + (t1 - t0) * k / 40))},{_fmt(by + ry * math.sin(t0 + (t1 - t0) * k / 40))}"
                        for k in range(41)
                    )
                    style = 'stroke-width="1.5" stroke-dasharray="6 5"' if dashed else 'stroke-width="2"'
                    return f'<polyline points="{pts}" fill="none" stroke="{color}" {style}/>'

                if lower_is_mid:
                    mid.append(arc(ta, tb, False))
                    back.append(arc(tb, ta + 2 * math.pi, True))
                else:
                    back.append(arc(ta, tb, True))
                    mid.append(arc(tb, ta + 2 * math.pi, False))
                # silhouette: apex, one tangent point, the visible (front) arc, the other tangent point
                t0, t1 = (ta, tb) if lower_is_mid else (tb, ta + 2 * math.pi)
                outline = " ".join(f"{_fmt(bx + rx * math.cos(t0 + (t1 - t0) * k / 40))},{_fmt(by + ry * math.sin(t0 + (t1 - t0) * k / 40))}" for k in range(41))
                back.append(f'<polygon points="{_fmt(axp)},{_fmt(ayp)} {outline}" fill="{fc}" fill-opacity="{fa * 0.7:.2f}" stroke="none"/>')
                mid.append(f'<path d="M{_fmt(pa[0])},{_fmt(pa[1])} L{_fmt(axp)},{_fmt(ayp)} L{_fmt(pb[0])},{_fmt(pb[1])}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linejoin="round"/>')
            else:  # apex inside the base outline (seen from above): the whole base shows
                mid.append(f'<ellipse cx="{_fmt(bx)}" cy="{_fmt(by)}" rx="{_fmt(rx)}" ry="{_fmt(ry)}" fill="none" stroke="{color}" stroke-width="2"/>')

    # highlighted sections
    for pg in (f.get("polygons") or [])[:6]:
        names = pg.get("points") if isinstance(pg, dict) else pg
        pts = [P(n) for n in names or []]
        if len(pts) < 3:
            raise FigureError("polygon needs 3 points")
        col = str(pg.get("color", "green")) if isinstance(pg, dict) else "green"
        fc, fa = FILL.get(col, FILL["green"])
        stroke = {"green": GREEN, "red": RED, "orange": "#d97706"}.get(col, BLUE)
        back.append(f'<polygon points="{" ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in (S(p) for p in pts))}" fill="{fc}" fill-opacity="{fa:.2f}" stroke="none"/>')
        for i in range(len(pts)):
            for p, q, hid in runs(pts[i], pts[(i + 1) % len(pts)], hidden_by(occluders)):
                mid.append(line(p, q, stroke, 1.8, hid))

    # extra segments
    for sg in (f.get("segments") or [])[:20]:
        a, b = P(sg.get("from")), P(sg.get("to"))
        col = {"green": GREEN, "red": RED, "blue": BLUE, "black": INK}.get(str(sg.get("color", "")), INK)
        if "dashed" in sg and sg["dashed"] is not None:
            mid.append(line(a, b, col, 1.8, bool(sg["dashed"])))
        else:
            for p, q, hid in runs(a, b, hidden_by(occluders)):
                mid.append(line(p, q, col, 1.8, hid))

    # names, lengths, angles
    cx_all = sum(S(points[n])[0] for n in named) / max(len(named), 1)
    cy_all = sum(S(points[n])[1] for n in named) / max(len(named), 1)
    taken = []
    for n in named:
        x, y = S(points[n])
        dx, dy = x - cx_all, y - cy_all
        ln = math.hypot(dx, dy) or 1
        lx, ly = x + dx / ln * 15, y + dy / ln * 15
        front.append(f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="2.6" fill="{INK}"/>')
        front.append(_label(lx, ly, n, size=17, weight="bold"))
        taken.append((lx, ly))
    for lb in (f.get("labels") or [])[:12]:
        (ax, ay), (bx, by) = S(P(lb.get("from"))), S(P(lb.get("to")))
        nx, ny = -(by - ay), bx - ax
        ln = math.hypot(nx, ny) or 1
        nx, ny = nx / ln, ny / ln
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if (mx + nx - cx_all) ** 2 + (my + ny - cy_all) ** 2 < (mx - cx_all) ** 2 + (my - cy_all) ** 2:
            nx, ny = -nx, -ny
        unknown = bool(lb.get("unknown"))
        anchor = "start" if nx > 0.35 else "end" if nx < -0.35 else "middle"
        front.append(_label(mx + nx * 10, my + ny * 12, lb.get("text", ""), size=17, anchor=anchor,
                            color=BLUE if unknown else INK, weight="bold"))
    for ang in (f.get("angles") or [])[:6]:
        (vx, vy), (ax, ay), (bx, by) = S(P(ang["vertex"])), S(P(ang["from"])), S(P(ang["to"]))
        a1, a2 = math.atan2(ay - vy, ax - vx), math.atan2(by - vy, bx - vx)
        if ang.get("right"):
            u1 = (math.cos(a1) * 11, math.sin(a1) * 11)
            u2 = (math.cos(a2) * 11, math.sin(a2) * 11)
            front.append(f'<path d="M{_fmt(vx + u1[0])},{_fmt(vy + u1[1])} L{_fmt(vx + u1[0] + u2[0])},{_fmt(vy + u1[1] + u2[1])} L{_fmt(vx + u2[0])},{_fmt(vy + u2[1])}" fill="none" stroke="{INK}" stroke-width="1.4"/>')
            continue
        d = (a2 - a1) % (2 * math.pi)
        if d > math.pi:
            a1, a2, d = a2, a1, 2 * math.pi - d
        r = 22
        front.append(f'<path d="M{_fmt(vx + r * math.cos(a1))},{_fmt(vy + r * math.sin(a1))} A{r},{r} 0 0 1 {_fmt(vx + r * math.cos(a2))},{_fmt(vy + r * math.sin(a2))}" fill="none" stroke="{RED}" stroke-width="1.8"/>')
        if ang.get("text"):
            mm = a1 + d / 2
            front.append(_label(vx + 36 * math.cos(mm), vy + 36 * math.sin(mm), ang["text"], size=14, color=RED, weight="bold"))

    return _svg("".join(back + mid + front), W, H)


RENDERERS = {"solid": _solid}
