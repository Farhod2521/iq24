import type { ReactNode } from "react";
import { ChevronRight } from "./icons";
import { Container } from "./ui";

type Subject = { name: string; lessons: string; tests: string; art: ReactNode };

/** A two-stop diagonal gradient, referenced by id from the icon below it. */
function Grad({ id, from, to }: { id: string; from: string; to: string }) {
  return (
    <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor={from} />
      <stop offset="1" stopColor={to} />
    </linearGradient>
  );
}

const subjects: Subject[] = [
  {
    name: "Matematika",
    lessons: "12 000+",
    tests: "25 000+",
    art: (
      <>
        <defs>
          <Grad id="g-math" from="#5d8bff" to="#1742d1" />
        </defs>
        <rect x="9" y="4" width="30" height="40" rx="6" fill="url(#g-math)" />
        <rect x="13" y="8" width="22" height="9" rx="2.5" fill="#dce7ff" />
        {[0, 1, 2].map((r) =>
          [0, 1, 2].map((c) => (
            <rect key={`${r}${c}`} x={13 + c * 8} y={21 + r * 7.5} width="6" height="5" rx="1.5" fill="white" opacity={c === 2 ? 1 : 0.85} />
          )),
        )}
      </>
    ),
  },
  {
    name: "Fizika",
    lessons: "8 500+",
    tests: "18 000+",
    art: (
      <>
        <defs>
          <Grad id="g-phys" from="#a78bfa" to="#ec4899" />
        </defs>
        <g fill="none" stroke="url(#g-phys)" strokeWidth="3">
          <ellipse cx="24" cy="24" rx="19" ry="7.5" />
          <ellipse cx="24" cy="24" rx="19" ry="7.5" transform="rotate(60 24 24)" />
          <ellipse cx="24" cy="24" rx="19" ry="7.5" transform="rotate(120 24 24)" />
        </g>
        <circle cx="24" cy="24" r="4.5" fill="#f97316" />
      </>
    ),
  },
  {
    name: "Kimyo",
    lessons: "7 200+",
    tests: "16 000+",
    art: (
      <>
        <defs>
          <Grad id="g-chem" from="#60a5fa" to="#1d4ed8" />
        </defs>
        <path d="M19 5h10v13l11 19a4 4 0 0 1-3.5 6h-25A4 4 0 0 1 8 37l11-19V5Z" fill="#e0ecff" stroke="#93b4f5" strokeWidth="1.5" />
        <path d="M13.5 29h21l5 8.5a3 3 0 0 1-2.6 4.5H11.1a3 3 0 0 1-2.6-4.5l5-8.5Z" fill="url(#g-chem)" />
        <rect x="17" y="3" width="14" height="4" rx="2" fill="#93b4f5" />
        <circle cx="21" cy="35" r="1.6" fill="white" opacity=".8" />
        <circle cx="27" cy="32" r="1.1" fill="white" opacity=".7" />
      </>
    ),
  },
  {
    name: "Biologiya",
    lessons: "6 800+",
    tests: "14 000+",
    art: (
      <>
        <defs>
          <Grad id="g-bio" from="#86efac" to="#15803d" />
        </defs>
        <path d="M41 6C22 6 9 15 9 30c0 4 1 7 3 10 3-9 10-17 20-22-8 6-14 14-17 24 3 1 6 2 9 2 15 0 18-17 17-38Z" fill="url(#g-bio)" />
        <path d="M12 40c4-9 11-17 20-22" fill="none" stroke="#dcfce7" strokeWidth="1.6" strokeLinecap="round" />
      </>
    ),
  },
  {
    name: "Tarix",
    lessons: "6 500+",
    tests: "13 000+",
    art: (
      <>
        <defs>
          <Grad id="g-hist" from="#fcd34d" to="#d97706" />
        </defs>
        <path d="M24 4 6 13h36L24 4Z" fill="url(#g-hist)" />
        <rect x="7" y="14" width="34" height="4" rx="1" fill="#f59e0b" />
        {[10, 18.5, 27, 35.5].map((x) => (
          <rect key={x} x={x - 1} y="19" width="5" height="17" rx="1.5" fill="url(#g-hist)" />
        ))}
        <rect x="6" y="37" width="36" height="4" rx="1" fill="#f59e0b" />
        <rect x="4" y="41" width="40" height="4" rx="1.5" fill="#b45309" />
      </>
    ),
  },
  {
    name: "Ona tili",
    lessons: "5 800+",
    tests: "12 000+",
    art: (
      <>
        <defs>
          <Grad id="g-lang" from="#fb7185" to="#be123c" />
        </defs>
        <path d="M8 8a4 4 0 0 1 4-4h26v34H12a4 4 0 0 0-4 4V8Z" fill="url(#g-lang)" />
        <path d="M8 42a4 4 0 0 1 4-4h26v6H12a4 4 0 0 1-4-2Z" fill="#fecdd3" />
        <rect x="15" y="11" width="16" height="9" rx="1.5" fill="white" opacity=".9" />
        <path d="M17 14h12M17 17h8" stroke="#be123c" strokeWidth="1.4" strokeLinecap="round" />
      </>
    ),
  },
  {
    name: "Adabiyot",
    lessons: "4 200+",
    tests: "9 500+",
    art: (
      <>
        <defs>
          <Grad id="g-lit" from="#c4b5fd" to="#7c3aed" />
        </defs>
        <path d="M42 4C26 7 14 19 11 35l4 2c3-6 8-11 14-14-5 4-9 9-11 15 15-2 23-15 24-34Z" fill="url(#g-lit)" />
        <path d="M6 44 26 20" stroke="#5b21b6" strokeWidth="2.2" strokeLinecap="round" />
      </>
    ),
  },
  {
    name: "Ingliz tili",
    lessons: "5 000+",
    tests: "11 000+",
    art: (
      <>
        <defs>
          <Grad id="g-eng" from="#38bdf8" to="#1d4ed8" />
        </defs>
        <text x="24" y="36" textAnchor="middle" fontSize="30" fontWeight="800" fontFamily="system-ui, sans-serif" fill="url(#g-eng)">
          Aa
        </text>
      </>
    ),
  },
  {
    name: "Geografiya",
    lessons: "4 800+",
    tests: "10 000+",
    art: (
      <>
        <defs>
          <Grad id="g-geo" from="#38bdf8" to="#1e40af" />
        </defs>
        <circle cx="24" cy="24" r="19" fill="url(#g-geo)" />
        <path
          d="M14 12c4 0 6 2 5 5s-5 2-6 6 3 5 2 9-4 2-6-1M27 7c-1 3 1 5 4 5s5 3 3 6-6 1-6 5 4 4 6 7 0 6-3 7"
          fill="#4ade80"
          stroke="#22c55e"
          strokeWidth="1"
        />
        <ellipse cx="18" cy="15" rx="6" ry="3" fill="white" opacity=".2" />
      </>
    ),
  },
  {
    name: "Informatika",
    lessons: "4 100+",
    tests: "9 000+",
    art: (
      <>
        <defs>
          <Grad id="g-info" from="#60a5fa" to="#4338ca" />
        </defs>
        <rect x="4" y="7" width="40" height="27" rx="4" fill="url(#g-info)" />
        <rect x="7.5" y="10.5" width="33" height="20" rx="2" fill="#dbeafe" />
        <path d="m15 17-3.5 3.5L15 24M33 17l3.5 3.5L33 24M26 15.5l-4 10" stroke="#4338ca" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
        <path d="M20 34h8l1.5 6h-11L20 34Z" fill="#818cf8" />
        <rect x="14" y="40" width="20" height="3" rx="1.5" fill="#4338ca" />
      </>
    ),
  },
];

