"use client";

import { BrandLogo } from "./brand-logo";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { getMe, LOGIN_ERRORS, type User } from "../_lib/api";
import { ChevronDown, Close, LogIn, Menu, Search, UserIcon } from "./icons";
import { LoginModal } from "./login-modal";

const links = [
  { href: "#bosh", label: "Bosh sahifa" },
  { href: "#fanlar", label: "Fanlar" },
  { href: "#testlar", label: "Testlar" },
  { href: "#ilova", label: "Ilova" },
  { href: "#narxlar", label: "Narxlar" },
  { href: "#biz-haqimizda", label: "Biz haqimizda" },
];

export function Logo({ light = false }: { light?: boolean }) {
  return (
    <a href="#bosh" className="flex items-center gap-2">
      <BrandLogo className={light ? "h-11" : "h-10"} />
    </a>
  );
}

function UzFlag({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 30 20" className={className} aria-hidden="true">
      <rect width="30" height="6.4" fill="#0099b5" />
      <rect y="6.4" width="30" height="0.6" fill="#ce1126" />
      <rect y="7" width="30" height="6" fill="white" />
      <rect y="13" width="30" height="0.6" fill="#ce1126" />
      <rect y="13.6" width="30" height="6.4" fill="#1eb53a" />
      <circle cx="5" cy="3.2" r="2.1" fill="white" />
      <circle cx="5.8" cy="3.2" r="1.8" fill="#0099b5" />
    </svg>
  );
}

export function Navbar() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [loginNotice, setLoginNotice] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const closeLogin = useCallback(() => {
    setLoginOpen(false);
    setLoginNotice(null);
  }, []);

  useEffect(() => {
    // "/?login=1" (from the dashboard guard or a failed Google sign-in) opens the dialog for signed-out visitors
    const params = new URLSearchParams(window.location.search);
    const wantsLogin = params.has("login");
    const notice = LOGIN_ERRORS[params.get("login_error") ?? ""] ?? null;
    if (wantsLogin) window.history.replaceState(null, "", window.location.pathname + window.location.hash);

    const openLogin = () => {
      if (!wantsLogin) return;
      setLoginNotice(notice);
      setLoginOpen(true);
    };
    getMe()
      .then((me) => {
        setUser(me);
        if (!me) openLogin();
      })
      .catch(openLogin); // backend unreachable: stay signed out
  }, []);

  // the tests live in the cabinet: signed-in visitors go there, everyone else signs in first
  const search = (e: FormEvent) => {
    e.preventDefault();
    if (user) router.push("/dashboard");
    else setLoginOpen(true);
  };

  return (
    <header className="sticky top-0 z-50 border-b border-white/60 bg-white/75 backdrop-blur-lg">
      <nav className="mx-auto flex h-20 max-w-7xl items-center gap-4 px-4 sm:px-6 lg:px-8 2xl:max-w-[96rem]">
        <Logo />

        <ul className="ml-4 hidden items-center gap-1 text-sm font-semibold whitespace-nowrap text-ink/80 xl:flex 2xl:ml-8 2xl:gap-2 2xl:text-[15px]">
          {links.map((l, i) => (
            <li key={l.href}>
              <a
                href={l.href}
                className={`rounded-xl px-3 py-2.5 transition-colors hover:text-brand-600 ${
                  i === 0 ? "bg-brand-50 text-brand-600" : ""
                }`}
              >
                {l.label}
              </a>
            </li>
          ))}
        </ul>

        <form
          onSubmit={search}
          className="ml-auto hidden h-11 min-w-0 flex-1 items-center gap-2 rounded-xl bg-white px-3.5 ring-1 ring-brand-100 focus-within:ring-2 focus-within:ring-brand-400 lg:flex xl:ml-4 xl:max-w-64 2xl:max-w-80"
        >
          <Search className="size-4 shrink-0 text-muted" />
          <input
            type="search"
            placeholder="Fan yoki mavzu qidiring..."
            aria-label="Qidirish"
            className="w-full min-w-0 bg-transparent text-sm text-ink outline-none placeholder:text-muted/80"
          />
        </form>

        <div className="ml-auto flex items-center gap-2.5 lg:ml-0">
          <button
            type="button"
            className="hidden h-11 items-center gap-2 rounded-xl bg-white px-3 text-sm font-bold text-ink ring-1 ring-brand-100 hover:bg-brand-50 sm:flex"
          >
            <UzFlag className="h-3.5 w-5 rounded-[3px] ring-1 ring-black/5" /> UZ
            <ChevronDown className="size-4 text-muted" />
          </button>
          {user ? (
            <Link
              href="/dashboard"
              className="hidden h-11 items-center gap-2 rounded-xl bg-brand-600 px-5 text-sm font-semibold whitespace-nowrap text-white shadow-lg shadow-brand-600/25 transition-colors hover:bg-brand-700 sm:inline-flex"
            >
              <UserIcon className="size-4" /> Kabinet
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => setLoginOpen(true)}
              className="hidden h-11 items-center gap-2 rounded-xl bg-brand-600 px-5 text-sm font-semibold whitespace-nowrap text-white shadow-lg shadow-brand-600/25 transition-colors hover:bg-brand-700 sm:inline-flex"
            >
              <LogIn className="size-4" /> Tizimga kirish
            </button>
          )}
          <button
            type="button"
            aria-label={open ? "Menyuni yopish" : "Menyuni ochish"}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="grid size-10 place-items-center rounded-xl text-ink hover:bg-brand-50 xl:hidden"
          >
            {open ? <Close className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </nav>

      {open && (
        <div className="border-t border-brand-100 bg-white px-4 pb-5 xl:hidden">
          <form onSubmit={search} className="mt-4 flex h-11 items-center gap-2 rounded-xl bg-brand-50/60 px-3.5 ring-1 ring-brand-100 lg:hidden">
            <Search className="size-4 shrink-0 text-muted" />
            <input
              type="search"
              placeholder="Fan yoki mavzu qidiring..."
              aria-label="Qidirish"
              className="w-full min-w-0 bg-transparent text-sm text-ink outline-none placeholder:text-muted/80"
            />
          </form>
          <ul className="flex flex-col py-2">
            {links.map((l) => (
              <li key={l.href}>
                <a
                  href={l.href}
                  onClick={() => setOpen(false)}
                  className="block rounded-lg px-3 py-3 text-[15px] font-medium text-ink hover:bg-brand-50"
                >
                  {l.label}
                </a>
              </li>
            ))}
          </ul>
          {user ? (
            <Link
              href="/dashboard"
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white"
            >
              <UserIcon className="size-4" /> Kabinet
            </Link>
          ) : (
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                setLoginOpen(true);
              }}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white"
            >
              <LogIn className="size-4" /> Tizimga kirish
            </button>
          )}
        </div>
      )}

      <LoginModal open={loginOpen} onClose={closeLogin} notice={loginNotice} />
    </header>
  );
}
