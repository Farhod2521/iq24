"use client";

import { BrandLogo } from "../../_components/brand-logo";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  Suspense,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ComponentType,
  type ReactNode,
  type SVGProps,
} from "react";
import { getMe, logout, type User } from "../../_lib/api";
import {
  ArrowRight,
  BarChart,
  Bell,
  BookOpen,
  Bookmark,
  ChevronDown,
  ClipboardList,
  Close,
  Crown,
  Home,
  LogOut,
  Medal,
  Menu,
  Search,
  Settings,
  Trophy,
  Users,
} from "../../_components/icons";
import { topStats } from "../dashboard-data";

type Icon = ComponentType<SVGProps<SVGSVGElement>>;

const nav: { label: string; Icon: Icon; href?: string; match?: string[] }[] = [
  { label: "Bosh sahifa", Icon: Home, href: "/dashboard" },
  { label: "Fanlar", Icon: BookOpen, href: "/dashboard#fanlar", match: ["/dashboard/books", "/dashboard/topics"] },
  { label: "Mening darslarim", Icon: Bookmark },
  { label: "Testlar", Icon: ClipboardList },
  { label: "Natijalar", Icon: BarChart },
  { label: "Reyting", Icon: Trophy },
  { label: "Yutuqlar", Icon: Medal },
  { label: "Do'stlar", Icon: Users },
  { label: "Sozlamalar", Icon: Settings },
]

function Avatar({ user, className }: { user: User; className: string }) {
  if (user.avatar_url) {
    // eslint-disable-next-line @next/next/no-img-element -- Google avatar on an arbitrary googleusercontent host
    return <img src={user.avatar_url} alt="" referrerPolicy="no-referrer" className={`rounded-full object-cover ${className}`} />;
  }
  const initials = user.full_name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
  return (
    <span className={`grid place-items-center rounded-full bg-gradient-to-br from-brand-600 to-sky-500 font-bold text-white ${className}`}>
      {initials || "?"}
    </span>
  );
}

function Coin({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className}>
      <circle cx="12" cy="12" r="10" fill="#f5b100" />
      <circle cx="12" cy="12" r="7" fill="#ffd34d" stroke="#e09a00" strokeWidth="1.2" />
      <path d="M12 8.5v7" stroke="#e09a00" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  );
}

function StarFill({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className={className}>
      <path fill="#2f6bff" d="m12 2.5 2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4l-5.9 3.1 1.2-6.5L2.5 9.4l6.6-.9L12 2.5Z" />
    </svg>
  );
}

type SidebarProps = { onSoon: (label: string) => void; onNavigate?: () => void };

// usePathname() is URL data: read it inside <Suspense>; the fallback is the same menu without a highlight
function ActiveSidebar(props: SidebarProps) {
  return <Sidebar {...props} path={usePathname()} />;
}

function SidebarWithActive(props: SidebarProps) {
  return (
    <Suspense fallback={<Sidebar {...props} path="" />}>
      <ActiveSidebar {...props} />
    </Suspense>
  );
}

