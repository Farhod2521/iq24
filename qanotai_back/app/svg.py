"""SVG sanitizer for test figures.

SVG is XML that browsers execute: it can carry <script>, on* event handlers, external references and
<foreignObject> HTML. Figures come from an AI model (untrusted), so they are rebuilt from scratch keeping only an
allowlist of drawing elements and attributes. Anything else is dropped; unparseable input is rejected.
"""

import re
import xml.etree.ElementTree as ET

from defusedxml import ElementTree as SafeET  # blocks entity-expansion / external-entity attacks while parsing

SVG_NS = "http://www.w3.org/2000/svg"
MAX_BYTES = 40_000
MAX_ELEMENTS = 600

ELEMENTS = {
    "svg", "g", "defs", "title", "desc", "marker",
    "path", "line", "polyline", "polygon", "rect", "circle", "ellipse", "text", "tspan",
}
ATTRIBUTES = {
    "viewBox", "width", "height", "preserveAspectRatio", "id", "transform",
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "d", "points", "dx", "dy",
    "fill", "fill-opacity", "fill-rule", "stroke", "stroke-width", "stroke-opacity", "stroke-dasharray",
    "stroke-linecap", "stroke-linejoin", "opacity",
    "font-size", "font-family", "font-weight", "font-style", "text-anchor", "dominant-baseline", "letter-spacing",
    "marker-start", "marker-mid", "marker-end",
    "markerWidth", "markerHeight", "refX", "refY", "orient", "markerUnits",
}
# attribute values may only point inside the same SVG: url(#id)
URL_REF = re.compile(r"url\(\s*#[A-Za-z][\w.-]*\s*\)")
SAFE_VALUE = re.compile(r"^[\w\s.,:;%#()+\-/'\"°]*$")


class InvalidSvg(ValueError):
    pass


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _copy(src: ET.Element, count: list[int]) -> ET.Element | None:
    name = _local(src.tag)
    if name not in ELEMENTS:
        return None
    count[0] += 1
    if count[0] > MAX_ELEMENTS:
        raise InvalidSvg("too many elements")

    out = ET.Element(name)
    for key, value in src.attrib.items():
        key = _local(key)
        if key not in ATTRIBUTES:
            continue  # drops on*, href, xlink:href, style, class, …
        value = value.strip()
        if "url(" in value and not URL_REF.fullmatch(value):
            continue
        if not SAFE_VALUE.match(value):
            continue
        out.set(key, value)
    out.text = src.text
    for child in src:
        clean = _copy(child, count)
        if clean is not None:
            clean.tail = child.tail
            out.append(clean)
    return out


def sanitize_svg(markup: str) -> str:
    """Return a safe, self-contained SVG string, or raise InvalidSvg."""
    markup = (markup or "").strip()
    if not markup or len(markup.encode()) > MAX_BYTES:
        raise InvalidSvg("empty or too large")
    # the model sometimes wraps the figure in a ```svg fence
    markup = re.sub(r"^```(?:svg|xml)?\s*|\s*```$", "", markup)
    try:
        root = SafeET.fromstring(markup)
    except Exception as e:  # defusedxml raises several types for malformed or hostile input
        raise InvalidSvg(str(e))
    if _local(root.tag) != "svg":
        raise InvalidSvg("root is not <svg>")

    clean = _copy(root, [0])
    if clean is None or not clean.get("viewBox"):
        raise InvalidSvg("missing viewBox")
    # size comes from the viewBox, so the figure scales with whatever box shows it
    clean.attrib.pop("width", None)
    clean.attrib.pop("height", None)
    clean.set("xmlns", SVG_NS)
    return ET.tostring(clean, encoding="unicode")
