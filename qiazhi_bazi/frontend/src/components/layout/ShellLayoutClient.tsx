"use client";

import { BottomNav } from "@/components/layout/BottomNav";
import { LabConfigProvider } from "@/features/lab-config/LabConfigContext";

export function ShellLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <LabConfigProvider>
      <div className="min-h-dvh pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))]">{children}</div>
      <BottomNav />
    </LabConfigProvider>
  );
}
