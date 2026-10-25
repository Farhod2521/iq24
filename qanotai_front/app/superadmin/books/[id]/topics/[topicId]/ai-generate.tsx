"use client";

import { MathText } from "../../../../../_components/math-text";
import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import { adminApi, type AiStatus, type Difficulty, type QuestionInput } from "../../../../../_lib/admin-api";
import { ApiError } from "../../../../../_lib/api";
import { Check, Sparkles } from "../../../../../_components/icons";
import { Field, inputClass, Modal, primaryButton } from "../../../../_components/ui";

const LETTERS = "ABCDEF";
const LEVELS: { value: Difficulty | "mixed"; label: string; dot?: string }[] = [
  { value: "easy", label: "Oson", dot: "bg-emerald-500" },
  { value: "medium", label: "O'rta", dot: "bg-amber-500" },
  { value: "hard", label: "Qiyin", dot: "bg-rose-500" },
  { value: "mixed", label: "Aralash" },
];
const BADGE: Record<Difficulty, string> = {
  easy: "bg-emerald-50 text-emerald-700 ring-emerald-100",
  medium: "bg-amber-50 text-amber-700 ring-amber-100",
  hard: "bg-rose-50 text-rose-700 ring-rose-100",
};
const LABEL: Record<Difficulty, string> = { easy: "Oson", medium: "O'rta", hard: "Qiyin" };

function Stepper({
  label,
  hint,
  value,
  onChange,
  min,
  max,
}: {
  label: string;
  hint: string;
  value: number;
  onChange: Dispatch<SetStateAction<number>>;
  min: number;
  max: number;
}) {
  const clamp = (v: number) => Math.min(max, Math.max(min, v));
  const set = (v: number) => onChange(clamp(v));
  const step = (d: number) => onChange((v) => clamp(v + d)); // functional, so quick repeated clicks all count
  return (
    <Field label={label} hint={hint}>
      <div className="flex items-center gap-2">
        <button type="button" onClick={() => step(-1)} className="grid size-11 shrink-0 place-items-center rounded-xl bg-slate-100 text-lg font-bold text-ink hover:bg-slate-200" aria-label={`${label}: kamaytirish`}>
          −
        </button>
        <input
          className={`${inputClass} text-center text-lg font-bold`}
          inputMode="numeric"
          value={value}
          onChange={(e) => set(Number(e.target.value.replace(/\D/g, "")) || 0)}
          aria-label={label}
        />
        <button type="button" onClick={() => step(1)} className="grid size-11 shrink-0 place-items-center rounded-xl bg-slate-100 text-lg font-bold text-ink hover:bg-slate-200" aria-label={`${label}: ko'paytirish`}>
          +
        </button>
      </div>
    </Field>
  );
}

/** An SVG figure from a draft, drawn through <img> so nothing inside it can run. */
function Figure({ svg, className = "" }: { svg: string; className?: string }) {
  // eslint-disable-next-line @next/next/no-img-element -- inline data URI, nothing for next/image to optimise
  return <img src={`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`} alt="Chizma" className={className} />;
}

type Step =
  | { kind: "form" }
  | { kind: "loading" }
  | { kind: "review"; drafts: QuestionInput[]; host: string; model: string; tokens: number; warning: string };