export function Subjects() {
  return (
    <section id="fanlar" className="scroll-mt-24 py-8 lg:py-10">
      <Container className="2xl:max-w-[96rem]">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <h2 className="flex items-center gap-2.5 text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
            <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
              <path d="M3 7c5-2 9-1 12 2v19c-3-3-7-4-12-2V7Z" fill="#1f55f5" />
              <path d="M29 7c-5-2-9-1-12 2v19c3-3 7-4 12-2V7Z" fill="#5d8bff" />
            </svg>
            Fanlar
          </h2>
          <p className="text-muted">Barcha fanlarni tanlang va o&apos;qishni boshlang</p>
        </div>

        <ul className="mt-7 grid grid-cols-1 gap-4 min-[420px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {subjects.map((s) => (
            <li key={s.name}>
              <a
                href="/dashboard"
                className="group flex h-full items-center gap-3.5 rounded-2xl bg-white p-4 shadow-card ring-1 ring-brand-100/70 transition hover:-translate-y-1 hover:ring-brand-300"
              >
                <svg viewBox="0 0 48 48" className="size-14 shrink-0 drop-shadow-[0_8px_10px_rgb(15_35_95/0.15)]" aria-hidden="true">
                  {s.art}
                </svg>
                <div className="min-w-0 flex-1">
                  <p className="font-bold text-ink">{s.name}</p>
                  <p className="mt-0.5 text-[13px] leading-snug text-muted">{s.lessons} dars</p>
                  <p className="text-[13px] leading-snug text-muted">{s.tests} test</p>
                </div>
                <ChevronRight className="size-5 shrink-0 text-ink/40 transition group-hover:translate-x-0.5 group-hover:text-brand-600" />
              </a>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
