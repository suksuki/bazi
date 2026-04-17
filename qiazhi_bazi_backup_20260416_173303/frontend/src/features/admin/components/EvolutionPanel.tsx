"use client";

import { useCallback, useEffect, useState } from "react";
import {
  evolutionAdmissionUrl,
  evolutionRunBatchUrl,
  evolutionStateUrl,
} from "@/features/stream-board/lib/evolutionApiUrl";

type HeatCell = {
  skill_id: string;
  maturity: number;
  fitness_score: number;
  generation_id: number;
  parameter_count: number;
};

type EvolutionState = {
  combination_space_total: number;
  admission: boolean;
  heatmap: HeatCell[];
  genes: Array<Record<string, unknown>>;
};

export function EvolutionPanel() {
  const [state, setState] = useState<EvolutionState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch(evolutionStateUrl(), { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const j = (await res.json()) as EvolutionState;
      setState(j);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const setAdmission = async (next: boolean) => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(evolutionAdmissionUrl(), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ admit_evolved_to_mainnet: next }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const runBatch = async () => {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch(evolutionRunBatchUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ n_seeds: 24 }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  const heat = state?.heatmap ?? [];

  return (
    <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
      <header className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-sm font-semibold text-zinc-100">演化仪表盘</h2>
          <p className="mt-0.5 text-[11px] text-zinc-500">
            设计空间基数 {state?.combination_space_total?.toLocaleString() ?? "—"}；基因成熟度越高表示该 Skill 参数面更活跃。
          </p>
        </div>
        <button
          type="button"
          onClick={() => refresh()}
          disabled={busy}
          className="rounded border border-violet-500/40 bg-violet-500/10 px-2 py-1 text-[11px] text-violet-200 hover:bg-violet-500/20 disabled:opacity-40"
        >
          刷新
        </button>
      </header>

      {error ? <div className="rounded border border-rose-500/40 bg-rose-500/10 px-2 py-1 text-[11px] text-rose-200">{error}</div> : null}

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
        <p className="text-[10px] font-medium uppercase tracking-wide text-amber-200/90">演化准入（并入 L1/L2 物理主网）</p>
        <p className="mt-1 text-[11px] text-zinc-400">
          关闭时 DNA 覆盖不生效；开启后高 fitness 的 `evolved_parameters` 才经 DnaOverlay 写入运行时 physics。
        </p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <span className={`text-xs font-mono ${state?.admission ? "text-emerald-300" : "text-zinc-500"}`}>
            当前：{state?.admission ? "已准入" : "未准入"}
          </span>
          <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-300">
            <input
              type="checkbox"
              checked={Boolean(state?.admission)}
              disabled={busy || !state}
              onChange={(e) => setAdmission(e.target.checked)}
              className="accent-amber-500"
            />
            允许演化参数覆盖主网
          </label>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
        <div className="flex items-center justify-between gap-2">
          <p className="text-[10px] font-medium uppercase tracking-wide text-cyan-200/90">基因成熟度热图</p>
          <button
            type="button"
            onClick={() => runBatch()}
            disabled={busy}
            className="rounded border border-cyan-600/40 bg-cyan-950/50 px-2 py-0.5 text-[10px] text-cyan-100 hover:bg-cyan-900/60 disabled:opacity-40"
          >
            静默跑一批（24）
          </button>
        </div>
        {heat.length === 0 ? (
          <p className="mt-2 text-[11px] text-zinc-500">暂无基因记录（`data/dna_registry.json`）。</p>
        ) : (
          <ul className="mt-2 space-y-1.5">
            {heat.map((row) => (
              <li key={row.skill_id} className="flex items-center gap-2 text-[11px] text-zinc-300">
                <span className="w-28 shrink-0 truncate font-mono text-zinc-400" title={row.skill_id}>
                  {row.skill_id}
                </span>
                <div className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-zinc-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-violet-600/80 to-amber-500/70"
                    style={{ width: `${Math.round(row.maturity * 100)}%` }}
                  />
                </div>
                <span className="w-10 shrink-0 text-right font-mono text-zinc-500">{row.maturity.toFixed(2)}</span>
                <span className="hidden text-zinc-600 sm:inline">g{row.generation_id}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
