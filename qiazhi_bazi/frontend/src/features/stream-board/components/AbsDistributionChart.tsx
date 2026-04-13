"use client";

import { lazy, Suspense, useMemo } from "react";

const PreviewDeltaPercentBadge = lazy(() =>
  import("./PreviewDeltaPercentBadge").then((m) => ({ default: m.PreviewDeltaPercentBadge })),
);
import { TEN_GOD_ORDER } from "@/features/ten-god-list/constants";
import { buildLockedDeitySet, extractHardRouteKeys } from "@/features/ten-god-list/utils";
import { buildRoutingHighlightDeities, ROUTING_CONFLICT_TOOLTIP } from "../utils/routingConflictHighlight";

function RoutingLightningIcon({ title }: { title: string }) {
  return (
    <span
      title={title}
      className="pointer-events-auto inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-amber-500/15 ring-1 ring-amber-500/40"
      style={{ color: "#F59E0B" }}
      aria-label={title}
    >
      <svg viewBox="0 0 24 24" className="h-2.5 w-2.5 fill-current" aria-hidden>
        <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" />
      </svg>
    </span>
  );
}

type Axis = { absolute_energy?: number; relative_percentage?: number };
type Comp = {
  total_score?: number;
  stem_score?: number;
  root_score?: number;
};

function LockIcon({ title }: { title: string }) {
  return (
    <span title={title} className="inline-flex items-center text-sky-300 transition-colors hover:text-sky-200" aria-label={title}>
      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M7 10V7.8C7 5.15 9.15 3 11.8 3C14.45 3 16.6 5.15 16.6 7.8V10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <rect x="5" y="10" width="14" height="11" rx="2.2" stroke="currentColor" strokeWidth="1.8" />
        <circle cx="12" cy="15.5" r="1.3" fill="currentColor" />
      </svg>
    </span>
  );
}

const BRANCH_MARK_LABEL: Record<string, string> = {
  he: "合",
  chong: "冲",
  xing: "刑",
  hai: "害",
  po: "破",
};

function BranchMarkStrip({ marks, t }: { marks: string[]; t: (s: string) => string }) {
  if (!marks.length) return null;
  return (
    <span className="ml-1 inline-flex flex-wrap gap-0.5 align-middle" title={t("地支合冲刑害破标记（与 Abs 阈值无关）")}>
      {marks.map((k) => (
        <span
          key={k}
          className={`inline-flex min-w-[1rem] items-center justify-center rounded px-0.5 text-[9px] font-semibold leading-none ring-1 ring-inset ${
            k === "he"
              ? "bg-sky-500/20 text-sky-200 ring-sky-500/35"
              : k === "chong"
                ? "bg-rose-500/20 text-rose-200 ring-rose-500/35"
                : k === "xing"
                  ? "bg-amber-500/20 text-amber-100 ring-amber-500/35"
                  : k === "hai"
                    ? "bg-violet-500/20 text-violet-100 ring-violet-500/35"
                    : k === "po"
                      ? "bg-zinc-600/40 text-zinc-200 ring-zinc-500/40"
                      : "bg-zinc-700/50 text-zinc-300 ring-zinc-600/40"
          }`}
        >
          {BRANCH_MARK_LABEL[k] || k}
        </span>
      ))}
    </span>
  );
}

