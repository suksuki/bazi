"use client";

import React, { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import type { LabLlmRoundEntry } from "@/features/stream-board/controller/labLlmRounds";

export type LogicPulseKind = "silent" | "llm" | "round";

export type PulseReplayOverlayState = {
  pulseId: string;
  label: string;
  kind: LogicPulseKind;
  hubLine?: string;
  roundEntry?: LabLlmRoundEntry | null;
  /** 环形缓冲中解析出的能量快照（可能为空） */
  energy: Record<string, number> | null;
  skeleton: string | null;
  /** 无缓冲命中时的说明 */
  bufferMiss?: boolean;
};

type RingRow = { ts: number; deityScores: Record<string, number>; skeleton: string | null };

type PulseReplayContextValue = {
  overlay: PulseReplayOverlayState | null;
  openPulseReplay: (next: PulseReplayOverlayState) => void;
  closePulseReplay: () => void;
  recordLabPulseSnapshot: (row: RingRow) => void;
  pickSnapshotNear: (at: number) => RingRow | null;
};

const PulseReplayContext = createContext<PulseReplayContextValue | null>(null);

export function PulseReplayProvider({ children }: { children: React.ReactNode }) {
  const ring = useRef<RingRow[]>([]);
  const [overlay, setOverlay] = useState<PulseReplayOverlayState | null>(null);

  const recordLabPulseSnapshot = useCallback((row: RingRow) => {
    ring.current.push({ ...row, deityScores: { ...row.deityScores } });
    if (ring.current.length > 48) ring.current.splice(0, ring.current.length - 48);
  }, []);

  const pickSnapshotNear = useCallback((at: number) => {
    const rows = ring.current.filter((r) => r.ts <= at);
    if (rows.length === 0) return null;
    return rows.reduce((best, cur) => (cur.ts >= best.ts ? cur : best));
  }, []);

  const openPulseReplay = useCallback((next: PulseReplayOverlayState) => {
    setOverlay(next);
  }, []);

  const closePulseReplay = useCallback(() => setOverlay(null), []);

  const value = useMemo(
    () => ({ overlay, openPulseReplay, closePulseReplay, recordLabPulseSnapshot, pickSnapshotNear }),
    [overlay, openPulseReplay, closePulseReplay, recordLabPulseSnapshot, pickSnapshotNear],
  );

  return <PulseReplayContext.Provider value={value}>{children}</PulseReplayContext.Provider>;
}

export function usePulseReplay(): PulseReplayContextValue | null {
  return useContext(PulseReplayContext);
}
