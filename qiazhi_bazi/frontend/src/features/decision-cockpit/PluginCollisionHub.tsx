"use client";

import { useMemo } from "react";
import { humanizePluginId, stripTimelineEnumJargon } from "./semanticLexicon";

type Props = {
  physicsTensor: Record<string, unknown> | null | undefined;
};

type ConflictEvent = {
  deity?: string;
  plugin_a?: string;
  plugin_b?: string;
  delta_a?: number;
  delta_b?: number;
  note?: string;
};

function extractMatchReason(row: Record<string, unknown>): string {
  const payload = row.payload && typeof row.payload === "object" ? (row.payload as Record<string, unknown>) : {};
  const ml = payload.matcher_logic;
  if (typeof ml === "string" && ml.trim()) return ml.trim().slice(0, 220);
  if (ml && typeof ml === "object" && !Array.isArray(ml)) {
    const o = ml as Record<string, unknown>;
    const cond = [o.condition, o.rule, o.pattern, o.summary].map((x) => (typeof x === "string" ? x : "")).find(Boolean);
    if (cond) return String(cond).slice(0, 220);
  }
  const verdict = typeof payload.verdict === "string" ? payload.verdict.trim() : "";
  if (verdict) return verdict.length > 220 ? `${verdict.slice(0, 218)}…` : verdict;
  const ev = Array.isArray(payload.evidence) ? (payload.evidence as unknown[]).map((x) => String(x)).filter(Boolean) : [];
  if (ev.length) {
    const head = ev.slice(0, 3).join("；");
    return head.length > 220 ? `${head.slice(0, 218)}…` : head;
  }
  const err = typeof payload.error === "string" ? payload.error.trim() : "";
  if (err) return `插件侧提示：${err.slice(0, 200)}`;
  return "（未返回结构化匹配条件；可查看终审 evidence 或插件 payload 原文）";
}

function pluginConfidence(row: Record<string, unknown>): number | null {
  const top = row.confidence_score;
  if (typeof top === "number" && Number.isFinite(top)) return top;
  const pl = row.payload && typeof row.payload === "object" ? (row.payload as Record<string, unknown>) : null;
  const c = pl && typeof pl.confidence === "number" && Number.isFinite(pl.confidence) ? (pl.confidence as number) : null;
  return c;
}

