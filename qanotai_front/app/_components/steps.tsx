import { Check } from "./icons";
import { HomeScreen, Phone, TopicsScreen } from "./phones";
import { Container, Eyebrow, StoreBadges } from "./ui";

const perks = ["Offline rejim", "Barcha qurilmalarda sinxronizatsiya", "Kunlik eslatmalar", "Qulay interfeys"];

export function AppPromo() {
  return (
    <section id="ilova" className="relative overflow-hidden py-12 lg:py-20">
      <div className="pointer-events-none absolute left-[-10%] top-0 size-[600px] rounded-full bg-[radial-gradient(circle,rgb(93_139_255/0.22),transparent_65%)]" />
      <Container className="relative grid items-center gap-12 lg:grid-cols-2">
        <div className="relative mx-auto h-[440px] w-full max-w-[480px] sm:h-[480px]">
          <div className="absolute inset-x-4 bottom-0 top-10 rounded-[3rem] bg-gradient-to-br from-brand-600 to-brand-400" />
          <Phone className="absolute left-0 top-0 z-10 w-[52%] rotate-[-6deg] sm:left-[8%] sm:w-[44%]">
            <HomeScreen />
          </Phone>
          <Phone className="absolute right-0 top-10 w-[50%] rotate-[6deg] sm:right-[8%] sm:w-[42%]">
            <TopicsScreen />
          </Phone>
        </div>

        <div>
          <Eyebrow>Ilovada hammasi mavjud</Eyebrow>
          <h2 className="mt-3 text-3xl font-extrabold leading-tight tracking-tight text-ink sm:text-[2.6rem]">
            Har doim, har joyda o&apos;qing va test ishlang
          </h2>
          <p className="mt-4 max-w-lg text-muted sm:text-lg">
            IQ24 mobil ilovasi bilan o&apos;qishni istalgan joyda davom ettiring. Offline rejim, sinxronizatsiya va
            qulay interfeys.
          </p>
          <ul className="mt-6 grid max-w-lg gap-3 sm:grid-cols-2">
            {perks.map((p) => (
              <li key={p} className="flex items-center gap-2.5 text-sm font-medium text-ink">
                <span className="grid size-5 place-items-center rounded-full bg-brand-600 text-white">
                  <Check className="size-3" strokeWidth={3} />
                </span>
                {p}
              </li>
            ))}
          </ul>
          <div className="mt-8">
            <StoreBadges />
          </div>
        </div>
      </Container>
    </section>
  );
}
