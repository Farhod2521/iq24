"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { adminApi, type AdminUser } from "../../_lib/admin-api";
import { Check, Search, Telegram } from "../../_components/icons";
import { Avatar, card, formatDate, inputClass, PageHead, timeAgo } from "../_components/ui";

type Page = { total: number; page: number; per_page: number; items: AdminUser[] };

export function UsersView() {
  const initialQ = useSearchParams().get("q") ?? "";
  // remount when the header search navigates here with a new ?q=
  return <UsersList key={initialQ} initialQ={initialQ} />;
}

function UsersList({ initialQ }: { initialQ: string }) {
  const [q, setQ] = useState(initialQ);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const t = setTimeout(() => {
      adminApi
        .users(q.trim(), page)
        .then(setData)
        .catch(() => setError("Foydalanuvchilarni yuklab bo'lmadi"));
    }, 250); // debounce typing
    return () => clearTimeout(t);
  }, [q, page]);

  const pages = data ? Math.max(1, Math.ceil(data.total / data.per_page)) : 1;

  return (
    <div className="flex flex-col gap-6">
      <PageHead title="Foydalanuvchilar" subtitle={data ? `Jami ${data.total} ta foydalanuvchi` : "Ro'yxatdan o'tgan foydalanuvchilar"} />

      <label className="relative max-w-xl">
        <span className="sr-only">Qidirish</span>
        <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
        <input
          className={`${inputClass} pl-12`}
          placeholder="Ism, e-mail, telefon yoki Telegram username…"
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setPage(1);
          }}
        />
      </label>

      {error && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{error}</p>}

      <div className={`overflow-x-auto ${card}`}>
        <table className="w-full min-w-[760px] text-left text-sm">
          <thead>
            <tr className="border-b border-brand-50 text-xs uppercase tracking-wider text-muted">
              <th className="px-5 py-4 font-semibold">Foydalanuvchi</th>
              <th className="px-5 py-4 font-semibold">Aloqa</th>
              <th className="px-5 py-4 font-semibold">Kirish usuli</th>
              <th className="px-5 py-4 font-semibold">Tarif</th>
              <th className="px-5 py-4 font-semibold">Ro&apos;yxatdan o&apos;tgan</th>
              <th className="px-5 py-4 font-semibold">Oxirgi kirish</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-brand-50">
            {data?.items.map((u) => (
              <tr key={u.id} className="hover:bg-brand-50/40">
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-3">
                    <Avatar name={u.full_name} src={u.avatar_url} className="size-9 text-xs" />
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-ink">{u.full_name}</p>
                      <p className="text-xs text-muted">ID {u.id}</p>
                    </div>
                  </div>
                </td>
                <td className="px-5 py-3.5 text-ink/80">
                  {u.email && <p className="truncate">{u.email}</p>}
                  {u.phone && <p>{u.phone}</p>}
                  {u.telegram_username && <p className="text-xs text-muted">@{u.telegram_username}</p>}
                  {!u.email && !u.phone && !u.telegram_username && <span className="text-muted">—</span>}
                </td>
                <td className="px-5 py-3.5">
                  <div className="flex flex-wrap gap-1.5">
                    {u.has_telegram && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2 py-1 text-xs font-semibold text-sky-700">
                        <Telegram className="size-3" /> Telegram
                      </span>
                    )}
                    {u.has_google && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
                        <Check className="size-3" strokeWidth={3} /> Google
                      </span>
                    )}
                  </div>
                </td>
                <td className="px-5 py-3.5">
                  <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-semibold text-brand-700">
                    {u.plan === "free" ? "Bepul" : u.plan}
                  </span>
                </td>
                <td className="px-5 py-3.5 text-ink/80">{formatDate(u.created_at)}</td>
                <td className="px-5 py-3.5 text-ink/80">{u.last_login_at ? timeAgo(u.last_login_at) : "—"}</td>
              </tr>
            ))}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center text-muted">
                  Foydalanuvchi topilmadi
                </td>
              </tr>
            )}
            {!data && (
              <tr>
                <td colSpan={6} className="px-5 py-12 text-center">
                  <span className="inline-block size-8 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex items-center justify-end gap-3 text-sm">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded-xl px-4 py-2 font-semibold text-brand-600 ring-1 ring-brand-100 disabled:opacity-40"
          >
            ← Oldingi
          </button>
          <span className="text-muted">
            {page} / {pages}
          </span>
          <button
            type="button"
            disabled={page >= pages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-xl px-4 py-2 font-semibold text-brand-600 ring-1 ring-brand-100 disabled:opacity-40"
          >
            Keyingi →
          </button>
        </div>
      )}
    </div>
  );
}
