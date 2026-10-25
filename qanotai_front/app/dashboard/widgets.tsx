"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { getCatalogBooks, type CatalogBook } from "../_lib/api";
import { ArrowRight, BookOpen, CalendarCheck, ChevronDown, Clock, Target, TrendingUp } from "../_components/icons";
import {
  dailyGoal,
  weekDays,
  weeklyLessons,
  weeklySummary,
} from "./dashboard-data";

const card = "rounded-3xl bg-white shadow-card ring-1 ring-brand-100/70";

function SectionHead({ title, onMore, children }: { title: string; onMore?: () => void; children?: ReactNode }) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div>
        <h2 className="text-xl font-extrabold tracking-tight text-ink sm:text-[1.4rem]">{title}</h2>
        {children}
      </div>
      {onMore && (
        <button
          type="button"
          onClick={onMore}
          className="flex shrink-0 items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700"
        >
          Barchasini ko&apos;rish <ArrowRight className="size-4" />
        </button>
      )}
    </div>
  );
}

// ─── hero ────────────────────────────────────────────────────────────────────

export function WelcomeBanner({ firstName, onContinue }: { firstName: string; onContinue: () => void }) {
  return (
    <section className="relative overflow-hidden rounded-3xl shadow-card ring-1 ring-brand-100/70">
      <Image
        src="/images/dashboard-hero.webp"
        alt=""
        fill
        priority
        unoptimized // full-res artwork; Next's resize + re-encode softens it
        className="object-cover object-[78%_62%]"
      />
      {/* the left of the scene is bright sky; a light wash keeps the copy crisp on every width */}
      <div className="absolute inset-0 bg-gradient-to-r from-white/80 via-white/35 via-30% to-transparent to-50% max-sm:bg-white/55" />
      <div className="relative max-w-md px-6 py-8 sm:px-14 sm:py-12">
        <p className="text-lg font-semibold text-ink sm:text-xl">👋 Xush kelibsiz,</p>
        <p className="mt-1 bg-gradient-to-r from-brand-700 to-brand-500 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent sm:text-5xl">
          {firstName}!
        </p>
        <p className="mt-4 max-w-xs text-[15px] leading-relaxed text-ink/80">
          Bugun yangi bilimlar seni katta maqsadlaringga yaqinlashtiradi.
        </p>
        <button
          type="button"
          onClick={onContinue}
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-brand-600 px-7 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-brand-600/30 transition-colors hover:bg-brand-700"
        >
          Darslarni davom ettirish <ArrowRight className="size-4" />
        </button>
      </div>
    </section>
  );
}

// ─── books (covers) ──────────────────────────────────────────────────

