import { Globe, Instagram, Telegram, Youtube } from "./icons";
import { Logo } from "./navbar";
import { Container, StoreBadges } from "./ui";

const columns = [
  { title: "Mahsulot", links: ["Imkoniyatlar", "Fanlar", "Ilova", "Narxlar"] },
  { title: "Yordam", links: ["Savollar", "Qo'llanma", "Bog'lanish"] },
  { title: "Huquqiy", links: ["Foydalanish shartlari", "Maxfiylik siyosati"] },
];

const socials = [
  { label: "Telegram", Icon: Telegram },
  { label: "Instagram", Icon: Instagram },
  { label: "YouTube", Icon: Youtube },
];

export function Footer() {
  return (
    <footer className="mt-8 bg-navy text-white">
      <Container className="grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-[1.4fr_repeat(3,0.8fr)_1.3fr]">
        <div>
          <Logo light />
          <p className="mt-4 max-w-xs text-sm text-white/60">Maqsading sari bir qanot oldinda.</p>
          <div className="mt-6 flex gap-3">
            {socials.map(({ label, Icon }) => (
              <a
                key={label}
                href="#"
                aria-label={label}
                className="grid size-10 place-items-center rounded-full bg-white/10 transition-colors hover:bg-brand-600"
              >
                <Icon className="size-[18px]" />
              </a>
            ))}
          </div>
        </div>

        {columns.map((c) => (
          <div key={c.title}>
            <h3 className="text-sm font-bold">{c.title}</h3>
            <ul className="mt-4 flex flex-col gap-2.5 text-sm text-white/60">
              {c.links.map((l) => (
                <li key={l}>
                  <a href={l === "Bog'lanish" ? "#boglanish" : "#"} className="transition-colors hover:text-white">
                    {l}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div>
          <h3 className="text-sm font-bold">Ilovani yuklab oling</h3>
          <div className="mt-4">
            <StoreBadges dark={false} size="sm" />
          </div>
        </div>
      </Container>

      <div className="border-t border-white/10">
        <Container className="flex flex-wrap items-center justify-between gap-4 py-6 text-xs text-white/50">
          <p>© 2026 IQ24. Barcha huquqlar himoyalangan.</p>
          <div className="flex items-center gap-5">
            <span>O&apos;zbekiston</span>
            <span className="flex items-center gap-1.5">
              <Globe className="size-3.5" /> O&apos;zbekcha (UZ)
            </span>
          </div>
        </Container>
      </div>
    </footer>
  );
}
