import { ArrowRight, Check, PlayCircle } from "./icons";
import { Container } from "./ui";

const options = [
  { key: "A", value: "−1", correct: true },
  { key: "B", value: "0" },
  { key: "C", value: "1" },
  { key: "D", value: "3" },
];

// answer sheet in the timer card: done questions are outlined, 12 is the current one
const DONE = new Set([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]);

function TimerRing() {
  const r = 34;
  const c = 2 * Math.PI * r;
  return (
    <div className="relative mx-auto size-24">
      <svg viewBox="0 0 80 80" className="size-full -rotate-90" aria-hidden="true">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#dce7ff" strokeWidth="6" />
        <circle cx="40" cy="40" r={r} fill="none" stroke="#1f55f5" strokeWidth="6" strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * 0.3} />
      </svg>
      <span className="absolute inset-0 grid place-items-center text-xl font-extrabold text-ink">00:25</span>
    </div>
  );
}

export function DtmTests() {
  return (
    <section id="testlar" className="scroll-mt-24 py-6 lg:py-10">
      <Container className="2xl:max-w-[96rem]">
        <div className="relative overflow-hidden rounded-[2rem] bg-gradient-to-br from-[#0b1d5e] via-[#11308f] to-brand-600 px-6 py-10 sm:px-10 lg:px-12 lg:py-12">
          <div className="pointer-events-none absolute -top-24 right-[30%] size-80 rounded-full bg-brand-400/25 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-32 -left-16 size-96 rounded-full bg-sky-400/15 blur-3xl" />

          <div className="relative grid items-center gap-10 lg:grid-cols-[1fr_1.15fr]">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">DTM formatidagi real testlar</h2>
              <p className="mt-4 max-w-md text-lg leading-relaxed text-white/75">
                Yillar bo&apos;yicha testlar, mavzuli testlar va onlayn imtihonlar bilan o&apos;zingizni sinab ko&apos;ring.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <a
                  href="/dashboard"
                  className="group inline-flex items-center gap-2.5 rounded-xl bg-brand-500 px-6 py-3.5 font-bold text-white shadow-lg shadow-black/20 transition-colors hover:bg-brand-400"
                >
                  Testlarni yechish <ArrowRight className="size-5 transition-transform group-hover:translate-x-1" />
                </a>
                <a
                  href="/dashboard"
                  className="inline-flex items-center gap-2.5 rounded-xl bg-white/10 px-6 py-3.5 font-bold text-white ring-1 ring-white/25 transition-colors hover:bg-white/15"
                >
                  <PlayCircle className="size-5" /> Namunaviy test
                </a>
              </div>
            </div>

            {/* a test in progress: the question card and the timer / answer sheet beside it */}
            <div className="relative flex items-start justify-center gap-4 lg:justify-end">
              <div className="w-full max-w-[22rem] -rotate-2 rounded-2xl bg-white p-5 shadow-2xl shadow-black/30">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-extrabold text-ink">
                    12<span className="font-medium text-muted">/30</span>
                  </span>
                  <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-semibold text-brand-600">Matematika</span>
                </div>
                <p className="mt-4 text-[15px] leading-relaxed font-medium text-ink">
                  Agar f(x) = x² − 4x + 3 bo&apos;lsa, f(2) ning qiymatini toping.
                </p>
                <ul className="mt-4 grid gap-2">
                  {options.map((o) => (
                    <li
                      key={o.key}
                      className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold ${
                        o.correct ? "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" : "bg-slate-50 text-ink ring-1 ring-slate-100"
                      }`}
                    >
                      {o.correct ? (
                        <span className="grid size-6 place-items-center rounded-full bg-emerald-500 text-white">
                          <Check className="size-3.5" strokeWidth={3} />
                        </span>
                      ) : (
                        <span className="grid size-6 place-items-center rounded-full bg-white text-xs text-muted ring-1 ring-slate-200">{o.key}</span>
                      )}
                      {o.value}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="hidden w-48 shrink-0 translate-y-6 rotate-2 rounded-2xl bg-white p-5 shadow-2xl shadow-black/30 sm:block">
                <TimerRing />
                <ol className="mt-5 grid grid-cols-5 gap-1.5">
                  {Array.from({ length: 15 }, (_, i) => i + 1).map((n) => (
                    <li
                      key={n}
                      className={`grid aspect-square place-items-center rounded-lg text-xs font-bold ${
                        n === 12
                          ? "bg-brand-600 text-white"
                          : DONE.has(n)
                            ? "bg-brand-50 text-brand-700 ring-1 ring-brand-200"
                            : "text-muted ring-1 ring-slate-200"
                      }`}
                    >
                      {n}
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