/** Claude drafts tests for the topic; the admin reviews them and saves the ones to keep. */
export function AiGenerateModal({
  topicId,
  topicTitle,
  onClose,
  onSaved,
}: {
  topicId: number;
  topicTitle: string;
  onClose: () => void;
  onSaved: (count: number) => void;
}) {
  const [difficulty, setDifficulty] = useState<Difficulty | "mixed">("medium");
  const [count, setCount] = useState(5);
  const [figureCount, setFigureCount] = useState(0);
  const total = count + figureCount;
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState<AiStatus | null>(null);

  useEffect(() => {
    adminApi
      .aiStatus()
      .then(setStatus)
      .catch(() => setStatus({ configured: false, host: "", model: "" }));
  }, []);
  const [step, setStep] = useState<Step>({ kind: "form" });
  const [picked, setPicked] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function generate() {
    setError("");
    setStep({ kind: "loading" });
    try {
      const r = await adminApi.generateQuestions(topicId, { difficulty, count, figure_count: figureCount, notes: notes.trim() || undefined });
      setPicked(new Set(r.questions.map((_, i) => i)));
      setStep({
        kind: "review",
        drafts: r.questions,
        host: r.host,
        model: r.model,
        tokens: r.input_tokens + r.output_tokens,
        warning: r.warning,
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "AI bilan bog'lanib bo'lmadi");
      setStep({ kind: "form" });
    }
  }

  async function save(drafts: QuestionInput[]) {
    const chosen = drafts.filter((_, i) => picked.has(i));
    if (!chosen.length) return;
    setSaving(true);
    setError("");
    try {
      await adminApi.saveQuestions(topicId, chosen);
      onSaved(chosen.length);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Saqlab bo'lmadi");
      setSaving(false);
    }
  }

  const toggle = (i: number) =>
    setPicked((s) => {
      const next = new Set(s);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });

  // the modal can't be dismissed mid-request — the work (and its cost) is already under way
  const close = step.kind === "loading" || saving ? () => {} : onClose;

  return (
    <Modal title="AI bilan test yaratish" onClose={close}>
      {step.kind === "form" && (
        <div className="flex flex-col gap-5">
          <p className="rounded-2xl bg-gradient-to-r from-brand-50 to-violet-50 px-4 py-3 text-sm text-ink/80 ring-1 ring-brand-100">
            <b className="text-ink">«{topicTitle}»</b> mavzusi bo&apos;yicha AI yangi testlar tuzadi. Siz ularni ko&apos;rib chiqib,
            keraklilarini saqlaysiz — hech narsa avtomatik qo&apos;shilmaydi.
          </p>

          {status &&
            (status.configured ? (
              <p className="flex items-center gap-2 text-sm text-muted">
                <span className="size-2 rounded-full bg-emerald-500" />
                AI: <b className="font-semibold text-ink">{status.model}</b> · {status.host}
              </p>
            ) : (
              <p className="rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-100">
                AI sozlanmagan: <code>.env</code> faylida <code>AI_URL</code>, <code>AI_KEY</code> va <code>AI_MODEL</code> ni kiriting.
              </p>
            ))}

          <fieldset>
            <legend className="text-sm font-semibold text-ink">Daraja</legend>
            <div className="mt-2 grid grid-cols-4 gap-1 rounded-xl bg-slate-100 p-1">
              {LEVELS.map((l) => (
                <button
                  key={l.value}
                  type="button"
                  onClick={() => setDifficulty(l.value)}
                  aria-pressed={difficulty === l.value}
                  className={`flex items-center justify-center gap-2 rounded-lg py-2 text-sm font-semibold transition ${
                    difficulty === l.value ? "bg-white text-ink shadow" : "text-muted hover:text-ink"
                  }`}
                >
                  {l.dot && <span className={`size-2 rounded-full ${l.dot}`} />} {l.label}
                </button>
              ))}
            </div>
          </fieldset>

          <div className="grid gap-4 sm:grid-cols-2">
            <Stepper label="Oddiy testlar" hint="Rasmsiz" value={count} onChange={setCount} min={0} max={20} />
            <Stepper label="Rasmli testlar" hint="Chizma bilan (SVG), 10 tagacha" value={figureCount} onChange={setFigureCount} min={0} max={10} />
          </div>
          {(total < 1 || total > 20) && <p className="-mt-2 text-xs font-medium text-rose-600">Jami 1 tadan 20 tagacha test bo&apos;lishi kerak.</p>}

          <Field label="Qo'shimcha izoh" hint="Ixtiyoriy. Masalan: «matnli masalalar ko'proq bo'lsin», «katta sonlar bilan»">
            <textarea className={`${inputClass} resize-none`} rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={1000} />
          </Field>

          {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">{error}</p>}

          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-muted">Odatda 20–90 soniya</span>
            <div className="flex gap-3">
              <button type="button" onClick={onClose} className="rounded-xl px-5 py-3 text-sm font-semibold text-muted hover:bg-brand-50">
                Bekor qilish
              </button>
              <button type="button" onClick={generate} disabled={status?.configured === false || total < 1 || total > 20} className={`${primaryButton} bg-gradient-to-r from-brand-600 to-violet-600`}>
                <Sparkles className="size-4" /> Yaratish
              </button>
            </div>
          </div>
        </div>
      )}

      {step.kind === "loading" && (
        <div className="flex flex-col items-center py-12 text-center">
          <span className="relative grid size-20 place-items-center rounded-full bg-gradient-to-br from-brand-600 to-violet-600 text-white shadow-lg shadow-brand-600/30">
            <span className="absolute inset-0 animate-ping rounded-full bg-violet-400/30" />
            <Sparkles className="relative size-9" />
          </span>
          <p className="mt-6 text-lg font-extrabold text-ink">AI testlarni tuzmoqda…</p>
          <p className="mt-2 max-w-sm text-sm text-muted">
            {total} ta savol{figureCount ? ` (${figureCount} tasi chizmali)` : ""} yozib, har birini qayta yechib tekshiryapti. Bu bir daqiqagacha vaqt olishi mumkin — oynani yopmang.
          </p>
        </div>
      )}

      {step.kind === "review" && (
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-muted">
              {step.drafts.length} ta test tayyor · {picked.size} tasi tanlangan
              <span className="ml-2 text-xs text-muted/70">
                ({step.model} · {step.host}, {step.tokens.toLocaleString("ru-RU")} token)
              </span>
            </p>
            <button
              type="button"
              onClick={() => setPicked(picked.size === step.drafts.length ? new Set() : new Set(step.drafts.map((_, i) => i)))}
              className="text-sm font-semibold text-brand-600 hover:underline"
            >
              {picked.size === step.drafts.length ? "Hech birini tanlamaslik" : "Hammasini tanlash"}
            </button>
          </div>

          {step.warning && (
            <p className="rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-800 ring-1 ring-amber-100">{step.warning}</p>
          )}

          <ol className="flex flex-col gap-3">
            {step.drafts.map((q, i) => {
              const on = picked.has(i);
              return (
                <li key={i} className={`rounded-2xl p-4 ring-1 transition ${on ? "bg-white ring-brand-300" : "bg-slate-50 opacity-60 ring-slate-200"}`}>
                  <label className="flex cursor-pointer items-start gap-3">
                    <input type="checkbox" checked={on} onChange={() => toggle(i)} className="mt-1 size-4 accent-brand-600" />
                    <div className="min-w-0 flex-1">
                      <span className={`inline-block rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ${BADGE[q.difficulty]}`}>{LABEL[q.difficulty]}</span>
                      <p className="mt-1.5 whitespace-pre-line text-sm font-semibold leading-relaxed text-ink">
                        <MathText text={q.text} />
                      </p>
                      {q.figure_svg && <Figure svg={q.figure_svg} className="mt-3 max-h-56 w-full max-w-md rounded-xl bg-white ring-1 ring-brand-100" />}
                    </div>
                  </label>
                  <ul className="mt-3 grid gap-1.5 pl-7 sm:grid-cols-2">
                    {q.options.map((o, j) => (
                      <li
                        key={j}
                        className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-sm ${
                          j === q.correct ? "bg-emerald-50 font-semibold text-emerald-800" : "text-ink/75"
                        }`}
                      >
                        <span className={`grid size-5 shrink-0 place-items-center rounded text-[11px] font-bold ${j === q.correct ? "bg-emerald-500 text-white" : "bg-slate-100 text-muted"}`}>
                          {LETTERS[j]}
                        </span>
                        <span className="min-w-0 flex-1">
                          <MathText text={o} />
                        </span>
                        {j === q.correct && <Check className="size-3.5 text-emerald-600" strokeWidth={3} />}
                      </li>
                    ))}
                  </ul>
                  {q.explanation && <p className="mt-2 pl-7 text-xs leading-relaxed text-muted">
                      <MathText text={q.explanation} />
                    </p>}
                </li>
              );
            })}
          </ol>

          {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">{error}</p>}

          <p className="text-xs text-muted">
            Saqlashdan oldin javoblarni ko&apos;zdan kechiring: AI ham xato qilishi mumkin. Saqlangan testni keyin tahrirlash mumkin.
          </p>
          <div className="sticky bottom-0 -mx-6 -mb-6 flex flex-wrap justify-end gap-3 border-t border-brand-50 bg-white px-6 py-4 sm:-mx-8 sm:-mb-8 sm:px-8">
            <button type="button" onClick={generate} disabled={saving} className="rounded-xl px-5 py-3 text-sm font-semibold text-brand-600 ring-1 ring-brand-200 hover:bg-brand-50 disabled:opacity-50">
              Qayta yaratish
            </button>
            <button type="button" onClick={() => save(step.drafts)} disabled={saving || picked.size === 0} className={primaryButton}>
              {saving ? "Saqlanmoqda…" : `Tanlanganlarni saqlash (${picked.size})`}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
