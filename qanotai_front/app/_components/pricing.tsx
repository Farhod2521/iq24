import type { ComponentType, SVGProps } from "react";
import { Check, Crown, Gem, Gift, Star } from "./icons";
import { Container, Eyebrow } from "./ui";

type Plan = {
  name: string;
  note: string;
  months: number; // 0 = free
  price: number; // total for the whole period, so'm
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
  tone: string;
  featured?: boolean;
};

const MONTHLY_PRICE = 39000; // the 1-month price; longer plans show their saving against it

const plans: Plan[] = [
  { name: "Bepul", note: "Imkoniyatlarni sinab ko'ring", months: 0, price: 0, Icon: Gift, tone: "bg-sky-50 text-sky-600" },
  { name: "1 oylik", note: "Boshlash uchun", months: 1, price: MONTHLY_PRICE, Icon: Crown, tone: "bg-amber-50 text-amber-500" },
  { name: "3 oylik", note: "Eng ko'p tanlanadi", months: 3, price: 99000, Icon: Star, tone: "bg-brand-600 text-white", featured: true },
  { name: "6 oylik", note: "Eng tejamkor", months: 6, price: 179000, Icon: Gem, tone: "bg-orange-50 text-orange-500" },
];

const FREE_FEATURES = ["3 ta test ishlash", "2 ta fan tanlash"];
const PAID_FEATURES = ["Cheksiz testlar", "Istalgancha fan tanlash"];

// Fixed formatting (not toLocaleString) so server and client render the same string
const fmt = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ");

export function Pricing() {
  return (
    <section id="narxlar" className="relative scroll-mt-24 overflow-hidden py-12 lg:py-16">
      <Container>
        <div className="mx-auto max-w-2xl text-center">
          <Eyebrow>Sizga mos reja tanlang</Eyebrow>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-ink sm:text-4xl">Mos reja, katta imkoniyatlar</h2>
          <p className="mt-2 text-muted">Har bir o&apos;quvchi uchun qulay tariflar. Uzoqroq muddatga oling — arzonroq tushadi.</p>
        </div>

        <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {plans.map((p) => {
            const fullPrice = MONTHLY_PRICE * p.months;
            const discount = p.months > 1 ? Math.round((1 - p.price / fullPrice) * 100) : 0;
            const features = p.months === 0 ? FREE_FEATURES : PAID_FEATURES;
            return (
              <li
                key={p.name}
                className={`relative flex flex-col rounded-3xl bg-white p-6 shadow-card ${
                  p.featured ? "ring-2 ring-brand-600 lg:-translate-y-3" : "ring-1 ring-brand-100/70"
                }`}
              >
                {p.featured && (
                  <span className="absolute -top-3 right-6 rounded-full bg-rose-500 px-3 py-1 text-[11px] font-bold text-white shadow">
                    Eng mashhur
                  </span>
                )}
                <div className="flex items-center gap-3">
                  <span className={`grid size-11 place-items-center rounded-2xl ${p.tone}`}>
                    <p.Icon className="size-5" />
                  </span>
                  <div>
                    <h3 className="text-lg font-extrabold text-ink">{p.name}</h3>
                    <p className="text-xs text-muted">{p.note}</p>
                  </div>
                  {discount > 0 && (
                    <span className="ml-auto self-start rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-bold text-emerald-600 ring-1 ring-emerald-100">
                      −{discount}%
                    </span>
                  )}
                </div>

                <p className="mt-6 flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold tracking-tight text-ink">{fmt(p.price)}</span>
                  <span className="text-sm font-medium text-muted">
                    so&apos;m{p.months > 0 && ` / ${p.months} oy`}
                  </span>
                </p>
                <p className="mt-1 h-4 text-xs text-muted">
                  {discount > 0 && (
                    <>
                      <s>{fmt(fullPrice)} so&apos;m</s> · oyiga {fmt(Math.round(p.price / p.months))} so&apos;m
                    </>
                  )}
                </p>

                <ul className="mt-5 flex flex-1 flex-col gap-2.5">
                  {features.map((f) => (
                    <li key={f} className="flex items-center gap-2.5 text-sm text-ink">
                      <span className="grid size-5 shrink-0 place-items-center rounded-full bg-emerald-500 text-white">
                        <Check className="size-3" strokeWidth={3} />
                      </span>
                      {f}
                    </li>
                  ))}
                </ul>

                <a
                  href="#ilova"
                  className={`mt-7 rounded-full py-3 text-center text-sm font-semibold transition-colors ${
                    p.months > 0
                      ? "bg-brand-600 text-white hover:bg-brand-700"
                      : "text-brand-600 ring-1 ring-brand-300 hover:bg-brand-50"
                  }`}
                >
                  {p.months === 0 ? "Hozir boshlash" : "Tanlash"}
                </a>
              </li>
            );
          })}
        </ul>
      </Container>

    </section>
  );
}
