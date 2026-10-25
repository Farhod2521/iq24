"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ApiError, getCatalogBook, type CatalogBookPage } from "../../../_lib/api";
import { ArrowRight, BookOpen, ChevronLeft, ClipboardList, Lock, Search } from "../../../_components/icons";
import { card, Spinner } from "../../_components/student-ui";

function ResultBadge({ percent }: { percent: number }) {
  const tone = percent >= 80 ? "bg-emerald-50 text-emerald-700 ring-emerald-100" : percent >= 50 ? "bg-amber-50 text-amber-700 ring-amber-100" : "bg-rose-50 text-rose-700 ring-rose-100";
  return <span className={`shrink-0 rounded-lg px-2.5 py-1 text-xs font-bold ring-1 tabular-nums ${tone}`}>{percent}%</span>;
}

export function BookView() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [book, setBook] = useState<CatalogBookPage | null>(null);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");

  useEffect(() => {
    getCatalogBook(Number(id))
      .then(setBook)
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) router.replace("/?login=1");
        else setError(e instanceof ApiError ? e.message : "Kitobni yuklab bo'lmadi");
      });
  }, [id, router]);

  const topics = useMemo(() => book?.topic_list ?? [], [book]);
  const visible = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return needle ? topics.filter((t) => t.title.toLowerCase().includes(needle) || String(t.number ?? "") === needle) : topics;
  }, [topics, q]);

  if (error) {
    return (
      <div className={`flex flex-col items-center px-6 py-16 text-center ${card}`}>
        <BookOpen className="size-10 text-brand-300" />
        <p className="mt-3 font-bold text-ink">{error}</p>
        <Link href="/dashboard" className="mt-4 text-sm font-semibold text-brand-600 hover:underline">
          ← Bosh sahifaga qaytish
        </Link>
      </div>
    );
  }
  if (!book) return <Spinner />;

  const lessons = topics.filter((t) => t.kind === "lesson").length;
  const withTests = topics.filter((t) => t.tests > 0);
  const done = withTests.filter((t) => t.attempts > 0);
  const avg = done.length ? Math.round(done.reduce((sum, t) => sum + (t.best_percent ?? 0), 0) / done.length) : null;
  const next = withTests.find((t) => t.attempts === 0) ?? withTests[0];

  return (
    <div className="flex flex-col gap-5">
      <Link href="/dashboard" className="inline-flex w-fit items-center gap-1 text-sm font-semibold text-brand-600 hover:text-brand-700">
        <ChevronLeft className="size-4" /> Bosh sahifa
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
            <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700">{book.subject}</span>
            <h1 className="mt-3 text-xl font-extrabold leading-snug text-ink">{book.title}</h1>
            {book.description && <p className="mt-2 text-sm text-muted">{book.description}</p>}
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              {[
                { k: "Mavzular", v: lessons },
                { k: "Testlar", v: book.tests },
                { k: "Ishlangan", v: `${done.length} / ${withTests.length}` },
                { k: "O'rtacha natija", v: avg === null ? "—" : `${avg}%` },
              ].map((r) => (
                <div key={r.k} className="rounded-xl bg-brand-50/60 px-3 py-2">
                  <dt className="text-xs text-muted">{r.k}</dt>
                  <dd className="font-bold text-ink">{r.v}</dd>
                </div>
              ))}
            </dl>
            {withTests.length > 0 && (
              <>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-brand-50">
                  <div className="h-full rounded-full bg-brand-600 transition-all" style={{ width: `${(done.length / withTests.length) * 100}%` }} />
                </div>
                <p className="mt-1.5 text-xs text-muted">Testli mavzularning {Math.round((done.length / withTests.length) * 100)}% i ishlangan</p>
              </>
            )}
            {next && (
              <Link
                href={`/dashboard/topics/${next.id}`}
                className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition-colors hover:bg-brand-700"
              >
                {done.length ? "Davom ettirish" : "Boshlash"} <ArrowRight className="size-4" />
              </Link>
            )}
          </div>
        </aside>

        {/* table of contents */}
        <section className={`p-5 sm:p-6 ${card}`}>
          <h2 className="text-xl font-extrabold text-ink">Mundarija</h2>
          <p className="text-sm text-muted">
            {lessons} ta mavzu · {book.tests} ta test
          </p>

          <label className="relative mt-5 block">
            <span className="sr-only">Mavzu qidirish</span>
            <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
            <input
              className="w-full rounded-xl bg-white py-3 pl-12 pr-4 text-[15px] text-ink ring-1 ring-brand-100 outline-none placeholder:text-muted/60 focus:ring-2 focus:ring-brand-500"
              placeholder="Mavzu nomi yoki raqami…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </label>

          {topics.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted">Bu kitobga hali mavzu qo&apos;shilmagan.</p>
          ) : (
            <ol className="mt-3 divide-y divide-brand-50">
              {visible.map((t) => {
                if (t.kind === "section") {
                  return (
                    <li key={t.id} className="pb-2 pt-6">
                      <p className="text-sm font-extrabold uppercase tracking-wide text-brand-700">{t.title}</p>
                    </li>
                  );
                }
                const lesson = t.kind === "lesson";
                const open = t.tests > 0;
                const row = (
                  <>
                    <span
                      className={`grid size-9 shrink-0 place-items-center rounded-xl text-sm font-bold ring-1 ${
                        lesson ? "bg-brand-50 text-brand-700 ring-brand-100" : "bg-amber-50 text-amber-600 ring-amber-100"
                      }`}
                    >
                      {lesson ? t.number ?? "•" : <ClipboardList className="size-4" />}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className={`block text-[15px] leading-snug ${lesson ? "font-semibold text-ink" : "font-bold text-ink/90"}`}>{t.title}</span>
                      {!lesson && <span className="text-xs font-semibold text-amber-600">Takrorlash</span>}
                      {t.attempts > 0 && <span className="block text-xs text-muted">{t.attempts} marta ishlangan</span>}
                    </span>
                    {t.best_percent !== null && <ResultBadge percent={t.best_percent} />}
                    <span
                      className={`shrink-0 rounded-lg px-2.5 py-1 text-xs font-semibold tabular-nums ${
                        open ? "bg-brand-50 text-brand-700" : "bg-slate-50 text-muted"
                      }`}
                    >
                      {open ? `${t.tests} ta test` : "Tez orada"}
                    </span>
                    {open ? (
                      <span className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-50 text-brand-600 transition-colors group-hover:bg-brand-600 group-hover:text-white">
                        <ArrowRight className="size-4" />
                      </span>
                    ) : (
                      <span className="grid size-8 shrink-0 place-items-center text-muted/50">
                        <Lock className="size-4" />
                      </span>
                    )}
                  </>
                );
                return (
                  <li key={t.id}>
                    {open ? (
                      <Link
                        href={`/dashboard/topics/${t.id}`}
                        className={`group -mx-2 flex items-center gap-3 rounded-xl px-2 py-3 transition-colors hover:bg-brand-50/60 ${lesson ? "" : "bg-amber-50/40"}`}
                      >
                        {row}
                      </Link>
                    ) : (
                      <div className={`-mx-2 flex items-center gap-3 rounded-xl px-2 py-3 opacity-55 ${lesson ? "" : "bg-amber-50/40"}`}>{row}</div>
                    )}
                  </li>
                );
              })}
              {visible.length === 0 && <li className="py-10 text-center text-sm text-muted">Hech narsa topilmadi</li>}
            </ol>
          )}
        </section>
      </div>
    </div>
  );
}
