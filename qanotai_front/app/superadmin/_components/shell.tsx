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
import type { Book } from "../../_lib/admin-api";
import { getMe, logout, type User } from "../../_lib/api";
import {
  BarChart,
  Bell,
  BookOpen,
  ChevronDown,
  ClipboardList,
  Close,
  Crown,
  FileText,
  Gem,
  HelpCircle,
  Home,
  Layers,
  ListChecks,
  LogOut,
  Menu,
  Percent,
  Search,
  Settings,
  Sparkles,
  UserIcon,
  Users,
} from "../../_components/icons";
import { BookFormModal } from "./book-form";
import { ConfirmDialog, Toasts, type ConfirmOptions, type Toast, type ToastTone } from "./feedback";
import { Avatar } from "./ui";

type Icon = ComponentType<SVGProps<SVGSVGElement>>;
type Item = { label: string; Icon: Icon; href?: string };

const SECTIONS: { title?: string; items: Item[] }[] = [
  { items: [{ label: "Bosh sahifa", Icon: Home, href: "/superadmin/dashboard" }] },
  {
    title: "Foydalanuvchilar",
    items: [
      { label: "Foydalanuvchilar", Icon: Users, href: "/superadmin/users" },
    ],
  },
  {
    title: "Ta'lim materiallari",
    items: [
      { label: "Fanlar", Icon: Layers, href: "/superadmin/subjects" },
      { label: "Kitoblar", Icon: BookOpen, href: "/superadmin/books" },
      { label: "Testlar", Icon: ClipboardList },
      { label: "Milliy sertifikatlar", Icon: FileText },
      { label: "Batafsil yechimlar", Icon: ListChecks },
    ],
  },
  {
    title: "Kontent va boshqa",
    items: [
      { label: "Bannerlar", Icon: Sparkles },
      { label: "Xabarnomalar", Icon: Bell },
      { label: "Statistik ma'lumotlar", Icon: BarChart },
    ],
  },
  {
    title: "To'lov va obuna",
    items: [
      { label: "Obunalar", Icon: Crown },
      { label: "To'lovlar", Icon: Gem },
      { label: "Promokodlar", Icon: Percent },
    ],
  },
  {
    title: "Tizim",
    items: [
      { label: "Sozlamalar", Icon: Settings },
      { label: "Yordam", Icon: HelpCircle },
    ],
  },
];

type AdminContext = {
  /** null until /api/auth/me confirms a superadmin (an overlay covers the page meanwhile) */
  user: User | null;
  soon: (what: string) => void;
  /** top-right notification */
  notify: (title: string, tone?: ToastTone, text?: string) => void;
  /** in-app confirmation dialog (replaces window.confirm) */
  ask: (options: ConfirmOptions) => void;
  openBookForm: (book: Book | null) => void;
  /** bumps after every save made through the shared book form, so pages can refetch */
  version: number;
};

const Ctx = createContext<AdminContext | null>(null);
export function useAdmin() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAdmin outside AdminShell");
  return ctx;
}

type SidebarProps = { onSoon: (label: string) => void; onNavigate: () => void };

