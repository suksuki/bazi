"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";

type Decision = {
  id?: string;
  title?: string;
  label?: string;
  priority?: number;
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
  locked = false,
  lockMessage = "",
  onAdopted,
}: {
  frames: Frame[];
  adoptedIds: string[];
  sessionId: string;
  locked?: boolean;
  lockMessage?: string;
  onAdopted?: (decision: Decision) => void;
}) {
  const [busyId, setBusyId] = useState<string>("");
  const latestSnapshot = useMemo(
    () =>
      [...(frames || [])].reverse().find((f) => {
        if (String(f?.layer || "").toUpperCase() !== "SNAPSHOT") return false;
        const sk = String((f?.payload as { snapshot_kind?: string })?.snapshot_kind || "").trim();
        return sk === "physics" || sk === "physical_void" || sk === "system_init_failure";
      }),
    [frames],
  );
  const { visible: decisions, hiddenCount } = useMemo(() => {
    const raw = (latestSnapshot?.payload?.pending_decisions || []).filter((d, idx) => {
      const id = String(d?.id || idx);
      return !adoptedIds.includes(id);
    });
    const sorted = [...raw].sort((a, b) => (Number(b.priority) || 0) - (Number(a.priority) || 0));
    const DISPLAY_CAP = 14;
    const cap = Math.min(sorted.length, DISPLAY_CAP);
    return { visible: sorted.slice(0, cap), hiddenCount: Math.max(0, sorted.length - cap) };
  }, [latestSnapshot?.payload?.pending_decisions, adoptedIds]);

  async function onPick(decision: Decision) {
    if (locked || busyId) return;
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
      <p className="mb-2 text-xs text-violet-200/80">Decision Inbox（按 priority 截取展示）</p>
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
              disabled={locked || busyId !== ""}
              className="rounded-full border border-violet-500/40 bg-violet-900/20 px-3 py-1.5 text-xs text-violet-100 transition hover:bg-violet-700/30 disabled:cursor-not-allowed disabled:opacity-75"
            >
              <span className="inline-flex items-center gap-1">
                {(d.label || d.title || "行动建议").trim()}
              </span>
            </motion.button>
          );
        })}
      </div>
      {locked && lockMessage ? <p className="mt-2 text-[11px] text-amber-200/85">{lockMessage}</p> : null}
      {hiddenCount > 0 ? (
        <p className="mt-2 text-[11px] text-zinc-500">另有 {hiddenCount} 条决策已接收但未展开，可拉高 SNAPSHOT 中 pending_decisions 上限或调低已采纳项。</p>
      ) : null}
    </section>
  );
}
