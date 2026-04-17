"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SEED_YEAR_MAX, SEED_YEAR_MIN } from "@/components/seedYearRange";
import type { SeedPayload } from "@/features/stream-board/models";
import type { FourPillars, TimelineSnapshot } from "@/types/bazi";

type SeedPreviewModule = {
  referenceYear: number;
  setReferenceYear: React.Dispatch<React.SetStateAction<number>>;
  referenceYearRef: React.MutableRefObject<number>;
  seedPreviewPillars: FourPillars | null;
  seedPreviewTimeline: TimelineSnapshot | null;
  seedPreviewBusy: boolean;
  seedPreviewError: string | null;
  refreshSeedPreview: (payload: SeedPayload) => Promise<void>;
  scheduleSeedDraftPreview: (payload: SeedPayload | null) => void;
  resetSeedPreviewState: () => void;
};

export function useSeedPreviewModule(apiBase: string): SeedPreviewModule {
  const [referenceYear, setReferenceYear] = useState(() => {
    const y = new Date().getFullYear();
    return Math.min(SEED_YEAR_MAX, Math.max(SEED_YEAR_MIN, y));
  });
  const referenceYearRef = useRef(referenceYear);
  const [seedPreviewPillars, setSeedPreviewPillars] = useState<FourPillars | null>(null);
  const [seedPreviewTimeline, setSeedPreviewTimeline] = useState<TimelineSnapshot | null>(null);
  const [seedPreviewBusy, setSeedPreviewBusy] = useState(false);
  const [seedPreviewError, setSeedPreviewError] = useState<string | null>(null);
  const seedDraftPreviewTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    referenceYearRef.current = referenceYear;
  }, [referenceYear]);

  const resetSeedPreviewState = useCallback(() => {
    if (seedDraftPreviewTimerRef.current) {
      clearTimeout(seedDraftPreviewTimerRef.current);
      seedDraftPreviewTimerRef.current = null;
    }
    setSeedPreviewPillars(null);
    setSeedPreviewTimeline(null);
    setSeedPreviewError(null);
    setSeedPreviewBusy(false);
  }, []);

  const refreshSeedPreview = useCallback(
    async (payload: SeedPayload) => {
      setSeedPreviewBusy(true);
      setSeedPreviewError(null);
      try {
        const res = await fetch(`${apiBase}/api/v1/seed-preview`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date: payload.date,
            time: payload.time,
            calendar: payload.calendar,
            gender: payload.gender,
            reference_year: referenceYearRef.current,
          }),
        });
        if (!res.ok) throw new Error(await res.text());
        const data = (await res.json()) as { pillars: FourPillars; timeline: TimelineSnapshot };
        setSeedPreviewPillars(data.pillars);
        setSeedPreviewTimeline(data.timeline);
      } catch (e) {
        setSeedPreviewError(e instanceof Error ? e.message : String(e));
        setSeedPreviewPillars(null);
        setSeedPreviewTimeline(null);
      } finally {
        setSeedPreviewBusy(false);
      }
    },
    [apiBase],
  );

  const scheduleSeedDraftPreview = useCallback(
    (payload: SeedPayload | null) => {
      if (seedDraftPreviewTimerRef.current) {
        clearTimeout(seedDraftPreviewTimerRef.current);
        seedDraftPreviewTimerRef.current = null;
      }
      if (!payload) {
        resetSeedPreviewState();
        return;
      }
      seedDraftPreviewTimerRef.current = setTimeout(() => {
        seedDraftPreviewTimerRef.current = null;
        void refreshSeedPreview(payload);
      }, 360);
    },
    [refreshSeedPreview, resetSeedPreviewState],
  );

  return {
    referenceYear,
    setReferenceYear,
    referenceYearRef,
    seedPreviewPillars,
    seedPreviewTimeline,
    seedPreviewBusy,
    seedPreviewError,
    refreshSeedPreview,
    scheduleSeedDraftPreview,
    resetSeedPreviewState,
  };
}