// usePathname() is URL data: it lives inside <Suspense>, and the fallback is the same menu without
// the active highlight, so the rest of the shell never waits on it.
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

  const row = (active: boolean) =>
    `flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-[14px] transition-colors ${
      active ? "bg-brand-50 font-semibold text-brand-600" : "font-medium text-ink/75 hover:bg-brand-50/60 hover:text-ink"
    }`;

  return (
    <div className="flex h-full flex-col overflow-y-auto px-3 py-6">
      <Link href="/superadmin/dashboard" onClick={onNavigate} className="flex items-center gap-2 px-3">
        <BrandLogo className="h-10" />
      </Link>

      <nav className="mt-7 flex flex-col gap-5 pb-4">
        {SECTIONS.map((section, si) => (
          <div key={si}>
            {section.title && (
              <p className="mb-1.5 px-3 text-[11px] font-bold uppercase tracking-wider text-muted/80">{section.title}</p>
            )}
            <ul className="flex flex-col gap-0.5">
              {section.items.map(({ label, Icon, href }) => {
                const active = !!href && path.startsWith(href);
                const icon = <Icon className={`size-[18px] shrink-0 ${active ? "text-brand-600" : "text-slate-500"}`} />;
                return (
                  <li key={label}>
                    {href ? (
                      <Link href={href} onClick={onNavigate} className={row(active)} aria-current={active ? "page" : undefined}>
                        {icon} {label}
                      </Link>
                    ) : (
                      <button type="button" onClick={() => onSoon(label)} className={row(false)}>
                        {icon} {label}
                      </button>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </div>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [failed, setFailed] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const [menu, setMenu] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [confirm, setConfirm] = useState<ConfirmOptions | null>(null);
  const [bookForm, setBookForm] = useState<{ book: Book | null } | null>(null);
  const [version, setVersion] = useState(0);
  const toastId = useRef(0);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMe()
      .then((me) => {
        if (!me) router.replace("/?login=1");
        else if (!me.is_superadmin) router.replace("/dashboard");
        else setUser(me);
      })
      .catch(() => setFailed(true));
  }, [router]);

  useEffect(() => {
    if (!menu) return;
    const onDown = (e: MouseEvent) => !menuRef.current?.contains(e.target as Node) && setMenu(false);
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [menu]);

  const notify = useCallback((title: string, tone: ToastTone = "success", text?: string) => {
    const id = ++toastId.current;
    setToasts((list) => [...list.slice(-3), { id, tone, title, text }]); // keep at most 4 on screen
  }, []);
  const dismiss = useCallback((id: number) => setToasts((list) => list.filter((t) => t.id !== id)), []);
  const ask = useCallback((options: ConfirmOptions) => setConfirm(options), []);
  const closeConfirm = useCallback(() => setConfirm(null), []);

  const soon = useCallback(
    (what: string) => {
      setDrawer(false);
      notify(what, "info", "Bu bo'lim tez orada ishga tushadi");
    },
    [notify],
  );
  const openBookForm = useCallback((book: Book | null) => setBookForm({ book }), []);
  const closeBookForm = useCallback(() => setBookForm(null), []);

  // The page always renders underneath so its data loads in parallel with the auth check and Next can
  // validate the segment; until a superadmin is confirmed an opaque overlay hides it. The API itself
  // refuses non-admins (403), so nothing leaks while the overlay is up.
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

  return (
    <Ctx.Provider value={{ user, soon, notify, ask, openBookForm, version }}>
      <div className="flex min-h-screen">
        <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r border-brand-100/70 bg-white lg:block">
          <SidebarWithActive onSoon={soon} onNavigate={() => {}} />
        </aside>

        {drawer && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <button type="button" aria-label="Menyuni yopish" className="absolute inset-0 bg-ink/40" onClick={() => setDrawer(false)} />
            <aside className="relative h-full w-72 bg-white shadow-2xl">
              <button
                type="button"
                aria-label="Menyuni yopish"
                onClick={() => setDrawer(false)}
                className="absolute right-3 top-5 z-10 grid size-9 place-items-center rounded-lg text-muted hover:bg-brand-50"
              >
                <Close className="size-5" />
              </button>
              <SidebarWithActive onSoon={soon} onNavigate={() => setDrawer(false)} />
            </aside>
          </div>
        )}

        <div className="min-w-0 flex-1">
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
                const q = new FormData(e.currentTarget).get("q")?.toString().trim() ?? "";
                router.push(`/superadmin/users${q ? `?q=${encodeURIComponent(q)}` : ""}`);
              }}
              className="relative hidden max-w-md flex-1 sm:block"
            >
              <Search className="pointer-events-none absolute left-4 top-1/2 size-5 -translate-y-1/2 text-muted" />
              <input
                name="q"
                type="search"
                placeholder="Foydalanuvchini qidirish (ism, e-mail, telefon)…"
                className="w-full rounded-2xl bg-white py-3 pl-12 pr-4 text-sm text-ink ring-1 ring-brand-100 outline-none placeholder:text-muted/70 focus:ring-2 focus:ring-brand-400"
              />
            </form>

            <div className="ml-auto flex items-center gap-2 sm:gap-4">
              <Link href="/" className="hidden rounded-xl px-3 py-2 text-sm font-semibold text-brand-600 hover:bg-white sm:block">
                Saytga o&apos;tish
              </Link>
              <button
                type="button"
                aria-label="Bildirishnomalar"
                onClick={() => soon("Xabarnomalar")}
                className="relative grid size-10 place-items-center rounded-xl text-ink/70 hover:bg-white"
              >
                <Bell className="size-5" />
              </button>
              <div ref={menuRef} className="relative">
                <button
                  type="button"
                  onClick={() => setMenu((v) => !v)}
                  aria-expanded={menu}
                  className="flex items-center gap-2 rounded-full py-1 pl-1 pr-2 hover:bg-white"
                >
                  {user ? (
                    <Avatar name={user.full_name} src={user.avatar_url} className="size-10 text-sm" />
                  ) : (
                    <span className="size-10 rounded-full bg-brand-100" />
                  )}
                  <span className="hidden text-left sm:block">
                    <span className="block text-sm font-semibold leading-tight text-ink">Superadmin</span>
                    <span className="block max-w-36 truncate text-xs text-muted">{user?.full_name}</span>
                  </span>
                  <ChevronDown className="size-4 text-muted" />
                </button>
                {menu && (
                  <div className="absolute right-0 top-full mt-2 w-64 rounded-2xl bg-white p-2 shadow-xl ring-1 ring-brand-100">
                    <Link href="/dashboard" className="flex items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-ink/80 hover:bg-brand-50">
                      <UserIcon className="size-4" /> O&apos;quvchi kabineti
                    </Link>
                    <button
                      type="button"
                      onClick={async () => {
                        await logout().catch(() => {});
                        router.replace("/");
                      }}
                      className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold text-ink/80 hover:bg-red-50 hover:text-red-600"
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
        <Toasts items={toasts} onDismiss={dismiss} />
        {confirm && <ConfirmDialog options={confirm} onClose={closeConfirm} />}

        {bookForm && (
          <BookFormModal
            book={bookForm.book}
            onClose={closeBookForm}
            onSaved={(saved) => {
              notify(bookForm.book ? "Kitob saqlandi" : "Kitob qo'shildi", "success", saved.title);
              setBookForm(null);
              setVersion((v) => v + 1);
            }}
          />
        )}
      </div>
    </Ctx.Provider>
  );
}
