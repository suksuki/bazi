"use client";

import { useMemo, useState } from "react";
import { RotateCcw, Sparkles } from "lucide-react";

import { V17_NatalInput } from "@/components/V17_NatalInput";
import { V17_PurpleVerdictCard } from "@/components/V17_PurpleVerdictCard";
import { useV17WebStream } from "@/hooks/useV17WebStream";

export default function OraclePage() {
  const [running, setRunning] = useState(false);
  const [streamEndpoint, setStreamEndpoint] = useState<string | null>("/v17/stream?will_proxy=stable");
  const [streamBody, setStreamBody] = useState<Record<string, unknown> | null>(null);
  const { frames } = useV17WebStream({
    endpoint: streamEndpoint,
    enabled: running,
    method: "POST",
    body: streamBody,
  });

  const hasNarrative = useMemo(
    () => frames.some((f) => String(f?.payload?.render_text || "").trim().length > 0),
    [frames],
  );

  function startRun(input: { birthTimeISO: string; gender: "male" | "female"; calendarType: "solar" | "lunar" }) {
    const query = new URLSearchParams({
      will_proxy: "stable",
      birth_time: input.birthTimeISO,
      gender: input.gender,
    });
    setStreamEndpoint(`/v17/stream?${query.toString()}`);
    setStreamBody({
      v17_origin: "v17_rebirth",
      calendar_type: input.calendarType,
    });
    setRunning(true);
  }

  function resetRun() {
    setRunning(false);
    setStreamBody(null);
  }

  return (
    <main className="min-h-screen bg-zinc-950 p-6 text-zinc-100">
      <section className="mx-auto flex w-full max-w-4xl flex-col gap-4">
        <header className="flex items-center justify-between gap-2 text-violet-300">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            <h1 className="text-lg font-semibold tracking-wide">V17 Oracle Temple</h1>
          </div>
          {running ? (
            <button
              type="button"
              onClick={resetRun}
              className="inline-flex items-center gap-1 rounded-md border border-violet-300/40 bg-violet-900/20 px-2 py-1 text-xs text-violet-100 hover:bg-violet-800/30"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              重测
            </button>
          ) : null}
        </header>

        <div className="relative">
          {running ? (
            <div className="absolute inset-0 z-20 animate-[fadeOut_280ms_ease-out_forwards] rounded-2xl bg-black/50 backdrop-blur-[1px]" />
          ) : null}
          {!running ? <V17_NatalInput onStart={startRun} /> : null}
        </div>

        {running ? (
          <div className="flex min-h-[60vh] items-stretch">
            <div className="w-full">
              <V17_PurpleVerdictCard frames={frames} />
              {!hasNarrative ? (
                <p className="mt-3 text-xs text-violet-200/80">V17 织造启动中，正在同步快照与叙事流...</p>
              ) : null}
            </div>
          </div>
        ) : null}
      </section>
    </main>
  );
}
