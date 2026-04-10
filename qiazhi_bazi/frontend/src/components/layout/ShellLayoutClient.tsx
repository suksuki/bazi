"use client";

import { LabConfigProvider } from "@/features/lab-config/LabConfigContext";
import { LabStoreProvider } from "@/features/stream-board/stores/useLabStore";

export function ShellLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <LabStoreProvider>
      <LabConfigProvider>{children}</LabConfigProvider>
    </LabStoreProvider>
  );
}