export function SubjectShelf({ onOpen }: { onOpen: () => void }) {
  const [items, setItems] = useState<CatalogBook[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    getCatalogBooks()
      .then(setItems)
      .catch(() => setFailed(true));
  }, []);

  return (
    <section id="fanlar" className="scroll-mt-24">
      <SectionHead title="Asosiy fanlar va testlar" onMore={onOpen}>
        <p className="mt-1 text-sm text-muted">
          Milliy sertifikat va abituriyentlar uchun zarur bo&apos;lgan barcha fanlar, minglab testlar va batafsil yechimlar.
        </p>
      </SectionHead>

      {failed ? (
        <p className={`mt-5 px-5 py-8 text-center text-sm text-muted ${card}`}>Kitoblarni yuklab bo&apos;lmadi. Sahifani yangilang.</p>
      ) : items && items.length === 0 ? (
        <p className={`mt-5 px-5 py-8 text-center text-sm text-muted ${card}`}>Hozircha kitoblar qo&apos;shilmagan.</p>
      ) : (
        <ul className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 2xl:grid-cols-6">
          {(items ?? Array.from({ length: 6 }, () => null)).map((s, i) =>
            s ? (
              <li key={s.id}>
                <Link
                  href={`/dashboard/books/${s.id}`}
                  className={`group flex w-full flex-col overflow-hidden text-left transition hover:-translate-y-1 hover:shadow-lg ${card}`}
                >
                  <span className="relative block h-44 bg-gradient-to-b from-brand-50 to-white">
                    {s.cover_url ? (
                      <Image
                        src={s.cover_url}
                        alt={s.title}
                        fill
                        unoptimized // covers come from /api/media or /images; small files, served as-is
                        className="object-contain p-3 drop-shadow-xl transition-transform group-hover:scale-105"
                      />
                    ) : (
                      <BookOpen className="absolute inset-0 m-auto size-12 text-brand-300" />
                    )}
                  </span>
                  <span className="flex items-end gap-1.5 px-2.5 pb-3.5 pt-3">
                    <span className="min-w-0 flex-1">
                      <span className="line-clamp-2 text-sm font-bold leading-snug tracking-tight text-ink" title={s.title}>
                        {s.title}
                      </span>
                      <span className="mt-0.5 block text-xs text-muted">{s.subject}</span>
                      <span className="block text-xs font-semibold text-brand-600">
                        {s.tests > 0 ? `${s.tests} ta test` : "Testlar tez orada"}
                      </span>
                    </span>
                    <span className="grid size-6 shrink-0 place-items-center rounded-full bg-brand-50 text-brand-600 transition-colors group-hover:bg-brand-600 group-hover:text-white">
                      <ArrowRight className="size-4" />
                    </span>
                  </span>
                </Link>
              </li>
            ) : (
              // loading placeholder
              <li key={`ph-${i}`} className={`h-[15.5rem] animate-pulse bg-brand-50/60 ${card}`} />
            ),
          )}
        </ul>
      )}
    </section>
  );
}

// ─── right column ────────────────────────────────────────────────────────────

