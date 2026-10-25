"use client";

import { MathText } from "../../../../../_components/math-text";
import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { adminApi, type Difficulty, type Question, type QuestionInput, type TopicDetail } from "../../../../../_lib/admin-api";
import { ApiError } from "../../../../../_lib/api";
import { Check, ChevronDown, ChevronLeft, ClipboardList, Close, Pencil, Sparkles, Trash } from "../../../../../_components/icons";
import { useAdmin } from "../../../../_components/shell";
import { Solutions } from "../../../../../_components/solutions";
import { AiGenerateModal } from "./ai-generate";
import { ActionMenu, card, Field, inputClass, Modal, primaryButton } from "../../../../_components/ui";

const LETTERS = "ABCDEF";

const DIFFICULTY: Record<Difficulty, { label: string; badge: string; dot: string }> = {
  easy: { label: "Oson", badge: "bg-emerald-50 text-emerald-700 ring-emerald-100", dot: "bg-emerald-500" },
  medium: { label: "O'rta", badge: "bg-amber-50 text-amber-700 ring-amber-100", dot: "bg-amber-500" },
  hard: { label: "Qiyin", badge: "bg-rose-50 text-rose-700 ring-rose-100", dot: "bg-rose-500" },
};
const LEVELS = Object.keys(DIFFICULTY) as Difficulty[];

