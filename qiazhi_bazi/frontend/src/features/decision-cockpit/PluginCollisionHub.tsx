"use client";

import { useMemo } from "react";
import { humanizePluginId, stripTimelineEnumJargon } from "./semanticLexicon";

type Props = {
  physicsTensor: Record<string, unknown> | null | undefined;
  /** 从 Inbox / Debug 跳转时高亮对应 plugin_outputs 行 */
  highlightPluginId?: string | null;
};

/** 博弈展示顺序：物理引擎 → 流派插件 → 其余按字典序 */
const PLUGIN_AUDIT_ORDER = [
  "sys.core.physics",
  "classical.blind_school.v1",
  "classical.wangshuai.v1",
];

type ConflictEvent = {
  deity?: string;
  plugin_a?: string;
  plugin_b?: string;
  delta_a?: number;
  delta_b?: number;
  note?: string;
};

type PluginAuditRow = {
  id: string;
  displayName: string;
  confidence: number | null;
  reason: string;
};

function extractMatchReason(row: Record<string, unknown>): string {
  const payload = row.payload && typeof row.payload === "object" ? (row.payload as Record<string, unknown>) : {};
  const ml = payload.matcher_logic;
  if (typeof ml === "string" && ml.trim()) return ml.trim().slice(0, 280);
  if (ml && typeof ml === "object" && !Array.isArray(ml)) {
    const o = ml as Record<string, unknown>;
    const cond = [o.condition, o.rule, o.pattern, o.summary].map((x) => (typeof x === "string" ? x : "")).find(Boolean);
    if (cond) return String(cond).slice(0, 280);
  }
  const verdict = typeof payload.verdict === "string" ? payload.verdict.trim() : "";
  if (verdict) return verdict.length > 280 ? `${verdict.slice(0, 278)}…` : verdict;
  const topVerdict = typeof row.verdict === "string" ? row.verdict.trim() : "";
  if (topVerdict) return topVerdict.length > 280 ? `${topVerdict.slice(0, 278)}…` : topVerdict;
  const ev = Array.isArray(row.evidence) ? (row.evidence as unknown[]).map((x) => String(x)).filter(Boolean) : [];
  if (ev.length) {
    const head = ev.slice(0, 4).join("；");
    return head.length > 280 ? `${head.slice(0, 278)}…` : head;
  }
  const err = typeof payload.error === "string" ? payload.error.trim() : "";
  if (err) return `插件侧提示：${err.slice(0, 200)}`;
  return "（未返回结构化匹配条件；可查看终审 logical_evidence 或插件 payload 原文）";
}

function pluginConfidence(row: Record<string, unknown>): number | null {
  const top = row.confidence_score;
  if (typeof top === "number" && Number.isFinite(top)) return top;
  const pl = row.payload && typeof row.payload === "object" ? (row.payload as Record<string, unknown>) : null;
  const c = pl && typeof pl.confidence === "number" && Number.isFinite(pl.confidence) ? (pl.confidence as number) : null;
  return c;
}

function sortPluginEntries(entries: [string, unknown][]): [string, unknown][] {
  const orderMap = new Map(PLUGIN_AUDIT_ORDER.map((id, i) => [id, i]));
  return [...entries].sort((a, b) => {
    const ia = orderMap.has(a[0]) ? (orderMap.get(a[0]) as number) : 999;
    const ib = orderMap.has(b[0]) ? (orderMap.get(b[0]) as number) : 999;
    if (ia !== ib) return ia - ib;
    return a[0].localeCompare(b[0]);
  });
}

