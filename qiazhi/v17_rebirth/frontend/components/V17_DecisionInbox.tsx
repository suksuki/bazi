"use client";

import { useCallback, useMemo, useState } from "react";
import { Check, X } from "lucide-react";

import { t, type AppLanguage } from "@/lib/i18n";
import type { Decision } from "@/hooks/useOracleSession";
import type { PlanDecisionClaim, PlanDecisionRoutingFeatures } from "@/types/decisionBrain";
import { V17PlanRoutingClaim, compactRoutingLabel } from "@/components/V17_PlanRoutingClaim";
import { V17_AutoDecisionSection } from "@/components/V17_AutoDecisionSection";
import { V17_ManualDecisionSection } from "@/components/V17_ManualDecisionSection";
import {
  buildDecisionCatalog,
  buildDecisionIndex,
  buildManualDecisionGroups,
  directionGroupLabel,
  normalizeBatchBucket,
  normalizeDecisionId,
  sourceLabel,
  type DecisionBatch,
  type DecisionWithId,
} from "@/components/decisionInboxUtils";

type BucketKind = "manual" | "auto" | "system" | "llm";

type Frame = {
  layer?: string;
  payload?: {
    decision_inbox_contract?: string;
    manual_inbox?: Decision[];
    auto_decisions?: Decision[];
    manual_decisions?: Decision[];
    all_decisions?: Decision[];
    claim_conflict_graph?: {
      graph_version?: string;
      summary?: {
        node_count?: number;
        claim_edge_count?: number;
        conflict_count?: number;
        open_conflict_count?: number;
        resolved_conflict_count?: number;
        conflict_sample_count?: number;
      };
      conflicts?: Array<{
        conflict_id?: string;
        conflict_type?: string;
        severity?: string;
        status?: string;
        target_god?: string;
        recommended_arbiter?: string;
        resolution_count?: number;
        why_conflict?: string;
      }>;
      nodes?: Array<{
        node_id?: string;
        plugin_id?: string;
        claim_text?: string;
        target_god?: string;
        conflict_count?: number;
      }>;
      edges?: Array<Record<string, unknown>>;
    };
    auto_resolutions?: Decision[];
    llm_arbitration_context?: Decision[];
    snapshot_kind?: string;
    pending_decisions?: Decision[];
    decision_batches?: Array<{
      batch_id?: string;
      bucket?: string;
      target_god?: string;
      source_anchor?: string;
      source_families?: string[];
      decision_ids?: string[];
      batch_ids?: string[];
      decision_count?: number;
      net_impact_ratio?: number;
      max_priority?: number;
      direction_key?: string;
      direction_label?: string;
      prompt_line?: string;
      labels?: string[];
    }>;
    decision_brain_state?: {
      plan_queue?: Array<{
        plan_id?: string;
        anchor?: string;
        status?: string;
        routing?: string;
        routing_reason?: string;
        routing_policy?: string;
        routing_features?: PlanDecisionRoutingFeatures;
        routing_claim?: PlanDecisionClaim;
        routing_scores?: Record<string, unknown>;
        decision_ids?: string[];
        impact_summary?: Record<string, number>;
        meta?: Record<string, unknown>;
        created_at?: string;
        updated_at?: string;
        batch_ids?: string[];
      }>;
    };
    decision_trace_index?: {
      contract?: string;
      plan_count?: number;
      items?: Array<{
        plan_id?: string;
        anchor?: string;
        status?: string;
        routing?: string;
        updated_at?: string;
        decision_count?: number;
        decision_ids?: string[];
        batch_ids?: string[];
        routing_reason?: string;
        routing_policy?: string;
        routing_scores?: Record<string, unknown>;
        decision_trace_count?: number;
        decision_trace?: PlanDecisionTrace[];
        impact_summary?: Record<string, number>;
        llm_prompt_preview?: boolean;
      }>;
    };
    plugins?: {
      knowledge_snapshot?: {
        claim_history?: {
          current_targets?: Record<string, Record<string, unknown>>;
        };
      };
    };
    god_rings?: {
      effect_scores?: Record<string, unknown>;
    };
  };
};

type FluxStateRow = {
  target: string;
  resolvedFlux: number;
  tension: number;
  reinforce: number;
  contest: number;
  outSupport: number;
  outResist: number;
  outNet: number;
  harm: number;
};

type DecisionActionMeta = {
  label: string;
  hint?: string;
};

