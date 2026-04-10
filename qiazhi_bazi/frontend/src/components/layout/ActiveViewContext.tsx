"use client";

import { createContext, useContext } from "react";

export type ShellActiveView = "lab" | "debug" | "admin";

export type ActiveViewContextValue = {
  activeView: ShellActiveView;
  setActiveView: (v: ShellActiveView) => void;
};

export const ActiveViewContext = createContext<ActiveViewContextValue | null>(null);

export function useActiveView(): ActiveViewContextValue {
  const ctx = useContext(ActiveViewContext);
  if (!ctx) {
    throw new Error("useActiveView must be used within ActiveViewContext.Provider");
  }
  return ctx;
}
