"use client";

import { useMemo, useState } from "react";

type ConfirmedDecisionItem = {
  id: string;
  label: string;
  is_confirmed: boolean;
  confirmed_at?: string;
};

type Props = {
  items: ConfirmedDecisionItem[];
  onRevoke?: (id: string) => void | Promise<void>;
};

export function WillReplayPanel({ items, onRevoke }: Props) {
  const [collapsed, setCollapsed] = useState(true);
  const sorted = useMemo(
    () => [...items].sort((a, b) => new Date(b.confirmed_at || 0).getTime() - new Date(a.confirmed_at || 0).getTime()),
    [items],
  );
  if (sorted.length === 0) return null;

  return (
    <section className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
      <button
        type="button"
        onClick={() => setCollapsed((v) => !v)}
        className="flex w-full items-center justify-between rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-left"
      >
        <span className="flex items-center gap-2 text-sm font-medium text-zinc-100">
          意志回放
          {collapsed ? <span className="inline-block h-2 w-2 rounded-full bg-red-500" aria-hidden="true" /> : null}
        </span>
        <span className="text-xs text-zinc-400">{collapsed ? "展开" : "收起"}</span>
      </button>
      {!collapsed ? (
        <ol className="mt-3">
          {sorted.map((item, index) => (
            <li key={item.id} className="relative pl-6">
              {index < sorted.length - 1 ? (
                <span
                  aria-hidden="true"
                  className="absolute left-[9px] top-4 h-[calc(100%+0.75rem)] border-l border-dashed border-fuchsia-500/55"
                />
              ) : null}
              <span
                aria-hidden="true"
                className="absolute left-0 top-2.5 h-[18px] w-[18px] rounded-full border border-fuchsia-400/70 bg-[#A855F7] shadow-[0_0_0_4px_rgba(168,85,247,0.16)] animate-pulse"
              />
              <div className="mb-3 rounded-lg border border-fuchsia-500/45 bg-fuchsia-500/10 p-3">
                <div className="flex items-start justify-between gap-3">
                  <p className="min-w-0 text-sm text-fuchsia-100">
                    <span className="text-fuchsia-300">[{item.id}]</span>
                    {" - "}
                    <span>{item.label || "--"}</span>
                    {" - "}
                    <span className="text-zinc-400">{item.confirmed_at ? new Date(item.confirmed_at).toLocaleString() : "--"}</span>
                  </p>
                  <button
                    type="button"
                    className="rounded-md border border-red-500/40 px-2 py-1 text-xs text-red-200 hover:bg-red-500/10"
                    onClick={() => onRevoke?.(item.id)}
                    aria-label={`Revert ${item.id}`}
                  >
                    ↺ Revert
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
