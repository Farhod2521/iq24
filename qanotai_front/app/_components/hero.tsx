import Image from "next/image";
import { ArrowRight, BarChart, FileText, GraduationCap, Layers, PlayCircle, Star } from "./icons";
import { Container } from "./ui";

const stats = [
  { value: "10+", label: "Fanlar", Icon: Layers, tone: "from-brand-50 to-brand-100 text-brand-600" },
  { value: "20 000+", label: "Video darslar", Icon: PlayCircle, tone: "from-sky-50 to-sky-100 text-sky-600" },
  { value: "100 000+", label: "Test savollari", Icon: FileText, tone: "from-indigo-50 to-indigo-100 text-indigo-600" },
  { value: "11 yillik", label: "Tajriba", Icon: GraduationCap, tone: "from-brand-50 to-brand-100 text-brand-700" },
  { value: "95%", label: "O'quvchilar natija ko'rsatgan", Icon: BarChart, tone: "from-emerald-50 to-emerald-100 text-emerald-600" },
];

const avatars = [
  { initials: "S", tone: "from-amber-300 to-orange-500" },
  { initials: "B", tone: "from-sky-300 to-brand-600" },
  { initials: "M", tone: "from-rose-300 to-pink-500" },
  { initials: "U", tone: "from-emerald-300 to-teal-600" },
];

export function Hero() {
  return (
    <section id="bosh" className="relative -mt-20 overflow-hidden pt-20">
      {/* large screens: the whole photo, uncropped, right under the navbar; its washed-out left part carries the copy */}
      <div className="pointer-events-none absolute inset-x-0 top-20 hidden aspect-[2004/785] xl:block">
        <Image src="/images/hero-student.webp" alt="" fill priority sizes="100vw" className="object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-white/70 from-15% to-transparent to-40%" />
        <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-b from-transparent to-background" />
        {/* handwritten note in the free sky above the subject icons */}
        <p className="absolute top-[3%] left-[41.5%] -rotate-[5deg] font-hand text-[1.55vw] leading-[1.05] font-bold text-brand-700">
          Katta maqsadlar
          <br />
          aniq bilimdan boshlanadi!
        </p>
      </div>

      <Container className="relative grid items-center pt-10 pb-10 xl:min-h-[39.2vw] xl:grid-cols-[minmax(0,31rem)_1fr] xl:pt-4 xl:pb-16 2xl:max-w-[96rem] 2xl:grid-cols-[minmax(0,37rem)_1fr]">
        <div>
          <span className="inline-flex items-center gap-2 rounded-full bg-white/90 py-1.5 pr-4 pl-1.5 text-[13px] font-semibold text-brand-700 shadow-card ring-1 ring-brand-100 sm:text-sm">
            <span className="grid size-6 place-items-center rounded-full bg-gradient-to-br from-amber-300 to-amber-500 text-white">
              <Star className="size-3.5" fill="currentColor" />
            </span>
            O&apos;zbekiston abituriyentlari uchun №1 platforma
          </span>

          <h1 className="mt-6 text-[2.5rem] leading-[1.06] font-extrabold tracking-[-0.03em] text-ink sm:text-6xl xl:text-[3rem] 2xl:text-[3.75rem]">
            Universitetga yo&apos;l
            <br />
            <span className="text-brand-600">bilimdan boshlanadi!</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink/70">
            Matematika, fizika, kimyo, biologiya, tarix va boshqa barcha fanlardan interaktiv darslar, testlar va
            tahlillar bilan o&apos;qishga tayyorlaning.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <a
              href="#fanlar"
              className="group inline-flex items-center gap-2.5 rounded-xl bg-brand-600 px-7 py-4 text-base font-bold text-white shadow-xl shadow-brand-600/30 transition-colors hover:bg-brand-700"
            >
              Bepul boshlash
              <ArrowRight className="size-5 transition-transform group-hover:translate-x-1" />
            </a>
            <a
              href="#ilova"
              className="inline-flex items-center gap-2.5 rounded-xl bg-white/90 px-6 py-4 text-base font-bold text-brand-600 shadow-card ring-1 ring-brand-100 transition-colors hover:text-brand-700"
            >
              <PlayCircle className="size-6" /> Videoni tomosha qilish
            </a>
          </div>

          <div className="mt-9 flex flex-wrap items-center gap-x-8 gap-y-4">
            <div className="flex items-center gap-3">
              <div className="flex -space-x-3">
                {avatars.map((a) => (
                  <span
                    key={a.initials}
                    className={`grid size-10 place-items-center rounded-full bg-gradient-to-br text-xs font-bold text-white ring-[3px] ring-white ${a.tone}`}
                  >
                    {a.initials}
                  </span>
                ))}
              </div>
              <div className="leading-tight">
                <p className="text-[15px] text-ink">
                  <b className="font-extrabold">100 000+</b> abituriyent
                </p>
                <p className="text-sm text-muted">biz bilan o&apos;qimoqda</p>
              </div>
            </div>
            <div className="leading-tight">
              <p className="flex items-center gap-1 text-amber-400">
                {[0, 1, 2, 3, 4].map((i) => (
                  <Star key={i} className="size-4" fill="currentColor" />
                ))}
                <b className="ml-1.5 text-[15px] font-extrabold text-ink">4.9</b>
              </p>
              <p className="mt-1 text-sm text-muted">O&apos;quvchilarning bahosi</p>
            </div>
          </div>
        </div>

        {/* small screens: the photo gets its own frame below the copy */}
        <div className="relative mt-10 aspect-[1.2] overflow-hidden rounded-[2rem] shadow-card ring-1 ring-white sm:aspect-[2] xl:hidden">
          <Image src="/images/hero-student.webp" alt="" fill sizes="100vw" className="object-cover object-[82%_center]" />
        </div>
      </Container>

      <Container className="relative z-10 pb-6 xl:-mt-14 2xl:max-w-[96rem]">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-6 rounded-3xl bg-white/95 p-6 shadow-card ring-1 ring-white backdrop-blur-md sm:grid-cols-3 lg:grid-cols-5 lg:gap-0 lg:divide-x lg:divide-brand-100">
          {stats.map(({ value, label, Icon, tone }) => (
            <div key={label} className="flex items-center gap-3 lg:px-5 2xl:gap-4">
              <span className={`grid size-12 shrink-0 place-items-center rounded-2xl bg-gradient-to-br ${tone}`}>
                <Icon className="size-6" />
              </span>
              <div>
                <dt className="sr-only">{label}</dt>
                <dd className="text-xl font-extrabold whitespace-nowrap text-ink">{value}</dd>
                <dd className="text-sm leading-snug text-muted">{label}</dd>
              </div>
            </div>
          ))}
        </dl>
      </Container>
    </section>
  );
}
