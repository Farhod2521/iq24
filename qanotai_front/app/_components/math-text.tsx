import { Fragment } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

// superscript characters → the plain characters they stand for
const SUP: Record<string, string> = {
  "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
  "⁺": "+", "⁻": "−", "⁼": "=", "⁽": "(", "⁾": ")",
  "ⁿ": "n", "ⁱ": "i", "ᵃ": "a", "ᵇ": "b", "ᶜ": "c", "ᵈ": "d", "ᵉ": "e", "ᵏ": "k", "ᵐ": "m", "ˣ": "x", "ʸ": "y",
};
const SUP_CHARS = Object.keys(SUP).join("");

// LaTeX written between $…$ (fractions, multi-level expressions) — typeset like a textbook
const LATEX = /\$([^$]+)\$/g;

// outside $…$: a superscript run, a leftover programmer-style power (^(…), ^{…}, ^123, ^n),
// or a plain numeric fraction "2/3" / mixed number "4 3/5" (drawn stacked, as in the book)
const TOKEN = new RegExp(
  `([${SUP_CHARS}]+)` +
    `|\\^\\s*(\\([^()]{1,16}\\)|\\{[^{}]{1,16}\\}|-?\\d+|[a-zA-Z])` +
    `|(?<![\\d,./])(?:(\\d+) )?(\\d+)/(\\d+)(?![\\d/,])`,
  "g",
);

type Part = string | { sup: string } | { tex: string };

function tex(src: string, key: number) {
  // \displaystyle: full-size stacked fractions as in the printed book (inline style shrinks them to footnote size)
  const html = katex.renderToString(`\\displaystyle ${src}`, { throwOnError: false, strict: "ignore", output: "html" });
  return <span key={key} className="math-tex" dangerouslySetInnerHTML={{ __html: html }} />;
}

function plainParts(text: string): Part[] {
  const parts: Part[] = [];
  let last = 0;
  for (const m of text.matchAll(TOKEN)) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    if (m[1]) {
      parts.push({ sup: [...m[1]].map((ch) => SUP[ch] ?? ch).join("") });
    } else if (m[2]) {
      parts.push({ sup: m[2].replace(/^[({]|[)}]$/g, "") });
    } else {
      parts.push({ tex: `${m[3] ?? ""}\\frac{${m[4]}}{${m[5]}}` });
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}

/**
 * Renders maths text as a student sees it in a textbook: LaTeX between $…$ is typeset (stacked fractions,
 * multi-level expressions), plain "2/3" and "4 3/5" become stacked fractions, and powers ("8²⁰²⁵", "8^2025")
 * become readable raised exponents.
 */
export function MathText({ text, className }: { text: string; className?: string }) {
  const parts: Part[] = [];
  let last = 0;
  for (const m of text.matchAll(LATEX)) {
    if (m.index > last) parts.push(...plainParts(text.slice(last, m.index)));
    parts.push({ tex: m[1] });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push(...plainParts(text.slice(last)));

  return (
    <span className={className}>
      {parts.map((p, i) =>
        typeof p === "string" ? (
          <Fragment key={i}>{p}</Fragment>
        ) : "tex" in p ? (
          tex(p.tex, i)
        ) : (
          <sup key={i} className="relative -top-[0.6em] ml-[0.05em] align-baseline text-[0.7em] font-semibold leading-none">
            {p.sup}
          </sup>
        ),
      )}
    </span>
  );
}