export function PluginCollisionHub({ physicsTensor }: Props) {
  const meta = (physicsTensor?.meta as Record<string, unknown> | undefined) || {};
  const cr = (meta.causal_routing as Record<string, unknown> | undefined) || {};

  const strategy = stripTimelineEnumJargon(String(cr.strategy_applied || cr.conflict_strategy || "—"));
  const decision = stripTimelineEnumJargon(String(cr.routing_decision || "").slice(0, 520));
  const events = useMemo(() => {
    const raw = cr.conflict_events;
    return Array.isArray(raw) ? (raw as ConflictEvent[]) : [];
  }, [cr.conflict_events]);
  const rank = useMemo(() => {
    const raw = cr.skill_sovereignty_rank;
    return Array.isArray(raw) ? (raw as Record<string, unknown>[]) : [];
  }, [cr.skill_sovereignty_rank]);
  const perPlugin = useMemo(() => {
    const raw = cr.per_plugin_vectors;
    if (!raw || typeof raw !== "object") return {} as Record<string, Record<string, number>>;
    const out: Record<string, Record<string, number>> = {};
    for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
      if (v && typeof v === "object" && !Array.isArray(v)) out[k] = v as Record<string, number>;
    }
    return out;
  }, [cr.per_plugin_vectors]);

  const plugins = (physicsTensor?.plugin_outputs as Record<string, unknown> | undefined) || {};
  const pluginRows = useMemo(() => {
    return Object.entries(plugins).map(([id, row]) => {
      const r = row && typeof row === "object" ? (row as Record<string, unknown>) : {};
      return {
        id,
        displayName: humanizePluginId(id),
        confidence: pluginConfidence(r),
        reason: extractMatchReason(r),
      };
    });
  }, [plugins]);

  const hasRouter = Object.keys(cr).length > 0;

  return (
    <div className="rounded-xl border border-violet-900/40 bg-zinc-950/60 p-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-violet-300/90">插件碰撞审计</p>
      <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
        汇总本次交互中各插件的匹配置信度与命中理由；下方为 CausalRouter 仲裁摘要（策略、极性冲突、主权排序）。
      </p>

      <div className="mt-3 space-y-2">
        <p className="text-[10px] uppercase tracking-wide text-zinc-500">匹配插件 · 得分 · 原因</p>
        <ul className="space-y-2">
          {pluginRows.length === 0 ? (
            <li className="text-[11px] text-zinc-600">暂无 plugin_outputs。</li>
          ) : (
            pluginRows.map((r) => (
              <li
                key={r.id}
                className="rounded border border-zinc-800/80 bg-zinc-900/50 px-2.5 py-2 text-[11px] text-zinc-200"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">{r.displayName}</span>
                  <span className="shrink-0 font-mono text-[10px] text-amber-200/90">
                    {r.confidence != null ? `置信度 ${(r.confidence * 100).toFixed(0)}%` : "置信度 —"}
                  </span>
                </div>
                <p className="mt-1.5 text-[10px] leading-relaxed text-zinc-400">
                  <span className="text-zinc-500">匹配原因：</span>
                  {r.reason}
                </p>
                <p className="mt-1 font-mono text-[9px] text-zinc-600">内部 ID：{r.id}</p>
              </li>
            ))
          )}
        </ul>
      </div>

      {!hasRouter ? (
        <p className="mt-4 text-[11px] text-zinc-600">当前张量未带 meta.causal_routing（完成 analyze-seed 后应出现）。</p>
      ) : (
        <div className="mt-4 space-y-3 border-t border-zinc-800/80 pt-3">
          <div>
            <p className="text-[10px] uppercase tracking-wide text-zinc-500">已应用路由策略</p>
            <p className="mt-0.5 text-[11px] leading-relaxed text-violet-100/90">{strategy}</p>
          </div>
          {decision ? (
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">系统最终叙事（routing_decision）</p>
              <p className="mt-1 text-[11px] leading-relaxed text-zinc-300">
                {decision}
                {String(cr.routing_decision || "").length > 520 ? "…" : ""}
              </p>
            </div>
          ) : null}

          {events.length > 0 ? (
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">极性冲突（两插件对同一十神轴符号相反）</p>
              <ul className="mt-2 max-h-40 space-y-2 overflow-auto">
                {events.map((ev, i) => (
                  <li
                    key={`ce-${i}`}
                    className="rounded border border-rose-900/40 bg-rose-950/20 px-2 py-1.5 text-[10px] text-rose-100/90"
                  >
                    <span className="font-medium text-amber-200/90">{String(ev.deity || "—")}</span> ·{" "}
                    <span className="text-zinc-300">{humanizePluginId(String(ev.plugin_a || "?"))}</span> (
                    {Number(ev.delta_a).toFixed(3)}) vs{" "}
                    <span className="text-zinc-300">{humanizePluginId(String(ev.plugin_b || "?"))}</span> (
                    {Number(ev.delta_b).toFixed(3)}) — {String(ev.note || "极性分歧")}
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[10px] text-zinc-500">
                仲裁结果已写入 merged_impact 与 routing_decision；若策略为流派主权/流派优先，盲派向量可覆盖与印比重叠的旺衰轴。
              </p>
            </div>
          ) : (
            <p className="text-[11px] text-zinc-600">未检出跨插件极性冲突事件。</p>
          )}

          {rank.length > 0 ? (
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">流派 / 技能主权排序</p>
              <ul className="mt-1 space-y-1">
                {rank.map((r, i) => (
                  <li key={`sr-${i}`} className="text-[10px] text-zinc-400">
                    <span className="font-medium text-zinc-300">{humanizePluginId(String(r.skill_id || "—"))}</span>
                    <span className="font-mono text-zinc-500"> · sov {String(r.sovereignty ?? "—")}</span>
                    {r.high_sovereignty ? <span className="text-amber-200/80"> · 高主权</span> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {Object.keys(perPlugin).length > 0 ? (
            <details className="rounded border border-zinc-800 bg-zinc-950/50">
              <summary className="cursor-pointer px-2 py-1.5 text-[10px] text-zinc-400">per_plugin_vectors（技术展开）</summary>
              <pre className="max-h-40 overflow-auto whitespace-pre-wrap break-all p-2 font-mono text-[9px] text-zinc-500">
                {JSON.stringify(perPlugin, null, 2)}
              </pre>
            </details>
          ) : null}
        </div>
      )}
    </div>
  );
}
