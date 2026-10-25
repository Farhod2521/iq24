import type { Metadata } from "next";
import { StudentShell } from "./_components/student-shell";

export const metadata: Metadata = {
  title: "Kabinet — IQ24",
};

export default function DashboardLayout({ children }: LayoutProps<"/dashboard">) {
  return <StudentShell>{children}</StudentShell>;
}
