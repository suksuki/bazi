"use client";

import { useCallback, useMemo, useState } from "react";
import type { PatternThresholdRow } from "@/features/stream-board/models";
import { PatternCollisionTraceDialog } from "@/features/stream-board/components/PatternCollisionTraceDialog";
import {
  affinityMatch,
  affinityPreWillProxy,
  allRowsStrictFingerprint,
  eligibleForTopCompetition,
  sortRowsByAffinityMatch,
  topEligibleByAffinity,
} from "@/features/stream-board/utils/patternWaterlineV7";

type Props = {
  /** 唯一数据源：须由 `parsePatternThresholdsPayload` 从 `physics_tensor.meta.pattern_thresholds` 解析而来 */
  committed: PatternThresholdRow[];
  /** V7：不再与 committed 合并参与主条；保留 prop 仅为兼容上游，主视觉忽略 */
  preview: PatternThresholdRow[] | null | undefined;
  shadowActive: boolean;
  patternThresholdsStatus?: string | null;
  /** 与顶栏格局标题同源（meta.l2_pattern_result_summary_v1 / 缺省文案） */
  codexHitSummary?: string;
  t: (s: string) => string;
  className?: string;
};

function rowKey(row: PatternThresholdRow, i: number) {
  const id = row.pattern_id?.trim() || row.name;
  return `${id}-${i}`;
}

function stabilityRisk(row: PatternThresholdRow): boolean {
  const tv = row.temporal_volatility ?? 0;
  return tv > 0.32 || row.stability < 0.42;
}

/** 相变态：匹配度 > 0.9 */
function isPhaseTransition(row: PatternThresholdRow): boolean {
  return affinityMatch(row) > 0.9;
}

function phaseWatermarkId(row: PatternThresholdRow): string | null {
  if (!isPhaseTransition(row)) return null;
  const pid = typeof row.pattern_id === "string" ? row.pattern_id.trim() : "";
  if (pid) return pid;
  const raw = typeof row.name === "string" ? row.name.trim() : "";
  if (!raw) return null;
  return raw.replace(/[·\s]/g, "_").toUpperCase();
}

function isHighAffinityTier(row: PatternThresholdRow): boolean {
  return affinityMatch(row) > 0.9;
}

function progressBarClassName(row: PatternThresholdRow, intercepted: boolean): string {
  if (intercepted) {
    return "bg-rose-600/75";
  }
  const hi = isHighAffinityTier(row);
  if (hi) {
    return "bg-gradient-to-r from-amber-300 via-yellow-300 to-amber-400/95 shadow-[0_0_10px_rgba(253,224,71,0.35)]";
  }
  const s = affinityMatch(row);
  if (s < 0.6) {
    return "bg-amber-600/80";
  }
  return "bg-violet-600/70 pattern-neutron-pulse";
}

function bubbleText(row: PatternThresholdRow): string {
  const zh = row.trace_display_zh?.filter(Boolean) ?? [];
  if (zh.length) return zh.join("\n");
  const tl = row.trace_logic?.filter(Boolean) ?? [];
  return tl.join("\n");
}