function QuestionForm({
  question,
  onClose,
  onSubmit,
}: {
  question: Question | null;
  onClose: () => void;
  onSubmit: (data: QuestionInput) => Promise<void>;
}) {
  const [difficulty, setDifficulty] = useState<Difficulty>(question?.difficulty ?? "medium");
  const [text, setText] = useState(question?.text ?? "");
  const [options, setOptions] = useState<string[]>(question?.options ?? ["", "", "", ""]);
  const [correct, setCorrect] = useState<number | null>(question ? question.correct : null);
  const [explanation, setExplanation] = useState(question?.explanation ?? "");
  const [image, setImage] = useState<string | null>(question?.image_url ?? null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function setOption(i: number, value: string) {
    setOptions((o) => o.map((v, j) => (j === i ? value : v)));
  }
  function removeOption(i: number) {
    setOptions((o) => o.filter((_, j) => j !== i));
    setCorrect((c) => (c === null || c === i ? null : c > i ? c - 1 : c));
  }

  async function pickImage(file: File | undefined) {
    if (!file) return;
    setError("");
    setUploading(true);
    try {
      setImage((await adminApi.upload(file)).url);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Rasmni yuklab bo'lmadi");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (text.trim().length < 2) return setError("Savol matnini kiriting");
    if (options.some((o) => !o.trim())) return setError("Barcha variantlarni to'ldiring");
    if (correct === null) return setError("To'g'ri javobni belgilang");
    setSaving(true);
    setError("");
    try {
      await onSubmit({
        difficulty,
        text: text.trim(),
        options: options.map((o) => o.trim()),
        correct,
        explanation: explanation.trim() || null,
        image_url: image,
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Saqlab bo'lmadi");
      setSaving(false);
    }
  }

  return (
    <Modal title={question ? "Testni tahrirlash" : "Yangi test"} onClose={onClose}>
      <form onSubmit={submit} noValidate className="flex flex-col gap-5">
        <fieldset>
          <legend className="text-sm font-semibold text-ink">Daraja</legend>
          <div className="mt-2 grid grid-cols-3 gap-1 rounded-xl bg-slate-100 p-1">
            {LEVELS.map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDifficulty(d)}
                aria-pressed={difficulty === d}
                className={`flex items-center justify-center gap-2 rounded-lg py-2 text-sm font-semibold transition ${
                  difficulty === d ? "bg-white text-ink shadow" : "text-muted hover:text-ink"
                }`}
              >
                <span className={`size-2 rounded-full ${DIFFICULTY[d].dot}`} /> {DIFFICULTY[d].label}
              </button>
            ))}
          </div>
        </fieldset>

        <Field label="Savol">
          <textarea className={`${inputClass} resize-none`} rows={3} value={text} onChange={(e) => setText(e.target.value)} placeholder="Masalan: Hisoblang: 2345 + 6789" autoFocus />
        </Field>

        <fieldset>
          <legend className="text-sm font-semibold text-ink">Variantlar</legend>
          <p className="text-xs text-muted">To&apos;g&apos;ri javob yonidagi doirachani bosing.</p>
          <div className="mt-2 flex flex-col gap-2">
            {options.map((o, i) => (
              <div key={i} className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCorrect(i)}
                  aria-label={`${LETTERS[i]} — to'g'ri javob`}
                  aria-pressed={correct === i}
                  className={`grid size-10 shrink-0 place-items-center rounded-xl text-sm font-bold ring-1 transition ${
                    correct === i ? "bg-emerald-500 text-white ring-emerald-500" : "bg-white text-muted ring-brand-100 hover:ring-emerald-300"
                  }`}
                >
                  {correct === i ? <Check className="size-4" strokeWidth={3} /> : LETTERS[i]}
                </button>
                <input className={inputClass} value={o} onChange={(e) => setOption(i, e.target.value)} placeholder={`${LETTERS[i]} variant`} />
                {options.length > 2 && (
                  <button type="button" onClick={() => removeOption(i)} aria-label="Variantni olib tashlash" className="grid size-9 shrink-0 place-items-center rounded-lg text-muted hover:bg-rose-50 hover:text-rose-600">
                    <Close className="size-4" />
                  </button>
                )}
              </div>
            ))}
          </div>
          {options.length < 6 && (
            <button type="button" onClick={() => setOptions((o) => [...o, ""])} className="mt-2 text-sm font-semibold text-brand-600 hover:underline">
              + Variant qo&apos;shish
            </button>
          )}
        </fieldset>

        <div>
          <p className="text-sm font-semibold text-ink">Rasm</p>
          <p className="text-xs text-muted">Ixtiyoriy — chizma, grafik yoki jadval (JPG, PNG, WEBP, 5 MB gacha)</p>
          {image ? (
            <div className="mt-2 flex items-start gap-3">
              <div className="relative h-40 w-full max-w-sm overflow-hidden rounded-xl bg-white ring-1 ring-brand-100">
                <Image src={image} alt="Savol rasmi" fill unoptimized className="object-contain p-2" />
              </div>
              <div className="flex flex-col gap-2 text-sm font-semibold">
                <button type="button" onClick={() => fileRef.current?.click()} className="text-brand-600 hover:underline">
                  Almashtirish
                </button>
                <button type="button" onClick={() => setImage(null)} className="text-rose-600 hover:underline">
                  Olib tashlash
                </button>
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="mt-2 flex h-24 w-full max-w-sm items-center justify-center rounded-xl border-2 border-dashed border-brand-100 text-sm font-semibold text-brand-600 hover:bg-brand-50/50 disabled:opacity-60"
            >
              {uploading ? "Yuklanmoqda…" : "+ Rasm yuklash"}
            </button>
          )}
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(e) => pickImage(e.target.files?.[0])} />
        </div>

        <Field label="Yechim" hint="Ixtiyoriy — o'quvchiga javobdan keyin ko'rsatiladi">
          <textarea className={`${inputClass} resize-none`} rows={3} value={explanation} onChange={(e) => setExplanation(e.target.value)} />
        </Field>

        {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">{error}</p>}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-xl px-5 py-3 text-sm font-semibold text-muted hover:bg-brand-50">
            Bekor qilish
          </button>
          <button type="submit" disabled={saving || uploading} className={primaryButton}>
            {saving ? "Saqlanmoqda…" : question ? "Saqlash" : "Qo'shish"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function QuestionCard({ q, index, onEdit, onDelete }: { q: Question; index: number; onEdit: () => void; onDelete: () => void }) {
  const [open, setOpen] = useState(false);
  const d = DIFFICULTY[q.difficulty as Difficulty] ?? DIFFICULTY.medium;
  return (
    <li className={`p-5 ${card}`}>
      <div className="flex items-start gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-600 text-sm font-bold text-white">{index}</span>
        <div className="min-w-0 flex-1">
          <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${d.badge}`}>
            <span className={`size-1.5 rounded-full ${d.dot}`} /> {d.label}
          </span>
          <p className="mt-2 whitespace-pre-line text-[15px] font-semibold leading-relaxed text-ink">
            <MathText text={q.text} />
          </p>
          {q.image_url && (
            <div className="relative mt-3 h-72 w-full max-w-xl overflow-hidden rounded-xl bg-white ring-1 ring-brand-100">
              <Image src={q.image_url} alt={`${index}-test rasmi`} fill unoptimized className="object-contain p-2" />
            </div>
          )}
        </div>
        <ActionMenu
          label={`${index}-test — amallar`}
          items={[
            { label: "Tahrirlash", icon: <Pencil className="size-4" />, onSelect: onEdit },
            { label: "O'chirish", icon: <Trash className="size-4" />, danger: true, onSelect: onDelete },
          ]}
        />
      </div>

      <ul className="mt-4 grid gap-2 sm:grid-cols-2">
        {q.options.map((o, i) => {
          const right = i === q.correct;
          return (
            <li
              key={i}
              className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm ring-1 ${
                right ? "bg-emerald-50 font-semibold text-emerald-800 ring-emerald-200" : "bg-white text-ink/80 ring-brand-100"
              }`}
            >
              <span className={`grid size-7 shrink-0 place-items-center rounded-lg text-xs font-bold ${right ? "bg-emerald-500 text-white" : "bg-slate-100 text-muted"}`}>
                {LETTERS[i]}
              </span>
              <span className="min-w-0 flex-1">
                <MathText text={o} />
              </span>
              {right && (
                <span className="flex shrink-0 items-center gap-1 text-xs font-bold text-emerald-600">
                  <Check className="size-4" strokeWidth={3} /> To&apos;g&apos;ri
                </span>
              )}
            </li>
          );
        })}
      </ul>

      {(q.explanation || q.solution || q.explainer) && (
        <div className="mt-3">
          <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open} className="flex items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700">
            Yechim <ChevronDown className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
          </button>
          {open &&
            (q.solution || q.explainer ? (
              <div className="mt-3">
                <Solutions solution={q.solution} explainer={q.explainer} />
              </div>
            ) : (
              <p className="mt-2 rounded-xl bg-brand-50/60 px-4 py-3 text-sm leading-relaxed text-ink/80">
                <MathText text={q.explanation ?? ""} />
              </p>
            ))}
        </div>
      )}
    </li>
  );
}

