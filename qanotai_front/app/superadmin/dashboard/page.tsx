"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState, type ComponentType, type ReactNode, type SVGProps } from "react";
import { adminApi, type Book, type Overview } from "../../_lib/admin-api";
import {
  ArrowRight,
  BookOpen,
  CalendarCheck,
  ClipboardList,
  Gem,
  Layers,
  Telegram,
  UserIcon,
  UserPlus,
  Users,
} from "../../_components/icons";
import { useAdmin } from "../_components/shell";
import { card, GrowthBadge, SUBJECT_COLORS, timeAgo } from "../_components/ui";

type Icon = ComponentType<SVGProps<SVGSVGElement>>;

function Spark({ values, tone }: { values: number[]; tone: string }) {
  const max = Math.max(1, ...values);
  return (
    <span className="flex h-8 items-end gap-[3px]" aria-hidden="true">
      {values.map((v, i) => (
        <span key={i} className={`w-1.5 rounded-sm ${tone}`} style={{ height: `${Math.max(12, (v / max) * 100)}%`, opacity: 0.35 + (i / values.length) * 0.65 }} />
      ))}
    </span>
  );
}

function Kpi({ Icon, tone, value, label, foot, spark }: { Icon: Icon; tone: string; value: ReactNode; label: string; foot: ReactNode; spark?: ReactNode }) {
  return (
    <div className={`flex items-start gap-3 p-4 ${card}`}>
      <span className={`grid size-11 shrink-0 place-items-center rounded-2xl ${tone}`}>
        <Icon className="size-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-xl font-extrabold text-ink">{value}</p>
        <p className="text-xs leading-snug text-muted">{label}</p>
        <div className="mt-2 flex items-end justify-between gap-2">
          <span>{foot}</span>
          {spark}
        </div>
      </div>
    </div>
  );
}

function SectionHead({ title, href, action }: { title: string; href?: string; action?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <h2 className="text-lg font-extrabold text-ink">{title}</h2>
      {href ? (
        <Link href={href} className="flex items-center gap-1.5 text-sm font-semibold text-brand-600 hover:text-brand-700">
          Barchasini ko&apos;rish <ArrowRight className="size-4" />
        </Link>
      ) : (
        action
      )}
    </div>
  );
}

