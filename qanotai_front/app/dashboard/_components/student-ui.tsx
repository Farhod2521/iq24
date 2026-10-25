"use client";

/** Shared bits for the student pages inside the dashboard shell. */

export const card = "rounded-3xl bg-white shadow-card ring-1 ring-brand-100/70";

export function Spinner() {
  return (
    <div className="grid h-72 place-items-center">
      <span aria-label="Yuklanmoqda" className="size-10 animate-spin rounded-full border-4 border-brand-100 border-t-brand-600" />
    </div>
  );
}

export const LEVEL: Record<string, { label: string; badge: string; dot: string; bar: string }> = {
  easy: { label: "Oson", badge: "bg-emerald-50 text-emerald-700 ring-emerald-100", dot: "bg-emerald-500", bar: "bg-emerald-500" },
  medium: { label: "O'rta", badge: "bg-amber-50 text-amber-700 ring-amber-100", dot: "bg-amber-500", bar: "bg-amber-500" },
  hard: { label: "Qiyin", badge: "bg-rose-50 text-rose-700 ring-rose-100", dot: "bg-rose-500", bar: "bg-rose-500" },
};
