"use client";

import { useCallback, useMemo, useState } from "react";
import { Check, X } from "lucide-react";

import { t, translateTerm, type AppLanguage } from "@/lib/i18n";
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

function localText(lang: AppLanguage, zh: string, en: string, ko: string): string {
  return lang === "en" ? en : lang === "ko" ? ko : zh;
}

function impactText(decision: Decision, lang: AppLanguage): string {
  const impact = decision.physical_impact || {};
  const ratio = typeof impact.impact_ratio === "number" ? Math.abs(impact.impact_ratio) : 0;
  const level = Number(impact.intensity_level || 0);
  if (ratio > 0) return `${localText(lang, "位移", "Shift", "이동")} ${(ratio * 100).toFixed(0)}% · L${level || "?"}`;
  if (level > 0) return `${localText(lang, "烈度", "Intensity", "강도")} L${level}`;
  return localText(lang, "等待仲裁", "Awaiting arbitration", "중재 대기");
}

function bucketReason(kind: BucketKind, decision: Decision, lang: AppLanguage): string {
  const target = translateTerm(lang, String(decision.target_god || decision.physical_impact?.target_god || "").trim());
  if (kind === "manual") {
    return target ? localText(lang, `已有明确目标神 ${target}，适合由你手动裁定。`, `The target god ${target} is clear, so this is suitable for manual judgement.`, `대상 십신 ${target}이 명확하여 수동 판정에 적합합니다.`) : localText(lang, "保留给你手动定夺。", "Kept for your manual decision.", "수동 판단을 위해 남겨둡니다.");
  }
  if (kind === "auto") {
    return target ? localText(lang, `系统已围绕 ${target} 完成静默处理或归档。`, `The system has silently handled or archived this around ${target}.`, `시스템이 ${target} 기준으로 조용히 처리하거나 보관했습니다.`) : localText(lang, "系统已将这条信息静默处理，不再占用你的决策位。", "The system handled this silently, so it no longer occupies a decision slot.", "시스템이 이 항목을 조용히 처리하여 결정 슬롯을 차지하지 않습니다.");
  }
  if (kind === "system") {
    return target ? localText(lang, `目标神 ${target} 已明确，满足自动处理条件。`, `The target god ${target} is clear and meets auto-handling conditions.`, `대상 십신 ${target}이 명확하여 자동 처리 조건을 충족합니다.`) : localText(lang, "系统将继续观察并尝试自动收敛。", "The system will keep observing and try to converge automatically.", "시스템이 계속 관찰하며 자동 수렴을 시도합니다.");
  }
  return target ? localText(lang, `可为模型提供 ${target} 方向的叙事参考，但不建议直接点按。`, `Can provide narrative context toward ${target}, but is not recommended as a direct action.`, `${target} 방향의 서사 참고를 제공할 수 있지만 직접 액션으로 권장하지는 않습니다.`) : localText(lang, "更适合作为叙事上下文，而不是直接动作。", "Better used as narrative context than a direct action.", "직접 액션보다 서사 컨텍스트에 더 적합합니다.");
}

function bucketAccessLabel(kind: BucketKind, lang: AppLanguage): string {
  if (kind === "manual") return localText(lang, "可手动执行", "Manual action", "수동 실행 가능");
  if (kind === "auto") return localText(lang, "系统归档", "System archived", "시스템 보관");
  if (kind === "system") return localText(lang, "系统自动", "System auto", "시스템 자동");
  return localText(lang, "叙事参考", "Narrative reference", "서사 참고");
}

function statusBadge(kind: BucketKind, decision: Decision, lang: AppLanguage): { label: string; className: string } {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  if (kind === "manual") {
    if (level >= 3 || ratio >= 0.1) {
      return {
        label: localText(lang, "需立即裁定", "Needs immediate judgement", "즉시 판정 필요"),
        className: "border-rose-500/30 bg-rose-950/40 text-rose-100",
      };
    }
    return {
      label: localText(lang, "等待你确认", "Awaiting your confirmation", "확인 대기"),
      className: "border-violet-500/25 bg-violet-950/35 text-violet-100",
    };
  }
  if (kind === "auto") {
    if (decision.resolved_from_llm) {
      return {
        label: localText(lang, "已自动承接", "Auto accepted", "자동 수용됨"),
        className: "border-cyan-500/25 bg-cyan-950/35 text-cyan-100",
      };
    }
    return {
      label: localText(lang, "后台静默处理", "Silent backend handling", "백그라운드 조용한 처리"),
      className: "border-amber-500/25 bg-amber-950/35 text-amber-100",
    };
  }
  if (kind === "system") {
    if (level >= 3) {
      return {
        label: localText(lang, "拟自动收敛", "Planned auto convergence", "자동 수렴 예정"),
        className: "border-amber-500/30 bg-amber-950/40 text-amber-100",
      };
    }
    return {
      label: localText(lang, "系统观察中", "System observing", "시스템 관찰 중"),
      className: "border-zinc-500/20 bg-zinc-900/70 text-zinc-300",
    };
  }
  return {
    label: localText(lang, "将注入 Prompt", "Will inject into prompt", "프롬프트에 주입 예정"),
    className: "border-cyan-500/30 bg-cyan-950/35 text-cyan-100",
  };
}

