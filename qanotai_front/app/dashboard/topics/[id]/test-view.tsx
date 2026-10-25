"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { ApiError, getTopicTest, submitTopicTest, type TestResult, type TopicTest } from "../../../_lib/api";
import { ArrowRight, BarChart, Bookmark, Check, ChevronDown, ChevronLeft, Clock, Close, FileText, Star, Target, TrendingUp } from "../../../_components/icons";
import { Solutions } from "../../../_components/solutions";
import { MathText } from "../../../_components/math-text";
import { card, LEVEL, Spinner } from "../../_components/student-ui";

const LETTERS = "ABCDEF";

function clock(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function LevelBadge({ difficulty }: { difficulty: string }) {
  const l = LEVEL[difficulty] ?? LEVEL.medium;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${l.badge}`}>
      <span className={`size-1.5 rounded-full ${l.dot}`} /> {l.label}
    </span>
  );
}

function QuestionImage({ src, alt }: { src: string; alt: string }) {
  return (
    <div className="relative mt-4 h-72 w-full max-w-xl overflow-hidden rounded-2xl bg-white ring-1 ring-brand-100 sm:h-80">
      <Image src={src} alt={alt} fill unoptimized className="object-contain p-2" />
    </div>
  );
}

// ─── taking the test ─────────────────────────────────────────────────────────

function ViewIcon({ mode, className = "" }: { mode: "all" | "single"; className?: string }) {
  return mode === "all" ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true" className={className}>
      <rect x="4" y="3.5" width="16" height="5" rx="1.5" />
      <rect x="4" y="10" width="16" height="5" rx="1.5" />
      <rect x="4" y="16.5" width="16" height="4" rx="1.5" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" aria-hidden="true" className={className}>
      <rect x="4" y="4" width="16" height="16" rx="2.5" />
      <path d="M8 9h8M8 13h5" />
    </svg>
  );
}

function QuestionBody({
  q,
  n,
  picked,
  onPick,
  flagged,
  onFlag,
  large,
}: {
  q: TopicTest["questions"][number];
  n: number;
  picked: number | undefined;
  onPick: (j: number) => void;
  flagged: boolean;
  onFlag: () => void;
  large: boolean;
}) {
  const level = LEVEL[q.difficulty] ?? LEVEL.medium;
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-lg bg-brand-50 px-3 py-1 text-sm font-bold text-brand-700">{n}-savol</span>
        <span className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1 text-sm font-semibold ring-1 ${level.badge}`}>
          <span className={`size-1.5 rounded-full ${level.dot}`} /> {level.label}
        </span>
        <button
          type="button"
          onClick={onFlag}
          aria-pressed={flagged}
          className={`ml-auto inline-flex items-center gap-1.5 rounded-lg px-3 py-1 text-sm font-semibold transition-colors ${
            flagged ? "bg-rose-50 text-rose-600 ring-1 ring-rose-200" : "text-muted hover:bg-slate-100 hover:text-ink"
          }`}
        >
          <Bookmark className="size-4" /> {flagged ? "Belgilangan" : "Belgilash"}
        </button>
      </div>
      <p className={`mt-4 whitespace-pre-line font-bold leading-relaxed text-ink ${large ? "text-xl sm:text-[1.6rem]" : "text-lg sm:text-xl"}`}>
        <MathText text={q.text} />
      </p>
      {q.image_url && <QuestionImage src={q.image_url} alt={`${n}-savol rasmi`} />}
      <div className="mt-5 flex flex-col gap-3" role="radiogroup" aria-label={`${n}-savol javoblari`}>
        {q.options.map((o, j) => {
          const on = picked === j;
          return (
            <button
              key={j}
              type="button"
              role="radio"
              aria-checked={on}
              onClick={() => onPick(j)}
              className={`flex items-center gap-4 rounded-2xl px-5 text-left transition ${large ? "py-4 text-lg" : "py-3 text-base"} ${
                on ? "bg-brand-50/70 ring-2 ring-brand-500" : "bg-white ring-1 ring-brand-100 hover:bg-brand-50/40 hover:ring-brand-200"
              }`}
            >
              <span className={`grid size-6 shrink-0 place-items-center rounded-full ring-2 ${on ? "ring-brand-600" : "ring-slate-300"}`}>
                {on && <span className="size-3 rounded-full bg-brand-600" />}
              </span>
              <span className={`grid size-10 shrink-0 place-items-center rounded-xl text-base font-bold ${on ? "bg-brand-600 text-white" : "bg-brand-50 text-brand-700"}`}>
                {LETTERS[j]}
              </span>
              <span className={`min-w-0 flex-1 ${on ? "font-semibold text-brand-900" : "text-ink"}`}>
                <MathText text={o} />
              </span>
            </button>
          );
        })}
      </div>
    </>
  );
}

