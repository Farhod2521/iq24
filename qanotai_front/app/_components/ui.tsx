import type { ReactNode } from "react";
import { AppleLogo, GooglePlayLogo } from "./icons";

export function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`mx-auto w-full max-w-7xl px-4 sm:px-6 lg:px-8 ${className}`}>{children}</div>;
}

export function Eyebrow({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-full bg-brand-50 px-3 py-1 text-[11px] font-bold uppercase tracking-wider text-brand-600 ring-1 ring-brand-100 ${className}`}
    >
      {children}
    </span>
  );
}

export function StoreBadges({ dark = true, size = "md" }: { dark?: boolean; size?: "sm" | "md" | "lg" }) {
  const base = {
    sm: "h-10 gap-2 px-3 rounded-lg [&_svg]:size-5",
    md: "h-12 gap-2.5 px-4 rounded-xl [&_svg]:size-6",
    lg: "h-16 gap-3 px-5 rounded-2xl [&_svg]:size-9 sm:h-[4.5rem] sm:px-6 [&_.store-top]:text-xs sm:[&_.store-top]:text-sm [&_.store-name]:text-xl sm:[&_.store-name]:text-[1.65rem]",
  }[size];
  const tone = dark
    ? "bg-ink text-white hover:bg-black"
    : "bg-white/10 text-white ring-1 ring-white/20 hover:bg-white/15";
  return (
    <div className="flex flex-wrap gap-3">
      <a href="#ilova" className={`inline-flex items-center transition-colors ${base} ${tone}`}>
        <GooglePlayLogo />
        <span className="flex flex-col gap-0.5 leading-none">
          <span className="store-top text-[9px] font-medium uppercase opacity-80">Get it on</span>
          <span className="store-name text-sm font-semibold">Google Play</span>
        </span>
      </a>
      <a href="#ilova" className={`inline-flex items-center transition-colors ${base} ${tone}`}>
        <AppleLogo />
        <span className="flex flex-col gap-0.5 leading-none">
          <span className="store-top text-[9px] font-medium opacity-80">Download on the</span>
          <span className="store-name text-sm font-semibold">App Store</span>
        </span>
      </a>
    </div>
  );
}

// "90 123 45 67" — the +998 prefix is fixed in front of the input
export function formatPhone(raw: string) {
  const d = raw.replace(/\D/g, "").slice(0, 9);
  return [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean).join(" ");
}
