import { ShellLayoutClient } from "@/components/layout/ShellLayoutClient";

export default function ShellLayout({ children }: { children: React.ReactNode }) {
  return <ShellLayoutClient>{children}</ShellLayoutClient>;
}
