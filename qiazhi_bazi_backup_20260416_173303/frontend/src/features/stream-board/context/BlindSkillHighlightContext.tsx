"use client";

import React, { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";

type Ctx = {
  highlightedBadgeId: string | null;
  setHighlightedBadgeId: (id: string | null) => void;
};

const BlindSkillHighlightContext = createContext<Ctx | null>(null);

export function BlindSkillHighlightProvider({ children }: { children: ReactNode }) {
  const [highlightedBadgeId, setHighlightedBadgeIdState] = useState<string | null>(null);
  const setHighlightedBadgeId = useCallback((id: string | null) => {
    setHighlightedBadgeIdState(id);
  }, []);
  const value = useMemo(
    () => ({ highlightedBadgeId, setHighlightedBadgeId }),
    [highlightedBadgeId, setHighlightedBadgeId],
  );
  return <BlindSkillHighlightContext.Provider value={value}>{children}</BlindSkillHighlightContext.Provider>;
}

/** 无 Provider 时安全降级（不联动徽章） */
export function useBlindSkillHighlight(): Ctx {
  const ctx = useContext(BlindSkillHighlightContext);
  if (!ctx) {
    return { highlightedBadgeId: null, setHighlightedBadgeId: () => undefined };
  }
  return ctx;
}
