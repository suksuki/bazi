"use client";

import { motion } from "framer-motion";
import { useMemo } from "react";
import { LiveVerdictText } from "@/features/verdict/LiveVerdictText";

type FrameRow = {
  timestamp?: string;
  source_id?: string;
  content_delta?: string;
  layer?: string;
  payload?: unknown;
};

function resolveWillTone(metadata: Record<string, unknown>): "stability" | "aggressive" | "default" {
  const reg = metadata.decision_impact_registry_v14_01;
  const events = Array.isArray((reg as { events?: unknown[] } | undefined)?.events)
    ? ((reg as { events?: unknown[] }).events as unknown[])
    : [];
  const recent = events.slice(-8);
  const blob = recent
    .map((e) => {
      const row = (e || {}) as Record<string, unknown>;
      return `${String(row.note || "")} ${String(row.narrative || "")} ${String(row.subject || "")}`;
    })
    .join(" ");
  if (blob.includes("稳健") || blob.includes("避险")) return "stability";
  if (blob.includes("激进") || blob.includes("进攻") || blob.includes("冒进")) return "aggressive";
  const uiWill = String(metadata.user_intention || "");
  if (uiWill === "seek_stability") return "stability";
  if (uiWill === "seek_wealth") return "aggressive";
  return "default";
}

export function PurpleVerdictCard({
  metadata,
  godOfUse = [],
  godOfTaboo = [],
  reactionKey = 0,
  className = "",
}: {
  metadata?: Record<string, unknown>;
  godOfUse?: string[];
  godOfTaboo?: string[];
  reactionKey?: number;
  className?: string;
}) {
  const md = (metadata || {}) as Record<string, unknown>;
  const frames = (Array.isArray(md.assertion_evolution_frames_v14) ? md.assertion_evolution_frames_v14 : []) as FrameRow[];
  const physicsFrames = frames.filter((f) => String(f.layer || "").toUpperCase() === "PHYSICS");
  const hasPierceHarmOscillation = physicsFrames.some((f) => {
    const t = `${String(f.content_delta || "")} ${JSON.stringify(f.payload || {})}`;
    return t.includes("穿害") || (t.includes("穿") && t.includes("害"));
  });
  const tone = resolveWillTone(md);

  const toneClass = useMemo(() => {
    if (tone === "stability") {
      return "border-blue-700/70 shadow-[0_0_28px_rgba(30,64,175,0.33)]";
    }
    if (tone === "aggressive") {
      return "border-amber-500/70 shadow-[0_0_28px_rgba(245,158,11,0.35)]";
    }
    return "border-violet-600/55 shadow-[0_0_24px_rgba(139,92,246,0.25)]";
  }, [tone]);

  const willTag = tone === "stability" ? "稳健" : tone === "aggressive" ? "激进" : "";
  const snapshotGods = useMemo(() => {
    for (let i = frames.length - 1; i >= 0; i--) {
      const f = frames[i];
      if (String(f.layer || "").toUpperCase() !== "SNAPSHOT") continue;
      const p = (f.payload || {}) as Record<string, unknown>;
      const use = Array.isArray(p.god_of_use) ? (p.god_of_use as unknown[]).map((x) => String(x || "").trim()).filter(Boolean) : [];
      const taboo = Array.isArray(p.god_of_taboo) ? (p.god_of_taboo as unknown[]).map((x) => String(x || "").trim()).filter(Boolean) : [];
      const runtimeMap = p.runtime_deity_map && typeof p.runtime_deity_map === "object" ? (p.runtime_deity_map as Record<string, unknown>) : {};
      let useResolved = use;
      let tabooResolved = taboo;
      if ((!useResolved.length || !tabooResolved.length) && Object.keys(runtimeMap).length > 0) {
        const ranked = Object.entries(runtimeMap)
          .map(([k, v]) => ({ k: String(k).trim(), v: Number(v || 0) }))
          .filter((x) => x.k && Number.isFinite(x.v))
          .sort((a, b) => b.v - a.v);
        if (!useResolved.length) useResolved = ranked.slice(0, 2).map((x) => x.k);
        if (!tabooResolved.length) tabooResolved = ranked.slice(-2).map((x) => x.k);
      }
      return { use: useResolved, taboo: tabooResolved };
    }
    return { use: [] as string[], taboo: [] as string[] };
  }, [frames]);
  const useDisplay = godOfUse.length ? godOfUse : snapshotGods.use;
  const tabooDisplay = godOfTaboo.length ? godOfTaboo : snapshotGods.taboo;

  return (
    <div className={`relative overflow-hidden rounded-xl border bg-zinc-950/95 ${toneClass} ${className}`}>
      <motion.div
        className="pointer-events-none absolute -left-24 -top-28 h-72 w-72 rounded-full blur-3xl"
        style={{
          background:
            tone === "stability"
              ? "radial-gradient(circle, rgba(59,130,246,0.22), transparent 72%)"
              : tone === "aggressive"
                ? "radial-gradient(circle, rgba(251,191,36,0.22), transparent 72%)"
                : "radial-gradient(circle, rgba(168,85,247,0.22), transparent 72%)",
        }}
        animate={{ x: ["0%", "8%", "0%"], y: ["0%", "4%", "0%"] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
      {hasPierceHarmOscillation ? (
        <motion.div
          className="pointer-events-none absolute inset-0 opacity-45"
          style={{
            backgroundImage:
              "repeating-linear-gradient(135deg, rgba(148,163,184,0.16) 0px, rgba(148,163,184,0.16) 2px, transparent 2px, transparent 8px)",
          }}
          animate={{ backgroundPositionX: ["0px", "16px", "0px"] }}
          transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
        />
      ) : null}
      {willTag ? (
        <div className="pointer-events-none absolute left-2 top-2 z-10 rounded border border-zinc-700 bg-black/45 px-2 py-[2px] text-[10px] text-zinc-200">
          [USER_WILL] {willTag}
        </div>
      ) : null}
      <div className="relative z-[1] p-3">
        <div className="mb-2 grid grid-cols-1 gap-2 md:grid-cols-2">
          <div className="rounded border border-emerald-600/45 bg-emerald-500/10 px-2 py-1">
            <p className="text-[10px] text-emerald-300/90">GodOfUse</p>
            <p className="text-xs font-medium text-emerald-100">{useDisplay.length ? useDisplay.join(" / ") : "--"}</p>
          </div>
          <div className="rounded border border-rose-600/45 bg-rose-500/10 px-2 py-1">
            <p className="text-[10px] text-rose-300/90">GodOfTaboo</p>
            <p className="text-xs font-medium text-rose-100">{tabooDisplay.length ? tabooDisplay.join(" / ") : "--"}</p>
          </div>
        </div>
        <LiveVerdictText metadata={metadata} reactionKey={reactionKey} />
      </div>
    </div>
  );
}

