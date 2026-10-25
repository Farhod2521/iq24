"use client";

import { useStudent } from "./_components/student-shell";
import { DailyGoal, QuoteCard, SubjectShelf, WeeklyStats, WelcomeBanner } from "./widgets";

export function Home() {
  const { user, soon } = useStudent();
  const firstName = user?.full_name.split(/\s+/)[0] ?? "";
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
      <div className="flex min-w-0 flex-col gap-8">
        <WelcomeBanner firstName={firstName} onContinue={() => document.getElementById("fanlar")?.scrollIntoView({ behavior: "smooth" })} />
        <SubjectShelf onOpen={() => soon("Fanlar")} />
      </div>
      <div className="flex flex-col gap-6">
        <DailyGoal />
        <WeeklyStats />
        <QuoteCard />
      </div>
    </div>
  );
}
