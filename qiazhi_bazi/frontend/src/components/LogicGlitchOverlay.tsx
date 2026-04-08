"use client";

import { useEffect, useState } from "react";

type Props = {
  active: boolean;
};

export function LogicGlitchOverlay({ active }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!active) return;
    setVisible(true);
    if (typeof navigator !== "undefined" && typeof navigator.vibrate === "function") {
      navigator.vibrate(35);
    }
    const timer = window.setTimeout(() => setVisible(false), 180);
    return () => window.clearTimeout(timer);
  }, [active]);

  if (!visible) return null;
  return (
    <div
      data-testid="logic-glitch-overlay"
      className="pointer-events-none fixed inset-0 z-40 mix-blend-screen"
      style={{
        background:
          "linear-gradient(120deg, rgba(255,0,80,0.16), rgba(0,255,220,0.12), rgba(255,255,255,0.06))",
        clipPath: "polygon(0 2%, 100% 0, 100% 28%, 0 34%, 0 38%, 100% 35%, 100% 66%, 0 70%, 0 74%, 100% 70%, 100% 100%, 0 98%)",
        transform: "translate3d(1px,-1px,0)",
      }}
    />
  );
}
