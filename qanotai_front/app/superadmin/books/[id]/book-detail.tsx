"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState, type FormEvent } from "react";
import { adminApi, type BookDetail, type Topic, type TopicInput, type TopicKind } from "../../../_lib/admin-api";
import { ApiError } from "../../../_lib/api";
import { BookOpen, ChevronDown, ChevronLeft, ClipboardList, Search } from "../../../_components/icons";
import { useAdmin } from "../../_components/shell";
import { card, Field, inputClass, Modal, primaryButton } from "../../_components/ui";

const KINDS: { value: TopicKind; label: string; short: string }[] = [
  { value: "lesson", label: "Mavzu", short: "Mavzu" },
  { value: "review", label: "Takrorlash testi", short: "Takrorlash" },
  { value: "answers", label: "Javoblar", short: "Javoblar" },
  { value: "section", label: "Bo'lim", short: "Bo'lim" },
];

function TopicBadge({ topic }: { topic: Topic }) {
  if (topic.kind === "lesson") {
    return (
      <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-brand-50 text-sm font-bold text-brand-700 ring-1 ring-brand-100">
        {topic.number ?? "•"}
      </span>
    );
  }
  return (
    <span
      className={`grid size-9 shrink-0 place-items-center rounded-xl ring-1 ${
        topic.kind === "review" ? "bg-amber-50 text-amber-600 ring-amber-100" : "bg-emerald-50 text-emerald-600 ring-emerald-100"
      }`}
    >
      <ClipboardList className="size-4" />
    </span>
  );
}

