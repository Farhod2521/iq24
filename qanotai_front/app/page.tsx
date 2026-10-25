import { Contact } from "./_components/contact";
import { DtmTests } from "./_components/dtm-tests";
import { Footer } from "./_components/footer";
import { Hero } from "./_components/hero";
import { Navbar } from "./_components/navbar";
import { Pricing } from "./_components/pricing";
import { AppPromo } from "./_components/steps";
import { Subjects } from "./_components/subjects";
import { Testimonials } from "./_components/testimonials";
import { Universities } from "./_components/universities";
import { WhyUs } from "./_components/why-us";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <Hero />
        <Subjects />
        <DtmTests />
        <WhyUs />
        <Universities />
        <Testimonials />
        <AppPromo />
        <Pricing />
        <Contact />
      </main>
      <Footer />
    </>
  );
}