export function DailyGoal() {
  const { lessonsDone, lessonsTotal, tasks } = dailyGoal;
  const r = 44;
  const circumference = 2 * Math.PI * r;
  return (
    <section className={`p-6 ${card}`}>
      <h2 className="text-lg font-extrabold text-ink">Bugungi maqsad</h2>
      <div className="mt-5 flex items-center gap-4">
        <div className="relative size-24 shrink-0">
          <svg viewBox="0 0 100 100" className="size-full -rotate-90">
            <circle cx="50" cy="50" r={r} fill="none" stroke="currentColor" strokeWidth="8" className="text-brand-50" />
            <circle
              cx="50"
              cy="50"
              r={r}
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - lessonsDone / lessonsTotal)}
              className="text-brand-600"
            />
          </svg>
          <div className="absolute inset-0 grid place-content-center text-center">
            <p className="text-2xl font-extrabold text-ink">
              {lessonsDone}
              <span className="text-lg text-muted">/{lessonsTotal}</span>
            </p>
            <p className="text-xs text-muted">dars</p>
          </div>
        </div>
        <ul className="flex flex-col gap-3">
          {tasks.map((t) => (
            <li key={t.label} className="flex items-center gap-2 whitespace-nowrap text-[13px] text-ink/85">
              <span
                className={`grid size-5 shrink-0 place-items-center rounded-full ${
                  t.done ? "bg-emerald-500 text-white" : "ring-2 ring-brand-100"
                }`}
              >
                {t.done && (
                  <svg viewBox="0 0 24 24" className="size-3" fill="none" stroke="currentColor" strokeWidth={3.5} aria-hidden="true">
                    <path d="m5 12 5 5 9-10" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </span>
              <span className={t.done ? "" : "text-muted"}>{t.label}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

const summaryIcon = {
  lessons: { Icon: CalendarCheck, tone: "bg-brand-50 text-brand-600" },
  accuracy: { Icon: Target, tone: "bg-rose-50 text-rose-500" },
  time: { Icon: Clock, tone: "bg-sky-50 text-sky-600" },
  growth: { Icon: TrendingUp, tone: "bg-indigo-50 text-indigo-600" },
};

export function WeeklyStats() {
  const periods = Object.keys(weeklyLessons);
  const [period, setPeriod] = useState(periods[0]);
  const values = weeklyLessons[period];
  const max = 8;
  const peak = values.indexOf(Math.max(...values));

  return (
    <section className={`p-6 ${card}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-extrabold text-ink">Statistika</h2>
        <label className="relative">
          <span className="sr-only">Davr</span>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="appearance-none rounded-xl bg-white py-2 pl-3 pr-8 text-sm font-semibold text-ink ring-1 ring-brand-100 outline-none focus:ring-brand-400"
          >
            {periods.map((p) => (
              <option key={p}>{p}</option>
            ))}
          </select>
          <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
        </label>
      </div>

      {/* bar chart: lessons per day */}
      <div className="mt-6 flex gap-2">
        <div className="flex h-36 flex-col justify-between pb-5 text-right text-[11px] text-muted">
          {[8, 6, 4, 2, 0].map((n) => (
            <span key={n} className="leading-none">
              {n}
            </span>
          ))}
        </div>
        <div className="relative flex h-36 flex-1 items-end justify-between gap-2 pb-5">
          {[0, 1, 2, 3].map((i) => (
            <span key={i} className="absolute inset-x-0 border-t border-dashed border-brand-50" style={{ top: `${i * 25}%` }} />
          ))}
          {values.map((v, i) => (
            <div key={weekDays[i]} className="relative flex h-full flex-1 flex-col items-center justify-end">
              {i === peak && (
                <span className="absolute z-10 whitespace-nowrap rounded-md bg-ink px-2 py-1 text-[11px] font-semibold text-white" style={{ bottom: `calc(${(v / max) * 100}% + 6px)` }}>
                  {v} dars
                </span>
              )}
              <span
                className={`w-full max-w-5 rounded-t-md ${i === peak ? "bg-brand-600" : "bg-gradient-to-t from-brand-400 to-brand-300"}`}
                style={{ height: `${(v / max) * 100}%` }}
                title={`${weekDays[i]}: ${v} dars`}
              />
              <span className="absolute -bottom-5 text-[11px] text-muted">{weekDays[i]}</span>
            </div>
          ))}
        </div>
      </div>

      <dl className="mt-6 grid grid-cols-2 gap-x-4 gap-y-5 border-t border-brand-50 pt-5">
        {weeklySummary.map((s) => {
          const { Icon, tone } = summaryIcon[s.kind];
          return (
            <div key={s.kind} className="flex items-center gap-3">
              <span className={`grid size-10 shrink-0 place-items-center rounded-xl ${tone}`}>
                <Icon className="size-5" />
              </span>
              <div>
                <dd className="text-lg font-extrabold leading-tight text-ink">{s.value}</dd>
                <dt className="text-xs text-muted">{s.label}</dt>
              </div>
            </div>
          );
        })}
      </dl>
    </section>
  );
}

export function QuoteCard() {
  return (
    <section className="relative min-h-72 overflow-hidden rounded-3xl bg-gradient-to-br from-sky-200 via-sky-100 to-amber-50 p-6 shadow-card ring-1 ring-brand-100/70">
      <div className="pointer-events-none absolute -left-10 -top-10 size-40 rounded-full bg-white/60 blur-2xl" />
      <blockquote className="relative max-w-[12rem] text-lg font-semibold leading-snug text-ink">
        “Har bir yangi bilim seni maqsadingga yana bir qanot yaqinlashtiradi.”
        <footer className="mt-3 text-sm font-medium text-muted">— IQ24</footer>
      </blockquote>
      <Image
        src="/images/books/stack.webp"
        alt=""
        width={722}
        height={560}
        sizes="200px"
       
        className="pointer-events-none absolute -bottom-3 -right-3 w-[52%] max-w-48 drop-shadow-xl"
      />
    </section>
  );
}
