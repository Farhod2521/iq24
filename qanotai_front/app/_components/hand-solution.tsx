import { MathText } from "./math-text";
import { BookOpen } from "./icons";

/** Step-by-step solution as stored on a question (backend: app/solution.py). */
export type ColumnOp = { a: string; b: string; op: string; result: string; partials?: string[] };

export type Solution = {
  /** physics notebook header: "Berilgan", SI conversion, "Topish kerak" */
  given?: string[];
  si?: string[];
  find?: string[];
  steps: { title: string; lines?: string[]; boxed?: boolean; column?: ColumnOp }[];
  answer: string;
  check?: {
    title?: string;
    lines?: string[];
    division?: { dividend: string; divisor: string; quotient: string; product: string; remainder: string };
  };
  conclusion?: string;
};

export const INK = "text-[#1e3a9e]";

/** Squared notebook paper, shared by both handwritten solutions. */
export const PAPER = {
  backgroundColor: "#fbfcff",
  backgroundImage:
    "linear-gradient(to right, rgb(31 85 245 / 0.09) 1px, transparent 1px), linear-gradient(to bottom, rgb(31 85 245 / 0.09) 1px, transparent 1px)",
  backgroundSize: "26px 26px",
};

/** "Berilgan: … / SI: … / Topish kerak: …" column of a physics notebook, ruled off from the solution. */
function Given({ solution }: { solution: Solution }) {
  return (
    <div className="w-fit min-w-[11rem] text-[1.6rem] leading-snug">
      <p className="text-[1.75rem]">Berilgan:</p>
      {solution.given!.map((g, i) => (
        <p key={i} className="whitespace-nowrap">
          <MathText text={g} />
        </p>
      ))}
      {solution.find && solution.find.length > 0 && (
        <div className="mt-2 border-t-2 border-current pt-2">
          {solution.find.map((f, i) => (
            <p key={i} className="whitespace-nowrap">
              <MathText text={f} />
            </p>
          ))}
        </div>
      )}
      {solution.si && solution.si.length > 0 && (
        <div className="mt-5">
          <p className="text-[1.75rem]">SI:</p>
          {solution.si.map((g, i) => (
            <p key={i} className="whitespace-nowrap">
              <MathText text={g} />
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

/** Column division as written in a school notebook. */
function Division({ d }: { d: NonNullable<NonNullable<Solution["check"]>["division"]> }) {
  return (
    <div className="inline-grid grid-cols-[auto_auto] text-[1.75rem] leading-[2.6rem]">
      <span className="pr-3 text-right">{d.dividend}</span>
      <span className="border-b-2 border-l-2 border-current pl-3">{d.divisor}</span>
      <span className="relative border-b-2 border-current pr-3 text-right">
        <span className="absolute -left-4 top-0">−</span>
        {d.product}
      </span>
      <span className="border-l-2 border-current pl-3">{d.quotient}</span>
      <span className="pr-3 text-right">{d.remainder}</span>
      <span />
    </div>
  );
}

/** Column addition / subtraction / multiplication, digits right-aligned like on squared paper. */
function Column({ c }: { c: ColumnOp }) {
  const partials = c.op === "×" ? (c.partials ?? []) : [];
  // each partial product of a column multiplication shifts one place left
  const rows = partials.map((p, i) => p + " ".repeat(i));
  const width = Math.max(c.a.length, c.b.length + 1, c.result.length, ...rows.map((r) => r.length)) + 1;
  const pad = (t: string) => t.padStart(width, " ");
  return (
    <div className="inline-flex flex-col items-end font-hand text-[1.7rem] leading-[2.3rem] tabular-nums">
      <span className="whitespace-pre">{pad(c.a)}</span>
      <span className="relative whitespace-pre">
        <span className="absolute left-0">{c.op}</span>
        {pad(c.b)}
      </span>
      <span className="w-full border-t-2 border-current" />
      {rows.length > 1 && (
        <>
          {rows.map((r, i) => (
            <span key={i} className="relative whitespace-pre">
              {i > 0 && <span className="absolute left-0">+</span>}
              {pad(r)}
            </span>
          ))}
          <span className="w-full border-t-2 border-current" />
        </>
      )}
      <span className="whitespace-pre">{pad(c.result)}</span>
    </div>
  );
}

/** The answer in a hand-drawn oval with a highlighter wash, like the last line of a notebook solution. */
function CircledAnswer({ text }: { text: string }) {
  return (
    <div className="relative mt-4 inline-block px-12 py-5">
      <span className="absolute inset-x-2 inset-y-3 -rotate-2 rounded-[50%] bg-brand-200/45 blur-[1px]" />
      <svg viewBox="0 0 300 100" preserveAspectRatio="none" aria-hidden="true" className="absolute inset-0 h-full w-full text-[#1e3a9e]">
        <path d="M150 8C70 6 10 24 8 52c-2 30 70 42 146 40 80-2 140-16 138-44C290 20 230 8 140 12" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M40 96c60 6 140 2 210-8" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
      <span className="relative text-[2.4rem] font-semibold leading-none">
        <MathText text={text} />
      </span>
    </div>
  );
}

export function HandSolution({ solution, question, number, difficulty }: { solution: Solution; question?: string; number?: number; difficulty?: { label: string; badge: string; dot: string } }) {
  const hasSide = !!(solution.check || solution.conclusion);
  const hasGiven = !!(solution.given && solution.given.length > 0);
  // with a "Berilgan" column the page is already split in two: check / conclusion go under the answer instead
  const sideBeside = hasSide && !hasGiven;
  return (
    <section className="rounded-3xl bg-white p-5 shadow-card ring-1 ring-brand-100/70 sm:p-7">
      <div className="flex items-center gap-4">
        <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-brand-600">
          <BookOpen className="size-6" />
        </span>
        <div>
          <h3 className="text-xl font-extrabold text-ink">Yechish usuli</h3>
          <p className="text-sm text-muted">Masalani bosqichma-bosqich yechamiz</p>
        </div>
      </div>

      {question && (
        <div className="mt-5 flex items-start gap-4 rounded-2xl bg-brand-50/50 p-4">
          {number && <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-brand-600 text-lg font-bold text-white">{number}</span>}
          <div>
            {difficulty && (
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${difficulty.badge}`}>
                <span className={`size-1.5 rounded-full ${difficulty.dot}`} /> {difficulty.label}
              </span>
            )}
            <p className="mt-1.5 font-semibold text-ink">{question}</p>
          </div>
        </div>
      )}

      {/* notebook page */}
      <div
        className={`mt-5 overflow-x-auto rounded-2xl p-6 font-hand font-semibold ring-1 ring-brand-100 sm:p-8 ${INK}`}
        style={PAPER}
      >
        <div className={solution.given && solution.given.length > 0 ? "flex flex-col gap-6 md:flex-row md:gap-8" : ""}>
        {solution.given && solution.given.length > 0 && <Given solution={solution} />}
        <div className={`grid min-w-0 flex-1 gap-8 ${sideBeside ? "lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]" : ""} ${hasGiven ? "md:border-l-2 md:border-current/70 md:pl-8" : ""}`}>
          <ol className="flex min-w-0 flex-col gap-5">
            {solution.steps.map((step, i) => (
              <li key={i}>
                <p className="text-[1.75rem] leading-tight">
                  <span className={i === 0 ? "rounded-lg bg-brand-100/70 px-2" : ""}>
                    {i + 1}. <MathText text={step.title} />:
                  </span>
                </p>
                {step.lines && step.lines.length > 0 && (
                  <div className={`mt-2 ml-7 flex flex-col gap-1 text-[1.7rem] leading-snug ${step.boxed ? "w-fit border-2 border-current px-5 py-2" : ""}`}>
                    {step.lines.map((line, j) => (
                      <span key={j} className="whitespace-pre-wrap">
                        <MathText text={line} />
                      </span>
                    ))}
                  </div>
                )}
                {step.column && (
                  <div className="mt-2 ml-10">
                    <Column c={step.column} />
                  </div>
                )}
              </li>
            ))}
            <li>
              <CircledAnswer text={solution.answer} />
            </li>
          </ol>

          {hasSide && (
            <div className={`flex min-w-0 flex-col gap-8 ${sideBeside ? "lg:border-l-2 lg:border-current/70 lg:pl-8" : ""}`}>
              {solution.check && (
                <div>
                  <p className="text-[1.75rem]">{solution.check.title || "Tekshirish"}:</p>
                  {solution.check.division && (
                    <div className="mt-3 pl-8">
                      <Division d={solution.check.division} />
                    </div>
                  )}
                  {solution.check.lines?.map((line, j) => (
                    <p key={j} className="ml-7 text-[1.7rem]">
                      <MathText text={line} />
                    </p>
                  ))}
                </div>
              )}
              {solution.conclusion && <p className="text-[1.65rem] leading-snug">
                  <MathText text={solution.conclusion} />
                </p>}
            </div>
          )}
        </div>
        </div>
      </div>
    </section>
  );
}
