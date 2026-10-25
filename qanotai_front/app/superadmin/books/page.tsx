"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";
import { adminApi, type Book, type Subject } from "../../_lib/admin-api";
import { BookOpen, Pencil, Search, Trash } from "../../_components/icons";
import { useAdmin } from "../_components/shell";
import { ActionMenu, card, formatDate, inputClass, PageHead, primaryButton } from "../_components/ui";

export default function BooksPage() {
  const { openBookForm, version, ask, notify } = useAdmin();
  const [books, setBooks] = useState<Book[] | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [subjectId, setSubjectId] = useState("");
  const [q, setQ] = useState("");
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    adminApi.subjects().then(setSubjects).catch(() => {});
  }, [version]);

  useEffect(() => {
    const t = setTimeout(() => {
      adminApi
        .books({ subject_id: subjectId ? Number(subjectId) : undefined, q })
        .then(setBooks)
        .catch(() => setError("Kitoblarni yuklab bo'lmadi"));
    }, 250); // debounce typing
    return () => clearTimeout(t);
  }, [subjectId, q, version, reload]);

  function remove(b: Book) {
    ask({
      title: "Kitobni o'chirish",
      message: (
        <>
          <b className="text-ink">«{b.title}»</b> kitobi butunlay o&apos;chiriladi. Bu amalni qaytarib bo&apos;lmaydi.
        </>
      ),
      onConfirm: async () => {
        await adminApi.deleteBook(b.id);
        notify("Muvaffaqiyatli o'chirildi", "success", `«${b.title}» kitobi o'chirildi`);
        setReload((r) => r + 1);
      },
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHead
        title="Kitoblar"
        subtitle="Platformadagi barcha kitoblar va ularning testlari"
        action={
          <button type="button" onClick={() => openBookForm(null)} className={primaryButton}>
            + Yangi kitob
          </button>
        }
      />

      <div className="flex flex-col gap-3 sm:flex-row">
        <label className="relative flex-1">
          <span className="sr-only">Qidirish</span>
          <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
          <input className={`${inputClass} pl-12`} placeholder="Kitob nomi bo'yicha qidirish…" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <select className={`${inputClass} sm:w-56`} value={subjectId} onChange={(e) => setSubjectId(e.target.value)} aria-label="Fan">
          <option value="">Barcha fanlar</option>
          {subjects.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}

      {books === null ? (
        <div className="grid h-60 place-items-center">
          <span className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
        </div>
      ) : books.length === 0 ? (
        <div className={`flex flex-col items-center px-6 py-16 text-center ${card}`}>
          <BookOpen className="size-10 text-brand-300" />
          <p className="mt-3 font-bold text-ink">Kitob topilmadi</p>
          <p className="mt-1 text-sm text-muted">Yangi kitob qo&apos;shing yoki qidiruvni o&apos;zgartiring.</p>
        </div>
      ) : (
        <ul className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6">
          {books.map((b) => (
            <li key={b.id} className={`flex flex-col ${card}`}>
              <div className="relative">
                <Link
                  href={`/superadmin/books/${b.id}`}
                  className="group relative block h-48 overflow-hidden rounded-t-3xl bg-gradient-to-b from-brand-50 to-white"
                >
                  {b.cover_url ? (
                    <Image src={b.cover_url} alt={b.title} fill unoptimized className="object-contain p-3 drop-shadow-lg transition-transform group-hover:scale-105" />
                  ) : (
                    <BookOpen className="absolute inset-0 m-auto size-12 text-brand-300" />
                  )}
                </Link>
                <span className="pointer-events-none absolute left-3 top-3 rounded-full bg-white/90 px-2.5 py-1 text-[11px] font-semibold text-brand-700 shadow-sm">
                  {b.subject_name}
                </span>
                <ActionMenu
                  label={`${b.title} — amallar`}
                  className="absolute right-3 top-3"
                  items={[
                    { label: "Tahrirlash", icon: <Pencil className="size-4" />, onSelect: () => openBookForm(b) },
                    { label: "O'chirish", icon: <Trash className="size-4" />, danger: true, onSelect: () => remove(b) },
                  ]}
                />
              </div>
              <Link href={`/superadmin/books/${b.id}`} className="flex flex-1 flex-col p-4 hover:[&_p:first-child]:text-brand-600">
                <p className="line-clamp-2 font-bold leading-snug text-ink transition-colors">{b.title}</p>
                <p className="mt-1 text-xs text-muted">
                  {b.year ? `${b.year} · ` : ""}
                  {b.test_count} ta test · {b.topic_count} ta mavzu
                </p>
                <p className="mt-1 text-[11px] text-muted/80">Qo&apos;shilgan: {formatDate(b.created_at)}</p>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
