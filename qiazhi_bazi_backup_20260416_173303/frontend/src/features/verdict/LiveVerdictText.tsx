"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";

type FrameRow = {
  source_id?: string;
  layer?: string;
  payload?: Record<string, unknown>;
};

function pluginEmphasisWords(frames: FrameRow[]): string[] {
  const out: string[] = [];
  for (const f of frames) {
    if (String(f.layer || "").toUpperCase() !== "PLUGIN") continue;
    const payload = (f.payload || {}) as Record<string, unknown>;
    const raw = String(payload.render_text || "");
    const tokens = raw
      .split(/[\s:|,，。；;]+/)
      .map((s) => s.trim())
      .filter((s) => s.length >= 2 && s.length <= 8);
    for (const t of tokens) {
      if (!out.includes(t)) out.push(t);
      if (out.length >= 20) return out;
    }
  }
  return out;
}

export function LiveVerdictText({
  metadata,
  reactionKey = 0,
}: {
  metadata?: Record<string, unknown>;
  reactionKey?: number;
}) {
  const [localWillFlash, setLocalWillFlash] = useState<"ACK" | "IGNORE" | "">("");
  const [optimisticActionFrames, setOptimisticActionFrames] = useState<FrameRow[]>([]);
  const frames = (Array.isArray(metadata?.assertion_evolution_frames_v14) ? metadata?.assertion_evolution_frames_v14 : []) as FrameRow[];
  const mergedFrames = useMemo(() => [...frames, ...optimisticActionFrames], [frames, optimisticActionFrames]);
  const liveLines = useMemo(() => {
    const out: string[] = [];
    for (const f of mergedFrames) {
      const layer = String(f.layer || "").toUpperCase();
      if (!["NARRATOR", "PLUGIN", "SNAPSHOT", "ACTION_TAKEN"].includes(layer)) continue;
      const payload = (f.payload || {}) as Record<string, unknown>;
      const content = String(payload.render_text || "").trim();
      if (!content) continue;
      for (const row of content.split("\n")) {
        const line = String(row || "").trim();
        if (line) out.push(line);
      }
    }
    return out.slice(-14);
  }, [mergedFrames]);
  const lines = useMemo(() => {
    return liveLines;
  }, [liveLines]);
  const pluginWords = useMemo(() => pluginEmphasisWords(mergedFrames), [mergedFrames]);
  const tone = useMemo(() => {
    const md = (metadata || {}) as Record<string, unknown>;
    const uiWill = String(md.user_intention || "");
    if (uiWill === "seek_stability") return "stability";
    if (uiWill === "seek_wealth") return "aggressive";
    return "default";
  }, [metadata]);
  const willTone = useMemo(() => {
    const reg = (metadata?.decision_impact_registry_v14_01 || {}) as { events?: Array<Record<string, unknown>> };
    const events = Array.isArray(reg.events) ? reg.events : [];
    const last = events.length ? events[events.length - 1] : null;
    const v = String(last?.verb || "").toUpperCase();
    if (v === "ACK") return "ACK";
    if (v === "IGNORE") return "IGNORE";
    return "";
  }, [metadata]);
  const torqueAmp = useMemo(() => {
    for (let i = mergedFrames.length - 1; i >= 0; i--) {
      const f = mergedFrames[i];
      if (String(f.layer || "").toUpperCase() !== "PHYSICS") continue;
      const payload = (f.payload || {}) as Record<string, unknown>;
      const t = Number(payload.torque ?? payload.tension ?? payload.global_conflict_tension ?? 0);
      if (Number.isFinite(t) && t > 0) return Math.max(0, Math.min(1, t));
    }
    return 0;
  }, [mergedFrames]);
  const collapseTick = localWillFlash || willTone ? 1 : 0;

  useEffect(() => {
    function onWillEvent(ev: Event) {
      const d = (ev as CustomEvent<{ verb?: string; action_id?: string; render_text?: string }>).detail || {};
      const v = String(d.verb || "").toUpperCase();
      if (v === "ACK" || v === "IGNORE") {
        setLocalWillFlash(v);
        window.setTimeout(() => setLocalWillFlash(""), 800);
      }
      const actionId = String(d.action_id || "").trim();
      const optimisticText = String(d.render_text || "").trim();
      if (actionId && optimisticText) {
        setOptimisticActionFrames((prev) => [
          ...prev.filter((x) => String(((x.payload || {}) as Record<string, unknown>).action_id || "") !== actionId).slice(-6),
          {
            layer: "ACTION_TAKEN",
            payload: { render_text: optimisticText, action_id: actionId, optimistic: true },
          },
        ]);
        window.setTimeout(
          () =>
            setOptimisticActionFrames((prev) =>
              prev.filter((x) => String(((x.payload || {}) as Record<string, unknown>).action_id || "") !== actionId),
            ),
          1200,
        );
      }
    }
    if (typeof window !== "undefined") {
      window.addEventListener("qiazhi:will-impact", onWillEvent as EventListener);
      return () => window.removeEventListener("qiazhi:will-impact", onWillEvent as EventListener);
    }
    return;
  }, []);

  if (!lines.length) return null;

  return (
    <motion.div
      key={`tone-${reactionKey}-${tone}`}
      initial={{ opacity: 0.96 }}
      animate={{
        opacity: collapseTick ? [0.82, 1] : 1,
        y: collapseTick ? [2, 0] : 0,
        scale: collapseTick ? [0.992, 1] : 1,
        boxShadow:
          tone === "stability"
            ? ["0 0 0 rgba(30,64,175,0)", "0 0 18px rgba(30,64,175,0.35)", "0 0 0 rgba(30,64,175,0)"]
            : tone === "aggressive"
              ? ["0 0 0 rgba(245,158,11,0)", "0 0 18px rgba(245,158,11,0.35)", "0 0 0 rgba(245,158,11,0)"]
              : undefined,
      }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`mt-2 overflow-x-hidden rounded-lg border p-2 ${
        localWillFlash === "ACK"
          ? "border-blue-500/70 bg-blue-950/20"
          : localWillFlash === "IGNORE"
            ? "border-amber-500/70 bg-amber-950/15"
            : "border-zinc-800/90 bg-black/20"
      }`}
      style={{
        backgroundImage: `radial-gradient(circle at 20% 18%, rgba(168,85,247,${0.1 + torqueAmp * 0.18}), transparent 48%), radial-gradient(circle at 78% 72%, rgba(192,132,252,${0.06 + torqueAmp * 0.14}), transparent 52%)`,
        transformOrigin: "center center",
      }}
    >
      <p className="mb-1 text-[10px] uppercase tracking-[0.2em] text-violet-300/70">Text Evolution</p>
      <motion.div layout transition={{ type: "spring", damping: 24, stiffness: 320 }}>
      <AnimatePresence initial={false}>
        {lines.map((line, i) => {
          const pluginHit = pluginWords.some((w) => w && line.includes(w));
          const ackBoost = willTone === "ACK" || localWillFlash === "ACK";
          const ignoreFade = willTone === "IGNORE" || localWillFlash === "IGNORE";
          return (
            <motion.p
              key={`${i}-${line}`}
              layout
              initial={{ opacity: 0, y: 6, scale: 0.996 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: 1,
                textShadow: pluginHit
                  ? ["0 0 0px rgba(168,85,247,0)", "0 0 10px rgba(168,85,247,0.45)", "0 0 0px rgba(168,85,247,0)"]
                  : undefined,
              }}
              transition={{ duration: 0.34, ease: "easeOut", delay: i * 0.015 }}
              className={`break-all whitespace-pre-wrap text-[13px] leading-relaxed ${
                ignoreFade ? "text-zinc-300/85" : "text-zinc-100/95"
              } ${(pluginHit || ackBoost) ? "font-bold" : "font-normal"}`}
            >
              {line}
            </motion.p>
          );
        })}
      </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}

