import Image from "next/image";
import { ArrowRight } from "./icons";
import { Container } from "./ui";

const universities = ["TDTU", "TATU", "TDIU", "TTA", "O'zMU"];

/** A columned university facade on a sky tile. */
function Campus() {
  return (
    <svg viewBox="0 0 120 72" className="w-full rounded-xl" aria-hidden="true">
      <defs>
        <linearGradient id="campus-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#bcd1ff" />
          <stop offset="1" stopColor="#eef4ff" />
        </linearGradient>
      </defs>
      <rect width="120" height="72" fill="url(#campus-sky)" />
      <ellipse cx="60" cy="74" rx="70" ry="10" fill="#86efac" opacity=".7" />
      <rect x="18" y="30" width="84" height="34" fill="#f8fafc" />
      <path d="M60 10 14 30h92L60 10Z" fill="#e2e8f0" />
      <path d="M60 14 24 28h72L60 14Z" fill="#cbd5e1" />
      <rect x="54" y="2" width="12" height="11" rx="1" fill="#f1f5f9" />
      <path d="M52 3h16l-8-5-8 5Z" fill="#94a3b8" />
      {[24, 34, 44, 72, 82, 92].map((x) => (
        <rect key={x} x={x} y="34" width="4" height="26" rx="1" fill="#cbd5e1" />
      ))}
      <rect x="53" y="42" width="14" height="22" rx="7" fill="#94a3b8" />
      <rect x="14" y="62" width="92" height="4" fill="#cbd5e1" />
    </svg>
  );
}

export function Universities() {
  return (
    <section className="py-6 lg:py-10">
      <Container className="2xl:max-w-[96rem]">
        <div className="grid items-stretch gap-6 lg:grid-cols-[0.75fr_2fr]">
          <div className="relative min-h-64 overflow-hidden rounded-[2rem] shadow-card">
            <Image src="/images/login-boy.webp" alt="Samarqand manzarasiga qarab o'tirgan abituriyent" fill sizes="(min-width: 1024px) 30vw, 100vw" className="object-cover object-[60%_70%]" />
          </div>

          <div className="relative grid items-center gap-8 rounded-[2rem] bg-white p-6 shadow-card ring-1 ring-brand-100/70 sm:p-10 md:grid-cols-[1fr_1.2fr]">
            <div>
              <h2 className="text-3xl leading-tight font-extrabold tracking-tight text-ink">
                Orzudagi universitetga
                <br />
                bir qadam yaqinroq!
              </h2>
              <p className="mt-4 max-w-sm leading-relaxed text-muted">
                Minglab abituriyentlar allaqachon IQ24 bilan maqsadiga erishmoqda. Endi sizning navbatingiz!
              </p>
              <a
                href="#narxlar"
                className="group mt-7 inline-flex items-center gap-2.5 rounded-xl bg-brand-600 px-6 py-3.5 font-bold text-white shadow-lg shadow-brand-600/25 transition-colors hover:bg-brand-700"
              >
                Hozir boshlash <ArrowRight className="size-5 transition-transform group-hover:translate-x-1" />
              </a>
            </div>

            <div className="relative">
              <p className="absolute -top-9 right-0 rotate-[-6deg] font-hand text-2xl font-bold text-brand-700">Top OTMlar sari!</p>
              <ul className="grid grid-cols-3 gap-2.5 sm:gap-3">
                {universities.map((u) => (
                  <li key={u} className="text-center">
                    <Campus />
                    <p className="mt-1.5 text-xs font-bold text-ink">{u}</p>
                  </li>
                ))}
                <li className="grid place-items-center rounded-xl bg-brand-50 p-3 text-center text-sm font-bold text-brand-600 ring-1 ring-brand-100">
                  va boshqa OTMlar
                </li>
              </ul>
            </div>
          </div>
        </div>
      </Container>
    </section>
  );
}
