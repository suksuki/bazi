"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { ADMIN_HEADERS, API_BASE } from "@/features/admin-settings/constants";

type CausalRoutingConfig = {
  conflict_strategy: "conservative" | "school_priority" | "manual_arbitration";
  school_sovereignty: boolean;
  priority_base_physics: number;
  priority_blind_school: number;
  layer_L1: number;
  layer_L2: number;
};

const DEFAULT_ROUTING: CausalRoutingConfig = {
  conflict_strategy: "conservative",
  school_sovereignty: false,
  priority_base_physics: 100,
  priority_blind_school: 80,
  layer_L1: 100,
  layer_L2: 80,
};

const RUNTIME_URL = `${API_BASE}/api/admin/runtime-config`;

function mergeRouting(raw: unknown): CausalRoutingConfig {
  if (!raw || typeof raw !== "object") return { ...DEFAULT_ROUTING };
  const o = raw as Record<string, unknown>;
  const s = String(o.conflict_strategy || "conservative");
  const strategy =
    s === "school_priority" || s === "manual_arbitration" ? (s as CausalRoutingConfig["conflict_strategy"]) : "conservative";
  return {
    conflict_strategy: strategy,
    school_sovereignty: Boolean(o.school_sovereignty),
    priority_base_physics: Number(o.priority_base_physics ?? DEFAULT_ROUTING.priority_base_physics),
    priority_blind_school: Number(o.priority_blind_school ?? DEFAULT_ROUTING.priority_blind_school),
    layer_L1: Number(o.layer_L1 ?? DEFAULT_ROUTING.layer_L1),
    layer_L2: Number(o.layer_L2 ?? DEFAULT_ROUTING.layer_L2),
  };
}

