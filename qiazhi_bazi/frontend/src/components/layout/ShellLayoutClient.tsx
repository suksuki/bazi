"use client";

import { BottomNav } from "@/components/layout/BottomNav";
import { LabConfigProvider } from "@/features/lab-config/LabConfigContext";
import { LabStoreProvider } from "@/features/stream-board/stores/useLabStore";

export function ShellLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <LabStoreProvider>
      <BottomNav />
      <LabConfigProvider>
        <div className="min-h-dvh pb-[calc(4.5rem+env(safe-area-inset-bottom,0px))]">{children}</div>
      </LabConfigProvider>
    </LabStoreProvider>
  );
}
