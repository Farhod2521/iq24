"use client";

import { BrandLogo } from "./brand-logo";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { ApiError, GOOGLE_LOGIN_URL, startTelegramLogin, telegramLoginStatus } from "../_lib/api";
import { ArrowRight, Close, Lock, Telegram } from "./icons";

function GoogleLogo({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 48 48" aria-hidden="true" className={className}>
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 13 4 4 13 4 24s9 20 20 20 20-9 20-20c0-1.3-.1-2.4-.4-3.5Z" />
      <path fill="#FF3D00" d="m6.3 14.7 6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7Z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44Z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5Z" />
    </svg>
  );
}

// hand-drawn accent strokes, sized in em so they follow the heading
function Sparkle({ className = "" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 60 50"
      aria-hidden="true"
      className={`text-amber-400 ${className}`}
      fill="none"
      stroke="currentColor"
      strokeWidth={6}
      strokeLinecap="round"
    >
      <path d="M8 34 20 6" />
      <path d="M22 40 46 18" />
      <path d="M30 48 56 44" />
    </svg>
  );
}

const POLL_MS = 2000;

export function LoginModal({ open, onClose, notice }: { open: boolean; onClose: () => void; notice?: string | null }) {
  const [telegram, setTelegram] = useState<{ token: string; url: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const panelRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Esc closes, the page behind doesn't scroll, focus moves into the dialog
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    panelRef.current?.focus();
    return () => {
      document.body.style.overflow = prevOverflow;
      document.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  // while the bot is open, ask the backend every couple of seconds whether it was confirmed
  useEffect(() => {
    if (!open || !telegram) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const status = await telegramLoginStatus(telegram.token);
        if (stopped) return;
        if (status === "confirmed") {
          router.push("/dashboard"); // the response just set the session cookie
          return;
        }
        if (status !== "pending") {
          setTelegram(null);
          setError(status === "rejected" ? "Kirish Telegram'da bekor qilindi." : "Vaqt tugadi. Qaytadan urinib ko'ring.");
          return;
        }
      } catch {
        // a dropped request is fine — try again on the next tick
      }
      if (!stopped) timer = setTimeout(tick, POLL_MS);
    };
    timer = setTimeout(tick, POLL_MS);
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [open, telegram, router]);

  if (!open) return null;

  async function loginWithTelegram() {
    setError("");
    setBusy(true);
    // open the tab synchronously inside the click so popup blockers allow it, then point it at the bot
    const tab = window.open("", "_blank");
    try {
      const { token, url } = await startTelegramLogin();
      if (tab) {
        tab.opener = null;
        tab.location.href = url;
      }
      setTelegram({ token, url });
    } catch (e) {
      tab?.close();
      setError(e instanceof ApiError ? e.message : "Server bilan bog'lanib bo'lmadi.");
    } finally {
      setBusy(false);
    }
  }

  const message = error || notice;

  // portalled to <body>: the sticky header's backdrop-filter would otherwise trap position:fixed
  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-ink/50 p-3 backdrop-blur-sm sm:p-6"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-title"
        tabIndex={-1}
        className="relative grid max-h-full w-full max-w-6xl overflow-y-auto rounded-[2rem] shadow-2xl outline-none lg:min-h-[720px] lg:grid-cols-[1.1fr_1fr] lg:overflow-hidden"
      >
        {/* backdrop: the same scene, softened, behind the sign-in card */}
        <Image
          src="/images/login-boy.webp"
          alt=""
          fill
          unoptimized
          className="pointer-events-none scale-110 object-cover object-[85%_center] blur-[3px] lg:origin-right lg:scale-[1.6] lg:object-right"
        />
        <div className="pointer-events-none absolute inset-0 bg-white/30" />

        {/* left: brand + slogan (large screens) */}
        <div className="relative hidden flex-col overflow-hidden p-12 lg:flex">
          <Image
            src="/images/login-boy.webp"
            alt="Samarqand manzarasiga qarab o'tirgan o'quvchi"
            fill
            unoptimized // served as-is: Next's resize + q75 re-encode made this artwork visibly soft
            className="pointer-events-none object-cover object-[45%_center]"
          />
          {/* keep the copy readable over the sky */}
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-white/80 via-white/25 via-45% to-transparent to-60%" />

          <div className="relative flex items-center gap-2">
            <BrandLogo className="h-11" />
          </div>

          <h2 className="relative mt-12 text-[3.4rem] font-extrabold leading-[1.08] tracking-[-0.03em] text-ink">
            <span className="relative">
              Bilim sari ilk
              <Sparkle className="absolute -top-[0.3em] -right-[0.75em] w-[0.6em]" />
            </span>
            <br />
            <span className="relative inline-block">
              <span className="bg-gradient-to-r from-brand-600 to-brand-500 bg-clip-text text-transparent">qadamingizni</span>
              <svg
                viewBox="0 0 300 24"
                preserveAspectRatio="none"
                aria-hidden="true"
                className="absolute -bottom-[0.12em] left-[0.05em] h-[0.18em] w-[85%] text-amber-400"
                fill="none"
                stroke="currentColor"
                strokeWidth={7}
                strokeLinecap="round"
              >
                <path d="M4 18C70 7 170 4 296 9" />
              </svg>
            </span>
            <br />
            boshlang
          </h2>
          <p className="relative mt-5 max-w-xs text-lg font-medium leading-relaxed text-ink/80">
            Hisobingizga kiring va o&apos;rganishni davom ettiring.
          </p>
        </div>

        {/* right: sign-in card */}
        <div className="relative flex items-center p-3 sm:p-6 lg:p-8">
          <div className="relative w-full rounded-[1.75rem] bg-white/95 px-5 py-10 shadow-card ring-1 ring-white backdrop-blur-md sm:px-10">
            <button
              type="button"
              onClick={onClose}
              aria-label="Yopish"
              className="absolute right-4 top-4 grid size-10 place-items-center rounded-full text-muted transition-colors hover:bg-brand-50 hover:text-ink"
            >
              <Close className="size-5" />
            </button>

            <div className="mx-auto grid size-16 place-items-center rounded-2xl bg-white shadow-card ring-1 ring-brand-100">
              <Image src="/brand/iq24-icon.png" alt="" width={44} height={44} unoptimized />
            </div>
            <h3 id="login-title" className="mt-6 text-center text-3xl font-extrabold tracking-tight text-ink sm:text-[2.1rem]">
              <span className="relative">
                Xush kelibsiz!
                <Sparkle className="absolute -top-[0.35em] -right-[0.7em] w-[0.55em]" />
              </span>
            </h3>
            <p className="mt-2 text-center text-muted">Davom etish uchun qulay usulni tanlang</p>

            {telegram ? (
              <div className="mt-8 flex flex-col items-center text-center">
                <span className="relative grid size-20 place-items-center rounded-full bg-gradient-to-br from-brand-600 to-sky-500 text-white shadow-lg shadow-brand-600/30">
                  <span className="absolute inset-0 animate-ping rounded-full bg-sky-400/40" />
                  <Telegram className="relative size-9" />
                </span>
                <h4 className="mt-6 text-xl font-extrabold text-ink">Telegram botda tasdiqlang</h4>
                <p className="mt-2 max-w-xs text-muted">
                  Botda <b className="text-ink">«✅ Tasdiqlash»</b> tugmasini bosing — bu sahifa o&apos;zi yangilanadi.
                </p>
                <p className="mt-4 flex items-center gap-2 text-sm text-muted">
                  <span className="size-4 animate-spin rounded-full border-2 border-brand-200 border-t-brand-600" />
                  Tasdiqlash kutilmoqda…
                </p>
                <a
                  href={telegram.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-600 to-sky-500 py-4 text-base font-bold text-white shadow-lg shadow-brand-600/25 transition hover:brightness-110"
                >
                  Botni ochish <ArrowRight className="size-5" />
                </a>
                <button
                  type="button"
                  onClick={() => setTelegram(null)}
                  className="mt-3 text-sm font-semibold text-brand-600 hover:underline"
                >
                  Boshqa usulni tanlash
                </button>
              </div>
            ) : (
              <div className="mt-8 flex flex-col gap-3">
                <a
                  href={GOOGLE_LOGIN_URL}
                  className="group flex items-center gap-3 rounded-2xl bg-white px-4 py-4 text-[15px] font-semibold text-ink shadow-card ring-1 ring-brand-100 transition hover:ring-brand-300 sm:gap-4 sm:px-5 sm:text-base"
                >
                  <GoogleLogo className="size-6 sm:size-7" />
                  <span className="flex-1 text-center">Google orqali davom etish</span>
                  <ArrowRight className="size-5 text-brand-600 transition-transform group-hover:translate-x-1" />
                </a>
                <button
                  type="button"
                  onClick={loginWithTelegram}
                  disabled={busy}
                  className="group flex items-center gap-3 rounded-2xl bg-gradient-to-r from-brand-600 to-sky-500 px-4 py-4 text-[15px] font-semibold text-white shadow-lg shadow-brand-600/25 transition hover:brightness-110 disabled:opacity-70 sm:gap-4 sm:px-5 sm:text-base"
                >
                  <Telegram className="size-6 sm:size-7" />
                  <span className="flex-1 text-center">Telegram orqali davom etish</span>
                  {busy ? (
                    <span className="size-5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                  ) : (
                    <ArrowRight className="size-5 transition-transform group-hover:translate-x-1" />
                  )}
                </button>
              </div>
            )}

            {message && (
              <p role="alert" className="mt-5 rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-red-700 ring-1 ring-red-100">
                {message}
              </p>
            )}

            <p className="mt-8 flex gap-3 text-sm text-muted">
              <Lock className="mt-0.5 size-5 shrink-0 text-brand-700" />
              <span>
                Ma&apos;lumotlaringiz xavfsiz saqlanadi.
                <br />
                Davom etish orqali{" "}
                <a href="#" className="font-medium text-brand-600 hover:underline">
                  foydalanish shartlariga
                </a>{" "}
                rozilik bildirasiz.
              </span>
            </p>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  );
}