export function RoutingMatrixPanel() {
  const [routing, setRouting] = useState<CausalRoutingConfig>(DEFAULT_ROUTING);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setStatus(null);
    try {
      const res = await fetch(RUNTIME_URL, { headers: ADMIN_HEADERS });
      if (!res.ok) throw new Error(`读取失败 ${res.status}`);
      const j = (await res.json()) as { config?: { causal_routing?: unknown } };
      setRouting(mergeRouting(j.config?.causal_routing));
    } catch (e) {
      setStatus(String(e));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    setBusy(true);
    setStatus(null);
    try {
      const cur = await fetch(RUNTIME_URL, { headers: ADMIN_HEADERS });
      if (!cur.ok) throw new Error(`读取 LLM 段失败 ${cur.status}`);
      const body = (await cur.json()) as { config?: { llm?: Record<string, unknown> } };
      const llm = (body.config?.llm && typeof body.config.llm === "object" ? body.config.llm : {}) as Record<string, unknown>;
      const res = await fetch(RUNTIME_URL, {
        method: "PUT",
        headers: { ...ADMIN_HEADERS, "Content-Type": "application/json" },
        body: JSON.stringify({ llm, causal_routing: routing }),
      });
      if (!res.ok) throw new Error(`保存失败 ${res.status}`);
      setStatus("已保存（仅更新 causal_routing，LLM 段未改动）。");
    } catch (e) {
      setStatus(String(e));
    } finally {
      setBusy(false);
    }
  };

  const preview = useMemo(() => {
    const s = routing.conflict_strategy;
    const ten = s === "school_priority" || routing.school_sovereignty ? "印比轴以盲派向量为单一事实源。" : "多插件十神影响按层级与权比加权融合。";
    const assertStyle =
      s === "manual_arbitration" ? "断言风格：暂停自动极性裁决，等待人工。" : "断言风格：与路由策略一致的折中/主权偏向。";
    const llm =
      routing.school_sovereignty || s === "school_priority"
        ? "LLM 知识注入：Skill 模板按 sovereignty 排序，盲派高主权条目靠前。"
        : "LLM 知识注入：Skill 按 sovereignty 弱排序，仍以全量模板约束。";
    return { ten, assertStyle, llm };
  }, [routing]);

  return (
    <div className="space-y-4 rounded-xl border border-zinc-800 bg-zinc-950/50 p-4">
      <header>
        <h2 className="text-sm font-semibold text-zinc-100">因果路由矩阵</h2>
        <p className="mt-0.5 text-[11px] text-zinc-500">写入 runtime_config.json 的 causal_routing；推演时由 CausalRouter 消费。</p>
      </header>

      {status ? <p className="text-[11px] text-amber-200/90">{status}</p> : null}

      <label className="block text-[11px] text-zinc-300">
        冲突解决策略
        <select
          className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-100"
          value={routing.conflict_strategy}
          disabled={busy}
          onChange={(e) =>
            setRouting((r) => ({ ...r, conflict_strategy: e.target.value as CausalRoutingConfig["conflict_strategy"] }))
          }
        >
          <option value="conservative">保守模式（加权求和）</option>
          <option value="school_priority">流派优先</option>
          <option value="manual_arbitration">人工仲裁</option>
        </select>
      </label>

      <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-300">
        <input
          type="checkbox"
          checked={routing.school_sovereignty}
          disabled={busy}
          onChange={(e) => setRouting((r) => ({ ...r, school_sovereignty: e.target.checked }))}
          className="accent-violet-500"
        />
        流派主权（L2 盲派 η/向量优先覆盖同类十神轴）
      </label>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block text-[11px] text-zinc-300">
          base_physics 权比
          <input
            type="number"
            min={1}
            max={200}
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-100"
            value={routing.priority_base_physics}
            disabled={busy}
            onChange={(e) => setRouting((r) => ({ ...r, priority_base_physics: Number(e.target.value) }))}
          />
        </label>
        <label className="block text-[11px] text-zinc-300">
          blind_school 权比
          <input
            type="number"
            min={1}
            max={200}
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-100"
            value={routing.priority_blind_school}
            disabled={busy}
            onChange={(e) => setRouting((r) => ({ ...r, priority_blind_school: Number(e.target.value) }))}
          />
        </label>
        <label className="block text-[11px] text-zinc-300">
          层级 L1 系数
          <input
            type="number"
            min={1}
            max={200}
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-100"
            value={routing.layer_L1}
            disabled={busy}
            onChange={(e) => setRouting((r) => ({ ...r, layer_L1: Number(e.target.value) }))}
          />
        </label>
        <label className="block text-[11px] text-zinc-300">
          层级 L2 系数
          <input
            type="number"
            min={1}
            max={200}
            className="mt-1 w-full rounded border border-zinc-700 bg-zinc-900 px-2 py-1 font-mono text-xs text-zinc-100"
            value={routing.layer_L2}
            disabled={busy}
            onChange={(e) => setRouting((r) => ({ ...r, layer_L2: Number(e.target.value) }))}
          />
        </label>
      </div>

      <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-[11px] leading-relaxed text-zinc-400">
        <p className="font-medium text-zinc-300">影响预览</p>
        <ul className="mt-2 list-inside list-disc space-y-1">
          <li>
            <span className="text-zinc-500">十神强弱：</span>
            {preview.ten}
          </li>
          <li>
            <span className="text-zinc-500">断言风格：</span>
            {preview.assertStyle}
          </li>
          <li>
            <span className="text-zinc-500">LLM 知识注入：</span>
            {preview.llm}
          </li>
        </ul>
      </div>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => save()}
          disabled={busy}
          className="rounded border border-emerald-600/50 bg-emerald-950/40 px-3 py-1.5 text-xs text-emerald-100 hover:bg-emerald-900/50 disabled:opacity-40"
        >
          保存路由配置
        </button>
        <button
          type="button"
          onClick={() => load()}
          disabled={busy}
          className="rounded border border-zinc-600 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 disabled:opacity-40"
        >
          重新加载
        </button>
      </div>
    </div>
  );
}