export function PatternWaterlinePanel({
  committed,
  preview: _preview,
  shadowActive,
  patternThresholdsStatus = null,
  codexHitSummary = "",
  t,
  className = "",
}: Props) {
  void _preview;
  void shadowActive;

  const status = String(patternThresholdsStatus || "").trim();

  const fingerprintOk = allRowsStrictFingerprint(committed);
  /** 仅非法典/指纹类异常时阻塞；EMPTY_NO_DATA 视为「尚无行」与 OK 一样不冒充报错态 */
  const showBlockingLoader =
    !fingerprintOk || (status !== "" && status !== "OK" && status !== "EMPTY_NO_DATA");

  const rows = useMemo(() => sortRowsByAffinityMatch(committed), [committed]);

  const topEligible = useMemo(() => topEligibleByAffinity(committed, 3), [committed]);
  const topEligibleKeys = useMemo(() => {
    const s = new Set<string>();
    for (const r of topEligible) {
      const k = r.pattern_id?.trim() || r.name;
      if (k) s.add(k);
    }
    return s;
  }, [topEligible]);

  const watermarkSource = useMemo(() => {
    const src = topEligible.filter((r) => affinityMatch(r) > 1e-6);
    if (!src.length) return null;
    return [...src].sort((a, b) => affinityMatch(b) - affinityMatch(a))[0];
  }, [topEligible]);

  const watermarkId = useMemo(() => {
    if (!watermarkSource) return null;
    return phaseWatermarkId(watermarkSource);
  }, [watermarkSource]);

  const gapLine = useMemo(() => {
    if (!watermarkSource) return "";
    const am = affinityMatch(watermarkSource);
    const gap = Math.max(0, (0.92 - am) * 100);
    const label = watermarkSource.i18n_key ? t(watermarkSource.i18n_key) : t(watermarkSource.name);
    return t("pattern.waterline.gapToCatastrophe").replace("{name}", label).replace("{pct}", gap.toFixed(1));
  }, [watermarkSource, t]);

  const [bubbleIdx, setBubbleIdx] = useState<number | null>(null);
  const [traceRow, setTraceRow] = useState<PatternThresholdRow | null>(null);
  const clearBubble = useCallback(() => setBubbleIdx(null), []);

  return (
    <div
      className={`relative mt-2 space-y-1.5 overflow-hidden rounded-md border border-violet-800/50 bg-zinc-950/90 p-2 ring-1 ring-violet-500/15 ${className}`}
      onMouseLeave={clearBubble}
    >
      <PatternCollisionTraceDialog row={traceRow} open={traceRow != null} onClose={() => setTraceRow(null)} t={t} />

      {watermarkId ? (
        <div
          className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center overflow-hidden rounded-md"
          aria-hidden
        >
          <span className="max-w-[100%] truncate px-1 text-center font-mono text-[clamp(2.25rem,14vw,4.5rem)] font-black uppercase leading-none tracking-[0.2em] text-amber-200/[0.07] select-none">
            {watermarkId}
          </span>
        </div>
      ) : null}
      <div className="relative z-10 space-y-1.5">
        <p className="text-[10px] font-semibold tracking-wide text-violet-200">{t("格局引力水位线")}</p>
        {codexHitSummary.trim() ? (
          <p className="text-[11px] font-semibold leading-snug text-zinc-100" data-testid="pattern-codex-hit-name">
            {codexHitSummary.trim()}
          </p>
        ) : null}

        {showBlockingLoader ? (
          <div
            data-testid="pattern-waterline-loader"
            className="space-y-2 py-3"
            aria-busy
            aria-label={t("pattern.waterline.awaitingStrict")}
          >
            <div className="h-2 w-full animate-pulse rounded bg-violet-900/40" />
            <div className="h-2 w-4/5 animate-pulse rounded bg-violet-900/30" />
            <div className="h-2 w-3/5 animate-pulse rounded bg-violet-900/25" />
            <p className="text-[9px] text-zinc-500">{t("pattern.waterline.awaitingStrict")}</p>
          </div>
        ) : gapLine ? (
          <p className="text-[10px] leading-snug text-zinc-400">{gapLine}</p>
        ) : (
          <p className="text-[10px] leading-snug text-zinc-500">{t("pattern.waterline.awaitingPhysics")}</p>
        )}

        {!showBlockingLoader ? (
          <p className="text-[9px] font-mono text-zinc-500">
            {t("pattern.waterline.affinityLegend")}
            <span className="text-cyan-600/90"> · {t("pattern.waterline.preWillLegend")}</span>
          </p>
        ) : null}

        {!showBlockingLoader ? (
          <ul className="space-y-1">
            {rows.map((row, i) => {
              const am = affinityMatch(row);
              const preWill = affinityPreWillProxy(row);
              const width = `${Math.round(am * 100)}%`;
              const preWillW =
                preWill != null && Math.abs(preWill - am) > 2e-3 ? `${Math.round(preWill * 100)}%` : null;
              const intercepted = row.exclusion_hit === true;
              const risk = stabilityRisk(row);
              const stabW = `${Math.round(row.stability * 100)}%`;
              const labelKey = row.i18n_key ?? row.name;
              const barShake = row.exclusion_hit === true;
              const trace = row.trace_logic?.length ? row.trace_logic.join(" · ") : undefined;
              const tip = bubbleText(row);
              const showBubble = bubbleIdx === i && barShake && tip.length > 0;
              const topMark = topEligibleKeys.has(row.pattern_id?.trim() || row.name);
              const gateOk = eligibleForTopCompetition(row);
              const rowTestId = row.pattern_id ? `pattern-waterline-row-${row.pattern_id}` : `pattern-waterline-row-${i}`;

              return (
                <li key={rowKey(row, i)} className="space-y-0.5">
                  <button
                    type="button"
                    data-testid={rowTestId}
                    className="w-full rounded border border-transparent px-0.5 py-0.5 text-left hover:border-violet-600/40 hover:bg-violet-950/20"
                    onClick={() => setTraceRow(row)}
                  >
                    <div className="flex items-center justify-between gap-2 text-[10px] text-zinc-400">
                      <span className="flex min-w-0 flex-1 items-center gap-1.5" title={trace}>
                        {topMark && gateOk ? (
                          <span className="shrink-0 rounded bg-emerald-900/50 px-1 font-mono text-[8px] text-emerald-200/90">
                            TOP
                          </span>
                        ) : null}
                        <span className="truncate">{t(labelKey)}</span>
                        {intercepted ? (
                          <span
                            data-testid={`${rowTestId}-intercepted`}
                            className="shrink-0 font-mono text-[8px] font-bold text-rose-400"
                          >
                            {t("pattern.collision.intercepted")}
                          </span>
                        ) : null}
                      </span>
                      <span className="shrink-0 font-mono text-zinc-500" title={t("pattern.waterline.affinityMatch")}>
                        {(am * 100).toFixed(1)}%
                      </span>
                    </div>
                  </button>
                  <div
                    className="relative h-1.5 w-full overflow-visible rounded bg-zinc-800"
                    onMouseEnter={() => {
                      if (barShake && tip) setBubbleIdx(i);
                    }}
                  >
                    {preWillW ? (
                      <div
                        className="absolute inset-y-0 left-0 z-0 rounded border border-dashed border-cyan-400/45 bg-cyan-500/10"
                        style={{ width: preWillW }}
                        title={t("pattern.waterline.preWillTooltip")}
                        aria-hidden
                      />
                    ) : null}
                    <div
                      className={`absolute inset-y-0 left-0 z-[1] rounded ${progressBarClassName(row, intercepted)} ${
                        barShake ? "animate-shake ring-1 ring-rose-500/40" : ""
                      }`}
                      style={{ width }}
                      title={!barShake ? trace ?? `Affinity_Match ${(am * 100).toFixed(0)}%` : undefined}
                    />
                    {showBubble ? (
                      <div
                        role="tooltip"
                        className="absolute bottom-full left-0 z-30 mb-1 max-w-[min(100%,18rem)] rounded-md border border-rose-500/40 bg-zinc-900/98 px-2 py-1.5 text-[9px] leading-snug text-rose-100 shadow-lg"
                      >
                        {tip.split("\n").map((line, li) => (
                          <p key={`${i}-b-${li}`} className={li ? "mt-0.5" : ""}>
                            {line}
                          </p>
                        ))}
                      </div>
                    ) : null}
                  </div>
                  <div className="flex items-center justify-between gap-2 text-[9px] text-zinc-500">
                    <span>{t("稳定性")}</span>
                    <span className="font-mono">{(row.stability * 100).toFixed(0)}%</span>
                  </div>
                  <div
                    className="relative h-1 w-full overflow-hidden rounded bg-zinc-800/90"
                    title={
                      risk
                        ? `temporal_volatility ${((row.temporal_volatility ?? 0) * 100).toFixed(0)}% · stability risk`
                        : `stability ${(row.stability * 100).toFixed(0)}%`
                    }
                  >
                    <div
                      className={`absolute inset-y-0 left-0 rounded ${
                        risk ? "bg-rose-500/90 phase-waterline-risk-shake" : "bg-emerald-600/55"
                      }`}
                      style={{ width: stabW }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