export default function AdminDashboard() {
  const { openBookForm, version } = useAdmin();
  const [data, setData] = useState<Overview | null>(null);
  const [books, setBooks] = useState<Book[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([adminApi.overview(), adminApi.books()])
      .then(([o, b]) => {
        setData(o);
        setBooks(b.slice(0, 6));
      })
      .catch(() => setError("Ma'lumotlarni yuklab bo'lmadi"));
  }, [version]);

  if (error) return <p className="rounded-2xl bg-rose-50 p-6 text-rose-700">{error}</p>;
  if (!data) {
    return (
      <div className="grid h-96 place-items-center">
        <span className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
      </div>
    );
  }

  const newPerDay = data.days.map((d) => d.new);
  const chartMax = Math.max(4, ...data.days.flatMap((d) => [d.new, d.active]));
  const subjectMax = Math.max(1, ...data.per_subject.map((s) => s.tests));

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="flex min-w-0 flex-col gap-6">
        {/* banner */}
        <section className="relative overflow-hidden rounded-3xl shadow-card ring-1 ring-brand-100/70">
          <Image src="/images/dashboard-hero.webp" alt="" fill priority unoptimized className="object-cover object-[78%_62%]" />
          <div className="absolute inset-0 bg-gradient-to-r from-white/85 via-white/40 via-30% to-transparent to-55% max-sm:bg-white/60" />
          <div className="relative max-w-md px-6 py-8 sm:px-12 sm:py-11">
            <p className="text-lg font-semibold text-ink">👋 Xush kelibsiz,</p>
            <p className="mt-1 bg-gradient-to-r from-brand-700 to-brand-500 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent sm:text-5xl">
              Superadmin!
            </p>
            <p className="mt-3 max-w-xs text-[15px] leading-relaxed text-ink/80">
              IQ24 ta&apos;lim platformasini boshqarish paneliga xush kelibsiz.
            </p>
            <button
              type="button"
              onClick={() => openBookForm(null)}
              className="mt-6 inline-flex items-center gap-2 rounded-full bg-brand-600 px-7 py-3.5 text-[15px] font-semibold text-white shadow-lg shadow-brand-600/30 transition-colors hover:bg-brand-700"
            >
              Yangi kitob qo&apos;shish <ArrowRight className="size-4" />
            </button>
          </div>
        </section>

        {/* KPIs */}
        <section className="grid grid-cols-2 gap-4 md:grid-cols-3 min-[1760px]:grid-cols-5">
          <Kpi
            Icon={Users}
            tone="bg-violet-50 text-violet-600"
            value={data.users.total.toLocaleString("ru-RU")}
            label="Jami foydalanuvchilar"
            foot={<GrowthBadge value={data.users.weekly_growth} />}
            spark={<Spark values={newPerDay} tone="bg-violet-500" />}
          />
          <Kpi Icon={Layers} tone="bg-amber-50 text-amber-600" value={data.subjects} label="Fanlar" foot={<Link href="/superadmin/subjects" className="whitespace-nowrap text-xs font-semibold text-brand-600">Boshqarish →</Link>} />
          <Kpi Icon={BookOpen} tone="bg-indigo-50 text-indigo-600" value={data.books} label="Kitoblar" foot={<Link href="/superadmin/books" className="whitespace-nowrap text-xs font-semibold text-brand-600">Boshqarish →</Link>} />
          <Kpi Icon={ClipboardList} tone="bg-sky-50 text-sky-600" value={data.tests.toLocaleString("ru-RU")} label="Testlar" foot={<span className="text-xs text-muted">kitoblar bo&apos;yicha</span>} />
          <Kpi Icon={Gem} tone="bg-orange-50 text-orange-500" value="0 so'm" label="Jami to'lovlar" foot={<span className="text-xs text-muted">tez orada</span>} />
        </section>

        {/* books */}
        <section className={`p-5 ${card}`}>
          <SectionHead title="Asosiy fanlar va kitoblar" href="/superadmin/books" />
          {books.length === 0 ? (
            <p className="mt-6 text-sm text-muted">Hali kitob qo&apos;shilmagan.</p>
          ) : (
            <ul className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 2xl:grid-cols-6">
              {books.map((b) => (
                <li key={b.id}>
                  <button
                    type="button"
                    onClick={() => openBookForm(b)}
                    className="group flex w-full flex-col overflow-hidden rounded-2xl text-left ring-1 ring-brand-100/80 transition hover:-translate-y-0.5 hover:shadow-lg"
                  >
                    <span className="relative block h-36 bg-gradient-to-b from-brand-50 to-white">
                      {b.cover_url ? (
                        <Image src={b.cover_url} alt={b.title} fill unoptimized className="object-contain p-2.5 drop-shadow-lg" />
                      ) : (
                        <BookOpen className="absolute inset-0 m-auto size-10 text-brand-300" />
                      )}
                    </span>
                    <span className="px-3 pb-3 pt-2.5">
                      <span className="line-clamp-2 text-[13px] font-bold leading-snug text-ink">
                        {b.title}
                        {b.year && ` (${b.year})`}
                      </span>
                      <span className="mt-1 flex items-center justify-between text-xs text-muted">
                        {b.test_count} ta test
                        <span className="grid size-6 place-items-center rounded-full bg-brand-50 text-brand-600 group-hover:bg-brand-600 group-hover:text-white">
                          <ArrowRight className="size-3.5" />
                        </span>
                      </span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* activity */}
          <section className={`p-5 ${card}`}>
            <SectionHead title="So'nggi faolliklar" href="/superadmin/users" />
            <ul className="mt-3 divide-y divide-brand-50">
              {data.activity.map((a, i) => (
                <li key={i} className="flex items-center gap-3 py-3">
                  <span className={`grid size-10 shrink-0 place-items-center rounded-xl ${a.kind === "user" ? "bg-brand-50 text-brand-600" : "bg-rose-50 text-rose-500"}`}>
                    {a.kind === "user" ? <UserPlus className="size-5" /> : <BookOpen className="size-5" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink">{a.title}</p>
                    <p className="truncate text-xs text-muted">{a.detail}</p>
                  </div>
                  <span className="shrink-0 text-xs text-muted">{timeAgo(a.at)}</span>
                </li>
              ))}
              {data.activity.length === 0 && <li className="py-6 text-sm text-muted">Hali faollik yo&apos;q.</li>}
            </ul>
          </section>

          {/* per subject */}
          <section className={`p-5 ${card}`}>
            <SectionHead title="Fanlar bo'yicha testlar" href="/superadmin/subjects" />
            <ul className="mt-4 flex flex-col gap-3.5">
              {data.per_subject.map((s) => {
                const c = SUBJECT_COLORS[s.color] ?? SUBJECT_COLORS.blue;
                return (
                  <li key={s.id} className="grid grid-cols-[1.75rem_6.5rem_1fr_3.5rem] items-center gap-3 text-sm">
                    <span className={`grid size-7 place-items-center rounded-lg ${c.soft}`}>
                      <BookOpen className="size-4" />
                    </span>
                    <span className="truncate text-ink">{s.name}</span>
                    <span className="h-2 overflow-hidden rounded-full bg-brand-50">
                      <span className={`block h-full rounded-full ${c.bar}`} style={{ width: `${(s.tests / subjectMax) * 100}%` }} />
                    </span>
                    <span className="text-right">
                      <span className="block font-semibold text-ink">{s.tests.toLocaleString("ru-RU")}</span>
                      <span className="block text-[11px] text-muted">{s.books} kitob</span>
                    </span>
                  </li>
                );
              })}
            </ul>
          </section>
        </div>
      </div>

      {/* right column */}
      <div className="flex flex-col gap-6">
        <section className={`p-5 ${card}`}>
          <h2 className="text-lg font-extrabold text-ink">Bugungi holat</h2>
          <ul className="mt-3 divide-y divide-brand-50">
            {[
              { Icon: UserPlus, tone: "bg-brand-50 text-brand-600", label: "Yangi ro'yxatdan o'tganlar", value: data.users.new_today, growth: <GrowthBadge value={data.users.new_today_growth} /> },
              { Icon: Users, tone: "bg-emerald-50 text-emerald-600", label: "Faol foydalanuvchilar", value: data.users.active_today, growth: <GrowthBadge value={data.users.active_today_growth} /> },
              { Icon: Gem, tone: "bg-amber-50 text-amber-600", label: "Yangi to'lovlar", value: "—", growth: <span className="text-xs text-muted">tez orada</span> },
              { Icon: CalendarCheck, tone: "bg-sky-50 text-sky-600", label: "Bajarilgan testlar", value: "—", growth: <span className="text-xs text-muted">tez orada</span> },
            ].map((r) => (
              <li key={r.label} className="flex items-center gap-3 py-3">
                <span className={`grid size-11 shrink-0 place-items-center rounded-2xl ${r.tone}`}>
                  <r.Icon className="size-5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-xs text-muted">{r.label}</p>
                  <p className="text-lg font-extrabold text-ink">{r.value}</p>
                </div>
                {r.growth}
              </li>
            ))}
          </ul>
        </section>

        <section className={`p-5 ${card}`}>
          <h2 className="text-lg font-extrabold text-ink">Foydalanuvchilar statistikasi</h2>
          <p className="text-xs text-muted">So&apos;nggi 7 kun</p>
          <div className="mt-5 flex h-40 items-end justify-between gap-2 border-b border-brand-50">
            {data.days.map((d) => (
              <div key={d.date} className="flex h-full flex-1 items-end justify-center gap-1" title={`${d.date}: ${d.new} yangi, ${d.active} faol`}>
                <span className="w-2.5 rounded-t bg-brand-600" style={{ height: `${(d.new / chartMax) * 100}%`, minHeight: d.new ? 4 : 0 }} />
                <span className="w-2.5 rounded-t bg-brand-200" style={{ height: `${(d.active / chartMax) * 100}%`, minHeight: d.active ? 4 : 0 }} />
              </div>
            ))}
          </div>
          <div className="mt-2 flex justify-between text-[11px] text-muted">
            {data.days.map((d) => (
              <span key={d.date} className="flex-1 text-center">
                {d.label}
              </span>
            ))}
          </div>
          <div className="mt-4 flex gap-5 text-xs text-muted">
            <span className="flex items-center gap-1.5">
              <span className="size-2.5 rounded-sm bg-brand-600" /> Yangi
            </span>
            <span className="flex items-center gap-1.5">
              <span className="size-2.5 rounded-sm bg-brand-200" /> Faol (oxirgi kirish)
            </span>
          </div>
        </section>

        <section className={`p-5 ${card}`}>
          <h2 className="text-lg font-extrabold text-ink">Tezkor amallar</h2>
          <div className="mt-4 grid grid-cols-3 gap-2.5">
            {[
              { label: "Yangi kitob", Icon: BookOpen, onClick: () => openBookForm(null) },
              { label: "Yangi fan", Icon: Layers, href: "/superadmin/subjects?new=1" },
              { label: "Foydalanuv-chilar", Icon: Users, href: "/superadmin/users" },
              { label: "Kitoblar", Icon: ClipboardList, href: "/superadmin/books" },
              { label: "Sayt", Icon: UserIcon, href: "/" },
              { label: "Telegram bot", Icon: Telegram, href: "https://t.me/qanotaibot" },
            ].map((a) => {
              const cls =
                "flex flex-col items-center gap-2 rounded-2xl px-2 py-3 text-center text-xs font-semibold text-ink/80 ring-1 ring-brand-100 transition hover:bg-brand-50 hover:text-brand-700";
              const inner = (
                <>
                  <a.Icon className="size-5 text-brand-600" />
                  {a.label}
                </>
              );
              return a.href ? (
                <Link key={a.label} href={a.href} className={cls} target={a.href.startsWith("http") ? "_blank" : undefined}>
                  {inner}
                </Link>
              ) : (
                <button key={a.label} type="button" onClick={a.onClick} className={cls}>
                  {inner}
                </button>
              );
            })}
          </div>
        </section>

        <section className="relative min-h-56 overflow-hidden rounded-3xl bg-gradient-to-br from-sky-200 via-sky-100 to-amber-50 p-6 shadow-card ring-1 ring-brand-100/70">
          <h2 className="relative max-w-[13rem] text-lg font-extrabold text-ink">Platformani yanada rivojlantiring</h2>
          <p className="relative mt-2 max-w-[12rem] text-sm text-ink/75">Yangi kitoblar va testlar qo&apos;shib, ko&apos;proq o&apos;quvchilarga bilim yetkazing!</p>
          <button
            type="button"
            onClick={() => openBookForm(null)}
            className="relative mt-5 inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-brand-600 shadow ring-1 ring-brand-100 hover:bg-brand-50"
          >
            Yangi kontent qo&apos;shish <ArrowRight className="size-4" />
          </button>
          <Image src="/images/books/stack.webp" alt="" width={722} height={560} sizes="180px" className="pointer-events-none absolute -bottom-3 -right-3 w-[45%] max-w-44 drop-shadow-xl" />
        </section>
      </div>
    </div>
  );
}