function Sidebar({ onSoon, onNavigate, path }: SidebarProps & { path: string }) {
  return (
    <div className="flex h-full flex-col px-4 py-6">
      <Link href="/dashboard" className="flex items-center gap-2 px-3" onClick={onNavigate}>
        <BrandLogo className="h-10" />
      </Link>

      <nav className="mt-9 flex flex-col gap-1">
        {nav.map(({ label, Icon, href, match }) => {
          const active = match ? match.some((m) => path.startsWith(m)) : href === path;
          const cls = `flex items-center gap-3 rounded-xl px-4 py-3 text-left text-[15px] font-medium transition-colors ${
            active ? "bg-brand-50 font-semibold text-brand-600" : "text-ink/75 hover:bg-brand-50/60 hover:text-ink"
          }`;
          const icon = <Icon className={`size-5 ${active ? "text-brand-600" : "text-slate-500"}`} />;
          return href ? (
            <Link key={label} href={href} onClick={onNavigate} aria-current={active ? "page" : undefined} className={cls}>
              {icon} {label}
            </Link>
          ) : (
            <button key={label} type="button" onClick={() => onSoon(label)} className={cls}>
              {icon} {label}
            </button>
          );
        })}
      </nav>

      <div className="mt-auto rounded-3xl bg-gradient-to-b from-brand-100 to-brand-50 p-5 text-center ring-1 ring-brand-100">
        <span className="text-3xl">👑</span>
        <p className="mt-1 text-lg font-extrabold text-ink">IQ24 Pro</p>
        <p className="mt-1 text-sm leading-snug text-muted">Ko&apos;proq imkoniyatlar sari bir qadam</p>
        <Link
          href="/#narxlar"
          className="mt-4 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition-colors hover:bg-brand-700"
        >
          Obuna bo&apos;lish <ArrowRight className="size-4" />
        </Link>
      </div>
    </div>
  );
}

type StudentContext = { user: User | null; soon: (what: string) => void };
const Ctx = createContext<StudentContext>({ user: null, soon: () => {} });
export const useStudent = () => useContext(Ctx);