export function TopicDetailView() {
  const { id, topicId } = useParams<{ id: string; topicId: string }>();
  const { ask, notify } = useAdmin();
  const [topic, setTopic] = useState<TopicDetail | null>(null);
  const [missing, setMissing] = useState(false);
  const [level, setLevel] = useState<Difficulty | "all">("all");
  const [form, setForm] = useState<{ question: Question | null } | null>(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    adminApi
      .topic(Number(topicId))
      .then(setTopic)
      .catch(() => setMissing(true));
  }, [topicId, reload]);

  const questions = useMemo(() => topic?.questions ?? [], [topic]);
  const counts = useMemo(() => Object.fromEntries(LEVELS.map((d) => [d, questions.filter((q) => q.difficulty === d).length])), [questions]);
  const visible = level === "all" ? questions : questions.filter((q) => q.difficulty === level);

  if (missing) {
    return (
      <div className={`flex flex-col items-center px-6 py-16 text-center ${card}`}>
        <ClipboardList className="size-10 text-brand-300" />
        <p className="mt-3 font-bold text-ink">Mavzu topilmadi</p>
        <Link href={`/superadmin/books/${id}`} className="mt-4 text-sm font-semibold text-brand-600 hover:underline">
          ← Kitobga qaytish
        </Link>
      </div>
    );
  }
  if (!topic) {
    return (
      <div className="grid h-80 place-items-center">
        <span className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
      </div>
    );
  }

  function remove(q: Question, index: number) {
    ask({
      title: "Testni o'chirish",
      message: <>{index}-test butunlay o&apos;chiriladi. Bu amalni qaytarib bo&apos;lmaydi.</>,
      onConfirm: async () => {
        await adminApi.deleteQuestion(q.id);
        notify("Muvaffaqiyatli o'chirildi", "success", `${index}-test o'chirildi`);
        setReload((r) => r + 1);
      },
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <Link href={`/superadmin/books/${topic.book_id}`} className="inline-flex w-fit items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700">
        <ChevronLeft className="size-4" /> {topic.book_title}
      </Link>

      <section className={`p-6 ${card}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <span className="grid size-12 shrink-0 place-items-center rounded-2xl bg-brand-50 text-lg font-extrabold text-brand-700 ring-1 ring-brand-100">
              {topic.number ?? <ClipboardList className="size-5" />}
            </span>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-muted">{topic.number ? `${topic.number}-mavzu` : "Takrorlash"}</p>
              <h1 className="mt-1 text-2xl font-extrabold leading-snug tracking-tight text-ink">{topic.title}</h1>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setAiOpen(true)}
              className={`${primaryButton} bg-gradient-to-r from-brand-600 to-violet-600 hover:from-brand-700 hover:to-violet-700`}
            >
              <Sparkles className="size-4" /> AI bilan yaratish
            </button>
            <button
              type="button"
              onClick={() => setForm({ question: null })}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-brand-600 ring-1 ring-brand-200 hover:bg-brand-50"
            >
              + Yangi test
            </button>
          </div>
        </div>

        {/* difficulty filter */}
        <div className="mt-6 flex flex-wrap gap-2">
          {(["all", ...LEVELS] as const).map((d) => {
            const active = level === d;
            const n = d === "all" ? questions.length : counts[d];
            return (
              <button
                key={d}
                type="button"
                onClick={() => setLevel(d)}
                aria-pressed={active}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold ring-1 transition ${
                  active ? "bg-brand-600 text-white ring-brand-600" : "bg-white text-ink/75 ring-brand-100 hover:bg-brand-50"
                }`}
              >
                {d !== "all" && <span className={`size-2 rounded-full ${DIFFICULTY[d].dot}`} />}
                {d === "all" ? "Barchasi" : DIFFICULTY[d].label}
                <span className={`rounded-full px-1.5 text-xs ${active ? "bg-white/20" : "bg-slate-100 text-muted"}`}>{n}</span>
              </button>
            );
          })}
        </div>
      </section>

      {questions.length === 0 ? (
        <div className={`flex flex-col items-center px-6 py-16 text-center ${card}`}>
          <ClipboardList className="size-10 text-brand-300" />
          <p className="mt-3 font-bold text-ink">Hali test qo&apos;shilmagan</p>
          <p className="mt-1 text-sm text-muted">Birinchi testni qo&apos;shing — variantlar va to&apos;g&apos;ri javob bilan.</p>
        </div>
      ) : (
        <ol className="flex flex-col gap-4">
          {visible.map((q) => {
            const index = questions.indexOf(q) + 1;
            return <QuestionCard key={q.id} q={q} index={index} onEdit={() => setForm({ question: q })} onDelete={() => remove(q, index)} />;
          })}
          {visible.length === 0 && <li className="py-10 text-center text-sm text-muted">Bu darajada test yo&apos;q</li>}
        </ol>
      )}

      {aiOpen && (
        <AiGenerateModal
          topicId={Number(topicId)}
          topicTitle={topic.title}
          onClose={() => setAiOpen(false)}
          onSaved={(n) => {
            notify("Testlar qo'shildi", "success", `AI yaratgan ${n} ta test saqlandi`);
            setAiOpen(false);
            setReload((r) => r + 1);
          }}
        />
      )}

      {form && (
        <QuestionForm
          question={form.question}
          onClose={() => setForm(null)}
          onSubmit={async (data) => {
            if (form.question) await adminApi.updateQuestion(form.question.id, data);
            else await adminApi.createQuestion(Number(topicId), data);
            notify(form.question ? "Test saqlandi" : "Test qo'shildi", "success");
            setForm(null);
            setReload((r) => r + 1);
          }}
        />
      )}
    </div>
  );
}
