"use client";

import { useState } from "react";

/** Arbiter 逻辑抽屉 */
export function useStreamBoardLogicDrawerState() {
  const [logicDrawerOpen, setLogicDrawerOpen] = useState(false);
  const [logicDrawerTitle, setLogicDrawerTitle] = useState("Arbiter Logic Drawer");
  const [logicDrawerFocus, setLogicDrawerFocus] = useState("");
  const [logicDrawerDetails, setLogicDrawerDetails] = useState<string[]>([]);
  const [logicDrawerTrace, setLogicDrawerTrace] = useState<Record<string, unknown> | null>(null);

  return {
    logicDrawerOpen,
    setLogicDrawerOpen,
    logicDrawerTitle,
    setLogicDrawerTitle,
    logicDrawerFocus,
    setLogicDrawerFocus,
    logicDrawerDetails,
    setLogicDrawerDetails,
    logicDrawerTrace,
    setLogicDrawerTrace,
  };
}