function FusionLinkIcon({ title }: { title: string }) {
  return (
    <span title={title} className="inline-flex text-cyan-400/90" aria-label={title}>
      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M10 13a5 5 0 0 1 7.07 0l1.41 1.42M14 11l1.41-1.42a5 5 0 0 0-7.07 0L7 11"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
        <path
          d="M7 11H5a2 2 0 0 0 0 4h2M17 13h2a2 2 0 0 1 0 4h-2"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}

export type AbsDistributionChartProps = {
  deityScores: Record<string, number>;
  deityEnergyAxes?: Record<string, Axis>;
  deityComponents?: Record<string, Comp>;
  /** `physics_tensor.meta.causal_routing`：用于冲突条高亮 */
  causalRouting?: Record<string, unknown> | null;
  topAnomaly?: string;
  hardRouteLogs?: string[];
  climateIntensity?: number;
  climateSeason?: string;
  onOpenLogic?: (payload: {
    title: string;
    focus: string;
    details: string[];
    deityTrace?: Record<string, unknown>;
  }) => void;
  onHoverDeity?: (deityName?: string) => void;
  deityTraceDetails?: Record<string, Record<string, unknown>>;
  /** physics_tensor.meta.stem_fusion_v1：邻柱天干五合展示 */
  stemFusionMeta?: Record<string, unknown> | null;
  /** physics_tensor.meta.l1_status_v1.per_deity：长生状态 Work_Efficiency */
  l1StatusPerDeity?: Record<string, { work_efficiency?: number }> | null;
  /** physics_tensor.meta.pivot_defense_v1.target_pivot：枢纽十神金色描边 */
  pivotDeity?: string | null;
  /** physics_tensor.meta.pivot_defense_v1：枢纽语义（命脉受损 / 枢纽稳固） */
  pivotDefenseSemantic?: string | null;
  /** physics_tensor.meta.interaction_marks_per_deity：合冲刑害破 → 十神微型标（不依赖 Abs 阈值） */
  interactionMarksPerDeity?: Record<string, string[]> | null;
  /** 已确认「个人能量补丁」累加影响的十神（metadata.manual_energy_patch） */
  manualInterventionDeities?: ReadonlySet<string> | null;
  /** 意志注塑前：与 deityScores 同口径的相对配比，用于虚线框对比 */
  preInjectionDeityScores?: Record<string, number> | null;
  preInjectionDeityEnergyAxes?: Record<string, Axis> | null;
  /** 为 false 时不渲染注塑前虚线参考（由主断言区 Toggle 控制） */
  preInjectionReferenceActive?: boolean;
  /** 影子预览：悬停意志补丁后的十神分（淡紫「影子指针」） */
  previewDeityScores?: Record<string, number> | null;
  previewDeityEnergyAxes?: Record<string, Axis> | null;
  /** 与 `computeDeityPreviewDeltaPercent` 对齐的相对变化率（%） */
  previewDeltaPctByDeity?: Record<string, number> | null;
  t?: (s: string) => string;
};

export function AbsDistributionChart({
  deityScores,
  deityEnergyAxes = {},
  deityComponents = {},
  causalRouting = null,
  topAnomaly = "",
  hardRouteLogs = [],
  climateIntensity = 0,
  climateSeason = "",
  onOpenLogic,
  onHoverDeity,
  deityTraceDetails = {},
  stemFusionMeta = null,
  l1StatusPerDeity = null,
  pivotDeity = null,
  pivotDefenseSemantic = null,
  interactionMarksPerDeity = null,
  manualInterventionDeities = null,
  preInjectionDeityScores = null,
  preInjectionDeityEnergyAxes = null,
  preInjectionReferenceActive = false,
  previewDeityScores = null,
  previewDeityEnergyAxes = null,
  previewDeltaPctByDeity = null,
  t = (s: string) => s,
}: AbsDistributionChartProps) {
  const anomalyTag = (topAnomaly || "").trim();
  const lockedByKeys = extractHardRouteKeys(hardRouteLogs);
  const lockedDeities = buildLockedDeitySet(hardRouteLogs);
  const routingMarks = useMemo(() => buildRoutingHighlightDeities(causalRouting), [causalRouting]);
  const fusionLinks = useMemo(() => {
    const raw = stemFusionMeta && typeof stemFusionMeta === "object" ? stemFusionMeta.display_links : null;
    return Array.isArray(raw) ? (raw as { deities?: string[]; stems?: string[]; mode?: string }[]) : [];
  }, [stemFusionMeta]);

  return (
    <div className="space-y-2">
      {TEN_GOD_ORDER.map((name) => {
        const relPct = Number((deityEnergyAxes[name]?.relative_percentage ?? deityScores[name]) ?? 0);
        const absEnergy = Number((deityEnergyAxes[name]?.absolute_energy ?? 0) ?? 0);
        const comp = deityComponents[name] || {};
        const stemScore = Number(comp.stem_score ?? relPct);
        const rootScore = Number(comp.root_score ?? 0);
        const totalScore = Number(comp.total_score ?? relPct);
        const totalAbsWidth = Math.max(0, Math.min(100, (absEnergy / 10) * 100));
        const ratioStem = totalScore > 0 ? Math.max(0, stemScore) / totalScore : 0;
        const ratioRoot = totalScore > 0 ? Math.max(0, rootScore) / totalScore : 0;
        const rootWidth = `${Math.max(0, Math.min(100, totalAbsWidth * ratioRoot))}%`;
        const stemWidth = `${Math.max(0, Math.min(100, totalAbsWidth * ratioStem))}%`;
        const hit = anomalyTag && (anomalyTag.includes(name) || (name === "比肩" && anomalyTag.includes("比劫")));
        const seasonIcon =
          climateSeason === "winter"
            ? "❄"
            : climateSeason === "summer"
              ? "☀"
              : climateSeason === "autumn"
                ? "🍂"
                : climateSeason === "spring"
                  ? "🌱"
                  : "";
        const showRouting = routingMarks.has(name);
        const fusionEntry = fusionLinks.find((l) => Array.isArray(l.deities) && l.deities.includes(name));
        const fusionTitle = fusionEntry
          ? t("天干五合：{stems}（{mode}）")
              .replace("{stems}", (fusionEntry.stems || []).join("+"))
              .replace(
                "{mode}",
                fusionEntry.mode === "transformed"
                  ? t("化气")
                  : fusionEntry.mode === "stuck"
                    ? t("羁绊")
                    : t("合而不化"),
              )
          : "";
        const branchMarks =
          interactionMarksPerDeity && typeof interactionMarksPerDeity === "object"
            ? (interactionMarksPerDeity[name] as string[] | undefined)
            : undefined;
        const branchMarkList = Array.isArray(branchMarks) ? branchMarks : [];
        const workEff = l1StatusPerDeity?.[name]?.work_efficiency;
        const effNum = typeof workEff === "number" && Number.isFinite(workEff) ? workEff : null;
        const effPct =
          effNum != null ? Math.max(0, Math.min(100, ((effNum - 0.4) / (1.25 - 0.4)) * 100)) : null;
        const effLabel =
          effNum != null
            ? effNum >= 1.15
              ? t("巅峰")
              : effNum <= 0.55
                ? t("低谷")
                : t("平区")
            : "";
        const isPivot = Boolean(pivotDeity && name === pivotDeity);
        const baseRelRaw = Number(
          (preInjectionDeityEnergyAxes?.[name]?.relative_percentage ?? preInjectionDeityScores?.[name]) ?? NaN,
        );
        const injectionBaselinePct =
          preInjectionDeityScores && Number.isFinite(baseRelRaw) ? Math.max(0, Math.min(100, baseRelRaw)) : null;

        const previewRelRaw = Number(
          (previewDeityEnergyAxes?.[name]?.relative_percentage ?? previewDeityScores?.[name]) ?? NaN,
        );
        const showShadowPreview =
          Boolean(previewDeityScores && Object.keys(previewDeityScores).length > 0) && Number.isFinite(previewRelRaw);
        const previewWidthPct = showShadowPreview ? Math.max(0, Math.min(100, previewRelRaw)) : 0;
        const deltaPct = previewDeltaPctByDeity?.[name];
        const deltaLabel =
          typeof deltaPct === "number" && Number.isFinite(deltaPct) && Math.abs(deltaPct) > 0.05
            ? `${deltaPct >= 0 ? "+" : ""}${deltaPct.toFixed(1)}%`
            : "";

        return (
          <div key={name} className="relative pt-2">
            {showRouting ? (
              <div className="absolute left-1/2 top-0 z-10 flex -translate-x-1/2 justify-center">
                <RoutingLightningIcon title={t(ROUTING_CONFLICT_TOOLTIP)} />
              </div>
            ) : null}
            <button
              type="button"
              onClick={() =>
                onOpenLogic?.({
                  title: `${name}${t(" 数值审计")}`,
                  focus: name,
                  details: [
                    `${name}: ${totalScore.toFixed(2)}% (Abs: ${absEnergy.toFixed(2)})`,
                    isPivot
                      ? `${t("[枢纽] ")}${t(
                          pivotDefenseSemantic || "旺衰引擎标定的 Target_Pivot（用神侧能量×能效）",
                        )}`
                      : "",
                    hit ? `${t("[审计预警] ")}${t(anomalyTag)}` : t("当前未命中该项异常关键词。"),
                    t("点击后可查看：基础动能 / 物理干预 / 归一化校准"),
                  ].filter(Boolean),
                  deityTrace: deityTraceDetails[name] as Record<string, unknown> | undefined,
                })
              }
              className={`w-full rounded-lg border bg-zinc-950 px-2 py-2 text-left transition-colors hover:bg-zinc-900/90 ${
                isPivot
                  ? "border-amber-400/85 shadow-[0_0_0_2px_rgba(251,191,36,0.45),0_0_14px_rgba(251,191,36,0.18)] ring-2 ring-amber-400/70 ring-offset-2 ring-offset-zinc-950"
                  : "border-zinc-800"
              }`}
              title={
                isPivot
                  ? t("枢纽十神（{s}）").replace("{s}", pivotDefenseSemantic || "Target_Pivot")
                  : t("点击查看演算路径")
              }
              onMouseEnter={() => onHoverDeity?.(name)}
              onMouseLeave={() => onHoverDeity?.(undefined)}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300">{name}</span>
                <span className="flex items-center gap-2">
                  {hit ? (
                    <span className="rounded-full border border-rose-500/60 bg-rose-500/20 px-2 py-0.5 text-[10px] text-rose-300">
                      {t("! 挑刺")}
                    </span>
                  ) : null}
                  {lockedDeities.has(name) ? (
                    <LockIcon
                      title={`${t("该能量场已根据共识参数 ")}${lockedByKeys.join(", ") || "N/A"}${t(" 锁定")}`}
                    />
                  ) : null}
                  {fusionEntry ? <FusionLinkIcon title={fusionTitle} /> : null}
                  {manualInterventionDeities?.has(name) ? (
                    <span
                      title={t("人工修正：已采纳个人能量补丁（展示层）")}
                      className="inline-flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full bg-violet-500/25 text-[10px] font-bold leading-none text-violet-200 ring-1 ring-violet-400/50"
                      aria-label={t("人工修正")}
                    >
                      ∆
                    </span>
                  ) : null}
                  {branchMarkList.length > 0 ? <BranchMarkStrip marks={branchMarkList} t={t} /> : null}
                  <span className="text-zinc-400">
                    {totalScore.toFixed(2)}%{" "}
                    <span className="text-sky-300">(Abs: {absEnergy.toFixed(2)})</span>
                    {climateIntensity > 0 ? (
                      <span className="ml-1 text-[10px] text-zinc-500" title={t("调候硬修正已启用")}>
                        {seasonIcon || "☁"}
                      </span>
                    ) : null}
                  </span>
                </span>
              </div>
              {injectionBaselinePct != null && preInjectionReferenceActive ? (
                <div
                  className="relative mt-1 h-1 w-full overflow-hidden rounded bg-zinc-900 ring-1 ring-zinc-700/80"
                  title={t("意志注塑前：十神相对配比参考（与当前实条对比）")}
                >
                  <div
                    className="pointer-events-none absolute inset-y-0 left-0 rounded border border-dashed border-cyan-400/65 bg-cyan-500/10"
                    style={{ width: `${injectionBaselinePct}%` }}
                  />
                  <div
                    className="relative h-full rounded bg-sky-500/75"
                    style={{ width: `${Math.max(0, Math.min(100, relPct))}%` }}
                  />
                </div>
              ) : null}
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded bg-zinc-800">
                <div className="flex h-full w-full">
                  <div className="h-full bg-amber-500/90" style={{ width: rootWidth }} />
                  <div className="h-full bg-amber-300/45" style={{ width: stemWidth }} />
                </div>
              </div>
              {showShadowPreview ? (
                <div className="relative z-[3] mt-1 h-1.5 w-full overflow-visible rounded bg-zinc-900/40 ring-1 ring-fuchsia-400/45">
                  <div
                    className="pointer-events-none h-full rounded bg-gradient-to-r from-fuchsia-500/45 via-fuchsia-300/55 to-fuchsia-500/45 blur-[0.45px] shadow-pointer"
                    style={{ width: `${previewWidthPct}%` }}
                    title={t("影子预览（未签发）")}
                  />
                  {deltaLabel ? (
                    <Suspense
                      fallback={
                        <span className="pointer-events-none absolute -right-1 -top-4 z-[5] flex h-4 min-w-[2.5rem] items-center justify-end whitespace-nowrap text-[9px] font-semibold text-fuchsia-100 shadow-preview-delta-pct tabular-nums">
                          {deltaLabel}
                        </span>
                      }
                    >
                      <PreviewDeltaPercentBadge deltaLabel={deltaLabel} />
                    </Suspense>
                  ) : null}
                </div>
              ) : null}
              {effPct != null ? (
                <div
                  className="mt-1 h-1 w-full overflow-hidden rounded bg-zinc-800"
                  title={`${t("十二长生能效 Work_Efficiency=")}${effNum?.toFixed(2)}${t("（约 0.4 低谷 — 1.25 巅峰）")}`}
                >
                  <div
                    className={`h-full rounded transition-[width,background-color,filter] duration-500 ease-in-out ${
                      effNum != null && effNum >= 1.15
                        ? "bg-emerald-500/85 brightness-110"
                        : effNum != null && effNum <= 0.55
                          ? "bg-rose-600/80 brightness-90"
                          : "bg-sky-500/70"
                    }`}
                    style={{ width: `${effPct}%` }}
                  />
                  <div className="sr-only">
                    {t("长生能效 ")}
                    {effLabel}
                  </div>
                </div>
              ) : null}
              <div className="mt-1 text-[10px] text-zinc-500">
                ({t("透:")}
                {stemScore.toFixed(2)} | {t("根:")}
                {rootScore.toFixed(2)})
              </div>
            </button>
          </div>
        );
      })}
    </div>
  );
}
