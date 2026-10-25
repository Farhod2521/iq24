"use client";

import { useRef } from "react";
import { ChevronLeft, ChevronRight, Quote } from "./icons";
import { Container } from "./ui";

// Namunaviy fikrlar: sayt ishga tushishidan oldin haqiqiy o'quvchilar fikri va natijalari bilan almashtiring.
const reviews = [
  { name: "Shahzoda", subject: "Matematika", score: "189,5", tone: "from-amber-300 to-orange-500", text: "IQ24 dagi testlar juda foydali bo'ldi. Har kuni test ishlab, zaif mavzularimni topdim va ustida ishladim." },
  { name: "Behruz", subject: "Fizika", score: "186,2", tone: "from-sky-300 to-brand-600", text: "Video darslar tushunarli va qisqa. Yechimlar qadam-baqadam yozilgani menga juda yoqdi." },
  { name: "Mohira", subject: "Kimyo", score: "182,1", tone: "from-rose-300 to-pink-500", text: "Mavzular juda yaxshi tuzilgan. Batafsil yechimlar orqali masalalarni o'zim yecha boshladim." },
  { name: "Ulug'bek", subject: "Tarix", score: "179,8", tone: "from-emerald-300 to-teal-600", text: "Testlar DTM formatiga juda yaqin. Imtihon kuni o'zimni xotirjam his qildim." },
  { name: "Madina", subject: "Biologiya", score: "184,0", tone: "from-violet-300 to-violet-600", text: "Reyting tufayli har kuni o'qishga motivatsiya bo'ldi. Natijamni oyma-oy kuzatib bordim." },
  { name: "Jasur", subject: "Ingliz tili", score: "181,4", tone: "from-indigo-300 to-indigo-600", text: "Telefonda ham, kompyuterda ham qulay. Bo'sh vaqtimda ham test ishlab yurdim." },
];

export function Testimonials() {
  const list = useRef<HTMLUListElement>(null);
  const scroll = (dir: 1 | -1) => {
    const el = list.current;
    if (el) el.scrollBy({ left: dir * (el.firstElementChild?.clientWidth ?? 300) * 1.05, behavior: "smooth" });
  };

  return (
    <section id="natijalar" className="scroll-mt-24 py-8 lg:py-10">
      <Container className="2xl:max-w-[96rem]">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h2 className="flex items-center gap-2.5 text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
              <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
                <path d="M9 4h14v9a7 7 0 0 1-14 0V4Z" fill="#f59e0b" />
                <path d="M9 7H4v2a5 5 0 0 0 5 5M23 7h5v2a5 5 0 0 1-5 5" fill="none" stroke="#f59e0b" strokeWidth="2.2" />
                <path d="M14 19h4v4h-4zM10 24h12v4H10z" fill="#d97706" />
              </svg>
              O&apos;quvchilarimiz natijalari
            </h2>
            <p className="mt-1 text-muted">Biz bilan o&apos;qib, yuqori natijalarga erishgan abituriyentlar</p>
          </div>
          <div className="hidden gap-2 sm:flex">
            {([-1, 1] as const).map((dir) => (
              <button
                key={dir}
                type="button"
                onClick={() => scroll(dir)}
                aria-label={dir < 0 ? "Oldingi" : "Keyingi"}
                className="grid size-11 place-items-center rounded-full bg-white text-ink shadow-card ring-1 ring-brand-100 transition-colors hover:bg-brand-600 hover:text-white"
              >
                {dir < 0 ? <ChevronLeft className="size-5" /> : <ChevronRight className="size-5" />}
              </button>
            ))}
          </div>
        </div>

        <ul
          ref={list}
          className="-mx-4 mt-7 flex snap-x snap-mandatory scroll-px-4 sm:scroll-px-0 gap-4 overflow-x-auto px-4 pb-4 [scrollbar-width:none] sm:mx-0 sm:px-0"
        >
          {reviews.map((r) => (
            <li
              key={r.name}
              className="w-[85%] shrink-0 snap-start rounded-2xl bg-white p-5 shadow-card ring-1 ring-brand-100/70 sm:w-[calc((100%-1rem)/2)] lg:w-[calc((100%-3rem)/4)]"
            >
              <div className="flex items-center gap-3">
                <span className={`grid size-12 shrink-0 place-items-center rounded-full bg-gradient-to-br font-bold text-white ${r.tone}`}>
                  {r.name[0]}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-bold text-ink">{r.name}</p>
                  <p className="text-sm text-muted">
                    {r.subject} · <b className="font-bold text-brand-600">{r.score}</b>
                  </p>
                </div>
                <Quote className="size-7 shrink-0 text-brand-200" />
              </div>
              <p className="mt-4 leading-relaxed text-ink/80">&ldquo;{r.text}&rdquo;</p>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