function Runner({ test, onFinish }: { test: TopicTest; onFinish: (answers: Record<number, number | null>, seconds: number) => Promise<void> }) {
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [flagged, setFlagged] = useState<Set<number>>(new Set());
  const [seconds, setSeconds] = useState(0);
  const [listOpen, setListOpen] = useState(true);
  const [mode, setMode] = useState<"all" | "single">("all");
  const [confirming, setConfirming] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const startedAt = useRef(0); // set when the runner mounts

  useEffect(() => {
    startedAt.current = Date.now();
    const t = setInterval(() => setSeconds(Math.floor((Date.now() - startedAt.current) / 1000)), 1000);
    return () => clearInterval(t);
  }, []);

  // in "all" mode the current question follows the scroll position
  useEffect(() => {
    if (mode !== "all") return;
    const els = test.questions.map((item) => document.getElementById(`q-${item.id}`)).filter((el): el is HTMLElement => !!el);
    const io = new IntersectionObserver(
      (entries) => {
        const top = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (top) setIndex(Number((top.target as HTMLElement).dataset.index));
      },
      { rootMargin: "-25% 0px -65% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [mode, test.questions]);

  const q = test.questions[index];
  const total = test.questions.length;
  const answered = Object.keys(answers).length;
  const last = index === total - 1;
  const suggestedMinutes = total; // about a minute per question
  const level = LEVEL[q.difficulty] ?? LEVEL.medium;

  const pick = (id: number, j: number) => setAnswers((a) => ({ ...a, [id]: j }));
  const flip = (id: number) =>
    setFlagged((s) => {
      const next = new Set(s);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  function goTo(i: number) {
    setIndex(i);
    if (mode === "all") document.getElementById(`q-${test.questions[i].id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function switchMode(m: "all" | "single") {
    setMode(m);
    if (m === "all") requestAnimationFrame(() => document.getElementById(`q-${q.id}`)?.scrollIntoView({ block: "start" }));
    else window.scrollTo({ top: 0 });
  }

  async function finish() {
    setSending(true);
    setError("");
    try {
      const all: Record<number, number | null> = {};
      for (const item of test.questions) all[item.id] = answers[item.id] ?? null;
      await onFinish(all, Math.floor((Date.now() - startedAt.current) / 1000));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Natijani yuborib bo'lmadi. Qayta urinib ko'ring.");
      setSending(false);
    }
  }

  const finishButton = (label: string) => (
    <button
      type="button"
      onClick={() => setConfirming(true)}
      className="inline-flex items-center gap-2 rounded-2xl bg-emerald-500 px-7 py-3.5 text-base font-bold text-white shadow-lg shadow-emerald-500/25 hover:bg-emerald-600"
    >
      <Check className="size-5" strokeWidth={3} /> {label}
    </button>
  );

  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="flex min-w-0 flex-col gap-5">
        {/* header */}
        <section className={`p-6 sm:p-8 ${card}`}>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <span className="inline-block rounded-lg bg-brand-50 px-3 py-1 text-xs font-bold uppercase tracking-wider text-brand-700">
                {test.topic_number ? `${test.topic_number}-mavzu` : "Takrorlash"}
              </span>
              <h1 className="mt-3 text-2xl font-extrabold leading-snug tracking-tight text-ink sm:text-[1.75rem]">{test.topic_title}</h1>
            </div>
            <div className="flex flex-col items-end gap-3">
              <div className="flex items-center gap-2">
                <div className="flex rounded-2xl bg-slate-100 p-1" role="group" aria-label="Ko'rinish">
                  {(["all", "single"] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => switchMode(m)}
                      aria-pressed={mode === m}
                      title={m === "all" ? "Barcha savollar" : "Bittalab"}
                      className={`grid size-9 place-items-center rounded-xl transition ${mode === m ? "bg-white text-brand-600 shadow" : "text-muted hover:text-ink"}`}
                    >
                      <ViewIcon mode={m} className="size-5" />
                      <span className="sr-only">{m === "all" ? "Barcha savollar" : "Bittalab"}</span>
                    </button>
                  ))}
                </div>
                <span className="inline-flex items-center gap-2 rounded-2xl bg-brand-50 px-4 py-2.5 text-lg font-bold tabular-nums text-brand-700">
                  <Clock className="size-5" /> {clock(seconds)}
                </span>
              </div>
              <div className="w-56">
                <p className="text-right text-sm text-muted">{mode === "all" ? `${answered}/${total} javob` : `${index + 1}/${total} savol`}</p>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-brand-50">
                  <div
                    className="h-full rounded-full bg-brand-600 transition-all"
                    style={{ width: `${((mode === "all" ? answered : index + 1) / total) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {mode === "single" && (
            <div className="mt-6 border-t border-brand-50 pt-6">
              <QuestionBody
                q={q}
                n={index + 1}
                picked={answers[q.id]}
                onPick={(j) => pick(q.id, j)}
                flagged={flagged.has(q.id)}
                onFlag={() => flip(q.id)}
                large
              />
              <div className="mt-8 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={() => setIndex((i) => Math.max(0, i - 1))}
                  disabled={index === 0}
                  className="inline-flex items-center gap-2 rounded-2xl px-6 py-3.5 text-base font-semibold text-brand-600 ring-1 ring-brand-200 hover:bg-brand-50 disabled:opacity-40"
                >
                  <ArrowRight className="size-5 rotate-180" /> Oldingi
                </button>
                {last ? (
                  finishButton("Yakunlash")
                ) : (
                  <button
                    type="button"
                    onClick={() => setIndex((i) => Math.min(total - 1, i + 1))}
                    className="inline-flex items-center gap-2 rounded-2xl bg-brand-600 px-7 py-3.5 text-base font-bold text-white shadow-lg shadow-brand-600/25 hover:bg-brand-700"
                  >
                    Keyingi <ArrowRight className="size-5" />
                  </button>
                )}
              </div>
            </div>
          )}
        </section>

        {mode === "all" && (
          <>
            {test.questions.map((item, i) => (
              <section key={item.id} id={`q-${item.id}`} data-index={i} className={`scroll-mt-24 p-6 sm:p-7 ${card}`}>
                <QuestionBody
                  q={item}
                  n={i + 1}
                  picked={answers[item.id]}
                  onPick={(j) => {
                    pick(item.id, j);
                    setIndex(i);
                  }}
                  flagged={flagged.has(item.id)}
                  onFlag={() => flip(item.id)}
                  large={false}
                />
              </section>
            ))}
            <div className={`flex flex-wrap items-center justify-between gap-3 p-6 ${card}`}>
              <p className="text-sm text-muted">
                {answered}/{total} savolga javob berildi{flagged.size > 0 && ` · ${flagged.size} ta belgilangan`}
              </p>
              {finishButton("Testni yakunlash")}
            </div>
          </>
        )}
      </div>

      {/* side panel */}
      <aside className={`p-6 lg:sticky lg:top-24 ${card}`}>
        <button type="button" onClick={() => setListOpen((v) => !v)} aria-expanded={listOpen} className="flex w-full items-center justify-between">
          <h2 className="text-lg font-extrabold text-ink">Savollar ro&apos;yxati</h2>
          <ChevronDown className={`size-5 text-ink/70 transition-transform ${listOpen ? "rotate-180" : ""}`} />
        </button>

        {listOpen && (
          <>
            <div className="mt-5 grid grid-cols-5 gap-2.5">
              {test.questions.map((item, i) => {
                const cur = i === index;
                const mark = flagged.has(item.id);
                const done = answers[item.id] !== undefined;
                const tone = cur
                  ? "bg-brand-600 text-white shadow-lg shadow-brand-600/30"
                  : mark
                    ? "bg-rose-100 text-rose-700 ring-1 ring-rose-200"
                    : done
                      ? "bg-emerald-100 text-emerald-700 ring-1 ring-emerald-200"
                      : "bg-white text-ink/70 ring-1 ring-brand-100 hover:bg-brand-50";
                return (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => goTo(i)}
                    aria-label={`${i + 1}-savol`}
                    aria-current={cur ? "step" : undefined}
                    className={`grid aspect-square place-items-center rounded-xl text-base font-bold transition ${tone}`}
                  >
                    {i + 1}
                  </button>
                );
              })}
            </div>
            <ul className="mt-5 flex flex-col gap-2.5 text-sm text-ink/75">
              {[
                ["bg-brand-600", "Joriy savol"],
                ["bg-brand-100", "Javob berilmagan"],
                ["bg-emerald-400", "Javob berilgan"],
                ["bg-rose-300", "Belgilangan"],
              ].map(([dot, label]) => (
                <li key={label} className="flex items-center gap-3">
                  <span className={`size-4 rounded-full ${dot}`} /> {label}
                </li>
              ))}
            </ul>
          </>
        )}

        <div className="mt-6 border-t border-brand-50 pt-6">
          <h2 className="text-lg font-extrabold text-ink">Test haqida</h2>
          <ul className="mt-4 flex flex-col gap-3.5 text-[15px] text-ink/80">
            <li className="flex items-center gap-3">
              <FileText className="size-5 shrink-0 text-ink/60" /> {total} savol · {answered} ta javob berildi
            </li>
            <li className="flex items-center gap-3">
              <Clock className="size-5 shrink-0 text-ink/60" /> Tavsiya etilgan vaqt: {suggestedMinutes} daqiqa
            </li>
            <li className="flex items-start gap-3">
              <BarChart className="mt-0.5 size-5 shrink-0 text-ink/60" /> Mavzu: {test.topic_title}
            </li>
            <li className="flex items-center gap-3">
              <Star className="size-5 shrink-0 text-ink/60" /> Qiyinchilik:
              <span className={`rounded-lg px-2.5 py-0.5 text-sm font-semibold ring-1 ${level.badge}`}>{level.label}</span>
            </li>
          </ul>
          <button
            type="button"
            onClick={() => setConfirming(true)}
            className="mt-6 w-full rounded-2xl bg-emerald-50 py-3 text-sm font-bold text-emerald-700 ring-1 ring-emerald-200 transition-colors hover:bg-emerald-100"
          >
            Testni yakunlash
          </button>
        </div>
      </aside>

      {confirming && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-ink/45 p-4 backdrop-blur-sm" onMouseDown={(e) => e.target === e.currentTarget && !sending && setConfirming(false)}>
          <div role="alertdialog" aria-modal="true" className="w-full max-w-sm animate-[dialog-in_.2s_ease-out] rounded-3xl bg-white p-7 text-center shadow-2xl">
            <h2 className="text-xl font-extrabold text-ink">Testni yakunlaysizmi?</h2>
            <p className="mt-2 text-muted">
              {answered} / {total} savolga javob berdingiz.
              {answered < total && ` ${total - answered} ta savol javobsiz qoladi.`}
              {flagged.size > 0 && ` ${flagged.size} ta savol belgilangan.`}
            </p>
            {error && <p className="mt-3 rounded-xl bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
            <div className="mt-6 grid grid-cols-2 gap-3">
              <button type="button" onClick={() => setConfirming(false)} disabled={sending} className="rounded-xl bg-slate-100 py-3 text-sm font-semibold text-ink/80 hover:bg-slate-200 disabled:opacity-50">
                Davom etish
              </button>
              <button type="button" onClick={finish} disabled={sending} className="rounded-xl bg-emerald-500 py-3 text-sm font-bold text-white hover:bg-emerald-600 disabled:opacity-70">
                {sending ? "Tekshirilmoqda…" : "Yakunlash"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── analysis ────────────────────────────────────────────────────────────────

function verdict(percent: number) {
  if (percent >= 90) return { title: "A'lo natija!", text: "Mavzuni juda yaxshi o'zlashtirgansiz. Keyingi mavzuga o'ting.", tone: "text-emerald-600", ring: "#10b981" };
  if (percent >= 70) return { title: "Yaxshi natija!", text: "Asosiy qismini bilasiz. Xato qilingan savollar yechimini ko'rib chiqing.", tone: "text-brand-600", ring: "#1f55f5" };
  if (percent >= 50) return { title: "Yomon emas", text: "Mavzuni yana bir bor takrorlab, testni qayta ishlang.", tone: "text-amber-600", ring: "#f59e0b" };
  return { title: "Takrorlash kerak", text: "Mavzu nazariyasini qayta o'qing va yechimlarni diqqat bilan ko'rib chiqing.", tone: "text-rose-600", ring: "#f43f5e" };
}

function Analysis({ test, result, onRetry }: { test: TopicTest; result: TestResult; onRetry: () => void }) {
  const [filter, setFilter] = useState<"all" | "wrong">(result.correct === result.total ? "all" : "wrong");
  const [openIds, setOpenIds] = useState<Set<number>>(new Set());
  const v = verdict(result.percent);
  const r = 52;
  const circumference = 2 * Math.PI * r;
  const avg = result.total ? Math.round(result.duration_seconds / result.total) : 0;
  const weakest = [...result.by_level].filter((l) => l.total > 0).sort((a, b) => a.correct / a.total - b.correct / b.total)[0];
  const items = result.review.map((item, i) => ({ item, n: i + 1 })).filter(({ item }) => filter === "all" || !item.is_correct);
  const delta = result.previous_percent !== null ? result.percent - result.previous_percent : null;

  return (
    <div className="flex flex-col gap-5">
      {/* score */}
      <section className={`flex flex-col items-center gap-6 p-6 sm:flex-row sm:p-8 ${card}`}>
        <div className="relative size-36 shrink-0">
          <svg viewBox="0 0 120 120" className="size-full -rotate-90">
            <circle cx="60" cy="60" r={r} fill="none" stroke="#eef4ff" strokeWidth="11" />
            <circle
              cx="60"
              cy="60"
              r={r}
              fill="none"
              stroke={v.ring}
              strokeWidth="11"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - result.percent / 100)}
              className="transition-all duration-700"
            />
          </svg>
          <div className="absolute inset-0 grid place-content-center text-center">
            <p className="text-3xl font-extrabold text-ink">{result.percent}%</p>
            <p className="text-xs text-muted">
              {result.correct}/{result.total}
            </p>
          </div>
        </div>
        <div className="min-w-0 flex-1 text-center sm:text-left">
          <p className="text-xs font-bold uppercase tracking-wider text-muted">{test.topic_title}</p>
          <h1 className={`mt-1 text-2xl font-extrabold sm:text-3xl ${v.tone}`}>{v.title}</h1>
          <p className="mt-2 text-muted">{v.text}</p>
          {delta !== null && (
            <p className={`mt-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${delta >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>
              <TrendingUp className="size-4" /> Oldingi urinish: {result.previous_percent}% ({delta >= 0 ? "+" : ""}
              {delta}%)
            </p>
          )}
        </div>
      </section>

      {/* numbers */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "To'g'ri", value: result.correct, tone: "bg-emerald-50 text-emerald-600", Icon: Check },
          { label: "Noto'g'ri", value: result.wrong, tone: "bg-rose-50 text-rose-600", Icon: Close },
          { label: "Javobsiz", value: result.skipped, tone: "bg-slate-100 text-slate-500", Icon: Target },
          { label: "Sarflangan vaqt", value: clock(result.duration_seconds), tone: "bg-brand-50 text-brand-600", Icon: Clock },
        ].map((s) => (
          <div key={s.label} className={`flex items-center gap-3 p-4 ${card}`}>
            <span className={`grid size-11 shrink-0 place-items-center rounded-2xl ${s.tone}`}>
              <s.Icon className="size-5" />
            </span>
            <div>
              <p className="text-xl font-extrabold text-ink tabular-nums">{s.value}</p>
              <p className="text-xs text-muted">{s.label}</p>
            </div>
          </div>
        ))}
      </section>

      {/* by level + advice */}
      <section className={`grid gap-6 p-6 sm:grid-cols-[1.2fr_1fr] ${card}`}>
        <div>
          <h2 className="text-lg font-extrabold text-ink">Daraja bo&apos;yicha</h2>
          <ul className="mt-4 flex flex-col gap-3.5">
            {result.by_level.map((l) => {
              const p = l.total ? Math.round((l.correct / l.total) * 100) : 0;
              const s = LEVEL[l.difficulty] ?? LEVEL.medium;
              return (
                <li key={l.difficulty} className="grid grid-cols-[4.5rem_1fr_4.5rem] items-center gap-3 text-sm">
                  <span className="flex items-center gap-2 font-semibold text-ink">
                    <span className={`size-2 rounded-full ${s.dot}`} /> {s.label}
                  </span>
                  <span className="h-2.5 overflow-hidden rounded-full bg-slate-100">
                    <span className={`block h-full rounded-full ${s.bar}`} style={{ width: `${p}%` }} />
                  </span>
                  <span className="text-right tabular-nums text-muted">
                    {l.correct}/{l.total} · {p}%
                  </span>
                </li>
              );
            })}
          </ul>
        </div>
        <div className="rounded-2xl bg-brand-50/60 p-4 text-sm leading-relaxed text-ink/85">
          <p className="font-bold text-ink">Tavsiyalar</p>
          <ul className="mt-2 list-disc space-y-1.5 pl-4">
            {weakest && weakest.correct < weakest.total && (
              <li>
                Eng ko&apos;p qiynalgan daraja — <b>{(LEVEL[weakest.difficulty] ?? LEVEL.medium).label.toLowerCase()}</b> savollar. Shu turdagi
                misollarni ko&apos;proq ishlang.
              </li>
            )}
            {result.skipped > 0 && <li>{result.skipped} ta savol javobsiz qoldi — taxmin qilib bo&apos;lsa ham javob belgilashni odat qiling.</li>}
            <li>Har bir savolga o&apos;rtacha {avg} soniya sarfladingiz{avg > 120 ? " — imtihonda vaqt yetmasligi mumkin, tezlikni oshiring." : "."}</li>
            {result.wrong > 0 && <li>Pastdagi noto&apos;g&apos;ri javoblarning yechimini o&apos;qib chiqing.</li>}
            <li>Eng yaxshi natijangiz: {result.best_percent}%.</li>
          </ul>
        </div>
      </section>

      {/* question by question */}
      <section className={`p-5 sm:p-6 ${card}`}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-extrabold text-ink">Savollar tahlili</h2>
          <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
            {(
              [
                ["wrong", `Xatolar (${result.total - result.correct})`],
                ["all", `Barchasi (${result.total})`],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                onClick={() => setFilter(k)}
                aria-pressed={filter === k}
                className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition ${filter === k ? "bg-white text-ink shadow" : "text-muted hover:text-ink"}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {items.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted">Xato yo&apos;q — barcha savollarga to&apos;g&apos;ri javob berdingiz! 🎉</p>
        ) : (
          <ol className="mt-4 flex flex-col gap-3">
            {items.map(({ item, n }) => {
              const open = openIds.has(item.id);
              const status = item.is_correct ? "correct" : item.chosen === null ? "skipped" : "wrong";
              return (
                <li
                  key={item.id}
                  className={`rounded-2xl p-4 ring-1 ${status === "correct" ? "ring-emerald-100" : status === "wrong" ? "bg-rose-50/30 ring-rose-100" : "bg-slate-50/60 ring-slate-200"}`}
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`grid size-8 shrink-0 place-items-center rounded-lg text-sm font-bold text-white ${
                        status === "correct" ? "bg-emerald-500" : status === "wrong" ? "bg-rose-500" : "bg-slate-400"
                      }`}
                    >
                      {n}
                    </span>
                    <LevelBadge difficulty={item.difficulty} />
                    <span className={`ml-auto text-xs font-bold ${status === "correct" ? "text-emerald-600" : status === "wrong" ? "text-rose-600" : "text-slate-500"}`}>
                      {status === "correct" ? "To'g'ri" : status === "wrong" ? "Noto'g'ri" : "Javob berilmagan"}
                    </span>
                  </div>
                  <p className="mt-2.5 whitespace-pre-line font-semibold leading-relaxed text-ink">
                    <MathText text={item.text} />
                  </p>
                  {item.image_url && <QuestionImage src={item.image_url} alt={`${n}-savol rasmi`} />}
                  <ul className="mt-3 grid gap-2 sm:grid-cols-2">
                    {item.options.map((o, j) => {
                      const right = j === item.correct;
                      const mine = j === item.chosen;
                      return (
                        <li
                          key={j}
                          className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm ring-1 ${
                            right ? "bg-emerald-50 font-semibold text-emerald-800 ring-emerald-200" : mine ? "bg-rose-50 text-rose-800 ring-rose-200" : "bg-white text-ink/75 ring-brand-100"
                          }`}
                        >
                          <span className={`grid size-6 shrink-0 place-items-center rounded-md text-xs font-bold ${right ? "bg-emerald-500 text-white" : mine ? "bg-rose-500 text-white" : "bg-slate-100 text-muted"}`}>
                            {LETTERS[j]}
                          </span>
                          <span className="min-w-0 flex-1">
                            <MathText text={o} />
                          </span>
                          {right && <span className="text-xs font-bold text-emerald-600">To&apos;g&apos;ri javob</span>}
                          {mine && !right && <span className="text-xs font-bold text-rose-600">Sizning javobingiz</span>}
                        </li>
                      );
                    })}
                  </ul>
                  {(item.explanation || item.solution || item.explainer) && (
                    <div className="mt-3">
                      <button
                        type="button"
                        onClick={() =>
                          setOpenIds((s) => {
                            const next = new Set(s);
                            if (next.has(item.id)) next.delete(item.id);
                            else next.add(item.id);
                            return next;
                          })
                        }
                        aria-expanded={open}
                        className="inline-flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700"
                      >
                        Yechimni ko&apos;rish <ChevronDown className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
                      </button>
                      {open &&
                        (item.solution || item.explainer ? (
                          <div className="mt-3">
                            <Solutions solution={item.solution} explainer={item.explainer} />
                          </div>
                        ) : (
                          <p className="mt-2 rounded-xl bg-brand-50/70 px-4 py-3 text-sm leading-relaxed text-ink/85">
                            <MathText text={item.explanation ?? ""} />
                          </p>
                        ))}
                    </div>
                  )}
                </li>
              );
            })}
          </ol>
        )}
      </section>

      <div className="flex flex-wrap justify-center gap-3 pb-6">
        <button type="button" onClick={onRetry} className="rounded-xl px-5 py-3 text-sm font-semibold text-brand-600 ring-1 ring-brand-200 hover:bg-brand-50">
          Qayta ishlash
        </button>
        <Link href={`/dashboard/books/${test.book_id}`} className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-brand-600/25 hover:bg-brand-700">
          Mavzularga qaytish <ArrowRight className="size-4" />
        </Link>
      </div>
    </div>
  );
}

export function TestView() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [test, setTest] = useState<TopicTest | null>(null);
  const [result, setResult] = useState<TestResult | null>(null);
  const [error, setError] = useState("");
  const [round, setRound] = useState(0); // bumps on "Qayta ishlash" to remount a fresh runner

  useEffect(() => {
    getTopicTest(Number(id))
      .then(setTest)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) router.replace("/?login=1");
        else setError(e instanceof ApiError ? e.message : "Testni yuklab bo'lmadi");
      });
  }, [id, router]);

  return (
    <div className={`mx-auto flex flex-col gap-5 ${result ? "max-w-4xl" : "max-w-7xl"}`}>
      <Link
        href={test ? `/dashboard/books/${test.book_id}` : "/dashboard"}
        className="inline-flex w-fit items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700"
      >
        <ChevronLeft className="size-4" /> {test ? test.book_title : "Bosh sahifa"}
      </Link>
      {error ? (
        <p className={`p-8 text-center text-muted ${card}`}>{error}</p>
      ) : !test ? (
        <Spinner />
      ) : result ? (
        <Analysis
          test={test}
          result={result}
          onRetry={() => {
            setResult(null);
            setRound((r) => r + 1);
            window.scrollTo({ top: 0 });
          }}
        />
      ) : (
        <Runner
          key={round}
          test={test}
          onFinish={async (answers, seconds) => {
            setResult(await submitTopicTest(test.topic_id, answers, seconds));
            window.scrollTo({ top: 0 });
          }}
        />
      )}
    </div>
  );
}
