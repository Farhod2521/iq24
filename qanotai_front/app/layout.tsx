import type { Metadata } from "next";
import { Caveat, Comic_Neue } from "next/font/google";
import "./globals.css";

// Comic Neue ships 300 / 400 / 700 only: semibold and extrabold text renders in its bold
const comic = Comic_Neue({
  variable: "--font-comic",
  weight: ["300", "400", "700"],
  style: ["normal", "italic"],
  subsets: ["latin"],
});

const caveat = Caveat({
  variable: "--font-caveat",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "IQ24 — Universitetga yo'l bilimdan boshlanadi",
  description:
    "Milliy sertifikat va oliy ta'limga kirish imtihonlariga tayyorlanish platformasi: testlar, nazariya, tahlil va sun'iy intellekt yordamchisi.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="uz"
      className={`${comic.variable} ${caveat.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}