export function PluginCollisionHub({ physicsTensor, highlightPluginId }: Props) {
  const meta = (physicsTensor?.meta as Record<string, unknown> | undefined) || {};
  const cr = (meta.causal_routing as Record<string, unknown> | undefined) || {};

  const strategy = stripTimelineEnumJargon(String(cr.strategy_applied || cr.conflict_strategy || "—"));
  const decision = stripTimelineEnumJargon(String(cr.routing_decision || "").slice(0, 720));
  const events = useMemo(() => {
    const raw = cr.conflict_events;
    return Array.isArray(raw) ? (raw as ConflictEvent[]) : [];
  }, [cr.conflict_events]);
  const rank = useMemo(() => {
    const raw = cr.skill_sovereignty_rank;
    return Array.isArray(raw) ? (raw as Record<string, unknown>[]) : [];
  }, [cr.skill_sovereignty_rank]);

  const plugins = (physicsTensor?.plugin_outputs as Record<string, unknown> | undefined) || {};
  const pluginRows = useMemo(() => {
    return sortPluginEntries(Object.entries(plugins)).map(([id, row]) => {
      const r = row && typeof row === "object" ? (row as Record<string, unknown>) : {};
      return {
        id,
        displayName: humanizePluginId(id),
        confidence: pluginConfidence(r),
        reason: extractMatchReason(r),
      } satisfies PluginAuditRow;
    });
  }, [plugins]);

  const hasRouter = Object.keys(cr).length > 0;

  return (
    <div className="rounded-xl border border-violet-900/40 bg-zinc-950/60 p-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-violet-300/90">插件碰撞博弈（全量 plugin_outputs）</p>
      <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
        物理事实仅来自各插件 `plugin_outputs` 行（无 tensor 顶栏回退）；`sys.core.physics` 为 L1 引擎唯一出口。下方为 CausalRouter 仲裁摘要。
      </p>

      {hasRouter ? (
        <div className="mt-3 rounded-lg border border-amber-500/25 bg-amber-950/15 px-3 py-2.5">
          <p className="text-[10px] font-medium uppercase tracking-wide text-amber-200/90">仲裁透视</p>
          <p className="mt-1 text-[11px] font-medium text-violet-100/95">策略：{strategy}</p>
          {decision ? (
            <p className="mt-1.5 text-[11px] leading-relaxed text-zinc-300">
              {decision}
              {String(cr.routing_decision || "").length > 720 ? "…" : ""}
            </p>
          ) : (
            <p className="mt-1 text-[11px] text-zinc-500">暂无 routing_decision 文本。</p>
          )}
          <p className="mt-2 text-[10px] leading-relaxed text-zinc-500">
            十神轴上的数值分歧来自各插件 payload 抽取的向量；LLM 终审应结合本摘要与下方各插件「匹配原因」采信或折中，而非仅看单一插件。
          </p>
        </div>
      ) : (
        <p className="mt-3 text-[11px] text-zinc-600">当前张量未带 meta.causal_routing（完成 analyze-seed 后应出现）。</p>
      )}

      <div className="mt-4 space-y-2">
        <p className="text-[10px] uppercase tracking-wide text-zinc-500">插件专家列表 · 置信度 · 命中理由</p>
        <ul className="space-y-2">
          {pluginRows.length === 0 ? (
            <li className="text-[11px] text-zinc-600">暂无 plugin_outputs。</li>
          ) : (
            pluginRows.map((r) => (
              <li
                key={r.id}
                id={`plugin-audit-row-${r.id}`}
                className={`rounded border px-2.5 py-2 text-[11px] text-zinc-200 ${
                  highlightPluginId && r.id === highlightPluginId
                    ? "border-amber-400/70 bg-amber-950/25 shadow-[0_0_0_1px_rgba(251,191,36,0.25)]"
                    : "border-zinc-800/80 bg-zinc-900/50"
                }`}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-medium text-zinc-100">{r.displayName}</span>
                  <span className="shrink-0 font-mono text-[10px] text-amber-200/90">
                    {r.confidence != null ? `置信度 ${Math.round(r.confidence * 100)}%` : "置信度 —"}
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

      {hasRouter ? (
        <div className="mt-4 space-y-3 border-t border-zinc-800/80 pt-3">
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
            </div>
          ) : (
            <p className="text-[11px] text-zinc-600">未检出跨插件极性冲突事件。</p>
          )}

          {rank.length > 0 ? (
            <div>
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">流派 / 技能主权排序</p>
              <ul className="mt-1 space-y-1">
                {rank.map((row, i) => (
                  <li key={`sr-${i}`} className="text-[10px] text-zinc-400">
                    <span className="font-medium text-zinc-300">{humanizePluginId(String(row.skill_id || "—"))}</span>
                    <span className="font-mono text-zinc-500"> · sov {String(row.sovereignty ?? "—")}</span>
                    {row.high_sovereignty ? <span className="text-amber-200/80"> · 高主权</span> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