function promptPreview(decision: Decision, lang: AppLanguage): string {
  const target = translateTerm(lang, String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim());
  const source = String(decision.source || "unknown").trim();
  const ratio = Math.abs(Number(decision.physical_impact?.impact_ratio || 0));
  const preview = ratio > 0
    ? localText(lang, `${target} 发生 ${(ratio * 100).toFixed(1)}% 相对位移`, `${target} has a ${(ratio * 100).toFixed(1)}% relative shift`, `${target}에 ${(ratio * 100).toFixed(1)}% 상대 이동 발생`)
    : localText(lang, `${target} 被纳入叙事仲裁参考`, `${target} is included as narrative arbitration context`, `${target}이 서사 중재 참고로 포함됨`);
  return localText(lang, `Prompt 将引用：${preview}，来源 ${source}。`, `Prompt will cite: ${preview}; source ${source}.`, `프롬프트가 인용합니다: ${preview}, 출처 ${source}.`);
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

function decisionFocusPreview(decision: Decision, lang: AppLanguage): string {
  const projectionText = compactProjection((decision as Decision & { cluster_projection?: Record<string, unknown> }).cluster_projection);
  const share = Number((decision as Decision & { projection_share?: number }).projection_share || 0);
  const target = translateTerm(lang, String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim());
  if (!projectionText && share <= 0) return "";
  return `${localText(lang, "主落点", "Primary target", "주 낙점")} ${target}${share > 0 ? ` · ${localText(lang, "占比", "share", "비중")} ${Math.round(share * 100)}%` : ""}${projectionText ? ` · ${projectionText}` : ""}`;
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

function patternConfidenceChip(decision: Decision, lang: AppLanguage): { label: string; className: string } | null {
  const score = Number(decision.pattern_confidence ?? NaN);
  if (!Number.isFinite(score) || score <= 0) return null;
  const label = String(decision.pattern_confidence_label || localText(lang, "格局置信", "Pattern confidence", "격국 신뢰도")).trim();
  return {
    label: `${label} ${Math.round(score * 100)}%`,
    className: patternConfidenceTone(score),
  };
}

function llmPolicyLabel(policy: string | undefined, lang: AppLanguage): string {
  if (policy === "auto_apply") return localText(lang, "可自动裁决", "Auto-judgement allowed", "자동 판정 가능");
  if (policy === "suggest_only") return localText(lang, "仅给建议", "Suggestion only", "제안만");
  return localText(lang, "仅作上下文", "Context only", "컨텍스트 전용");
}

function llmStateLabel(state: string | undefined, lang: AppLanguage): string {
  if (state === "collapsed_to_system") return localText(lang, "已转入自动处理", "Moved to auto handling", "자동 처리로 이동됨");
  if (state === "promoted_to_manual") return localText(lang, "已转入手动入口", "Moved to manual inbox", "수동 입구로 이동됨");
  if (state === "pending_context") return localText(lang, "等待模型消化", "Waiting for model digestion", "모델 소화 대기");
  return localText(lang, "处理中", "Processing", "처리 중");
}

function arbitrationRule(kind: BucketKind, lang: AppLanguage): { title: string; detail: string; accent: string } {
  if (kind === "manual") {
    return {
      title: localText(lang, "进入条件", "Entry Condition", "진입 조건"),
      detail: localText(lang, "存在明确目标神，且属于可执行动作，不是诊断态或纯说明态。", "There is a clear target god and the item is executable, not diagnostic or descriptive only.", "명확한 대상 십신이 있고, 진단/설명 전용이 아닌 실행 가능한 항목입니다."),
      accent: "text-violet-100 border-violet-500/20 bg-violet-950/20",
    };
  }
  if (kind === "auto") {
    return {
      title: localText(lang, "进入条件", "Entry Condition", "진입 조건"),
      detail: localText(lang, "系统可自行结算、自动归档，或仅作为提示词素材保留，不再要求你逐条确认。", "The system can settle, archive, or keep this as prompt material without asking you to confirm each item.", "시스템이 자체 결산/자동 보관하거나 프롬프트 소재로 보존할 수 있어 개별 확인이 필요 없습니다."),
      accent: "text-amber-100 border-amber-500/20 bg-amber-950/20",
    };
  }
  if (kind === "system") {
    return {
      title: localText(lang, "进入条件", "Entry Condition", "진입 조건"),
      detail: localText(lang, "烈度较高，且满足自动处理阈值，系统可先行收敛。", "Intensity is high enough and meets the auto-handling threshold, so the system can converge first.", "강도가 높고 자동 처리 임계값을 충족하여 시스템이 먼저 수렴할 수 있습니다."),
      accent: "text-amber-100 border-amber-500/20 bg-amber-950/20",
    };
  }
  return {
    title: localText(lang, "进入条件", "Entry Condition", "진입 조건"),
    detail: localText(lang, "更适合作为叙事依据、诊断上下文或提示词引用，而非直接动作。", "Better suited as narrative evidence, diagnostic context, or prompt reference than a direct action.", "직접 액션보다 서사 근거, 진단 컨텍스트, 프롬프트 참조에 더 적합합니다."),
    accent: "text-cyan-100 border-cyan-500/20 bg-cyan-950/20",
  };
}

function baseRoutingRationale(kind: BucketKind, decision: Decision, lang: AppLanguage): string[] {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  const target = translateTerm(lang, String(decision.target_god || impact.target_god || "").trim() || "未定目标");
  const source = String(decision.source_label || sourceLabel(decision)).trim() || "未知来源";
  const ratioText = ratio > 0 ? `${(ratio * 100).toFixed(1)}%` : localText(lang, "观察", "observe", "관찰");
  const lines: string[] = [
    `${localText(lang, "来源", "Source", "출처")} ${source}`,
    `${localText(lang, "目标", "Target", "대상")} ${target}`,
    `${localText(lang, "位移", "Shift", "이동")} ${ratioText} · ${localText(lang, "烈度", "Intensity", "강도")} L${level}`,
  ];
  if (kind === "manual") {
    lines.push(localText(lang, "规则：可人工确认且可回溯", "Rule: manually confirmable and traceable", "규칙: 수동 확인 및 추적 가능"));
    if (level >= 3) lines.push(localText(lang, "触发阈值：烈度 >= 3", "Trigger threshold: intensity >= 3", "트리거 임계값: 강도 >= 3"));
    if (ratio >= 0.08) lines.push(localText(lang, "触发阈值：位移 >= 8%", "Trigger threshold: shift >= 8%", "트리거 임계값: 이동 >= 8%"));
    return lines;
  }
  if (kind === "auto" || kind === "system") {
    const rawPolicy = String((decision as Decision & { llm_resolution_policy?: string }).llm_resolution_policy || "").trim().toLowerCase();
    const state = String((decision as Decision & { llm_resolution_state?: string }).llm_resolution_state || "").trim().toLowerCase();
    if (rawPolicy) lines.push(`${localText(lang, "策略", "Policy", "전략")} ${llmPolicyLabel(rawPolicy, lang)}`);
    if (state && state !== "none") lines.push(`${localText(lang, "状态", "Status", "상태")} ${llmStateLabel(state, lang)}`);
    if (ratio > 0.02 && level >= 2) lines.push(localText(lang, "按规则自动收敛或归档", "Auto-converged or archived by rule", "규칙에 따라 자동 수렴 또는 보관"));
    return lines;
  }
  const rawPolicy = String((decision as Decision & { llm_resolution_policy?: string }).llm_resolution_policy || "").trim();
  if (rawPolicy) {
    lines.push(`${localText(lang, "叙事策略", "Narrative policy", "서사 전략")} ${llmPolicyLabel(rawPolicy, lang)}`);
  } else {
    lines.push(`${localText(lang, "叙事策略", "Narrative policy", "서사 전략")} ${llmPolicyLabel(undefined, lang)}`);
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
  lang: AppLanguage,
): string[] {
  const state = decisionFluxState(decision, effectScores, currentTargets);
  if (!state) return [];
  const target = translateTerm(lang, state.target);
  const lines = [
    `M3 ${target} · ${localText(lang, "流后", "post-flow", "흐름 후")} ${formatSigned(state.resolvedFlux)} · ${localText(lang, "张力", "tension", "장력")} ${state.tension.toFixed(2)} · ${localText(lang, "放大", "reinforce", "증폭")} ${state.reinforce.toFixed(2)} · ${localText(lang, "对抗", "contest", "대항")} ${state.contest.toFixed(2)}`,
  ];
  if (Math.abs(state.outNet) > 0.001 || state.outSupport > 0 || state.outResist > 0) {
    lines.push(
      `M3 ${localText(lang, "外推", "outbound", "외부 추정")} · ${localText(lang, "支撑", "support", "지지")} ${state.outSupport.toFixed(2)} / ${localText(lang, "压制", "resist", "압제")} ${state.outResist.toFixed(2)} / ${localText(lang, "净值", "net", "순값")} ${formatSigned(state.outNet)}`,
    );
  }
  return lines;
}

function decisionFluxHint(
  kind: BucketKind,
  decision: Decision,
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
  lang: AppLanguage,
): string[] {
  const state = decisionFluxState(decision, effectScores, currentTargets);
  if (!state) return [];
  const target = translateTerm(lang, state.target);
  if (kind === "manual") {
    if (state.tension >= 0.28 || state.contest >= 0.12) {
      return [localText(lang, `M3 判读：${target} 当前拉扯偏高，保留人工裁决更稳。`, `M3 reading: ${target} has high tension; manual judgement is steadier.`, `M3 판독: ${target}의 장력이 높아 수동 판정이 더 안정적입니다.`)];
    }
    if (Math.abs(state.resolvedFlux) >= 0.22 && state.reinforce >= 0.12) {
      return [localText(lang, `M3 判读：${target} 走势已较清晰，但仍建议人工收口确认。`, `M3 reading: ${target}'s trend is clearer, but manual closure is still recommended.`, `M3 판독: ${target}의 흐름은 비교적 명확하지만 수동 마무리 확인을 권장합니다.`)];
    }
    return [];
  }
  if (kind === "system" || kind === "auto") {
    if (state.reinforce >= 0.15 && state.tension < 0.28) {
      return [localText(lang, `M3 判读：${target} 同向放大明显、张力可控，适合自动收敛。`, `M3 reading: ${target} is reinforcing clearly with controlled tension, suitable for auto convergence.`, `M3 판독: ${target}은 동방향 증폭이 뚜렷하고 장력이 제어되어 자동 수렴에 적합합니다.`)];
    }
    if (state.tension >= 0.28) {
      return [localText(lang, `M3 判读：${target} 仍有明显拉扯，自动侧以归档/观察更稳。`, `M3 reading: ${target} still has clear tension; auto side should archive or observe.`, `M3 판독: ${target}에는 여전히 뚜렷한 장력이 있어 자동 측은 보관/관찰이 더 안정적입니다.`)];
    }
    return [];
  }
  if (state.tension >= 0.24 || state.contest >= 0.1) {
    return [localText(lang, `M3 判读：${target} 存在争执与解释空间，适合交给 LLM。`, `M3 reading: ${target} has contest and interpretive room, suitable for LLM review.`, `M3 판독: ${target}에는 다툼과 해석 여지가 있어 LLM 검토에 적합합니다.`)];
  }
  return [localText(lang, `M3 判读：${target} 张力较低，更适合作为提示词素材。`, `M3 reading: ${target} has low tension and is better as prompt material.`, `M3 판독: ${target}은 장력이 낮아 프롬프트 소재에 더 적합합니다.`)];
}

function groupFluxSummaryLines(
  decisions: Decision[],
  effectScores: Record<string, unknown>,
  currentTargets: Record<string, unknown>,
  lang: AppLanguage,
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
        `${translateTerm(lang, item.target)} ${localText(lang, "张力", "tension", "장력")} ${item.tension.toFixed(2)} / ${localText(lang, "放大", "reinforce", "증폭")} ${item.reinforce.toFixed(2)} / ${localText(lang, "流后", "post-flow", "흐름 후")} ${formatSigned(item.resolvedFlux)}`,
    )
    .join(" · ");
  const lines = [`M3 ${localText(lang, "实时场", "live field", "실시간 장")}：${summary}`];
  const dominant = states[0];
  if (dominant && dominant.tension >= 0.28) {
    lines.push(localText(lang, `M3 判读：${translateTerm(lang, dominant.target)} 是本组的主要拉扯点，建议联动观察。`, `M3 reading: ${translateTerm(lang, dominant.target)} is the main tension point in this group; linked observation is recommended.`, `M3 판독: ${translateTerm(lang, dominant.target)}이 이 그룹의 주요 장력 지점이므로 연동 관찰을 권장합니다.`));
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

function actionMetaFromFluxState(state: FluxStateRow | null, count = 1, lang: AppLanguage = "zh"): DecisionActionMeta {
  const suffix = count > 1 ? ` (${count})` : "";
  if (!state?.target) {
    return {
      label: count > 1 ? `${localText(lang, "批量处理本组", "Process this group", "이 그룹 일괄 처리")}${suffix}` : localText(lang, "处理", "Process", "처리"),
      hint: "",
    };
  }
  const target = translateTerm(lang, state.target);
  if (state.tension >= 0.28 || state.contest >= 0.12) {
    return {
      label: count > 1 ? `${localText(lang, "整组裁定", "Judge group", "그룹 판정")} ${target}${suffix}` : `${localText(lang, "人工裁定", "Manual judgement", "수동 판정")} ${target}`,
      hint: localText(lang, `${target} 当前拉扯偏高，建议先人工收口再放行。`, `${target} has high tension; close it manually before releasing.`, `${target}의 장력이 높아 먼저 수동으로 마무리한 뒤 진행하는 것이 좋습니다.`),
    };
  }
  if (state.reinforce >= 0.15 && state.resolvedFlux >= 0.18) {
    return {
      label: count > 1 ? `${localText(lang, "确认整组执行", "Confirm group execution", "그룹 실행 확인")}${suffix}` : `${localText(lang, "确认执行", "Confirm execution", "실행 확인")} ${target}`,
      hint: localText(lang, `${target} 同向放大清晰，可直接确认执行。`, `${target} is clearly reinforcing and can be confirmed directly.`, `${target}의 동방향 증폭이 명확하여 바로 실행 확인할 수 있습니다.`),
    };
  }
  if (state.resolvedFlux <= -0.18 || state.harm >= 0.22) {
    return {
      label: count > 1 ? `${localText(lang, "整组审定", "Review group", "그룹 심사")} ${target}${suffix}` : `${localText(lang, "审定", "Review", "심사")} ${target}`,
      hint: localText(lang, `${target} 当前净效偏负，建议谨慎确认。`, `${target} currently has negative net effect; confirm carefully.`, `${target}의 현재 순효과가 음수라 신중한 확인을 권장합니다.`),
    };
  }
  return {
    label: count > 1 ? `${localText(lang, "批量处理本组", "Process this group", "이 그룹 일괄 처리")}${suffix}` : `${localText(lang, "处理", "Process", "처리")} ${target}`,
    hint: localText(lang, `${target} 当前可进入常规处理路径。`, `${target} can enter the normal handling path.`, `${target}은 현재 일반 처리 경로에 들어갈 수 있습니다.`),
  };
}

function decisionReasonTags(kind: BucketKind, decision: Decision, lang: AppLanguage = "zh"): string[] {
  const impact = decision.physical_impact || {};
  const ratio = Math.abs(Number(impact.impact_ratio || 0));
  const level = Number(impact.intensity_level || 0);
  const target = String(decision.target_god || impact.target_god || "").trim();
  const tags: string[] = [];
  if (target) tags.push(`${localText(lang, "目标神", "target", "대상")}:${translateTerm(lang, target)}`);
  if (level > 0) tags.push(`${localText(lang, "烈度", "intensity", "강도")}:L${level}`);
  if (ratio > 0) tags.push(`${localText(lang, "位移", "shift", "이동")}:${(ratio * 100).toFixed(0)}%`);
  if (kind === "manual") tags.push(localText(lang, "人工裁决", "Manual judgement", "수동 판정"));
  if (kind === "auto") tags.push(localText(lang, "后台处理", "Backend handling", "백그라운드 처리"));
  if (kind === "system") tags.push(localText(lang, "自动收敛", "Auto convergence", "자동 수렴"));
  if (kind === "llm") tags.push(localText(lang, "叙事引用", "Narrative citation", "서사 인용"));
  return tags.slice(0, 4);
}

function arbitrationModeLabel(kind: BucketKind, lang: AppLanguage): string {
  if (kind === "manual") return localText(lang, "手动", "Manual", "수동");
  if (kind === "auto") return localText(lang, "自动", "Auto", "자동");
  if (kind === "system") return localText(lang, "自动", "Auto", "자동");
  return localText(lang, "叙事", "Narrative", "서사");
}

function arbitrationTrace(kind: BucketKind, decision: Decision, lang: AppLanguage): string {
  if (String(decision.arbitration_trace || "").trim()) {
    return String(decision.arbitration_trace || "").trim();
  }
  const impact = decision.physical_impact || {};
  const level = Number(impact.intensity_level || 0);
  const source = String(decision.source_label || "").trim() || sourceLabel(decision);
  const levelText = level > 0 ? `L${level}` : "L?";
  return `${source} -> ${levelText} -> ${arbitrationModeLabel(kind, lang)}`;
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

function formatPlanDecisionTrace(trace: PlanDecisionTrace[], lang: AppLanguage): string[] {
  if (!trace.length) return [];
  return trace
    .slice(0, 8)
    .map((item) => {
      const idx = typeof item.trace_index === "number" ? item.trace_index + 1 : null;
      const label = String(item.label || item.decision_id || localText(lang, "未命名", "Untitled", "이름 없음")).trim();
      const source = String(item.source || "unknown").trim();
      const target = translateTerm(lang, String(item.target_god || "未定目标").trim());
      const ratio = Number(item.impact_ratio || 0);
      const ratioText =
        ratio > 0 ? `↑${(ratio * 100).toFixed(1)}%` : ratio < 0 ? `↓${Math.abs(ratio * 100).toFixed(1)}%` : localText(lang, "观察", "observe", "관찰");
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
}, lang: AppLanguage): string[] {
  const route = String(plan.routing || "system").trim().toUpperCase() || "SYSTEM";
  const reason = String(plan.routing_reason || "").trim();
  const policy = String(plan.routing_policy || "").trim();
  const scores = compactRoutingScores(plan.routing_scores);
  const lines: string[] = [`${localText(lang, "路由通道", "Route channel", "라우팅 채널")} ${route}`];
  if (policy) lines.push(`${localText(lang, "策略", "Policy", "전략")} ${policy}`);
  if (reason) lines.push(`${localText(lang, "原因", "Reason", "사유")} ${reason}`);
  if (scores) lines.push(`${localText(lang, "候选分数", "Candidate scores", "후보 점수")} ${scores}`);
  const tension = asNumber(plan.routing_scores?.live_tension);
  const reinforce = asNumber(plan.routing_scores?.live_reinforce);
  const contest = asNumber(plan.routing_scores?.live_contest);
  if (tension > 0 || reinforce > 0 || contest > 0) {
    lines.push(`M3 ${localText(lang, "张力", "tension", "장력")} ${tension.toFixed(2)} · ${localText(lang, "放大", "reinforce", "증폭")} ${reinforce.toFixed(2)} · ${localText(lang, "对抗", "contest", "대항")} ${contest.toFixed(2)}`);
    if (route === "LLM" && (tension >= 0.24 || contest >= 0.1)) {
      lines.push(localText(lang, "M3 判读：当前目标争执偏高，模型预审更合适。", "M3 reading: the current target has high contest; model pre-review is more suitable.", "M3 판독: 현재 대상의 다툼이 높아 모델 사전 검토가 더 적합합니다."));
    } else if (route === "SYSTEM" && reinforce >= 0.15 && tension < 0.28) {
      lines.push(localText(lang, "M3 判读：同向放大清晰，可先走系统收敛。", "M3 reading: reinforcement is clear, so system convergence can go first.", "M3 판독: 동방향 증폭이 명확하여 시스템 수렴을 먼저 진행할 수 있습니다."));
    } else if (route === "USER" && tension >= 0.28) {
      lines.push(localText(lang, "M3 判读：张力偏高，保留人工确认更稳。", "M3 reading: tension is high, so manual confirmation is steadier.", "M3 판독: 장력이 높아 수동 확인이 더 안정적입니다."));
    }
  }
  if (plan.updated_at) lines.push(`${localText(lang, "更新时间", "Updated", "업데이트 시간")} ${String(plan.updated_at)}`);
  return lines;
}

function compactRoutingLines(lines: string[]): string {
  const safe = (lines || []).map((line) => String(line || "").trim()).filter(Boolean);
  return safe.join(" · ");
}

function derivePlanActionMeta(plan: {
  routing?: string;
  routing_scores?: Record<string, unknown>;
}, lang: AppLanguage): PlanActionMeta {
  const route = String(plan.routing || "system").trim().toLowerCase();
  const tension = asNumber(plan.routing_scores?.live_tension);
  const reinforce = asNumber(plan.routing_scores?.live_reinforce);
  const contest = asNumber(plan.routing_scores?.live_contest);
  if (route === "llm") {
    return {
      approveLabel: localText(lang, "提交模型预审", "Submit model pre-review", "모델 사전 검토 제출"),
      rejectLabel: localText(lang, "放弃预审", "Skip pre-review", "사전 검토 포기"),
      escalateLabel: localText(lang, "改走人工", "Switch to manual", "수동으로 전환"),
      withdrawLabel: localText(lang, "撤回计划", "Withdraw plan", "계획 철회"),
      recommended: "APPROVED",
      hint:
        tension >= 0.24 || contest >= 0.1
          ? localText(lang, "推荐动作：提交模型预审，当前争执较高，适合先让模型判读。", "Recommended: submit model pre-review; contest is high enough for the model to read first.", "추천 액션: 모델 사전 검토 제출. 현재 다툼이 높아 모델 판독이 먼저 적합합니다.")
          : localText(lang, "推荐动作：提交模型预审，当前更像解释型分歧。", "Recommended: submit model pre-review; this looks like an interpretive difference.", "추천 액션: 모델 사전 검토 제출. 현재는 해석형 분기처럼 보입니다."),
    };
  }
  if (route === "user") {
    return {
      approveLabel: tension >= 0.28 ? localText(lang, "确认人工裁定", "Confirm manual judgement", "수동 판정 확인") : localText(lang, "确认执行", "Confirm execution", "실행 확인"),
      rejectLabel: localText(lang, "驳回本计划", "Reject this plan", "이 계획 반려"),
      escalateLabel: localText(lang, "升级给模型", "Escalate to model", "모델로 승격"),
      withdrawLabel: localText(lang, "撤回计划", "Withdraw plan", "계획 철회"),
      recommended: "APPROVED",
      hint:
        tension >= 0.28
          ? localText(lang, "推荐动作：确认人工裁定，当前张力偏高，保留人为收口更稳。", "Recommended: confirm manual judgement; tension is high and human closure is steadier.", "추천 액션: 수동 판정 확인. 현재 장력이 높아 사람이 마무리하는 편이 더 안정적입니다.")
          : localText(lang, "推荐动作：确认执行，这组计划已适合你直接拍板。", "Recommended: confirm execution; this plan group is ready for your call.", "추천 액션: 실행 확인. 이 계획 묶음은 직접 결정하기에 적합합니다."),
    };
  }
  if (tension >= 0.28) {
    return {
      approveLabel: localText(lang, "仍按系统执行", "Still run by system", "그래도 시스템 실행"),
      rejectLabel: localText(lang, "阻止执行", "Block execution", "실행 차단"),
      escalateLabel: localText(lang, "改由人工裁决", "Switch to manual judgement", "수동 판정으로 전환"),
      withdrawLabel: localText(lang, "撤回计划", "Withdraw plan", "계획 철회"),
      recommended: "ESCALATE",
      hint: localText(lang, "推荐动作：改由人工裁决，当前张力偏高，不宜直接自动执行。", "Recommended: switch to manual judgement; tension is too high for direct auto execution.", "추천 액션: 수동 판정으로 전환. 현재 장력이 높아 바로 자동 실행하기 어렵습니다."),
    };
  }
  if (reinforce >= 0.15 && tension < 0.28) {
    return {
      approveLabel: localText(lang, "确认自动执行", "Confirm auto execution", "자동 실행 확인"),
      rejectLabel: localText(lang, "阻止执行", "Block execution", "실행 차단"),
      escalateLabel: localText(lang, "改走人工", "Switch to manual", "수동으로 전환"),
      withdrawLabel: localText(lang, "撤回计划", "Withdraw plan", "계획 철회"),
      recommended: "APPROVED",
      hint: localText(lang, "推荐动作：确认自动执行，同向放大清晰且张力可控。", "Recommended: confirm auto execution; reinforcement is clear and tension is controlled.", "추천 액션: 자동 실행 확인. 동방향 증폭이 명확하고 장력이 제어됩니다."),
    };
  }
  return {
    approveLabel: localText(lang, "确认系统处理", "Confirm system handling", "시스템 처리 확인"),
    rejectLabel: localText(lang, "否决本计划", "Reject this plan", "이 계획 부결"),
    escalateLabel: localText(lang, "升档人工", "Escalate to manual", "수동 승격"),
    withdrawLabel: localText(lang, "撤回计划", "Withdraw plan", "계획 철회"),
    recommended: contest >= 0.1 ? "ESCALATE" : "APPROVED",
    hint:
      contest >= 0.1
        ? localText(lang, "推荐动作：升档人工，当前仍有对抗残留。", "Recommended: escalate to manual; contest remains.", "추천 액션: 수동 승격. 현재 대항 잔여가 있습니다.")
        : localText(lang, "推荐动作：确认系统处理，当前可按常规路径推进。", "Recommended: confirm system handling; this can proceed normally.", "추천 액션: 시스템 처리 확인. 현재 일반 경로로 진행할 수 있습니다."),
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

function planDisplayName(plan: PlanQueueItem, lang: AppLanguage = "zh"): string {
  const action = String(plan.action || plan.meta?.action || "").trim();
  const anchor = String(plan.anchor || "").trim();
  const trace = Array.isArray(plan.meta?.decision_trace) ? (plan.meta?.decision_trace as PlanDecisionTrace[]) : [];
  const firstTraceLabel = String(trace[0]?.label || "").trim();
  if (anchor && anchor.toLowerCase() !== "manual") return anchor;
  if (action && action.toLowerCase() !== "plan_action") return action;
  if (firstTraceLabel) return firstTraceLabel;
  if (anchor) return anchor;
  return localText(lang, "未命名计划", "Untitled plan", "이름 없는 계획");
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
  const ui = (zh: string, en: string, ko: string) =>
    lang === "en" ? en : lang === "ko" ? ko : zh;

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
        target: String(raw?.target_god || batchDecisions[0]?.target_god || batchDecisions[0]?.physical_impact?.target_god || localText(lang, "未定目标", "Unspecified target", "미정 대상")).trim(),
        source_anchor: String(raw?.source_anchor || batchDecisions[0]?.source || batchDecisions[0]?.plugin_id || "").trim(),
        source_families: sourceFamilies,
        decisions: batchDecisions,
        decision_count: batchDecisions.length,
        net_impact_ratio: netImpactRatio,
        max_priority: Number(raw?.max_priority || 0),
        direction_key: String(raw?.direction_key || "").trim() || undefined,
        direction_label: String(raw?.direction_label || "").trim() || undefined,
        prompt_line: String(raw?.prompt_line || "").trim() || localText(lang, "自动批次已生成，可一次提交。", "Auto batch is ready and can be submitted together.", "자동 배치가 생성되어 한 번에 제출할 수 있습니다."),
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
  }, [batchRows, allDecisionIndex, adoptedIdSet, lang]);
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
        target: String(raw?.target_god || batchDecisions[0]?.target_god || batchDecisions[0]?.physical_impact?.target_god || localText(lang, "未定目标", "Unspecified target", "미정 대상")).trim(),
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
        prompt_line: String(raw?.prompt_line || "").trim() || localText(lang, "自动批次已生成，可用于系统审阅。", "Auto batch is ready for system review.", "자동 배치가 생성되어 시스템 검토에 사용할 수 있습니다."),
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
  }, [batchRows, allDecisionIndex, adoptedIdSet, lang]);

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
    (decision: Decision) => decisionFluxSummaryLines(decision, godRingEffectScores, knowledgeCurrentTargets, lang),
    [godRingEffectScores, knowledgeCurrentTargets, lang],
  );
  const singleDecisionActionMeta = useCallback(
    (decision: Decision) =>
      actionMetaFromFluxState(
        decisionFluxState(decision, godRingEffectScores, knowledgeCurrentTargets),
        1,
        lang,
      ),
    [godRingEffectScores, knowledgeCurrentTargets, lang],
  );
  const groupDecisionActionMeta = useCallback(
    (items: Decision[]) =>
      actionMetaFromFluxState(
        dominantFluxState(items, godRingEffectScores, knowledgeCurrentTargets),
        items.length,
        lang,
      ),
    [godRingEffectScores, knowledgeCurrentTargets, lang],
  );
  const groupFluxRationale = useCallback(
    (items: Decision[]) => groupFluxSummaryLines(items, godRingEffectScores, knowledgeCurrentTargets, lang),
    [godRingEffectScores, knowledgeCurrentTargets, lang],
  );
  const singleDecisionButtonLabel = useCallback(
    (decision: Decision) => singleDecisionActionMeta(decision).label,
    [singleDecisionActionMeta],
  );
  const routingRationale = useCallback(
    (kind: BucketKind, decision: Decision) => [
      ...baseRoutingRationale(kind, decision, lang),
      ...decisionFluxHint(kind, decision, godRingEffectScores, knowledgeCurrentTargets, lang),
    ],
    [godRingEffectScores, knowledgeCurrentTargets, lang],
  );
  const localizedStatusBadge = useCallback((kind: BucketKind, decision: Decision) => statusBadge(kind, decision, lang), [lang]);
  const localizedBucketAccessLabel = useCallback((kind: BucketKind) => bucketAccessLabel(kind, lang), [lang]);
  const localizedBucketReason = useCallback((kind: BucketKind, decision: Decision) => bucketReason(kind, decision, lang), [lang]);
  const localizedImpactText = useCallback((decision: Decision) => impactText(decision, lang), [lang]);
  const localizedDecisionFocusPreview = useCallback((decision: Decision) => decisionFocusPreview(decision, lang), [lang]);
  const localizedPatternConfidenceChip = useCallback((decision: Decision) => patternConfidenceChip(decision, lang), [lang]);
  const localizedLlmPolicyLabel = useCallback((policy: string | undefined) => llmPolicyLabel(policy, lang), [lang]);
  const localizedLlmStateLabel = useCallback((state: string | undefined) => llmStateLabel(state, lang), [lang]);
  const localizedPromptPreview = useCallback((decision: Decision) => promptPreview(decision, lang), [lang]);
  const localizedDecisionReasonTags = useCallback((kind: BucketKind, decision: Decision) => decisionReasonTags(kind, decision, lang), [lang]);
  const localizedArbitrationTrace = useCallback((kind: BucketKind, decision: Decision) => arbitrationTrace(kind, decision, lang), [lang]);
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
            {manualOnly ? t(lang, "decision.manual.header") : ui("手动入口 / 自动回执", "Manual Inbox / Auto Receipts", "수동 입구 / 자동 회신")}
            {!manualOnly && latestSnapshot?.payload?.decision_inbox_contract ? ` · ${latestSnapshot.payload.decision_inbox_contract}` : ""}
          </p>
        </div>

        {!manualOnly && conflictGraphSummary.conflict_count ? (
          <div className="mb-3 rounded-xl border border-zinc-700/20 bg-zinc-950/60 p-3">
            <p className="text-[11px] tracking-[0.22em] text-zinc-300">CLAIM CONFLICT GRAPH</p>
            <div className="mt-2 grid gap-2 text-[10px]">
              <p className="text-zinc-400">
                {ui("版本", "Version", "버전")} {String(conflictGraph.graph_version || "v17.claim_graph.1")} · {ui("冲突", "Conflicts", "충돌")} {Number(conflictGraphSummary.conflict_count || 0)} /
                {ui("开放", "Open", "열림")} {Number(conflictGraphSummary.open_conflict_count || 0)} / {ui("节点", "Nodes", "노드")} {Number(conflictGraphSummary.node_count || 0)}
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
                          {cid} · {String(row?.conflict_type || "conflict")} · {ui("严重度", "Severity", "심각도")} {String(row?.severity || "P3")}
                        </p>
                        <p className="text-zinc-400">
                          {ui("目标", "Target", "대상")} {translateTerm(lang, String(row?.target_god || "未定目标"))} · {ui("主裁", "Arbiter", "중재자")} {String(row?.recommended_arbiter || "system")} ·
                          {ui("状态", "Status", "상태")} {status}
                        </p>
                        <p className="mt-0.5 text-zinc-500">{String(row?.why_conflict || ui("待补充冲突原因", "Conflict reason pending", "충돌 사유 대기")).trim()}</p>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-zinc-500">{ui("已构建冲突图，但当前无冲突明细。", "The conflict graph is built, but no conflict details are present.", "충돌 그래프는 생성되었지만 현재 충돌 상세가 없습니다.")}</p>
              )}
            </div>
          </div>
        ) : null}
        <div className="flex items-center gap-2 text-[10px]">
          <span className="rounded-full border border-violet-500/25 bg-violet-900/20 px-2 py-1 text-violet-100">
            {ui("手动", "Manual", "수동")} {decisions.length}
          </span>
          {!manualOnly ? (
            <>
              <span className="rounded-full border border-amber-500/20 bg-amber-950/30 px-2 py-1 text-amber-100">
                {ui("自动", "Auto", "자동")} {autoInboxRows.length + autoDecisionBatches.length}
              </span>
              <span className="rounded-full border border-zinc-500/20 bg-zinc-900/20 px-2 py-1 text-zinc-100">
                Plan {planQueue.length}
              </span>
            </>
          ) : null}
          {focusedDecisionId ? (
            <span className="rounded-full border border-emerald-500/25 bg-emerald-950/20 px-2 py-1 text-emerald-200">
              {ui("聚焦", "Focused", "포커스")} {focusedDecisionId}
            </span>
          ) : null}
        </div>
      </div>

      {!manualOnly && activePlanQueue.length ? (
        <div className="mb-3 rounded-xl border border-zinc-700/25 bg-zinc-950/60 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-zinc-300">{ui("计划队列", "Plan Queue", "계획 큐")}</p>
            <span className="text-[10px] text-zinc-500">{ui("系统按计划批次推进，不再逐条串行处理", "The system advances by plan batches instead of serial single-item handling.", "시스템은 단건 직렬 처리 대신 계획 배치 단위로 진행합니다.")}</span>
          </div>
                <div className="space-y-2">
            {activePlanQueue.slice(0, 8).map((plan) => {
              const statusTone = planStatusTone(plan.status);
              const impacts = planImpactBriefs(plan.impact_summary);
              const llmReviewPrompt = String(plan.meta?.llm_review_prompt || "").trim();
              const routingLabel = compactRoutingLabel(plan.routing, lang);
              const routingReason = String(plan.routing_reason || (plan.meta?.routing_reason as string) || "").trim();
              const routingPolicy = String(plan.routing_policy || (plan.meta?.routing_policy as string) || "").trim();
              const claim = plan.routing_claim || (plan.meta?.routing_claim as PlanDecisionClaim | undefined);
              const routingRationaleLines = planRoutingRationale(plan, lang);
              const actionMeta = derivePlanActionMeta(plan, lang);
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
                      {planDisplayName(plan, lang)} · {plan.routing ? `${ui("策略", "Policy", "전략")} ${plan.routing}` : ui("未设置策略", "No policy set", "전략 미설정")}
                    </p>
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${statusTone}`}>{plan.status || "pending"}</span>
                  </div>
                  <p className="mt-1 break-words text-[10px] text-zinc-400">
                    PlanID {plan.plan_id || "N/A"} · {ui("批次", "Batches", "배치")} {(plan.batch_ids || []).length} {ui("个", "", "개")}
                  </p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${planRoutingTone(plan.routing)}`}>{routingLabel}</span>
                    <span className="rounded-full border border-zinc-500/20 px-1.5 py-0.5 text-[9px] text-zinc-200">
                      {ui("路由类型", "Route Type", "라우팅 유형")} {String(plan.routing || "system").trim().toUpperCase()}
                    </span>
                  </div>
                  <V17PlanRoutingClaim
                    routingLabel={routingLabel}
                    routingReason={routingReason}
                    routingPolicy={routingPolicy}
                    routingFeatures={plan.routing_features || (plan.meta?.routing_features as PlanDecisionRoutingFeatures | undefined)}
                    claim={claim}
                    lang={lang}
                  />
                  {routingRationaleLines.length ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">
                      {compactRoutingLines(routingRationaleLines)}
                    </p>
                  ) : null}
                  <p className="mt-1 text-[9px] text-sky-200/85">{actionMeta.hint}</p>
                  {impacts.length ? (
                    <p className="mt-1 text-[10px] text-zinc-300">
                      {ui("影响速览", "Impact Brief", "영향 요약")}：{impacts.join(" · ")}
                    </p>
                  ) : null}
                  {llmReviewPrompt ? (
                    <div className="mt-2 border-t border-zinc-700/20 pt-2">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-zinc-400">{ui("模型预审提示", "Model Pre-review Prompt", "모델 사전 검토 프롬프트")}</p>
                      <pre className="mt-1 max-h-28 overflow-auto whitespace-pre-wrap rounded-md border border-amber-500/20 bg-zinc-950/70 p-1.5 text-[9px] leading-tight text-amber-100">
                        {llmReviewPrompt}
                      </pre>
                    </div>
                  ) : null}
                  {Array.isArray(plan.meta?.decision_trace) &&
                  (plan.meta?.decision_trace as PlanDecisionTrace[]).length ? (
                    <div className="mt-2 border-t border-zinc-700/20 pt-2">
                      <p className="text-[9px] uppercase tracking-[0.12em] text-zinc-400">{ui("决策证据", "Decision Evidence", "결정 증거")}</p>
                      <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[9px] leading-tight text-zinc-300">
                        {formatPlanDecisionTrace(plan.meta?.decision_trace as PlanDecisionTrace[], lang).map((line) => (
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
              <p className="text-[10px] text-zinc-500">{ui("另有已完成计划隐藏，按需可展开详情。", "Additional completed plans are hidden; expand details when needed.", "완료된 계획 일부가 숨겨져 있습니다. 필요하면 상세를 펼치세요.")}</p>
            ) : null}
          </div>
        </div>
      ) : null}

      {!manualOnly && decisionTraceIndex.items.length ? (
        <div className="mb-3 rounded-xl border border-zinc-700/20 bg-zinc-950/50 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[11px] tracking-[0.22em] text-zinc-300">{ui("计划溯源", "Plan Trace", "계획 추적")}</p>
            <span className="text-[10px] text-zinc-500">
              {ui("计划溯源索引", "Plan trace index", "계획 추적 인덱스")} · {Number(decisionTraceIndex.plan_count || 0)} {ui("条", "rows", "건")} · {decisionTraceIndex.contract}
            </span>
          </div>
          <div className="space-y-1">
            {decisionTraceIndex.items.map((item) => {
              const route = String(item.routing || "system").trim().toUpperCase() || "SYSTEM";
              const routeLabel = route === "LLM" ? ui("模型预审", "Model pre-review", "모델 사전 검토") : route === "SYSTEM" ? ui("自动处理", "Auto handling", "자동 처리") : route === "USER" ? ui("手动入口", "Manual inbox", "수동 입구") : route;
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
                      {item.anchor || ui("未命名计划", "Untitled plan", "이름 없는 계획")} · {item.plan_id || "unknown"}
                    </p>
                    <span className="rounded-full border border-zinc-700/30 px-1.5 py-0.5 text-[9px] text-zinc-200">
                      {routeLabel}
                    </span>
                  </div>
                  {planRoutingRationale(item, lang).length ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">
                      {compactRoutingLines(planRoutingRationale(item, lang))}
                    </p>
                  ) : null}
                  <p className="mt-1 text-zinc-500">
                    {ui("状态", "Status", "상태")} {String(item.status || "pending")} · {ui("依据决策", "Source decisions", "근거 결정")} {Number(item.decision_count || item.decision_ids?.length || 0)} {ui("条", "rows", "건")} · {ui("跟踪条目", "Trace entries", "추적 항목")} {Number(item.decision_trace_count || 0)}
                  </p>
                  {Array.isArray(item.decision_trace) && item.decision_trace.length ? (
                    <p className="mt-1 break-words text-zinc-400">
                      {formatPlanDecisionTrace(item.decision_trace, lang).slice(0, 3).join(" · ")}
                    </p>
                  ) : null}
                  {(item.routing_reason || item.routing_policy) ? (
                    <p className="mt-1 text-[9px] text-zinc-500">
                      {ui("原因", "Reason", "사유")} {String(item.routing_reason || "") || String(item.routing_policy || "")} · policy {String(item.routing_policy || "").trim() || "-"}
                    </p>
                  ) : null}
                  {compactRoutingScores(item.routing_scores) ? (
                    <p className="mt-1 break-words text-[9px] text-zinc-500">
                      {ui("路由候选分数", "Route candidate scores", "라우팅 후보 점수")}：{compactRoutingScores(item.routing_scores)}
                    </p>
                  ) : null}
                  {item.llm_prompt_preview ? <p className="mt-1 text-cyan-200/80">{ui("该计划包含模型预审提示上下文", "This plan includes model pre-review prompt context", "이 계획에는 모델 사전 검토 프롬프트 컨텍스트가 포함됩니다.")}</p> : null}
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {!manualOnly && failedPlanQueue.length ? (
        <div className="mb-3 rounded-xl border border-rose-500/20 bg-rose-950/10 p-2">
          <p className="text-[10px] text-rose-200/85">{ui("最近异常计划（最近 4 条）", "Recent abnormal plans (last 4)", "최근 이상 계획(최근 4건)")}</p>
          <div className="mt-2 space-y-1">
            {failedPlanQueue.slice(0, 4).map((plan) => {
              const statusTone = planStatusTone(plan.status);
              return (
                <div key={`failed_${plan.plan_id || plan.anchor || plan.updated_at}`} className="rounded-md border border-rose-500/15 px-2 py-1.5">
                  <div className="flex items-center justify-between text-[9px]">
                    <span className="text-zinc-200">{planDisplayName(plan, lang)}</span>
                    <span className={`rounded-full border px-1.5 py-0.5 ${statusTone}`}>{plan.status || "FAILED"}</span>
                  </div>
                  <p className="mt-0.5 text-[9px] text-zinc-500">
                    PlanID {plan.plan_id || "N/A"} · {ui("批次", "Batches", "배치")} {(plan.batch_ids || []).length}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

        {!manualOnly && terminalPlanQueue.length ? (
          <div className="mb-3 rounded-xl border border-zinc-700/20 bg-zinc-950/45 p-2">
            <p className="text-[10px] text-zinc-400">{ui("最近已完成计划（最近 4 条）", "Recently completed plans (last 4)", "최근 완료 계획(최근 4건)")}</p>
            <div className="mt-2 space-y-1">
              {terminalPlanQueue.slice(0, 4).map((plan) => {
                const statusTone = planStatusTone(plan.status);
                return (
                  <div key={`history_${plan.plan_id || plan.anchor || plan.updated_at}`} className="rounded-md border border-zinc-700/20 px-2 py-1.5">
                    <div className="flex items-center justify-between text-[9px]">
                      <span className="text-zinc-300">{planDisplayName(plan, lang)}</span>
                      <span className={`rounded-full border px-1.5 py-0.5 ${statusTone}`}>{plan.status || "DONE"}</span>
                    </div>
                    <p className="mt-0.5 text-[9px] text-zinc-500">
                      PlanID {plan.plan_id || "N/A"} · {ui("批次", "Batches", "배치")} {(plan.batch_ids || []).length}
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
          const rule = arbitrationRule(kind, lang);
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
          statusBadge={localizedStatusBadge}
          singleDecisionButtonLabel={singleDecisionButtonLabel}
          singleDecisionActionMeta={singleDecisionActionMeta}
          groupDecisionActionMeta={groupDecisionActionMeta}
          impactText={localizedImpactText}
          patternProfileSummary={patternProfileSummary}
          decisionFocusPreview={localizedDecisionFocusPreview}
          bucketReason={localizedBucketReason}
          routingRationale={routingRationale}
          fluxRationale={fluxRationale}
          groupFluxRationale={groupFluxRationale}
          compactRoutingLines={compactRoutingLines}
          patternConfidenceChip={localizedPatternConfidenceChip}
          decisionReasonTags={localizedDecisionReasonTags}
          directionGroupLabel={directionGroupLabel}
          godRingBiasSummary={godRingBiasSummary}
          groupGodRingBiasSummary={groupGodRingBiasSummary}
          lang={lang}
        />

        {!manualOnly ? (
          <V17_AutoDecisionSection
            passiveLlmContextCount={passiveLlmContextCount}
            passiveLlmContextRows={passiveLlmContextRows}
            autoDecisionBatches={autoDecisionBatches}
            autoInboxRows={autoInboxRows}
            focusedDecisionId={focusedDecisionId}
            statusBadge={localizedStatusBadge}
            bucketAccessLabel={localizedBucketAccessLabel}
            bucketReason={localizedBucketReason}
            impactText={localizedImpactText}
            patternProfileSummary={patternProfileSummary}
            patternConfidenceChip={localizedPatternConfidenceChip}
            routingRationale={routingRationale}
            fluxRationale={fluxRationale}
            groupFluxRationale={groupFluxRationale}
            compactRoutingLines={compactRoutingLines}
            arbitrationTrace={localizedArbitrationTrace}
            decisionFocusPreview={localizedDecisionFocusPreview}
            decisionReasonTags={localizedDecisionReasonTags}
            llmPolicyLabel={localizedLlmPolicyLabel}
            llmStateLabel={localizedLlmStateLabel}
            promptPreview={localizedPromptPreview}
            godRingBiasSummary={godRingBiasSummary}
            groupGodRingBiasSummary={groupGodRingBiasSummary}
            lang={lang}
          />
        ) : null}
      </div>
      {lockMessage ? (
        <p className={`mt-2 text-[11px] ${locked ? "text-amber-200/85" : "text-rose-200/85"}`}>
          {lockMessage}
        </p>
      ) : null}
      {hiddenCount > 0 ? (
        <p className="mt-2 text-[11px] text-zinc-500">
          {ui(`另有 ${hiddenCount} 条手动决策已接收但未展开，可提高当前快照的 manual_inbox 展示上限或继续收敛已采纳项。`, `${hiddenCount} additional manual decisions were received but not expanded; raise the current snapshot manual_inbox display limit or continue converging adopted items.`, `추가 수동 결정 ${hiddenCount}건이 수신되었지만 펼쳐지지 않았습니다. 현재 스냅샷의 manual_inbox 표시 한도를 높이거나 채택 항목 수렴을 계속하세요.`)}
        </p>
      ) : null}
    </section>
  );
}
