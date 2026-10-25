"use client";

import { useEffect, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { ApiError } from "../../_lib/api";
import { Check, Close, Trash } from "../../_components/icons";

// ─── toasts (top-right) ──────────────────────────────────────────────────────

export type ToastTone = "success" | "error" | "info";
export type Toast = { id: number; tone: ToastTone; title: string; text?: string };

const TOAST_MS = 3500;

const toneStyle: Record<ToastTone, { icon: ReactNode; ring: string; badge: string; bar: string }> = {
  success: {
    icon: <Check className="size-4" strokeWidth={3} />,
    ring: "ring-emerald-100",
    badge: "bg-emerald-500 text-white shadow-emerald-500/30",
    bar: "bg-emerald-500",
  },
  error: { icon: <span className="text-sm font-black">!</span>, ring: "ring-rose-100", badge: "bg-rose-500 text-white shadow-rose-500/30", bar: "bg-rose-500" },
  info: { icon: <span className="text-sm font-black">i</span>, ring: "ring-brand-100", badge: "bg-brand-600 text-white shadow-brand-600/30", bar: "bg-brand-600" },
};

export function Toasts({ items, onDismiss }: { items: Toast[]; onDismiss: (id: number) => void }) {
  if (items.length === 0) return null; // also keeps the portal (document.body) out of server rendering
  return createPortal(
    <div aria-live="polite" className="pointer-events-none fixed right-4 top-4 z-[200] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3 sm:right-6 sm:top-6">
      {items.map((t) => (
        <ToastCard key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>,
    document.body,
  );
}

function ToastCard({ toast, onDismiss }: { toast: Toast; onDismiss: (id: number) => void }) {
  const s = toneStyle[toast.tone];
  useEffect(() => {
    const t = setTimeout(() => onDismiss(toast.id), TOAST_MS);
    return () => clearTimeout(t);
  }, [toast.id, onDismiss]);

  return (
    <div
      role={toast.tone === "error" ? "alert" : "status"}
      className={`pointer-events-auto relative flex animate-[toast-in_.28s_cubic-bezier(.2,.9,.3,1.2)] items-start gap-3 overflow-hidden rounded-2xl bg-white/95 p-4 pr-10 shadow-2xl shadow-ink/10 ring-1 backdrop-blur-md ${s.ring}`}
    >
      <span className={`grid size-8 shrink-0 place-items-center rounded-full shadow-lg ${s.badge}`}>{s.icon}</span>
      <div className="min-w-0 pt-0.5">
        <p className="text-sm font-bold text-ink">{toast.title}</p>
        {toast.text && <p className="mt-0.5 text-sm text-muted">{toast.text}</p>}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        aria-label="Yopish"
        className="absolute right-2.5 top-2.5 grid size-7 place-items-center rounded-full text-muted hover:bg-brand-50 hover:text-ink"
      >
        <Close className="size-4" />
      </button>
      {/* time left before it disappears */}
      <span
        className={`absolute inset-x-0 bottom-0 h-0.5 origin-left opacity-60 ${s.bar}`}
        style={{ animation: `toast-timer ${TOAST_MS}ms linear forwards` }}
      />
    </div>
  );
}

// ─── confirm dialog ──────────────────────────────────────────────────────────

export type ConfirmOptions = {
  title: string;
  message: ReactNode;
  confirmLabel?: string;
  /** runs while the dialog shows a spinner; a thrown ApiError is shown inside the dialog */
  onConfirm: () => Promise<void>;
};

export function ConfirmDialog({ options, onClose }: { options: ConfirmOptions; onClose: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && !busy && onClose();
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      document.removeEventListener("keydown", onKey);
    };
  }, [busy, onClose]);

  async function confirm() {
    setBusy(true);
    setError("");
    try {
      await options.onConfirm();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Amalni bajarib bo'lmadi. Qaytadan urinib ko'ring.");
      setBusy(false);
    }
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[150] flex animate-[fade-in_.15s_ease-out] items-center justify-center bg-ink/45 p-4 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && !busy && onClose()}
    >
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="w-full max-w-md animate-[dialog-in_.22s_cubic-bezier(.2,.9,.3,1.2)] rounded-3xl bg-white p-7 text-center shadow-2xl"
      >
        <span className="relative mx-auto grid size-16 place-items-center rounded-full bg-rose-50 text-rose-500">
          <span className="absolute inset-0 rounded-full ring-8 ring-rose-50/60" />
          <Trash className="relative size-7" />
        </span>
        <h2 id="confirm-title" className="mt-5 text-xl font-extrabold text-ink">
          {options.title}
        </h2>
        <div className="mt-2 text-[15px] leading-relaxed text-muted">{options.message}</div>

        {error && <p className="mt-4 rounded-xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700 ring-1 ring-rose-100">{error}</p>}

        <div className="mt-7 grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            autoFocus
            className="rounded-xl bg-slate-100 py-3 text-sm font-semibold text-ink/80 transition-colors hover:bg-slate-200 disabled:opacity-50"
          >
            Bekor qilish
          </button>
          <button
            type="button"
            onClick={confirm}
            disabled={busy}
            className="flex items-center justify-center gap-2 rounded-xl bg-rose-500 py-3 text-sm font-semibold text-white shadow-lg shadow-rose-500/30 transition-colors hover:bg-rose-600 disabled:opacity-70"
          >
            {busy ? (
              <span className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            ) : (
              <Trash className="size-4" />
            )}
            {busy ? "O'chirilmoqda…" : (options.confirmLabel ?? "O'chirish")}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
