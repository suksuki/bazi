"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";

type Decision = {
  id?: string;
  title?: string;
  label?: string;
};

type Frame = {
  layer?: string;
  payload?: {
    pending_decisions?: Decision[];
  };
};

export function V17_DecisionInbox({
  frames,
  adoptedIds,
  sessionId,
  onAdopted,
}: {
  frames: Frame[];
  adoptedIds: string[];
  sessionId: string;
  onAdopted?: (decision: Decision) => void;
}) {
  const [busyId, setBusyId] = useState<string>("");
  const latestSnapshot = useMemo(
    () => [...(frames || [])].reverse().find((f) => String(f?.layer || "").toUpperCase() === "SNAPSHOT"),
    [frames],
  );
  const decisions = (latestSnapshot?.payload?.pending_decisions || []).filter((d, idx) => {
    const id = String(d?.id || idx);
    return !adoptedIds.includes(id);
  });

  async function onPick(decision: Decision) {
    const id = String(decision.id || decision.title || "pick");
    setBusyId(id);
    onAdopted?.(decision);
    try {
      await fetch("/api/v17/action", {
        method: "POST",
        headers: { "Content-Type": "application/json", v17_origin: "v17_rebirth" },
        body: JSON.stringify({
          signal: "ACTION_TAKEN",
          action: String(decision.label || decision.title || "").trim(),
          session_id: sessionId || "default",
          v17_origin: "v17_rebirth",
        }),
      });
    } finally {
      setBusyId("");
    }
  }

  if (!decisions.length) return null;

  return (
    <section className="rounded-xl border border-violet-700/40 bg-zinc-950/70 p-3">
      <p className="mb-2 text-xs text-violet-200/80">Decision Inbox</p>
      <div className="flex flex-wrap gap-2">
        {decisions.map((d, idx) => {
          const id = String(d.id || idx);
          return (
            <motion.button
              key={id}
              type="button"
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => onPick(d)}
              disabled={busyId === id}
              className="rounded-full border border-violet-500/40 bg-violet-900/20 px-3 py-1.5 text-xs text-violet-100 transition hover:bg-violet-700/30 disabled:opacity-75"
            >
              <span className="inline-flex items-center gap-1">
                {(d.label || d.title || "行动建议").trim()}
              </span>
            </motion.button>
          );
        })}
      </div>
    </section>
  );
}
