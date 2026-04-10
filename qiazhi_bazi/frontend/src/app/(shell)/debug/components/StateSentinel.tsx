"use client";

import { useMemo, useState } from "react";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";

type AuditFilter = "ALL" | "CRITICAL" | "WILL";

export function StateSentinel() {
  const { state } = useLabStore();
  const rows = state.updates || [];
  const [filter, setFilter] = useState<AuditFilter>("ALL");

  const visible = useMemo(() => {
    if (filter === "ALL") return rows;
    if (filter === "CRITICAL") {
      return rows.filter((row) => typeof row.abs_delta === "number" && row.abs_delta > 100);
    }
    return rows.filter((row) => row.reversionImpact || row.decisionMutation);
  }, [rows, filter]);

  const segments: { id: AuditFilter; label: string }[] = [
    { id: "ALL", label: "ALL" },
    { id: "CRITICAL", label: "CRITICAL" },
    { id: "WILL", label: "WILL" },
  ];

  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-3">
      <h2 className="text-sm font-medium text-zinc-200">State Sentinel</h2>
      <p className="mt-1 text-[11px] text-zinc-500">最近 5 次 Model 更新。</p>

      <div
        className="mt-2 inline-flex rounded-lg border border-zinc-700 bg-zinc-950/80 p-0.5"
        role="tablist"
        aria-label="审计视角"
      >
        {segments.map((seg) => (
          <button
            key={seg.id}
            type="button"
            role="tab"
            aria-selected={filter === seg.id}
            className={`rounded-md px-2.5 py-1 text-[10px] font-medium uppercase tracking-wide ${
              filter === seg.id
                ? "bg-zinc-700 text-zinc-100"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
            onClick={() => setFilter(seg.id)}
          >
            {seg.label}
          </button>
        ))}
      </div>

      <ul className="mt-2 space-y-2">
        {visible.length === 0 ? (
          <li className="text-xs text-zinc-500">当前筛选下无记录。</li>
        ) : (
          visible.map((row) => (
            <li
              key={row.id}
              className={`rounded border px-2 py-1 text-[11px] ${
                row.overload || row.reversionImpact
                  ? "border-[#A855F7]/60 bg-fuchsia-500/10 text-fuchsia-200"
                  : "border-zinc-800 bg-zinc-950/70 text-zinc-300"
              }`}
            >
              <p>{new Date(row.ts).toLocaleTimeString()} | keys: {row.keys.join(", ") || "--"}</p>
              <p>abs_delta: {typeof row.abs_delta === "number" ? row.abs_delta.toFixed(2) : "--"}</p>
              {row.last_log ? <p className="text-[10px] text-zinc-400">{row.last_log}</p> : null}
            </li>
          ))
        )}
      </ul>
    </section>
  );
}
