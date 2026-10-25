import type { ReactNode } from "react";
import {
  BarChart,
  Bell,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Close,
  Flame,
  Home,
  Timer,
  UserIcon,
} from "./icons";

/* Phone frame. Screens are drawn in HTML so they stay sharp at any size. */
export function Phone({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`aspect-[9/19] rounded-[2.4rem] bg-[#0d1530] p-[7px] shadow-phone ring-1 ring-black/40 ${className}`}
    >
      <div className="relative h-full w-full overflow-hidden rounded-[2rem] bg-[#f6f8ff]">
        <div className="absolute left-1/2 top-2 z-10 h-[18px] w-[34%] -translate-x-1/2 rounded-full bg-[#0d1530]" />
        <div className="flex h-full flex-col">{children}</div>
      </div>
    </div>
  );
}

function StatusBar() {
  return (
    <div className="flex items-center justify-between px-5 pt-3 pb-1 text-[9px] font-semibold text-ink">
      <span>9:41</span>
      <span className="flex items-center gap-1">
        <span className="flex items-end gap-px">
          {[3, 5, 7, 9].map((h) => (
            <span key={h} className="w-[2px] rounded-sm bg-ink" style={{ height: h }} />
          ))}
        </span>
        <span className="ml-0.5 h-[7px] w-[14px] rounded-[2px] border border-ink p-px">
          <span className="block h-full w-3/4 rounded-[1px] bg-ink" />
        </span>
      </span>
    </div>
  );
}

function Ring({ value, size = 46 }: { value: number; size?: number }) {
  const r = 18;
  const c = 2 * Math.PI * r;
  return (
    <svg viewBox="0 0 44 44" width={size} height={size} className="shrink-0">
      <circle cx="22" cy="22" r={r} fill="none" stroke="rgb(255 255 255 / .25)" strokeWidth="5" />
      <circle
        cx="22"
        cy="22"
        r={r}
        fill="none"
        stroke="white"
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray={`${(c * value) / 100} ${c}`}
        transform="rotate(-90 22 22)"
      />
      <text x="22" y="25.5" textAnchor="middle" fontSize="10" fontWeight="700" fill="white">
        {value}%
      </text>
    </svg>
  );
}

const subjectTiles = [
  { name: "Matematika", tests: 250, glyph: "π", tone: "bg-brand-100 text-brand-600" },
  { name: "Ona tili", tests: 198, glyph: "Aa", tone: "bg-rose-100 text-rose-500" },
  { name: "Tarix", tests: 180, glyph: "🏛", tone: "bg-amber-100 text-amber-600" },
  { name: "Ingliz tili", tests: 220, glyph: "En", tone: "bg-violet-100 text-violet-600" },
];

function TabBar({ active = 0 }: { active?: number }) {
  const items = [
    { label: "Bosh sahifa", Icon: Home },
    { label: "Testlar", Icon: ClipboardList },
    { label: "Statistika", Icon: BarChart },
    { label: "Profil", Icon: UserIcon },
  ];
  return (
    <div className="mt-auto grid grid-cols-4 border-t border-slate-200/70 bg-white px-2 pt-2 pb-4">
      {items.map(({ label, Icon }, i) => (
        <div
          key={label}
          className={`flex flex-col items-center gap-0.5 text-[7px] font-medium ${i === active ? "text-brand-600" : "text-slate-400"}`}
        >
          <Icon className="size-3.5" />
          {label}
        </div>
      ))}
    </div>
  );
}

export function HomeScreen() {
  return (
    <>
      <StatusBar />
      <div className="flex items-start justify-between px-4 pt-2">
        <div>
          <p className="text-[12px] font-bold text-ink">Salom, Farhod! 👋</p>
          <p className="text-[8px] text-muted">Bugun ham maqsad sari olg&apos;a!</p>
        </div>
        <Bell className="size-4 text-ink" />
      </div>
      <div className="mt-3 grid grid-cols-[1fr_1.35fr] gap-2 px-4">
        <div className="rounded-xl bg-white p-2 shadow-card">
          <Flame className="size-4 text-orange-500" />
          <p className="mt-1 text-[12px] font-extrabold text-ink">7 kun</p>
          <p className="text-[7px] text-muted">ketma-ket o&apos;qish</p>
        </div>
        <div className="flex items-center justify-between gap-1 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 p-2 text-white">
          <div>
            <p className="text-[8px] font-bold leading-tight">Milliy sertifikat</p>
            <p className="text-[8px] font-bold">2026</p>
            <p className="mt-1 text-[6.5px] opacity-80">Tayyorgarlik darajasi</p>
          </div>
          <Ring value={68} size={40} />
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between px-4">
        <p className="text-[10px] font-bold text-ink">Asosiy fanlar</p>
        <p className="text-[8px] font-semibold text-brand-600">Barchasi</p>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 px-4">
        {subjectTiles.map((s) => (
          <div key={s.name} className="rounded-xl bg-white p-2 shadow-card">
            <span className={`grid size-6 place-items-center rounded-lg text-[10px] font-bold ${s.tone}`}>{s.glyph}</span>
            <p className="mt-1.5 text-[8px] font-bold text-ink">{s.name}</p>
            <p className="text-[7px] text-muted">{s.tests} ta test</p>
          </div>
        ))}
      </div>
      <TabBar />
    </>
  );
}