function TopicForm({
  topic,
  nextNumber,
  onClose,
  onSubmit,
}: {
  topic: Topic | null;
  nextNumber: number;
  onClose: () => void;
  onSubmit: (data: TopicInput) => Promise<void>;
}) {
  const [kind, setKind] = useState<TopicKind>(topic?.kind ?? "lesson");
  const [number, setNumber] = useState(String(topic?.number ?? nextNumber));
  const [title, setTitle] = useState(topic?.title ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (title.trim().length < 2) return setError("Mavzu nomini kiriting");
    setSaving(true);
    setError("");
    try {
      await onSubmit({
        kind,
        number: kind === "lesson" && number ? Number(number) : null,
        title: title.trim(),
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Saqlab bo'lmadi");
      setSaving(false);
    }
  }

  return (
    <Modal title={topic ? "Mavzuni tahrirlash" : "Yangi mavzu"} onClose={onClose}>
      <form onSubmit={submit} noValidate className="flex flex-col gap-5">
        <fieldset>
          <legend className="text-sm font-semibold text-ink">Turi</legend>
          <div className="mt-2 grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1 sm:grid-cols-4">
            {KINDS.map((k) => (
              <button
                key={k.value}
                type="button"
                onClick={() => setKind(k.value)}
                aria-pressed={kind === k.value}
                className={`rounded-lg py-2 text-sm font-semibold transition ${kind === k.value ? "bg-white text-brand-700 shadow" : "text-muted hover:text-ink"}`}
              >
                {k.label}
              </button>
            ))}
          </div>
        </fieldset>
        <div className={`grid gap-4 ${kind === "lesson" ? "grid-cols-[110px_1fr]" : ""}`}>
          {kind === "lesson" && (
            <Field label="Raqami">
              <input className={inputClass} inputMode="numeric" value={number} onChange={(e) => setNumber(e.target.value.replace(/\D/g, "").slice(0, 4))} />
            </Field>
          )}
          <Field label="Nomi">
            <input
              className={inputClass}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={kind === "lesson" ? "Masalan: Natural sonlar va ular ustida amallar" : "Masalan: 1-5-mavzular boʻyicha takrorlash testi"}
              autoFocus
            />
          </Field>
        </div>
        {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">{error}</p>}
        <div className="flex justify-end gap-3">
          <button type="button" onClick={onClose} className="rounded-xl px-5 py-3 text-sm font-semibold text-muted hover:bg-brand-50">
            Bekor qilish
          </button>
          <button type="submit" disabled={saving} className={primaryButton}>
            {saving ? "Saqlanmoqda…" : topic ? "Saqlash" : "Qo'shish"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function BookDetailView() {
  const { id } = useParams<{ id: string }>();
  const bookId = Number(id);
  const { openBookForm, version, ask, notify } = useAdmin();
  const [book, setBook] = useState<BookDetail | null>(null);
  const [missing, setMissing] = useState(false);
  const [q, setQ] = useState("");
  const [form, setForm] = useState<{ topic: Topic | null } | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    adminApi
      .book(bookId)
      .then(setBook)
      .catch(() => setMissing(true));
  }, [bookId, version, reload]);

  const topics = useMemo(() => book?.topics ?? [], [book]);
  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return needle ? topics.filter((t) => t.title.toLowerCase().includes(needle) || String(t.number ?? "") === needle) : topics;
  }, [topics, q]);
  const counts = useMemo(
    () => ({
      lesson: topics.filter((t) => t.kind === "lesson").length,
      review: topics.filter((t) => t.kind === "review").length,
      answers: topics.filter((t) => t.kind === "answers").length,
    }),
    [topics],
  );
  const nextNumber = Math.max(0, ...topics.map((t) => t.number ?? 0)) + 1;

  if (missing) {
    return (
      <div className={`flex flex-col items-center px-6 py-16 text-center ${card}`}>
        <BookOpen className="size-10 text-brand-300" />
        <p className="mt-3 font-bold text-ink">Kitob topilmadi</p>
        <Link href="/superadmin/books" className="mt-4 text-sm font-semibold text-brand-600 hover:underline">
          ← Kitoblarga qaytish
        </Link>
      </div>
    );
  }
  if (!book) {
    return (
      <div className="grid h-80 place-items-center">
        <span className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
      </div>
    );
  }

  async function move(index: number, delta: -1 | 1) {
    const ids = topics.map((t) => t.id);
    const j = index + delta;
    if (j < 0 || j >= ids.length) return;
    [ids[index], ids[j]] = [ids[j], ids[index]];
    const byId = new Map(topics.map((t) => [t.id, t]));
    setBook((b) => b && { ...b, topics: ids.map((i) => byId.get(i)!) }); // optimistic
    try {
      await adminApi.reorderTopics(bookId, ids);
    } catch {
      notify("Tartibni saqlab bo'lmadi", "error");
      setReload((r) => r + 1);
    }
  }

  function remove(t: Topic) {
    ask({
      title: "Mavzuni o'chirish",
      message: (
        <>
          <b className="text-ink">«{t.title}»</b> kitobdan o&apos;chiriladi.
        </>
      ),
      onConfirm: async () => {
        await adminApi.deleteTopic(t.id);
        notify("Muvaffaqiyatli o'chirildi", "success", t.title);
        setReload((r) => r + 1);
      },
    });
  }

  const reordering = q.trim() === ""; // moving rows only makes sense in the full list

  return (
    <div className="flex flex-col gap-6">
      <Link href="/superadmin/books" className="inline-flex w-fit items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700">
        <ChevronLeft className="size-4" /> Kitoblar
      </Link>

      <div className="grid items-start gap-6 lg:grid-cols-[300px_minmax(0,1fr)]">
        {/* book */}
        <aside className={`overflow-hidden lg:sticky lg:top-24 ${card}`}>
          <div className="relative h-72 bg-gradient-to-b from-brand-50 to-white">
            {book.cover_url ? (
              <Image src={book.cover_url} alt={book.title} fill priority unoptimized className="object-contain p-5 drop-shadow-xl" />
            ) : (
              <BookOpen className="absolute inset-0 m-auto size-14 text-brand-300" />
            )}
          </div>
          <div className="p-5">
            <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700">{book.subject_name}</span>
            <h1 className="mt-3 text-xl font-extrabold leading-snug text-ink">{book.title}</h1>
            {book.description && <p className="mt-2 text-sm text-muted">{book.description}</p>}
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              {[
                { k: "Nashr yili", v: book.year ?? "—" },
                { k: "Testlar", v: book.test_count },
                { k: "Mavzular", v: counts.lesson },
                { k: "Takrorlash testlari", v: counts.review },
              ].map((r) => (
                <div key={r.k} className="rounded-xl bg-brand-50/60 px-3 py-2">
                  <dt className="text-xs text-muted">{r.k}</dt>
                  <dd className="font-bold text-ink">{r.v}</dd>
                </div>
              ))}
            </dl>
            <button
              type="button"
              onClick={() => openBookForm(book)}
              className="mt-4 w-full rounded-xl bg-brand-50 py-2.5 text-sm font-semibold text-brand-600 hover:bg-brand-100"
            >
              Kitobni tahrirlash
            </button>
          </div>
        </aside>

        {/* table of contents */}
        <section className={`p-5 sm:p-6 ${card}`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-extrabold text-ink">Mundarija</h2>
              <p className="text-sm text-muted">
                {counts.lesson} ta mavzu · {counts.review} ta takrorlash testi
                {counts.answers > 0 && ` · javoblar`}
              </p>
            </div>
            <button type="button" onClick={() => setForm({ topic: null })} className={primaryButton}>
              + Yangi mavzu
            </button>
          </div>

          <label className="relative mt-5 block">
            <span className="sr-only">Mavzu qidirish</span>
            <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
            <input className={`${inputClass} pl-12`} placeholder="Mavzu nomi yoki raqami…" value={q} onChange={(e) => setQ(e.target.value)} />
          </label>

          {topics.length === 0 ? (
            <div className="mt-6 flex flex-col items-center rounded-2xl border-2 border-dashed border-brand-100 px-6 py-12 text-center">
              <BookOpen className="size-10 text-brand-300" />
              <p className="mt-3 font-bold text-ink">Hali mavzu qo&apos;shilmagan</p>
              <p className="mt-1 text-sm text-muted">Kitob mundarijasidagi mavzularni birma-bir qo&apos;shing.</p>
            </div>
          ) : (
            <ol className="mt-4 divide-y divide-brand-50">
              {visible.map((t) => {
                const index = topics.indexOf(t);
                const kind = KINDS.find((k) => k.value === t.kind)!;
                return (
                  <li key={t.id} className={`group flex items-center gap-3 py-3 ${t.kind !== "lesson" && t.kind !== "section" ? "-mx-2 rounded-xl px-2" : ""} ${t.kind === "review" ? "bg-amber-50/40" : t.kind === "answers" ? "bg-emerald-50/40" : ""} ${t.kind === "section" ? "pt-6" : ""}`}>
                    {t.kind === "section" ? (
                      <p className="min-w-0 flex-1 text-sm font-extrabold uppercase tracking-wide text-brand-700">{t.title}</p>
                    ) : (
                      <>
                    <TopicBadge topic={t} />
                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/superadmin/books/${bookId}/topics/${t.id}`}
                        className={`block text-[15px] leading-snug hover:text-brand-600 ${t.kind === "lesson" ? "font-semibold text-ink" : "font-bold text-ink/90"}`}
                      >
                        {t.title}
                      </Link>
                      {t.kind !== "lesson" && (
                        <p className={`text-xs font-semibold ${t.kind === "review" ? "text-amber-600" : "text-emerald-600"}`}>{kind.short}</p>
                      )}
                    </div>
                    <Link
                      href={`/superadmin/books/${bookId}/topics/${t.id}`}
                      className={`shrink-0 rounded-lg px-2.5 py-1 text-xs font-semibold tabular-nums transition-colors ${
                        t.question_count ? "bg-brand-50 text-brand-700 hover:bg-brand-100" : "bg-slate-50 text-muted hover:bg-slate-100"
                      }`}
                    >
                      {t.question_count} ta test
                    </Link>
                      </>
                    )}
                    <div className="flex shrink-0 items-center gap-1 opacity-100 transition-opacity sm:opacity-0 sm:group-hover:opacity-100 sm:group-focus-within:opacity-100">
                      {reordering && (
                        <>
                          <button
                            type="button"
                            onClick={() => move(index, -1)}
                            disabled={index === 0}
                            aria-label="Yuqoriga"
                            className="grid size-8 place-items-center rounded-lg text-muted hover:bg-brand-50 hover:text-ink disabled:opacity-30"
                          >
                            <ChevronDown className="size-4 rotate-180" />
                          </button>
                          <button
                            type="button"
                            onClick={() => move(index, 1)}
                            disabled={index === topics.length - 1}
                            aria-label="Pastga"
                            className="grid size-8 place-items-center rounded-lg text-muted hover:bg-brand-50 hover:text-ink disabled:opacity-30"
                          >
                            <ChevronDown className="size-4" />
                          </button>
                        </>
                      )}
                      <button
                        type="button"
                        onClick={() => setForm({ topic: t })}
                        className="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-brand-600 hover:bg-brand-50"
                      >
                        Tahrirlash
                      </button>
                      <button type="button" onClick={() => remove(t)} className="rounded-lg px-2.5 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50">
                        O&apos;chirish
                      </button>
                    </div>
                  </li>
                );
              })}
              {visible.length === 0 && <li className="py-10 text-center text-sm text-muted">Hech narsa topilmadi</li>}
            </ol>
          )}
        </section>
      </div>

      {form && (
        <TopicForm
          topic={form.topic}
          nextNumber={nextNumber}
          onClose={() => setForm(null)}
          onSubmit={async (data) => {
            if (form.topic) await adminApi.updateTopic(form.topic.id, data);
            else await adminApi.createTopic(bookId, data);
            notify(form.topic ? "Mavzu saqlandi" : "Mavzu qo'shildi", "success", data.title);
            setForm(null);
            setReload((r) => r + 1);
          }}
        />
      )}
    </div>
  );
}
