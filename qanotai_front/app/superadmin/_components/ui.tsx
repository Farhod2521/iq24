"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import type { Growth, SubjectColor } from "../../_lib/admin-api";
import { Close, MoreHorizontal } from "../../_components/icons";

export const card = "rounded-3xl bg-white shadow-card ring-1 ring-brand-100/70";

export const SUBJECT_COLORS: Record<SubjectColor, { label: string; dot: string; bar: string; soft: string }> = {
  blue: { label: "Ko'k", dot: "bg-brand-600", bar: "bg-brand-500", soft: "bg-brand-50 text-brand-600" },
  violet: { label: "Binafsha", dot: "bg-violet-500", bar: "bg-violet-500", soft: "bg-violet-50 text-violet-600" },
  emerald: { label: "Yashil", dot: "bg-emerald-500", bar: "bg-emerald-500", soft: "bg-emerald-50 text-emerald-600" },
  rose: { label: "Qizil", dot: "bg-rose-500", bar: "bg-rose-400", soft: "bg-rose-50 text-rose-600" },
  amber: { label: "Sariq", dot: "bg-amber-500", bar: "bg-amber-400", soft: "bg-amber-50 text-amber-600" },
  sky: { label: "Moviy", dot: "bg-sky-500", bar: "bg-sky-500", soft: "bg-sky-50 text-sky-600" },
  slate: { label: "Kulrang", dot: "bg-slate-500", bar: "bg-slate-400", soft: "bg-slate-100 text-slate-600" },
};

export function GrowthBadge({ value }: { value: Growth }) {
  if (value === null) return <span className="text-xs text-muted">—</span>;
  const up = value >= 0;
  return (
    <span className={`text-xs font-semibold ${up ? "text-emerald-600" : "text-rose-600"}`}>
      {up ? "↑" : "↓"} {up ? "+" : ""}
      {value}%
    </span>
  );
}

export function timeAgo(iso: string) {
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "hozirgina";
  if (s < 3600) return `${Math.floor(s / 60)} daqiqa oldin`;
  if (s < 86400) return `${Math.floor(s / 3600)} soat oldin`;
  if (s < 86400 * 30) return `${Math.floor(s / 86400)} kun oldin`;
  return formatDate(iso);
}

// dd.mm.yyyy regardless of the browser locale
export function formatDate(iso: string) {
  const d = new Date(iso);
  return [d.getDate(), d.getMonth() + 1].map((n) => String(n).padStart(2, "0")).join(".") + "." + d.getFullYear();
}

export function Avatar({ name, src, className }: { name: string; src?: string | null; className: string }) {
  if (src) {
    // eslint-disable-next-line @next/next/no-img-element -- Google avatar on an arbitrary googleusercontent host
    return <img src={src} alt="" referrerPolicy="no-referrer" className={`shrink-0 rounded-full object-cover ${className}`} />;
  }
  const initials = name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join("");
  return (
    <span className={`grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-brand-600 to-sky-500 font-bold text-white ${className}`}>
      {initials || "?"}
    </span>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      document.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-ink/50 p-4 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div role="dialog" aria-modal="true" aria-label={title} className="max-h-full w-full max-w-2xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl sm:p-8">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-xl font-extrabold text-ink">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Yopish" className="grid size-9 place-items-center rounded-full text-muted hover:bg-brand-50">
            <Close className="size-5" />
          </button>
        </div>
        <div className="mt-6">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export const inputClass =
  "w-full rounded-xl bg-white px-4 py-3 text-[15px] text-ink ring-1 ring-brand-100 outline-none transition placeholder:text-muted/60 focus:ring-2 focus:ring-brand-500";

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-sm font-semibold text-ink">{label}</span>
      {children}
      {hint && <span className="text-xs text-muted">{hint}</span>}
    </label>
  );
}

export function PageHead({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">{title}</h1>
        {subtitle && <p className="mt-1 text-muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export const primaryButton =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition-colors hover:bg-brand-700 disabled:opacity-60";

export type MenuItem = { label: string; icon?: ReactNode; danger?: boolean; onSelect: () => void };

/** "⋯" button with a small dropdown of actions. Pass a positioning class (e.g. "absolute right-3 top-3")
 *  to place it; without one it sits in the flow as `relative`. */
export function ActionMenu({ items, label = "Amallar", className = "relative" }: { items: MenuItem[]; label?: string; className?: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className={className}>
      <button
        type="button"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className={`grid size-9 place-items-center rounded-full shadow-sm ring-1 transition-colors ${
          open ? "bg-brand-600 text-white ring-brand-600" : "bg-white/95 text-ink/70 ring-brand-100 hover:text-ink"
        }`}
      >
        <MoreHorizontal className="size-5" />
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-full z-20 mt-2 w-44 origin-top-right animate-[dialog-in_.15s_ease-out] rounded-2xl bg-white p-1.5 shadow-xl ring-1 ring-brand-100"
        >
          {items.map((item) => (
            <button
              key={item.label}
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                item.onSelect();
              }}
              className={`flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition-colors ${
                item.danger ? "text-rose-600 hover:bg-rose-50" : "text-ink/80 hover:bg-brand-50 hover:text-ink"
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