type PlanActionMeta = {
  approveLabel: string;
  rejectLabel: string;
  escalateLabel: string;
  withdrawLabel: string;
  recommended: "APPROVED" | "REJECTED" | "ESCALATE" | "WITHDRAW";
  hint: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asNumber(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function formatSigned(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function impactText(decision: Decision): string {
  const impact = decision.physical_impact || {};
  const ratio = typeof impact.impact_ratio === "number" ? Math.abs(impact.impact_ratio) : 0;
  const level = Number(impact.intensity_level || 0);
  if (ratio > 0) return `位移 ${(ratio * 100).toFixed(0)}% · L${level || "?"}`;
  if (level > 0) return `烈度 L${level}`;
  return "等待仲裁";
}

function bucketReason(kind: BucketKind, decision: Decision): string {
  const target = String(decision.target_god || decision.physical_impact?.target_god || "").trim();
  if (kind === "manual") {
    return target ? `已有明确目标神 ${target}，适合由你手动裁定。` : "保留给你手动定夺。";
  }
  if (kind === "auto") {
    return target ? `系统已围绕 ${target} 完成静默处理或归档。` : "系统已将这条信息静默处理，不再占用你的决策位。";
  }
  if (kind === "system") {
    return target ? `目标神 ${target} 已明确，满足自动处理条件。` : "系统将继续观察并尝试自动收敛。";
  }
  return target ? `可为模型提供 ${target} 方向的叙事参考，但不建议直接点按。` : "更适合作为叙事上下文，而不是直接动作。";
}

function bucketAccessLabel(kind: BucketKind): string {
  if (kind === "manual") return "可手动执行";
  if (kind === "auto") return "系统归档";
  if (kind === "system") return "系统自动";
  return "叙事参考";
}

function statusBadge(kind: BucketKind, decision: Decision): { label: string; className: string } {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  if (kind === "manual") {
    if (level >= 3 || ratio >= 0.1) {
      return {
        label: "需立即裁定",
        className: "border-rose-500/30 bg-rose-950/40 text-rose-100",
      };
    }
    return {
      label: "等待你确认",
      className: "border-violet-500/25 bg-violet-950/35 text-violet-100",
    };
  }
  if (kind === "auto") {
    if (decision.resolved_from_llm) {
      return {
        label: "已自动承接",
        className: "border-cyan-500/25 bg-cyan-950/35 text-cyan-100",
      };
    }
    return {
      label: "后台静默处理",
      className: "border-amber-500/25 bg-amber-950/35 text-amber-100",
    };
  }
  if (kind === "system") {
    if (level >= 3) {
      return {
        label: "拟自动收敛",
        className: "border-amber-500/30 bg-amber-950/40 text-amber-100",
      };
    }
    return {
      label: "系统观察中",
      className: "border-zinc-500/20 bg-zinc-900/70 text-zinc-300",
    };
  }
  return {
    label: "将注入 Prompt",
    className: "border-cyan-500/30 bg-cyan-950/35 text-cyan-100",
  };
}

function promptPreview(decision: Decision): string {
  const target = String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim();
  const source = String(decision.source || "unknown").trim();
  const ratio = Math.abs(Number(decision.physical_impact?.impact_ratio || 0));
  const preview = ratio > 0
    ? `${target} 发生 ${(ratio * 100).toFixed(1)}% 相对位移`
    : `${target} 被纳入叙事仲裁参考`;
  return `Prompt 将引用：${preview}，来源 ${source}。`;
}

function compactProjection(projection: unknown): string {
  if (!projection || typeof projection !== "object") return "";
  const entries = Object.entries(projection as Record<string, unknown>)
    .map(([key, value]) => [key, Number(value || 0)] as const)
    .filter(([, value]) => Number.isFinite(value) && value > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  return entries.map(([key, value]) => `${key} ${Math.round(value * 100)}%`).join(" · ");
}

function decisionFocusPreview(decision: Decision): string {
  const projectionText = compactProjection((decision as Decision & { cluster_projection?: Record<string, unknown> }).cluster_projection);
  const share = Number((decision as Decision & { projection_share?: number }).projection_share || 0);
  const target = String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim();
  if (!projectionText && share <= 0) return "";
  return `主落点 ${target}${share > 0 ? ` · 占比 ${Math.round(share * 100)}%` : ""}${projectionText ? ` · ${projectionText}` : ""}`;
}

function biasPairs(value: unknown): Array<{ name: string; score: number }> {
  return Object.entries((value && typeof value === "object" ? (value as Record<string, unknown>) : {}))
    .map(([name, raw]) => ({ name: String(name || "").trim(), score: Number(raw || 0) }))
    .filter((row) => row.name && Number.isFinite(row.score) && row.score > 0)
    .sort((a, b) => b.score - a.score);
}

function godRingBiasSummary(decision: Decision): { useText: string; tabooText: string } | null {
  const bias = decision.physical_impact?.god_ring_bias;
  const usePairs = biasPairs(bias?.use_bias).slice(0, 3);
  const tabooPairs = biasPairs(bias?.taboo_bias).slice(0, 3);
  if (!usePairs.length && !tabooPairs.length) return null;
  return {
    useText: usePairs.map((item) => `${item.name} +${item.score.toFixed(2)}`).join(" · "),
    tabooText: tabooPairs.map((item) => `${item.name} +${item.score.toFixed(2)}`).join(" · "),
  };
}

function groupGodRingBiasSummary(decisions: Decision[]): { useText: string; tabooText: string } | null {
  const useBias: Record<string, number> = {};
  const tabooBias: Record<string, number> = {};
  for (const decision of decisions || []) {
    const bias = decision.physical_impact?.god_ring_bias;
    for (const item of biasPairs(bias?.use_bias)) {
      useBias[item.name] = (useBias[item.name] || 0) + item.score;
    }
    for (const item of biasPairs(bias?.taboo_bias)) {
      tabooBias[item.name] = (tabooBias[item.name] || 0) + item.score;
    }
  }
  const usePairs = biasPairs(useBias).slice(0, 4);
  const tabooPairs = biasPairs(tabooBias).slice(0, 4);
  if (!usePairs.length && !tabooPairs.length) return null;
  return {
    useText: usePairs.map((item) => `${item.name} +${item.score.toFixed(2)}`).join(" · "),
    tabooText: tabooPairs.map((item) => `${item.name} +${item.score.toFixed(2)}`).join(" · "),
  };
}

function patternProfileSummary(decision: Decision): string {
  const profile = Array.isArray(decision.pattern_profile) ? decision.pattern_profile : [];
  if (!profile.length) {
    const candidate = String(decision.pattern_candidate || decision.pattern_name || "").trim();
    const scope = String(decision.pattern_scope_label || "").trim();
    return [candidate, scope].filter(Boolean).join(" · ");
  }
  return profile
    .slice(0, 3)
    .map((item) => {
      const family = String(item?.family || "").trim();
      const percent = Number(item?.percent || 0);
      if (!family) return "";
      return `${family} ${Number.isFinite(percent) && percent > 0 ? `${Math.round(percent)}%` : ""}`.trim();
    })
    .filter(Boolean)
    .join(" / ");
}

function patternConfidenceTone(score: number): string {
  if (score >= 0.82) return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (score >= 0.64) return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (score >= 0.48) return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function patternConfidenceChip(decision: Decision): { label: string; className: string } | null {
  const score = Number(decision.pattern_confidence ?? NaN);
  if (!Number.isFinite(score) || score <= 0) return null;
  const label = String(decision.pattern_confidence_label || "格局置信").trim();
  return {
    label: `${label} ${Math.round(score * 100)}%`,
    className: patternConfidenceTone(score),
  };
}

function llmPolicyLabel(policy: string | undefined): string {
  if (policy === "auto_apply") return "可自动裁决";
  if (policy === "suggest_only") return "仅给建议";
  return "仅作上下文";
}

function llmStateLabel(state: string | undefined): string {
  if (state === "collapsed_to_system") return "已转入自动处理";
  if (state === "promoted_to_manual") return "已转入手动入口";
  if (state === "pending_context") return "等待模型消化";
  return "处理中";
}

function arbitrationRule(kind: BucketKind): { title: string; detail: string; accent: string } {
  if (kind === "manual") {
    return {
      title: "进入条件",
      detail: "存在明确目标神，且属于可执行动作，不是诊断态或纯说明态。",
      accent: "text-violet-100 border-violet-500/20 bg-violet-950/20",
    };
  }
  if (kind === "auto") {
    return {
      title: "进入条件",
      detail: "系统可自行结算、自动归档，或仅作为提示词素材保留，不再要求你逐条确认。",
      accent: "text-amber-100 border-amber-500/20 bg-amber-950/20",
    };
  }
  if (kind === "system") {
    return {
      title: "进入条件",
      detail: "烈度较高，且满足自动处理阈值，系统可先行收敛。",
      accent: "text-amber-100 border-amber-500/20 bg-amber-950/20",
    };
  }
  return {
    title: "进入条件",
    detail: "更适合作为叙事依据、诊断上下文或提示词引用，而非直接动作。",
    accent: "text-cyan-100 border-cyan-500/20 bg-cyan-950/20",
  };
}

function baseRoutingRationale(kind: BucketKind, decision: Decision): string[] {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  const target = String(decision.target_god || impact.target_god || "").trim() || "未定目标";
  const source = String(decision.source_label || sourceLabel(decision)).trim() || "未知来源";
  const ratioText = ratio > 0 ? `${(ratio * 100).toFixed(1)}%` : "观察";
  const lines: string[] = [`来源 ${source}`, `目标 ${target}`, `位移 ${ratioText} · 烈度 L${level}`];
  if (kind === "manual") {
    lines.push("规则：可人工确认且可回溯");
    if (level >= 3) lines.push("触发阈值：烈度 >= 3");
    if (ratio >= 0.08) lines.push("触发阈值：位移 >= 8%");
    return lines;
  }
  if (kind === "auto" || kind === "system") {
    const rawPolicy = String((decision as Decision & { llm_resolution_policy?: string }).llm_resolution_policy || "").trim().toLowerCase();
    const state = String((decision as Decision & { llm_resolution_state?: string }).llm_resolution_state || "").trim().toLowerCase();
    if (rawPolicy) lines.push(`策略 ${llmPolicyLabel(rawPolicy)}`);
    if (state && state !== "none") lines.push(`状态 ${llmStateLabel(state)}`);
    if (ratio > 0.02 && level >= 2) lines.push("按规则自动收敛或归档");
    return lines;
  }
  const rawPolicy = String((decision as Decision & { llm_resolution_policy?: string }).llm_resolution_policy || "").trim();
  if (rawPolicy) {
    lines.push(`叙事策略 ${llmPolicyLabel(rawPolicy)}`);
  } else {
    lines.push("叙事策略 仅作上下文");
  }
  return lines;
}

function decisionFluxState(
  decision: Decision,
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
): FluxStateRow | null {
  const target = String(decision.target_god || decision.physical_impact?.target_god || "").trim();
  if (!target) return null;
  const effectRow = asRecord(effectScores[target]);
  const currentRow = asRecord(currentTargets[target]);
  const resolvedFlux = asNumber(
    effectRow.resolved_utility_flux,
    asNumber(effectRow.resolved_utility, asNumber(currentRow.resolved_utility_flux)),
  );
  const tension = asNumber(effectRow.flux_tension_load, asNumber(currentRow.flux_tension_load));
  const reinforce = asNumber(effectRow.flux_reinforce_load, asNumber(currentRow.flux_reinforce_load));
  const contest = asNumber(effectRow.contest_pressure, asNumber(currentRow.contest_pressure));
  const outSupport = asNumber(effectRow.flux_out_support);
  const outResist = asNumber(effectRow.flux_out_resist);
  const outNet = asNumber(effectRow.flux_out_net);
  const harm = asNumber(effectRow.harm_score, asNumber(currentRow.harm_score));
  if (![resolvedFlux, tension, reinforce, contest, outSupport, outResist, outNet, harm].some((value) => Math.abs(value) > 0.0001)) {
    return null;
  }
  return {
    target,
    resolvedFlux,
    tension,
    reinforce,
    contest,
    outSupport,
    outResist,
    outNet,
    harm,
  };
}

function decisionFluxSummaryLines(
  decision: Decision,
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
): string[] {
  const state = decisionFluxState(decision, effectScores, currentTargets);
  if (!state) return [];
  const lines = [
    `M3 ${state.target} · 流后 ${formatSigned(state.resolvedFlux)} · 张力 ${state.tension.toFixed(2)} · 放大 ${state.reinforce.toFixed(2)} · 对抗 ${state.contest.toFixed(2)}`,
  ];
  if (Math.abs(state.outNet) > 0.001 || state.outSupport > 0 || state.outResist > 0) {
    lines.push(
      `M3 外推 · 支撑 ${state.outSupport.toFixed(2)} / 压制 ${state.outResist.toFixed(2)} / 净值 ${formatSigned(state.outNet)}`,
    );
  }
  return lines;
}

function decisionFluxHint(
  kind: BucketKind,
  decision: Decision,
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
): string[] {
  const state = decisionFluxState(decision, effectScores, currentTargets);
  if (!state) return [];
  if (kind === "manual") {
    if (state.tension >= 0.28 || state.contest >= 0.12) {
      return [`M3 判读：${state.target} 当前拉扯偏高，保留人工裁决更稳。`];
    }
    if (Math.abs(state.resolvedFlux) >= 0.22 && state.reinforce >= 0.12) {
      return [`M3 判读：${state.target} 走势已较清晰，但仍建议人工收口确认。`];
    }
    return [];
  }
  if (kind === "system" || kind === "auto") {
    if (state.reinforce >= 0.15 && state.tension < 0.28) {
      return [`M3 判读：${state.target} 同向放大明显、张力可控，适合自动收敛。`];
    }
    if (state.tension >= 0.28) {
      return [`M3 判读：${state.target} 仍有明显拉扯，自动侧以归档/观察更稳。`];
    }
    return [];
  }
  if (state.tension >= 0.24 || state.contest >= 0.1) {
    return [`M3 判读：${state.target} 存在争执与解释空间，适合交给 LLM。`];
  }
  return [`M3 判读：${state.target} 张力较低，更适合作为提示词素材。`];
}

function groupFluxSummaryLines(
  decisions: Decision[],
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
): string[] {
  const states = Array.from(
    new Map(
      (decisions || [])
        .map((decision) => decisionFluxState(decision, effectScores, currentTargets))
        .filter((item): item is FluxStateRow => Boolean(item))
        .sort(
          (left, right) =>
            Math.abs(right.tension) + Math.abs(right.resolvedFlux) + right.reinforce -
            (Math.abs(left.tension) + Math.abs(left.resolvedFlux) + left.reinforce),
        )
        .map((item) => [item.target, item]),
    ).values(),
  ).slice(0, 2);
  if (!states.length) return [];
  const summary = states
    .map(
      (item) =>
        `${item.target} 张力 ${item.tension.toFixed(2)} / 放大 ${item.reinforce.toFixed(2)} / 流后 ${formatSigned(item.resolvedFlux)}`,
    )
    .join(" · ");
  const lines = [`M3 实时场：${summary}`];
  const dominant = states[0];
  if (dominant && dominant.tension >= 0.28) {
    lines.push(`M3 判读：${dominant.target} 是本组的主要拉扯点，建议联动观察。`);
  }
  return lines;
}

function dominantFluxState(
  decisions: Decision[],
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
): FluxStateRow | null {
  return (decisions || [])
    .map((decision) => decisionFluxState(decision, effectScores, currentTargets))
    .filter((item): item is FluxStateRow => Boolean(item))
    .sort(
      (left, right) =>
        Math.abs(right.tension) +
          Math.abs(right.resolvedFlux) +
          right.reinforce +
          right.contest -
        (Math.abs(left.tension) + Math.abs(left.resolvedFlux) + left.reinforce + left.contest),
    )[0] || null;
}

function actionMetaFromFluxState(state: FluxStateRow | null, count = 1): DecisionActionMeta {
  const suffix = count > 1 ? ` (${count})` : "";
  if (!state?.target) {
    return {
      label: count > 1 ? `批量处理本组${suffix}` : "处理",
      hint: "",
    };
  }
  if (state.tension >= 0.28 || state.contest >= 0.12) {
    return {
      label: count > 1 ? `整组裁定 ${state.target}${suffix}` : `人工裁定 ${state.target}`,
      hint: `${state.target} 当前拉扯偏高，建议先人工收口再放行。`,
    };
  }
  if (state.reinforce >= 0.15 && state.resolvedFlux >= 0.18) {
    return {
      label: count > 1 ? `确认整组执行${suffix}` : `确认执行 ${state.target}`,
      hint: `${state.target} 同向放大清晰，可直接确认执行。`,
    };
  }
  if (state.resolvedFlux <= -0.18 || state.harm >= 0.22) {
    return {
      label: count > 1 ? `整组审定 ${state.target}${suffix}` : `审定 ${state.target}`,
      hint: `${state.target} 当前净效偏负，建议谨慎确认。`,
    };
  }
  return {
    label: count > 1 ? `批量处理本组${suffix}` : `处理 ${state.target}`,
    hint: `${state.target} 当前可进入常规处理路径。`,
  };
}

function decisionReasonTags(kind: BucketKind, decision: Decision): string[] {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  const target = String(decision.target_god || impact.target_god || "").trim();
  const tags: string[] = [];
  if (target) tags.push(`目标神:${target}`);
  if (level > 0) tags.push(`烈度:L${level}`);
  if (ratio > 0) tags.push(`位移:${(ratio * 100).toFixed(0)}%`);
  if (kind === "manual") tags.push("人工裁决");
  if (kind === "auto") tags.push("后台处理");
  if (kind === "system") tags.push("自动收敛");
  if (kind === "llm") tags.push("叙事引用");
  return tags.slice(0, 4);
}

function arbitrationModeLabel(kind: BucketKind): string {
  if (kind === "manual") return "手动";
  if (kind === "auto") return "自动";
  if (kind === "system") return "自动";
  return "叙事";
}

function arbitrationTrace(kind: BucketKind, decision: Decision): string {
  if (String(decision.arbitration_trace || "").trim()) {
    return String(decision.arbitration_trace || "").trim();
  }
  const impact = decision.physical_impact || {};
  const level = Number(impact.intensity_level || 0);
  const source = String(decision.source_label || "").trim() || sourceLabel(decision);
  const levelText = level > 0 ? `L${level}` : "L?";
  return `${source} -> ${levelText} -> ${arbitrationModeLabel(kind)}`;
}

function isPassiveLlmContext(decision: Decision): boolean {
  const policy = String(decision.llm_resolution_policy || "").trim().toLowerCase();
  const result = String(decision.llm_resolution_result || "").trim().toLowerCase();
  const state = String(decision.llm_resolution_state || "").trim().toLowerCase();
  return policy === "context_only" || result === "consume_context" || state === "pending_context";
}

function decisionTarget(decision: Decision): string {
  return String(decision.target_god || decision.physical_impact?.target_god || "").trim();
}

function isActionableManualDecision(decision: Decision): boolean {
  const status = String(decision.status || "").trim().toUpperCase();
  if (status && !new Set(["PENDING", "AWAIT_REVIEW"]).has(status)) return false;
  if (isPassiveLlmContext(decision)) return false;
  const mode = String(decision.arbitration_mode || "manual").trim().toLowerCase();
  if (mode && mode !== "manual") return false;
  const impact = decision.physical_impact || {};
  const hasRatio = Object.prototype.hasOwnProperty.call(impact, "impact_ratio");
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  if (!decisionTarget(decision)) return false;
  if (hasRatio && ratio <= 1e-6) return false;
  const llmState = String(decision.llm_resolution_state || "").trim().toLowerCase();
  if (llmState === "promoted_to_manual" && !String(decision.id || "").trim()) return false;
  return true;
}

function formatPlanDecisionTrace(trace: PlanDecisionTrace[]): string[] {
  if (!trace.length) return [];
  return trace
    .slice(0, 8)
    .map((item) => {
      const idx = typeof item.trace_index === "number" ? item.trace_index + 1 : null;
      const label = String(item.label || item.decision_id || "未命名").trim();
      const source = String(item.source || "unknown").trim();
      const target = String(item.target_god || "未定目标").trim();
      const ratio = Number(item.impact_ratio || 0);
      const ratioText =
        ratio > 0 ? `↑${(ratio * 100).toFixed(1)}%` : ratio < 0 ? `↓${Math.abs(ratio * 100).toFixed(1)}%` : "观察";
      const prefix = idx == null ? "" : `${idx}. `;
      return `${prefix}${label} @${target} ${ratioText} / ${source}`;
    })
    .filter(Boolean);
}

type PlanDecisionTrace = {
  trace_index?: number;
  decision_id?: string;
  label?: string;
  source?: string;
  target_god?: string;
  impact_ratio?: number;
  priority?: number;
  routing_hint?: string;
  exclusivity_key?: string;
  source_event?: string;
};

type PlanQueueItem = {
  plan_id?: string;
  anchor?: string;
  status?: string;
  routing?: string;
  routing_reason?: string;
  routing_policy?: string;
  routing_features?: PlanDecisionRoutingFeatures;
  routing_claim?: PlanDecisionClaim;
  routing_scores?: Record<string, unknown>;
  action?: string;
  decision_ids?: string[];
  impact_summary?: Record<string, number>;
  meta?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
  batch_ids?: string[];
};

type PlanDecisionTraceIndexItem = {
  plan_id?: string;
  anchor?: string;
  status?: string;
  routing?: string;
  updated_at?: string;
  decision_count?: number;
  decision_ids?: string[];
  batch_ids?: string[];
  routing_reason?: string;
  routing_policy?: string;
  routing_scores?: Record<string, unknown>;
  decision_trace_count?: number;
  decision_trace?: PlanDecisionTrace[];
  impact_summary?: Record<string, number>;
  llm_prompt_preview?: boolean;
};

type AutoInboxRow = {
  key: string;
  decision: Decision;
  channel: "system" | "llm" | "context";
};

function planStatusTone(status?: string): string {
  const normalized = String(status || "unknown").toLowerCase();
  if (normalized === "completed" || normalized === "done") {
    return "border-emerald-500/30 bg-emerald-950/35 text-emerald-100";
  }
  if (normalized === "failed" || normalized === "rejected") {
    return "border-rose-500/30 bg-rose-950/35 text-rose-100";
  }
  if (normalized === "processing") {
    return "border-amber-500/30 bg-amber-950/35 text-amber-100";
  }
  return "border-violet-500/25 bg-violet-950/30 text-violet-100";
}

function planRoutingTone(routing?: string): string {
  const normalized = String(routing || "system").trim().toLowerCase();
  if (normalized === "llm") {
    return "border-cyan-500/25 bg-cyan-950/30 text-cyan-100";
  }
  if (normalized === "user") {
    return "border-rose-500/25 bg-rose-950/30 text-rose-100";
  }
  return "border-emerald-500/25 bg-emerald-950/30 text-emerald-100";
}

function compactRoutingScores(scores?: Record<string, unknown>): string {
  if (!scores || typeof scores !== "object") return "";
  const text = Object.entries(scores)
    .map(([name, value]) => {
      const num = Number(value);
      if (!Number.isFinite(num)) return "";
      return `${name} ${num.toFixed(2)}`;
    })
    .filter(Boolean)
    .sort();
  return text.join(" · ");
}

function planRoutingRationale(plan: {
  routing?: string;
  routing_reason?: string;
  routing_policy?: string;
  routing_scores?: Record<string, unknown>;
  updated_at?: string;
}): string[] {
  const route = String(plan.routing || "system").trim().toUpperCase() || "SYSTEM";
  const reason = String(plan.routing_reason || "").trim();
  const policy = String(plan.routing_policy || "").trim();
  const scores = compactRoutingScores(plan.routing_scores);
  const lines: string[] = [`路由通道 ${route}`];
  if (policy) lines.push(`策略 ${policy}`);
  if (reason) lines.push(`原因 ${reason}`);
  if (scores) lines.push(`候选分数 ${scores}`);
  const tension = asNumber(plan.routing_scores?.live_tension);
  const reinforce = asNumber(plan.routing_scores?.live_reinforce);
  const contest = asNumber(plan.routing_scores?.live_contest);
  if (tension > 0 || reinforce > 0 || contest > 0) {
    lines.push(`M3 张力 ${tension.toFixed(2)} · 放大 ${reinforce.toFixed(2)} · 对抗 ${contest.toFixed(2)}`);
    if (route === "LLM" && (tension >= 0.24 || contest >= 0.1)) {
      lines.push("M3 判读：当前目标争执偏高，模型预审更合适。");
    } else if (route === "SYSTEM" && reinforce >= 0.15 && tension < 0.28) {
      lines.push("M3 判读：同向放大清晰，可先走系统收敛。");
    } else if (route === "USER" && tension >= 0.28) {
      lines.push("M3 判读：张力偏高，保留人工确认更稳。");
    }
  }
  if (plan.updated_at) lines.push(`更新时间 ${String(plan.updated_at)}`);
  return lines;
}

function compactRoutingLines(lines: string[]): string {
  const safe = (lines || []).map((line) => String(line || "").trim()).filter(Boolean);
  return safe.join(" · ");
}

function derivePlanActionMeta(plan: {
  routing?: string;
  routing_scores?: Record<string, unknown>;
}): PlanActionMeta {
  const route = String(plan.routing || "system").trim().toLowerCase();
  const tension = asNumber(plan.routing_scores?.live_tension);
  const reinforce = asNumber(plan.routing_scores?.live_reinforce);
  const contest = asNumber(plan.routing_scores?.live_contest);
  if (route === "llm") {
    return {
      approveLabel: "提交模型预审",
      rejectLabel: "放弃预审",
      escalateLabel: "改走人工",
      withdrawLabel: "撤回计划",
      recommended: "APPROVED",
      hint:
        tension >= 0.24 || contest >= 0.1
          ? "推荐动作：提交模型预审，当前争执较高，适合先让模型判读。"
          : "推荐动作：提交模型预审，当前更像解释型分歧。",
    };
  }
  if (route === "user") {
    return {
      approveLabel: tension >= 0.28 ? "确认人工裁定" : "确认执行",
      rejectLabel: "驳回本计划",
      escalateLabel: "升级给模型",
      withdrawLabel: "撤回计划",
      recommended: "APPROVED",
      hint:
        tension >= 0.28
          ? "推荐动作：确认人工裁定，当前张力偏高，保留人为收口更稳。"
          : "推荐动作：确认执行，这组计划已适合你直接拍板。",
    };
  }
  if (tension >= 0.28) {
    return {
      approveLabel: "仍按系统执行",
      rejectLabel: "阻止执行",
      escalateLabel: "改由人工裁决",
      withdrawLabel: "撤回计划",
      recommended: "ESCALATE",
      hint: "推荐动作：改由人工裁决，当前张力偏高，不宜直接自动执行。",
    };
  }
  if (reinforce >= 0.15 && tension < 0.28) {
    return {
      approveLabel: "确认自动执行",
      rejectLabel: "阻止执行",
      escalateLabel: "改走人工",
      withdrawLabel: "撤回计划",
      recommended: "APPROVED",
      hint: "推荐动作：确认自动执行，同向放大清晰且张力可控。",
    };
  }
  return {
    approveLabel: "确认系统处理",
    rejectLabel: "否决本计划",
    escalateLabel: "升档人工",
    withdrawLabel: "撤回计划",
    recommended: contest >= 0.1 ? "ESCALATE" : "APPROVED",
    hint:
      contest >= 0.1
        ? "推荐动作：升档人工，当前仍有对抗残留。"
        : "推荐动作：确认系统处理，当前可按常规路径推进。",
  };
}

function planIsTerminal(status?: string): boolean {
  const normalized = String(status || "").trim().toUpperCase();
  return new Set(["COMPLETED", "DONE", "APPROVED", "REJECTED", "COMMITTED", "FAILED"]).has(normalized);
}

function planIsClosedLoop(status?: string): boolean {
  const normalized = String(status || "").trim().toUpperCase();
  return new Set(["COMPLETED", "DONE", "APPROVED", "REJECTED", "COMMITTED"]).has(normalized);
}

function planIsFailed(status?: string): boolean {
  return String(status || "").trim().toUpperCase() === "FAILED";
}

function planDisplayName(plan: PlanQueueItem): string {
  const action = String(plan.action || plan.meta?.action || "").trim();
  const anchor = String(plan.anchor || "").trim();
  const trace = Array.isArray(plan.meta?.decision_trace) ? (plan.meta?.decision_trace as PlanDecisionTrace[]) : [];
  const firstTraceLabel = String(trace[0]?.label || "").trim();
  if (anchor && anchor.toLowerCase() !== "manual") return anchor;
  if (action && action.toLowerCase() !== "plan_action") return action;
  if (firstTraceLabel) return firstTraceLabel;
  if (anchor) return anchor;
  return "未命名计划";
}

function planImpactBriefs(impact?: Record<string, number>): string[] {
  if (!impact) return [];
  return Object.entries(impact)
    .filter(([, value]) => Number.isFinite(value))
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 4)
    .map(([name, value]) => `${name}: ${(value * 100).toFixed(0)}%`);
}

export function V17_DecisionInbox({
  frames,
  adoptedIds,
  focusedDecisionId,
  viewMode = "full",
  locked = false,
  lockMessage = "",
  onAdopted,
  onAdoptedBatch,
  onPlanAction,
  lang = "zh",
}: {
  frames: Frame[];
  adoptedIds: string[];
  focusedDecisionId?: string;
  viewMode?: "full" | "manual_only";
  locked?: boolean;
  lockMessage?: string;
  onAdopted?: (decision: Decision & { status: "APPROVED" | "REJECTED" }) => void | Promise<void>;
  onAdoptedBatch?: (
    decisions: Decision[],
    status: "APPROVED" | "REJECTED",
    batchIds?: string[],
  ) => void | Promise<void>;
  onPlanAction?: (
    plan: PlanQueueItem,
    status: "APPROVED" | "REJECTED" | "ESCALATE" | "WITHDRAW",
  ) => void | Promise<void>;
  lang?: AppLanguage;
}) {
  const [busyId, setBusyId] = useState<string>("");
  const manualOnly = viewMode === "manual_only";

  const latestSnapshot = useMemo(() => 
    [...(frames || [])].reverse().find(f => 
      String(f?.layer || "").toUpperCase() === "SNAPSHOT" && 
      ["physics", "physical_void", "system_init_failure"].includes(String(f?.payload?.snapshot_kind || ""))
    ), [frames]);

  const manualSeed = useMemo(() => {
    const source =
      latestSnapshot?.payload?.manual_inbox ||
      latestSnapshot?.payload?.manual_decisions ||
      latestSnapshot?.payload?.pending_decisions ||
      [];
    return source.filter((decision) => isActionableManualDecision(decision));
  }, [latestSnapshot?.payload?.manual_inbox, latestSnapshot?.payload?.manual_decisions, latestSnapshot?.payload?.pending_decisions]);

  const { visible: sortedManualDecisions, hiddenCount } = useMemo(() => {
    const source = manualSeed.length ? manualSeed : [];
    const raw = source.filter((d, idx) => {
      const id = normalizeDecisionId(d, idx);
      return !adoptedIds.includes(id);
    });
    const sorted = [...raw].sort((a, b) => (Number(b.priority) || 0) - (Number(a.priority) || 0));
    const DISPLAY_CAP = 14;
    const cap = Math.min(sorted.length, DISPLAY_CAP);
    return { visible: sorted.slice(0, cap), hiddenCount: Math.max(0, sorted.length - cap) };
  }, [manualSeed, adoptedIds]);

  const decisions = useMemo(
    () =>
      sortedManualDecisions.map((decision, idx) => ({
        ...decision,
        _ui_id: normalizeDecisionId(decision, idx),
      })),
    [sortedManualDecisions],
  );
  const allDecisionCatalog = useMemo(
    () => buildDecisionCatalog(decisions, latestSnapshot?.payload?.all_decisions || []),
    [decisions, latestSnapshot?.payload?.all_decisions],
  );

  const allDecisionIndex = useMemo(() => buildDecisionIndex(allDecisionCatalog), [allDecisionCatalog]);
  const adoptedIdSet = useMemo(() => new Set(adoptedIds.map((id) => String(id || "").trim()).filter(Boolean)), [adoptedIds]);
  const manualGroups = useMemo(() => buildManualDecisionGroups(decisions), [decisions]);

  const batchRows = useMemo(() => latestSnapshot?.payload?.decision_batches || [], [latestSnapshot]);
  const conflictGraph = latestSnapshot?.payload?.claim_conflict_graph || {};
  const conflictGraphSummary = conflictGraph.summary || {};
  const conflictGraphConflicts = Array.isArray((latestSnapshot?.payload?.claim_conflict_graph || {}).conflicts)
    ? (latestSnapshot?.payload?.claim_conflict_graph || {}).conflicts
    : [];
  const topConflictRows = (conflictGraphConflicts || []).slice(0, 6);
  const manualDecisionBatches = useMemo(() => {
    if (!batchRows.length) return [];
    const rows: DecisionBatch[] = [];
    for (const raw of batchRows) {
      const bucket = normalizeBatchBucket(String(raw?.bucket || "manual"));
      if (bucket !== "manual") continue;
      const sourceFamilies = Array.isArray(raw?.source_families)
        ? raw.source_families.map((value) => String(value || "").trim()).filter(Boolean)
        : [];
      const batchId = String(raw?.batch_id || "").trim();
      const batchIds = batchId
        ? [batchId]
        : Array.isArray(raw?.batch_ids)
          ? raw.batch_ids.map((id) => String(id || "").trim()).filter(Boolean)
          : [];
      const decisionIds = Array.isArray(raw?.decision_ids)
        ? raw.decision_ids.map((value) => String(value || "").trim()).filter(Boolean)
        .filter((id) => !adoptedIdSet.has(id))
        : [];
      if (!decisionIds.length) continue;
      const batchDecisions = Array.from(
        new Set(
          decisionIds.flatMap((id) => {
            const matched = allDecisionIndex.get(id);
            if (matched) return [matched];
              const synthetic: DecisionWithId = {
                id,
              status: "pending",
              arbitration_mode: "manual",
              target_god: String(raw?.target_god || "").trim() || undefined,
              source: String(raw?.source_anchor || "manual_batch").trim(),
              physical_impact: {
                target_god: String(raw?.target_god || "").trim() || undefined,
                impact_ratio: Number(netImpactRatio) / Math.max(decisionIds.length, 1),
                intensity_level: 1,
              },
              _ui_id: `synthetic_${String(raw?.batch_id || "").trim() || "batch"}_${id}`,
            };
            return [synthetic];
          })
            .filter((item): item is DecisionWithId => Boolean(item)),
        ),
      );
      if (!batchDecisions.length) continue;
      const netImpactRatio = batchDecisions.reduce((sum, decision) => {
        const impactRatio = Number(decision.physical_impact?.impact_ratio || 0);
        return Number.isFinite(impactRatio) ? sum + impactRatio : sum;
      }, 0);
      if (!Number.isFinite(netImpactRatio) || Math.abs(netImpactRatio) <= 1e-6) continue;
      rows.push({
        batch_id: String(raw?.batch_id || `${bucket}:${raw?.source_anchor || "unknown"}:${decisionIds.join(",")}`).trim(),
        bucket: "manual",
        target: String(raw?.target_god || batchDecisions[0]?.target_god || batchDecisions[0]?.physical_impact?.target_god || "未定目标").trim(),
        source_anchor: String(raw?.source_anchor || batchDecisions[0]?.source || batchDecisions[0]?.plugin_id || "").trim(),
        source_families: sourceFamilies,
        decisions: batchDecisions,
        decision_count: batchDecisions.length,
        net_impact_ratio: netImpactRatio,
        max_priority: Number(raw?.max_priority || 0),
        direction_key: String(raw?.direction_key || "").trim() || undefined,
        direction_label: String(raw?.direction_label || "").trim() || undefined,
        prompt_line: String(raw?.prompt_line || "").trim() || "自动批次已生成，可一次提交。",
        batch_ids: batchIds.length ? batchIds : undefined,
        labels: (Array.isArray(raw?.labels) ? raw.labels : []).map((value) => String(value || "").trim()).filter(Boolean),
      });
    }
    return rows.sort(
      (a, b) =>
        Math.abs(b.net_impact_ratio) - Math.abs(a.net_impact_ratio) ||
        b.max_priority - a.max_priority ||
        b.decision_count - a.decision_count,
    );
  }, [batchRows, allDecisionIndex, adoptedIdSet]);
  const groupedManualDecisionBatches = useMemo(
    () => manualDecisionBatches.filter((group) => group.decisions.length > 1),
    [manualDecisionBatches],
  );
  const singleManualDecisionBatches = useMemo(
    () => manualDecisionBatches.filter((group) => group.decisions.length <= 1),
    [manualDecisionBatches],
  );

  const autoDecisionBatches = useMemo(() => {
    if (!batchRows.length) return [];
    const rows: DecisionBatch[] = [];
    for (const raw of batchRows) {
      const bucket = normalizeBatchBucket(String(raw?.bucket || "system"));
      if (bucket === "manual") continue;
      const sourceFamilies = Array.isArray(raw?.source_families)
        ? raw.source_families.map((value) => String(value || "").trim()).filter(Boolean)
        : [];
      const batchId = String(raw?.batch_id || "").trim();
      const batchIds = batchId
        ? [batchId]
        : Array.isArray(raw?.batch_ids)
          ? raw.batch_ids.map((id) => String(id || "").trim()).filter(Boolean)
          : [];
      const decisionIds = Array.isArray(raw?.decision_ids)
        ? raw.decision_ids.map((value) => String(value || "").trim()).filter(Boolean)
        .filter((id) => !adoptedIdSet.has(id))
        : [];
      if (!decisionIds.length) continue;
      const batchDecisions = Array.from(
        new Set(
          decisionIds.flatMap((id) => {
            const matched = allDecisionIndex.get(id);
            if (matched) return [matched];
            const synthetic: DecisionWithId = {
              id,
              status: "pending",
              arbitration_mode: bucket,
              target_god: String(raw?.target_god || "").trim() || undefined,
              source: String(raw?.source_anchor || "auto_batch").trim(),
              physical_impact: {
                target_god: String(raw?.target_god || "").trim() || undefined,
                impact_ratio: Number.isFinite(Number(raw?.net_impact_ratio || 0))
                  ? Number(raw?.net_impact_ratio || 0) / Math.max(decisionIds.length, 1)
                  : 0,
                intensity_level: 1,
              },
              _ui_id: `synthetic_${String(raw?.batch_id || "").trim() || "batch"}_${id}`,
            };
            return [synthetic];
          })
            .filter((item): item is DecisionWithId => Boolean(item)),
        ),
      );
      if (!batchDecisions.length) continue;
      rows.push({
        batch_id: String(raw?.batch_id || `${bucket}:${raw?.source_anchor || "unknown"}:${decisionIds.join(",")}`).trim(),
        bucket,
        target: String(raw?.target_god || batchDecisions[0]?.target_god || batchDecisions[0]?.physical_impact?.target_god || "未定目标").trim(),
        source_anchor: String(raw?.source_anchor || batchDecisions[0]?.source || batchDecisions[0]?.plugin_id || "").trim(),
        source_families: sourceFamilies,
        decisions: batchDecisions,
        decision_count: batchDecisions.length,
        net_impact_ratio: batchDecisions.reduce((sum, decision) => {
          const impactRatio = Number(decision.physical_impact?.impact_ratio || 0);
          return Number.isFinite(impactRatio) ? sum + impactRatio : sum;
        }, 0),
        max_priority: Number(raw?.max_priority || 0),
        direction_key: String(raw?.direction_key || "").trim() || undefined,
        direction_label: String(raw?.direction_label || "").trim() || undefined,
        prompt_line: String(raw?.prompt_line || "").trim() || "自动批次已生成，可用于系统审阅。",
        batch_ids: batchIds.length ? batchIds : undefined,
        labels: (Array.isArray(raw?.labels) ? raw.labels : []).map((value) => String(value || "").trim()).filter(Boolean),
      });
    }
    return rows.sort(
      (a, b) =>
        Math.abs(b.net_impact_ratio) - Math.abs(a.net_impact_ratio) ||
        b.max_priority - a.max_priority ||
        b.decision_count - a.decision_count,
    );
  }, [batchRows, allDecisionIndex, adoptedIdSet]);

  const autoResolutions = useMemo(
    () => (latestSnapshot?.payload?.auto_resolutions || []).slice(0, 6),
    [latestSnapshot?.payload?.auto_resolutions],
  );
  const planQueue = useMemo(
    () =>
      (latestSnapshot?.payload?.decision_brain_state?.plan_queue || [])
        .map((raw): PlanQueueItem => {
          const meta = raw?.meta && typeof raw.meta === "object" ? (raw.meta as Record<string, unknown>) : undefined;
          const routingReason = String((meta && typeof meta.routing_reason === "string" ? meta.routing_reason : "") || "").trim();
          const routingPolicy = String((meta && typeof meta.routing_policy === "string" ? meta.routing_policy : "") || "").trim();
          const rawRoutingReason = String((typeof raw?.routing_reason === "string" && raw.routing_reason) || "").trim();
          const rawRoutingPolicy = String((typeof raw?.routing_policy === "string" && raw.routing_policy) || "").trim();
          const rawRoutingFeatures =
            raw && typeof raw.routing_features === "object" && raw.routing_features !== null
              ? (raw.routing_features as PlanDecisionRoutingFeatures)
              : undefined;
          const rawRoutingClaim =
            raw && typeof raw.routing_claim === "object" && raw.routing_claim !== null
              ? (raw.routing_claim as PlanDecisionClaim)
              : undefined;
          const routingFeatures =
            meta && typeof meta.routing_features === "object" && meta.routing_features !== null
              ? (meta.routing_features as PlanDecisionRoutingFeatures)
              : undefined;
          const action = String(meta && typeof meta.action === "string" ? meta.action : "").trim();
          const routingClaim =
            rawRoutingClaim ||
            (meta && typeof meta.routing_claim === "object" && meta.routing_claim !== null
              ? (meta.routing_claim as PlanDecisionClaim)
              : undefined);
          const routingScores =
            meta && typeof meta.routing_scores === "object" && meta.routing_scores !== null
              ? (meta.routing_scores as Record<string, unknown>)
              : undefined;
          const rawRoutingScores =
            raw && typeof raw.routing_scores === "object" && raw.routing_scores !== null
              ? (raw.routing_scores as Record<string, unknown>)
              : undefined;
          return {
            plan_id: String(raw?.plan_id || "").trim() || undefined,
            anchor: String(raw?.anchor || "").trim() || undefined,
            status: String(raw?.status || "").trim() || undefined,
            routing: String(raw?.routing || "").trim() || undefined,
            routing_reason: rawRoutingReason || routingReason || undefined,
            routing_policy: rawRoutingPolicy || routingPolicy || undefined,
            routing_features: rawRoutingFeatures || routingFeatures,
            routing_claim: routingClaim,
            routing_scores: rawRoutingScores || routingScores,
            action: action || undefined,
            decision_ids: Array.isArray(raw?.decision_ids) ? raw.decision_ids.map((id) => String(id || "").trim()).filter(Boolean) : undefined,
            impact_summary: raw?.impact_summary && typeof raw.impact_summary === "object" ? raw.impact_summary : undefined,
            meta: raw?.meta && typeof raw.meta === "object" ? raw.meta : undefined,
            created_at: String(raw?.created_at || "").trim() || undefined,
            updated_at: String(raw?.updated_at || "").trim() || undefined,
            batch_ids: Array.isArray(raw?.batch_ids) ? raw.batch_ids.map((id) => String(id || "").trim()).filter(Boolean) : undefined,
          };
        }),
    [latestSnapshot],
  );
  const activePlanQueue = useMemo(
    () =>
      planQueue
        .filter((item) => !planIsTerminal(item.status) || planIsFailed(item.status))
        .sort((a, b) => String(a.anchor || "").localeCompare(String(b.anchor || ""))),
    [planQueue],
  );
  const failedPlanQueue = useMemo(
    () =>
      planQueue
        .filter((item) => planIsFailed(item.status))
        .sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || ""))),
    [planQueue],
  );
  const terminalPlanQueue = useMemo(
    () =>
      planQueue
        .filter((item) => planIsClosedLoop(item.status))
        .sort((a, b) => String(b.updated_at || "").localeCompare(String(a.updated_at || ""))),
    [planQueue],
  );

  const decisionTraceIndex = useMemo(() => {
    const payload = latestSnapshot?.payload?.decision_trace_index;
    const rawItems = payload?.items;
    const items = Array.isArray(rawItems) ? (rawItems as PlanDecisionTraceIndexItem[]) : [];
    const enrichedItems = items.map((item) => {
      const maybeRaw = item as Record<string, unknown>;
      const meta = maybeRaw.meta as Record<string, unknown> | undefined;
      const metaRoutingScores =
        meta && typeof meta === "object" && meta.routing_scores && typeof meta.routing_scores === "object"
          ? (meta.routing_scores as Record<string, unknown>)
          : undefined;
      return {
        ...item,
        routing_scores: item.routing_scores || metaRoutingScores,
      } as PlanDecisionTraceIndexItem;
    });
    return {
      contract: String((payload?.contract || "").trim()) || "v17.decision.trace_index.v1",
      plan_count: Number((payload?.plan_count || items.length) || 0),
      items: enrichedItems.slice(0, 20),
    };
  }, [latestSnapshot]);
  const llmArbitrationSource = useMemo(
    () => latestSnapshot?.payload?.llm_arbitration_context || [],
    [latestSnapshot?.payload?.llm_arbitration_context],
  );
  const llmArbitration = useMemo(
    () => llmArbitrationSource.filter((row) => !isPassiveLlmContext(row)).slice(0, 6),
    [llmArbitrationSource],
  );
  const passiveLlmContextRows = useMemo(
    () => llmArbitrationSource.filter((row) => isPassiveLlmContext(row)).slice(0, 3),
    [llmArbitrationSource],
  );
  const passiveLlmContextCount = llmArbitrationSource.filter((row) => isPassiveLlmContext(row)).length;
  const autoDecisionBatchDecisionIds = useMemo(() => {
    const ids = new Set<string>();
    for (const batch of autoDecisionBatches) {
      for (const decision of batch.decisions) {
        if (decision.id) ids.add(String(decision.id));
      }
    }
    return ids;
  }, [autoDecisionBatches]);
  const autoDecisionSource = useMemo(
    () => latestSnapshot?.payload?.auto_decisions || [],
    [latestSnapshot?.payload?.auto_decisions],
  );
  const godRingEffectScores = useMemo(() => {
    const raw = latestSnapshot?.payload?.god_rings?.effect_scores;
    return raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  }, [latestSnapshot?.payload?.god_rings?.effect_scores]);
  const knowledgeCurrentTargets = useMemo(() => {
    const raw = latestSnapshot?.payload?.plugins?.knowledge_snapshot?.claim_history?.current_targets;
    return raw && typeof raw === "object" ? (raw as Record<string, unknown>) : {};
  }, [latestSnapshot?.payload?.plugins?.knowledge_snapshot?.claim_history?.current_targets]);
  const fluxRationale = useCallback(
    (decision: Decision) => decisionFluxSummaryLines(decision, godRingEffectScores, knowledgeCurrentTargets),
    [godRingEffectScores, knowledgeCurrentTargets],
  );
  const singleDecisionActionMeta = useCallback(
    (decision: Decision) =>
      actionMetaFromFluxState(
        decisionFluxState(decision, godRingEffectScores, knowledgeCurrentTargets),
      ),
    [godRingEffectScores, knowledgeCurrentTargets],
  );
  const groupDecisionActionMeta = useCallback(
    (items: Decision[]) =>
      actionMetaFromFluxState(
        dominantFluxState(items, godRingEffectScores, knowledgeCurrentTargets),
        items.length,
      ),
    [godRingEffectScores, knowledgeCurrentTargets],
  );
  const groupFluxRationale = useCallback(
    (items: Decision[]) => groupFluxSummaryLines(items, godRingEffectScores, knowledgeCurrentTargets),
    [godRingEffectScores, knowledgeCurrentTargets],
  );
  const singleDecisionButtonLabel = useCallback(
    (decision: Decision) => singleDecisionActionMeta(decision).label,
    [singleDecisionActionMeta],
  );
  const routingRationale = useCallback(
    (kind: BucketKind, decision: Decision) => [
      ...baseRoutingRationale(kind, decision),
      ...decisionFluxHint(kind, decision, godRingEffectScores, knowledgeCurrentTargets),
    ],
    [godRingEffectScores, knowledgeCurrentTargets],
  );
  const autoInboxRows = useMemo(() => {
    if (Array.isArray(autoDecisionSource) && autoDecisionSource.length) {
      return autoDecisionSource
        .slice(0, 12)
        .filter((decision) => !(decision.id && autoDecisionBatchDecisionIds.has(String(decision.id))))
        .map((decision, idx) => ({
          key: `auto_${String(decision.id || decision.label || idx)}`,
          decision,
          channel: ((String((decision as Decision & { auto_bucket?: string }).auto_bucket || "").trim().toLowerCase() as
            "system" | "llm" | "context") || (isPassiveLlmContext(decision) ? "context" : "system")) as
            "system" | "llm" | "context",
        }));
    }
    const rows: AutoInboxRow[] = [];
    autoResolutions.forEach((decision, idx) => {
      if (decision.id && autoDecisionBatchDecisionIds.has(String(decision.id))) return;
      rows.push({
        key: `system_${String(decision.id || decision.label || idx)}`,
        decision,
        channel: "system",
      });
    });
    llmArbitration.forEach((decision, idx) => {
      if (decision.id && autoDecisionBatchDecisionIds.has(String(decision.id))) return;
      rows.push({
        key: `llm_${String(decision.id || decision.label || idx)}`,
        decision,
        channel: "llm",
      });
    });
    passiveLlmContextRows.forEach((decision, idx) => {
      rows.push({
        key: `context_${String(decision.id || decision.label || idx)}`,
        decision,
        channel: "context",
      });
    });
    return rows.slice(0, 12);
  }, [autoDecisionBatchDecisionIds, autoDecisionSource, autoResolutions, llmArbitration, passiveLlmContextRows]);

  async function onVote(decision: DecisionWithId, status: "APPROVED" | "REJECTED") {
    if (locked || busyId) return;
    const id = String(decision.id || decision._ui_id || decision.label || "vote");
    setBusyId(id);
    try {
      await onAdopted?.({ ...decision, id, status });
    } finally {
      setBusyId("");
    }
  }

  async function onBatchVote(
    group: { decisions: DecisionWithId[]; batch_ids?: string[]; batch_id?: string },
    status: "APPROVED" | "REJECTED",
  ) {
    if (locked || !group.decisions.length) return;
    const busyKey = String(group.batch_id || group.batch_ids?.[0] || group.decisions[0]?._ui_id || "batch_vote");
    setBusyId(busyKey);
    try {
    if (onAdoptedBatch) {
      const batchIds = Array.from(new Set([...(group.batch_ids || []), ...(group.batch_id ? [group.batch_id] : [])]));
      await onAdoptedBatch(group.decisions, status, batchIds);
      return;
    }
    for (const decision of group.decisions) {
      await onVote(decision, status);
    }
    } finally {
      setBusyId("");
    }
  }

  async function onPlanVote(
    plan: PlanQueueItem,
    status: "APPROVED" | "REJECTED" | "ESCALATE" | "WITHDRAW",
  ) {
    if (locked || !plan.plan_id) return;
    const busyKey = `plan_${plan.plan_id}`;
    setBusyId(busyKey);
    if (onPlanAction) {
      try {
        await onPlanAction(plan, status);
      } finally {
        setBusyId("");
      }
      return;
    }
    setBusyId("");
  }

  if (manualOnly) {
    if (!decisions.length) return null;
  } else if (!decisions.length && !autoInboxRows.length && !autoDecisionBatches.length && !planQueue.length) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-violet-700/40 bg-[linear-gradient(180deg,rgba(8,4,20,0.92),rgba(10,10,16,0.82))] p-3 shadow-[0_16px_50px_rgba(76,29,149,0.18)]">
        <div className="mb-3 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.24em] text-violet-200/85">DECISION INBOX</p>
          <p className="mt-1 text-[11px] text-zinc-500">
            {manualOnly ? t(lang, "decision.manual.header") : "手动入口 / 自动回执"}
            {!manualOnly && latestSnapshot?.payload?.decision_inbox_contract ? ` · ${latestSnapshot.payload.decision_inbox_contract}` : ""}
          </p>
        </div>

        {!manualOnly && conflictGraphSummary.conflict_count ? (
          <div className="mb-3 rounded-xl border border-zinc-700/20 bg-zinc-950/60 p-3">
            <p className="text-[11px] tracking-[0.22em] text-zinc-300">CLAIM CONFLICT GRAPH</p>
            <div className="mt-2 grid gap-2 text-[10px]">
              <p className="text-zinc-400">
                版本 {String(conflictGraph.graph_version || "v17.claim_graph.1")} · 冲突 {Number(conflictGraphSummary.conflict_count || 0)} /
                开放 {Number(conflictGraphSummary.open_conflict_count || 0)} / 节点 {Number(conflictGraphSummary.node_count || 0)}
              </p>
              {topConflictRows.length ? (
                <div className="space-y-1">
                  {topConflictRows.map((row) => {
                    const cid = String(row?.conflict_id || "unknown").trim();
                    const status = String(row?.status || "open").trim();
                    return (
                      <div
                        key={cid}
                        className="rounded-lg border border-zinc-700/25 bg-zinc-900/70 px-2 py-1.5 text-[10px] text-zinc-300"
                      >
                        <p className="text-zinc-200">
                          {cid} · {String(row?.conflict_type || "conflict")} · 严重度 {String(row?.severity || "P3")}
                        </p>
                        <p className="text-zinc-400">
                          目标 {String(row?.target_god || "未定目标")} · 主裁 {String(row?.recommended_arbiter || "system")} ·
                          状态 {status}
                        </p>
                        <p className="mt-0.5 text-zinc-500">{String(row?.why_conflict || "待补充冲突原因").trim()}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-zinc-500">已构建冲突图，但当前无冲突明细。</p>
              )}
            </div>
          </div>
        ) : null}
        <div className="flex items-center gap-2 text-[10px]">
          <span className="rounded-full border border-violet-500/25 bg-violet-900/20 px-2 py-1 text-violet-100">
            手动 {decisions.length}
          </span>
          {!manualOnly ? (
            <>
              <span className="rounded-full border border-amber-500/20 bg-amber-950/30 px-2 py-1 text-amber-100">
                自动 {autoInboxRows.length + autoDecisionBatches.length}
              </span>
              <span className="rounded-full border border-zinc-500/20 bg-zinc-900/20 px-2 py-1 text-zinc-100">
                Plan {planQueue.length}
              </span>
            </>
          ) : null}
          {focusedDecisionId ? (
            <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-2 py-1 text-emerald-200">
              聚焦 {focusedDecisionId}
            </span>
          ) : null}
        </div>
      </div>

      {!manualOnly && activePlanQueue.length ? (
        <div className="mb-3 rounded-xl border border-zinc-700/25 bg-zinc-950/60 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-zinc-300">计划队列</p>
            <span className="text-[10px] text-zinc-500">系统按计划批次推进，不再逐条串行处理</span>
          </div>
                <div className="space-y-2">
            {activePlanQueue.slice(0, 8).map((plan) => {
              const statusTone = planStatusTone(plan.status);
              const impacts = planImpactBriefs(plan.impact_summary);
              const llmReviewPrompt = String(plan.meta?.llm_review_prompt || "").trim();
              const routingLabel = compactRoutingLabel(plan.routing);
              const routingReason = String(plan.routing_reason || (plan.meta?.routing_reason as string) || "").trim();
              const routingPolicy = String(plan.routing_policy || (plan.meta?.routing_policy as string) || "").trim();
              const claim = plan.routing_claim || (plan.meta?.routing_claim as PlanDecisionClaim | undefined);
              const routingRationaleLines = planRoutingRationale(plan);
              const actionMeta = derivePlanActionMeta(plan);
              const approveLabel = actionMeta.approveLabel;
              const rejectLabel = actionMeta.rejectLabel;
              return (
                <div
                  key={plan.plan_id || `${plan.anchor || "plan"}:${plan.updated_at || ""}:${plan.routing || ""}`}
                  className={`rounded-lg border bg-zinc-900/70 p-2 ${
                    focusedDecisionId && Array.isArray(plan.decision_ids) && plan.decision_ids.includes(focusedDecisionId)
                      ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                      : "border-zinc-700/25"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-[10px] text-zinc-100">
                      {planDisplayName(plan)} · {plan.routing ? `策略 ${plan.routing}` : "未设置策略"}
                    </p>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${statusTone}`}>{plan.status || "pending"}</span>
                  </div>
                  <p className="mt-1 break-words text-[10px] text-zinc-400">
                    PlanID {plan.plan_id || "N/A"} · 批次 {(plan.batch_ids || []).length} 个
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${planRoutingTone(plan.routing)}`}>{routingLabel}</span>
                    <span className="rounded-full border border-zinc-500/20 px-1.5 py-0.5 text-[9px] text-zinc-200">
                      路由类型 {String(plan.routing || "system").trim().toUpperCase()}
                    </span>
                  </div>
                  <V17PlanRoutingClaim
                    routingLabel={routingLabel}
                    routingReason={routingReason}
                    routingPolicy={routingPolicy}
                    routingFeatures={plan.routing_features || (plan.meta?.routing_features as PlanDecisionRoutingFeatures | undefined)}
                    claim={claim}
                  />
                  {routingRationaleLines.length ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">
                      {compactRoutingLines(routingRationaleLines)}
                    </p>
                  ) : null}
                  <p className="mt-1 text-[9px] text-sky-200/85">{actionMeta.hint}</p>
                  {impacts.length ? (
                    <p className="mt-1 text-[10px] text-zinc-300">
                      影响速览：{impacts.join(" · ")}
                    </p>
                  ) : null}
                  {llmReviewPrompt ? (
                    <div className="mt-2 border-t border-zinc-700/20 pt-2">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-zinc-400">模型预审提示</p>
                      <pre className="mt-1 max-h-28 overflow-auto whitespace-pre-wrap rounded-md border border-amber-500/20 bg-zinc-950/70 p-1.5 text-[9px] leading-tight text-amber-100">
                        {llmReviewPrompt}
                      </pre>
                    </div>
                  ) : null}
                  {Array.isArray(plan.meta?.decision_trace) &&
                  (plan.meta?.decision_trace as PlanDecisionTrace[]).length ? (
                    <div className="mt-2 border-t border-zinc-700/20 pt-2">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-zinc-400">决策证据</p>
                      <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[9px] leading-tight text-zinc-300">
                        {formatPlanDecisionTrace(plan.meta?.decision_trace as PlanDecisionTrace[]).map((line) => (
                          <li key={line} className="break-words">
                            {line}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
              <div className="mt-2 flex items-center gap-2 border-t border-zinc-700/20 pt-2">
                  <button
                    type="button"
                    onClick={() => onPlanVote(plan, "REJECTED")}
                    disabled={locked || busyId !== ""}
                    className={`flex h-7 flex-1 items-center justify-center gap-1 rounded-lg border text-[10px] transition disabled:opacity-30 ${
                      actionMeta.recommended === "REJECTED"
                        ? "border-red-400/40 bg-red-900/35 text-red-100 shadow-[0_0_0_1px_rgba(248,113,113,0.22)]"
                        : "border-red-500/20 bg-red-950/20 text-red-300 hover:bg-red-500/40 hover:text-red-100"
                    }`}
                  >
                  <X className="h-3 w-3" /> {rejectLabel}
                  </button>
                <button
                  type="button"
                  onClick={() => onPlanVote(plan, "APPROVED")}
                  disabled={locked || busyId !== ""}
                  className={`flex h-7 flex-1 items-center justify-center gap-1 rounded-lg border text-[10px] transition disabled:opacity-30 ${
                    actionMeta.recommended === "APPROVED"
                      ? "border-emerald-400/40 bg-emerald-900/35 text-emerald-100 shadow-[0_0_0_1px_rgba(52,211,153,0.24)]"
                      : "border-emerald-500/20 bg-emerald-950/20 text-emerald-300 hover:bg-emerald-500/40 hover:text-emerald-100"
                  }`}
                >
                  <Check className="h-3 w-3" /> {approveLabel}
                </button>
              </div>
              <div className="mt-1.5 flex items-center gap-2 border-t border-zinc-700/20 pt-2">
                <button
                  type="button"
                  onClick={() => onPlanVote(plan, "ESCALATE")}
                  disabled={locked || busyId !== ""}
                  className={`flex h-7 flex-1 items-center justify-center gap-1 rounded-lg border text-[10px] transition disabled:opacity-30 ${
                    actionMeta.recommended === "ESCALATE"
                      ? "border-amber-400/40 bg-amber-900/35 text-amber-100 shadow-[0_0_0_1px_rgba(251,191,36,0.24)]"
                      : "border-amber-500/20 bg-amber-950/20 text-amber-300 hover:bg-amber-500/40 hover:text-amber-100"
                  }`}
                >
                  <span className="h-3 w-3 rounded-full border border-current" />
                  {actionMeta.escalateLabel}
                </button>
                <button
                  type="button"
                  onClick={() => onPlanVote(plan, "WITHDRAW")}
                  disabled={locked || busyId !== ""}
                  className={`flex h-7 flex-1 items-center justify-center gap-1 rounded-lg border text-[10px] transition disabled:opacity-30 ${
                    actionMeta.recommended === "WITHDRAW"
                      ? "border-sky-400/40 bg-sky-900/35 text-sky-100 shadow-[0_0_0_1px_rgba(56,189,248,0.24)]"
                      : "border-sky-500/20 bg-sky-950/20 text-sky-300 hover:bg-sky-500/40 hover:text-sky-100"
                  }`}
                >
                  <span className="h-3 w-3 rounded-full border border-current" />
                  {actionMeta.withdrawLabel}
                </button>
              </div>
            </div>
          );
        })}
            {planQueue.length > activePlanQueue.length ? (
              <p className="text-[10px] text-zinc-500">另有已完成计划隐藏，按需可展开详情。</p>
            ) : null}
          </div>
        </div>
      ) : null}

      {!manualOnly && decisionTraceIndex.items.length ? (
        <div className="mb-3 rounded-xl border border-zinc-700/20 bg-zinc-950/50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-zinc-300">计划溯源</p>
            <span className="text-[10px] text-zinc-500">
              计划溯源索引 · {Number(decisionTraceIndex.plan_count || 0)} 条 · {decisionTraceIndex.contract}
            </span>
          </div>
          <div className="space-y-1">
            {decisionTraceIndex.items.map((item) => {
              const route = String(item.routing || "system").trim().toUpperCase() || "SYSTEM";
              const routeLabel = route === "LLM" ? "模型预审" : route === "SYSTEM" ? "自动处理" : route === "USER" ? "手动入口" : route;
              return (
                <div
                  key={item.plan_id}
                  className={`rounded-lg border bg-zinc-900/60 px-2 py-1.5 text-[10px] text-zinc-300 ${
                    focusedDecisionId && Array.isArray(item.decision_ids) && item.decision_ids.includes(focusedDecisionId)
                      ? "border-emerald-500/35 shadow-[0_0_0_1px_rgba(16,185,129,0.22)]"
                      : "border-zinc-700/25"
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-zinc-200">
                      {item.anchor || "未命名计划"} · {item.plan_id || "unknown"}
                    </p>
                    <span className="rounded-full border border-zinc-700/30 px-1.5 py-0.5 text-[9px] text-zinc-200">
                      {routeLabel}
                    </span>
                  </div>
                  {planRoutingRationale(item).length ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">
                      {compactRoutingLines(planRoutingRationale(item))}
                    </p>
                  ) : null}
                  <p className="mt-1 text-zinc-500">
                    状态 {String(item.status || "pending")} · 依据决策 {Number(item.decision_count || item.decision_ids?.length || 0)} 条 · 跟踪条目 {Number(item.decision_trace_count || 0)}
                  </p>
                  {Array.isArray(item.decision_trace) && item.decision_trace.length ? (
                    <p className="mt-1 break-words text-zinc-400">
                      {formatPlanDecisionTrace(item.decision_trace).slice(0, 3).join(" · ")}
                    </p>
                  ) : null}
                  {(item.routing_reason || item.routing_policy) ? (
                    <p className="mt-1 text-[9px] text-zinc-500">
                      原因 {String(item.routing_reason || "") || String(item.routing_policy || "")} · policy {String(item.routing_policy || "").trim() || "-"}
                    </p>
                  ) : null}
                  {compactRoutingScores(item.routing_scores) ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">
                      路由候选分数：{compactRoutingScores(item.routing_scores)}
                    </p>
                  ) : null}
                  {item.llm_prompt_preview ? <p className="mt-1 text-cyan-200/80">该计划包含模型预审提示上下文</p> : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {!manualOnly && failedPlanQueue.length ? (
        <div className="mb-3 rounded-xl border border-rose-500/20 bg-rose-950/10 p-2">
          <p className="text-[10px] text-rose-200/85">最近异常计划（最近 4 条）</p>
          <div className="mt-2 space-y-1">
            {failedPlanQueue.slice(0, 4).map((plan) => {
              const statusTone = planStatusTone(plan.status);
              return (
                <div key={`failed_${plan.plan_id || plan.anchor || plan.updated_at}`} className="rounded-md border border-rose-500/15 px-2 py-1.5">
                  <div className="flex items-center justify-between text-[9px]">
                    <span className="text-zinc-200">{planDisplayName(plan)}</span>
                    <span className={`rounded-full border px-1.5 py-0.5 ${statusTone}`}>{plan.status || "FAILED"}</span>
                  </div>
                  <p className="mt-0.5 text-[9px] text-zinc-500">
                    PlanID {plan.plan_id || "N/A"} · 批次 {(plan.batch_ids || []).length}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

        {!manualOnly && terminalPlanQueue.length ? (
          <div className="mb-3 rounded-xl border border-zinc-700/20 bg-zinc-950/45 p-2">
            <p className="text-[10px] text-zinc-400">最近已完成计划（最近 4 条）</p>
            <div className="mt-2 space-y-1">
              {terminalPlanQueue.slice(0, 4).map((plan) => {
                const statusTone = planStatusTone(plan.status);
                return (
                  <div key={`history_${plan.plan_id || plan.anchor || plan.updated_at}`} className="rounded-md border border-zinc-700/20 px-2 py-1.5">
                    <div className="flex items-center justify-between text-[9px]">
                      <span className="text-zinc-300">{planDisplayName(plan)}</span>
                      <span className={`rounded-full border px-1.5 py-0.5 ${statusTone}`}>{plan.status || "DONE"}</span>
                    </div>
                    <p className="mt-0.5 text-[9px] text-zinc-500">
                      PlanID {plan.plan_id || "N/A"} · 批次 {(plan.batch_ids || []).length}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        ) : null}

        {!manualOnly ? (
          <div className="mb-3 grid gap-2 lg:grid-cols-2">
            {(["manual", "system", "llm", "auto"] as BucketKind[]).map((kind) => {
          const rule = arbitrationRule(kind);
          return (
            <div key={kind} className={`rounded-xl border px-3 py-2 text-[10px] leading-relaxed ${rule.accent}`}>
              <p className="tracking-[0.2em]">{kind.toUpperCase()}</p>
              <p className="mt-1 text-zinc-300">{rule.title}</p>
              <p className="mt-1 text-zinc-400">{rule.detail}</p>
            </div>
          );
            })}
          </div>
        ) : null}

      <div className={`grid gap-3 ${manualOnly ? "" : "lg:grid-cols-[1.25fr_0.95fr]"}`}>
        <V17_ManualDecisionSection
          decisionsLength={decisions.length}
          groupedManualDecisionBatches={groupedManualDecisionBatches}
          singleManualDecisionBatches={singleManualDecisionBatches}
          manualGroups={manualGroups}
          focusedDecisionId={focusedDecisionId}
          locked={locked}
          busyId={busyId}
          onVote={onVote}
          onBatchVote={onBatchVote}
          statusBadge={statusBadge}
          singleDecisionButtonLabel={singleDecisionButtonLabel}
          singleDecisionActionMeta={singleDecisionActionMeta}
          groupDecisionActionMeta={groupDecisionActionMeta}
          impactText={impactText}
          patternProfileSummary={patternProfileSummary}
          decisionFocusPreview={decisionFocusPreview}
          bucketReason={bucketReason}
          routingRationale={routingRationale}
          fluxRationale={fluxRationale}
          groupFluxRationale={groupFluxRationale}
          compactRoutingLines={compactRoutingLines}
          patternConfidenceChip={patternConfidenceChip}
          decisionReasonTags={decisionReasonTags}
          directionGroupLabel={directionGroupLabel}
          godRingBiasSummary={godRingBiasSummary}
          groupGodRingBiasSummary={groupGodRingBiasSummary}
        />

        {!manualOnly ? (
          <V17_AutoDecisionSection
            passiveLlmContextCount={passiveLlmContextCount}
            passiveLlmContextRows={passiveLlmContextRows}
            autoDecisionBatches={autoDecisionBatches}
            autoInboxRows={autoInboxRows}
            focusedDecisionId={focusedDecisionId}
            statusBadge={statusBadge}
            bucketAccessLabel={bucketAccessLabel}
            bucketReason={bucketReason}
            impactText={impactText}
            patternProfileSummary={patternProfileSummary}
            patternConfidenceChip={patternConfidenceChip}
            routingRationale={routingRationale}
            fluxRationale={fluxRationale}
            groupFluxRationale={groupFluxRationale}
            compactRoutingLines={compactRoutingLines}
            arbitrationTrace={arbitrationTrace}
            decisionFocusPreview={decisionFocusPreview}
            decisionReasonTags={decisionReasonTags}
            llmPolicyLabel={llmPolicyLabel}
            llmStateLabel={llmStateLabel}
            promptPreview={promptPreview}
            godRingBiasSummary={godRingBiasSummary}
            groupGodRingBiasSummary={groupGodRingBiasSummary}
          />
        ) : null}
      </div>
      {lockMessage ? (
        <p className={`mt-2 text-[11px] ${locked ? "text-amber-200/85" : "text-rose-200/85"}`}>
          {lockMessage}
        </p>
      ) : null}
      {hiddenCount > 0 ? (
        <p className="mt-2 text-[11px] text-zinc-500">另有 {hiddenCount} 条手动决策已接收但未展开，可提高当前快照的 `manual_inbox` 展示上限或继续收敛已采纳项。</p>
      ) : null}
    </section>
  );
}
