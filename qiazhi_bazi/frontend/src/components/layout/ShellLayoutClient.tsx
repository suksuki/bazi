"use client";

import { LabConfigProvider } from "@/features/lab-config/LabConfigContext";
import { LabStoreProvider } from "@/features/stream-board/stores/useLabStore";
import { PulseReplayProvider } from "@/features/stream-board/stores/pulseReplayContext";

export function ShellLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <LabStoreProvider>
      <PulseReplayProvider>
        <LabConfigProvider>{children}</LabConfigProvider>
      </PulseReplayProvider>
    </LabStoreProvider>
  );
}
