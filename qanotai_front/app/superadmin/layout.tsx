import type { Metadata } from "next";
import { AdminShell } from "./_components/shell";

export const metadata: Metadata = {
  title: "Superadmin — IQ24",
  robots: { index: false },
};

export default function SuperadminLayout({ children }: LayoutProps<"/superadmin">) {
  return <AdminShell>{children}</AdminShell>;
}
