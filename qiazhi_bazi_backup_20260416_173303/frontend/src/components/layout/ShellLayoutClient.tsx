"use client";

import { LabConfigProvider } from "@/features/lab-config/LabConfigContext";
import { GlobalWillAura } from "@/features/stream-board/components/GlobalWillAura";
import { PhaseTransitionAura } from "@/features/stream-board/components/PhaseTransitionAura";
import { LabStoreProvider } from "@/features/stream-board/stores/useLabStore";
import { PulseReplayProvider } from "@/features/stream-board/stores/pulseReplayContext";

export function ShellLayoutClient({ children }: { children: React.ReactNode }) {
  return (
    <LabStoreProvider>
      <PulseReplayProvider>
        <LabConfigProvider>
          {children}
          <GlobalWillAura />
          <PhaseTransitionAura />
        </LabConfigProvider>
      </PulseReplayProvider>
    </LabStoreProvider>
  );
}