export function TestScreen() {
  const options = ["2", "3", "4", "5"];
  return (
    <>
      <StatusBar />
      <div className="flex items-center justify-between px-4 pt-2 text-ink">
        <Close className="size-3.5" />
        <span className="flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[8px] font-bold text-brand-600">
          <Timer className="size-3" /> 28:15
        </span>
        <span className="text-[8px] font-semibold text-muted">12/30</span>
      </div>
      <div className="mx-4 mt-2 h-1 rounded-full bg-slate-200">
        <div className="h-full w-2/5 rounded-full bg-brand-500" />
      </div>
      <p className="mt-2 px-4 text-[7px] font-bold uppercase tracking-wide text-brand-600">Matematika · 12-savol</p>
      <p className="mt-1 px-4 text-[10px] font-bold leading-snug text-ink">
        Agar 2x + 5 = 13 bo&apos;lsa, x ning qiymati nechaga teng?
      </p>
      <div className="mt-3 flex flex-col gap-1.5 px-4">
        {options.map((o, i) => {
          const picked = i === 2;
          return (
            <div
              key={o}
              className={`flex items-center gap-2 rounded-lg border px-2 py-1.5 text-[9px] font-semibold ${
                picked ? "border-brand-500 bg-brand-50 text-brand-700" : "border-slate-200 bg-white text-ink"
              }`}
            >
              <span
                className={`grid size-4 place-items-center rounded-full text-[7px] font-bold ${
                  picked ? "bg-brand-600 text-white" : "bg-slate-100 text-muted"
                }`}
              >
                {"ABCD"[i]}
              </span>
              {o}
              {picked && <Check className="ml-auto size-3 text-brand-600" />}
            </div>
          );
        })}
      </div>
      <div className="mt-auto px-4 pb-5">
        <div className="flex items-center justify-between">
          <span className="grid size-7 place-items-center rounded-lg bg-white text-muted shadow-card">
            <ChevronLeft className="size-3.5" />
          </span>
          <span className="rounded-lg bg-brand-600 px-5 py-2 text-[9px] font-bold text-white">Keyingi</span>
        </div>
      </div>
    </>
  );
}

export function TopicsScreen() {
  const topics = [
    { name: "Sonlar va amallar", done: 100 },
    { name: "Algebra", done: 72 },
    { name: "Tenglamalar", done: 54 },
    { name: "Funksiyalar", done: 30 },
    { name: "Geometriya", done: 12 },
    { name: "Ehtimollik", done: 0 },
  ];
  return (
    <>
      <StatusBar />
      <div className="flex items-center gap-2 px-4 pt-2">
        <ChevronLeft className="size-3.5 text-ink" />
        <p className="text-[12px] font-bold text-ink">Matematika</p>
        <span className="ml-auto text-[8px] font-semibold text-muted">4/12</span>
      </div>
      <div className="mx-4 mt-2 grid grid-cols-3 rounded-lg bg-slate-100 p-0.5 text-center text-[8px] font-semibold">
        <span className="rounded-md bg-white py-1 text-brand-600 shadow-sm">Darslar</span>
        <span className="py-1 text-muted">Testlar</span>
        <span className="py-1 text-muted">Tahlil</span>
      </div>
      <div className="mt-2 flex flex-col gap-1.5 px-4">
        {topics.map((t, i) => (
          <div key={t.name} className="flex items-center gap-2 rounded-lg bg-white px-2 py-1.5 shadow-card">
            <span
              className={`grid size-5 place-items-center rounded-md text-[8px] font-bold ${
                t.done === 100 ? "bg-emerald-100 text-emerald-600" : "bg-brand-50 text-brand-600"
              }`}
            >
              {t.done === 100 ? <Check className="size-3" /> : i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[8.5px] font-semibold text-ink">{t.name}</p>
              <div className="mt-0.5 h-[3px] rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-brand-500" style={{ width: `${t.done}%` }} />
              </div>
            </div>
            <ChevronRight className="size-3 text-slate-400" />
          </div>
        ))}
      </div>
      <TabBar active={1} />
    </>
  );
}