/** Sidebar + top bar around every /dashboard page. The page renders underneath while the session is checked. */
export function StudentShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [failed, setFailed] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [menu, setMenu] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMe()
      .then((me) => (me ? setUser(me) : router.replace("/?login=1")))
      .catch(() => setFailed(true));
  }, [router]);

  // close the profile menu on an outside click
  useEffect(() => {
    if (!menu) return;
    const onDown = (e: MouseEvent) => !menuRef.current?.contains(e.target as Node) && setMenu(false);
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [menu]);

  const soon = useCallback((what: string) => {
    setDrawer(false);
    setToast(`«${what}» bo'limi tez orada ishga tushadi`);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2600);
  }, []);

  async function signOut() {
    await logout().catch(() => {});
    router.replace("/");
  }

  const gate = (failed || !user) && (
    <div className="fixed inset-0 z-[90] grid place-items-center bg-background p-6 text-center">
      {failed ? (
        <div>
          <p className="text-lg font-bold text-ink">Server bilan bog&apos;lanib bo&apos;lmadi</p>
          <p className="mt-1 text-muted">Birozdan so&apos;ng sahifani yangilang.</p>
        </div>
      ) : (
        <span aria-label="Yuklanmoqda" className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
      )}
    </div>
  );

  const firstName = user?.full_name.split(/\s+/)[0] ?? "";

  return (
    <Ctx.Provider value={{ user, soon }}>
    <div className="flex min-h-screen">
      {/* sidebar (desktop) */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r border-brand-100/70 bg-white lg:block">
        <SidebarWithActive onSoon={soon} />
      </aside>

      {/* sidebar (mobile drawer) */}
      {drawer && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button type="button" aria-label="Menyuni yopish" className="absolute inset-0 bg-ink/40" onClick={() => setDrawer(false)} />
          <aside className="relative h-full w-72 bg-white shadow-2xl">
            <button
              type="button"
              aria-label="Menyuni yopish"
              onClick={() => setDrawer(false)}
              className="absolute right-3 top-5 grid size-9 place-items-center rounded-lg text-muted hover:bg-brand-50"
            >
              <Close className="size-5" />
            </button>
            <SidebarWithActive onSoon={soon} onNavigate={() => setDrawer(false)} />
          </aside>
        </div>
      )}

      <div className="min-w-0 flex-1">
        {/* top bar */}
        <header className="sticky top-0 z-30 flex items-center gap-3 bg-background/85 px-4 py-4 backdrop-blur-md sm:px-6 lg:px-8">
          <button
            type="button"
            aria-label="Menyuni ochish"
            onClick={() => setDrawer(true)}
            className="grid size-10 shrink-0 place-items-center rounded-xl text-ink ring-1 ring-brand-100 lg:hidden"
          >
            <Menu className="size-5" />
          </button>

          <form
            role="search"
            onSubmit={(e) => {
              e.preventDefault();
              soon("Qidiruv");
            }}
            className="relative hidden max-w-md flex-1 sm:block"
          >
            <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
            <input
              type="search"
              placeholder="Dars, mavzu yoki test qidiring..."
              className="w-full rounded-2xl bg-white py-3 pl-12 pr-4 text-sm text-ink ring-1 ring-brand-100 outline-none placeholder:text-muted/70 focus:ring-2 focus:ring-brand-400"
            />
          </form>

          <div className="ml-auto flex items-center gap-2 sm:gap-6">
            <dl className="hidden items-center gap-6 md:flex">
              {[
                { icon: <span className="text-2xl leading-none">🔥</span>, value: topStats.streakDays, label: "Kun ketma-ket" },
                { icon: <Coin className="size-7" />, value: topStats.coins, label: "Tangalar" },
                { icon: <StarFill className="size-7" />, value: topStats.points.toLocaleString("ru-RU"), label: "Ballar" },
              ].map((s) => (
                <div key={s.label} className="flex items-center gap-2">
                  {s.icon}
                  <div className="leading-tight">
                    <dd className="text-[15px] font-extrabold text-ink">{s.value}</dd>
                    <dt className="text-[11px] text-muted">{s.label}</dt>
                  </div>
                </div>
              ))}
            </dl>

            <button
              type="button"
              aria-label="Bildirishnomalar"
              onClick={() => soon("Bildirishnomalar")}
              className="relative grid size-10 place-items-center rounded-xl text-ink/70 hover:bg-white"
            >
              <Bell className="size-5" />
              <span className="absolute right-2 top-2 size-2 rounded-full bg-rose-500 ring-2 ring-background" />
            </button>

            <div ref={menuRef} className="relative">
              <button
                type="button"
                onClick={() => setMenu((v) => !v)}
                aria-expanded={menu}
                className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 hover:bg-white"
              >
                {user ? <Avatar user={user} className="size-10 text-sm" /> : <span className="size-10 rounded-full bg-brand-100" />}
                <span className="hidden max-w-32 truncate text-sm font-semibold text-ink sm:block">{firstName}</span>
                <ChevronDown className="size-4 text-muted" />
              </button>
              {menu && user && (
                <div className="absolute right-0 top-full mt-2 w-72 rounded-2xl bg-white p-4 shadow-xl ring-1 ring-brand-100">
                  <div className="flex items-center gap-3">
                    <Avatar user={user} className="size-11 text-sm" />
                    <div className="min-w-0">
                      <p className="truncate font-bold text-ink">{user.full_name}</p>
                      <p className="truncate text-xs text-muted">
                        {user.email ?? (user.telegram_username ? `@${user.telegram_username}` : user.phone ?? "")}
                      </p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center gap-2 rounded-xl bg-brand-50 px-3 py-2 text-xs font-semibold text-brand-700">
                    <Crown className="size-4" /> {user.plan === "free" ? "Bepul" : user.plan} tarif
                  </div>
                  {user.is_superadmin && (
                    <Link
                      href="/superadmin/dashboard"
                      className="mt-3 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-brand-700 hover:bg-brand-50"
                    >
                      <Settings className="size-4" /> Superadmin panel
                    </Link>
                  )}
                  <button
                    type="button"
                    onClick={signOut}
                    className="mt-1 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-ink/80 hover:bg-red-50 hover:text-red-600"
                  >
                    <LogOut className="size-4" /> Chiqish
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        <main className="px-4 pb-10 sm:px-6 lg:px-8">{children}</main>
      </div>

      {gate}
      {toast && (
        <div role="status" className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-white shadow-xl">
          {toast}
        </div>
      )}
    </div>
    </Ctx.Provider>
  );
}
