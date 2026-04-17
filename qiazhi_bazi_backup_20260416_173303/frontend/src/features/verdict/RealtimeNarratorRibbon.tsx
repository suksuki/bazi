"use client";

import { useEffect, useRef, useState } from "react";
import { API_BASE } from "@/features/stream-board/constants";

type NarrResp = { text?: string };

export function RealtimeNarratorRibbon({
  metadata,
  physicsTensor,
  refreshKey = 0,
}: {
  metadata?: Record<string, unknown>;
  physicsTensor?: Record<string, unknown> | null;
  refreshKey?: number;
}) {
  const [text, setText] = useState("旁白待命中：点击决策项后将实时生成前瞻导引。");
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function pull() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/realtime-narrator`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            metadata: metadata || {},
            physics_tensor: physicsTensor || {},
            max_chars: 240,
          }),
        });
        if (!res.ok) return;
        const data = (await res.json()) as NarrResp;
        if (!cancelled && data?.text) setText(String(data.text));
      } catch {
        // silent
      }
    }

    pull(); // instant refresh on inbox interaction
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = window.setInterval(pull, 6000);

    return () => {
      cancelled = true;
      if (timerRef.current) window.clearInterval(timerRef.current);
      timerRef.current = null;
    };
  }, [metadata, physicsTensor, refreshKey]);

  return (
    <div className="mb-2 overflow-hidden rounded-lg border border-fuchsia-500/35 bg-fuchsia-950/25">
      <div className="px-2 pt-1 text-[10px] uppercase tracking-[0.2em] text-fuchsia-200/70">Realtime Narrator</div>
      <div className="relative h-8">
        <div className="absolute inset-y-0 left-0 w-10 bg-gradient-to-r from-fuchsia-950/80 to-transparent" />
        <div className="absolute inset-y-0 right-0 w-10 bg-gradient-to-l from-fuchsia-950/80 to-transparent" />
        <div className="animate-[marquee_20s_linear_infinite] whitespace-nowrap px-3 text-sm leading-8 text-fuchsia-100/95">
          {text}
        </div>
      </div>
    </div>
  );
}

