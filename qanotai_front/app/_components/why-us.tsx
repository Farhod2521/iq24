import type { ComponentType, SVGProps } from "react";
import { BarChart, Crown, Play, Target } from "./icons";
import { Container } from "./ui";

type Reason = { title: string; text: string; Icon: ComponentType<SVGProps<SVGSVGElement>>; tone: string };

const reasons: Reason[] = [
  { title: "DTM formatidagi testlar", text: "Real imtihonga yaqin savollar", Icon: Target, tone: "from-rose-400 to-rose-600 shadow-rose-500/30" },
  { title: "Sifatli video darslar", text: "Tajribali ustozlar tomonidan tushuntirilgan", Icon: Play, tone: "from-amber-400 to-orange-500 shadow-orange-500/30" },
  { title: "Shaxsiy tahlil", text: "Natijalaringiz bo'yicha zaif va kuchli mavzular", Icon: BarChart, tone: "from-violet-400 to-violet-600 shadow-violet-500/30" },
  { title: "Top reyting", text: "O'zbekiston bo'ylab o'quvchilar bilan bellashing", Icon: Crown, tone: "from-emerald-400 to-emerald-600 shadow-emerald-500/30" },
];

export function WhyUs() {
  return (
    <section id="biz-haqimizda" className="scroll-mt-24 py-8 lg:py-10">
      <Container className="2xl:max-w-[96rem]">
        <h2 className="flex items-center gap-2.5 text-2xl font-extrabold tracking-tight text-ink sm:text-3xl">
          <svg viewBox="0 0 32 32" className="size-8" aria-hidden="true">
            <path d="M16 6 2 12.5 16 19l14-6.5L16 6Z" fill="#1f55f5" />
            <path d="M8 16v6c0 2 4 4 8 4s8-2 8-4v-6l-8 3.7L8 16Z" fill="#5d8bff" />
            <path d="M27 13.5v7" stroke="#1742d1" strokeWidth="2" strokeLinecap="round" />
          </svg>
          Nega aynan IQ24?
        </h2>

        <ul className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {reasons.map(({ title, text, Icon, tone }) => (
            <li key={title} className="flex items-center gap-4 rounded-2xl bg-white p-5 shadow-card ring-1 ring-brand-100/70">
              <span className={`grid size-14 shrink-0 place-items-center rounded-full bg-gradient-to-br text-white shadow-lg ${tone}`}>
                <Icon className="size-6" />
              </span>
              <div>
                <h3 className="font-bold text-ink">{title}</h3>
                <p className="mt-1 text-sm leading-snug text-muted">{text}</p>
              </div>
            </li>
          ))}
        </ul>
      </Container>
    </section>
  );
}
