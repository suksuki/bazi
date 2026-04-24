"use client";

import { type ReactNode, useCallback, useEffect, useState } from "react";
import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

import { V17_AppShell } from "@/components/V17_AppShell";
import { V17_AdminUsersPanel, type AdminAuthUser } from "@/components/V17_AdminUsersPanel";
import { V17_DecisionInbox } from "@/components/V17_DecisionInbox";
import { V17_GodRingExplainCard } from "@/components/V17_GodRingExplainCard";
import { V17_NatalInput } from "@/components/V17_NatalInput";
import { V17_PurpleVerdictCard } from "@/components/V17_PurpleVerdictCard";
import { V17_SixPillarsPanel } from "@/components/V17_SixPillarsPanel";
import { V17_SurfaceTabs } from "@/components/V17_SurfaceTabs";
import { V17_TracePanel } from "@/components/V17_TracePanel";
import type { OracleSurface } from "@/lib/accessControl";
import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";
import { ORACLE_FEATURE_MODULES, resolveFeatureTabs } from "@/lib/featureRegistry";
import { t } from "@/lib/i18n";
import { useOracleSession } from "@/hooks/useOracleSession";
import { useV17Runtime } from "@/hooks/useV17Runtime";
import { classicalPatternCatalog } from "@/types/classicalPatternCatalog";

type OracleSurfaceTab = OracleSurface;
type ContentSurfaceTab = Exclude<OracleSurfaceTab, "trace">;
type AuxiliarySectionKey = "structure" | "runtime" | "authority" | "patterns" | "collaboration";

function asLooseRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumberValue(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item || "").trim()).filter(Boolean) : [];
}

function topicHubTone(tone: "primary" | "stable" | "watch" | "soft" | "risk" | "muted"): string {
  if (tone === "primary") return "border-cyan-500/25 bg-cyan-950/25 text-cyan-50";
  if (tone === "stable") return "border-emerald-500/25 bg-emerald-950/20 text-emerald-50";
  if (tone === "watch") return "border-amber-500/25 bg-amber-950/20 text-amber-50";
  if (tone === "soft") return "border-fuchsia-500/25 bg-fuchsia-950/20 text-fuchsia-50";
  if (tone === "risk") return "border-rose-500/25 bg-rose-950/20 text-rose-50";
  return "border-zinc-800 bg-zinc-950/60 text-zinc-300";
}

function topicHubBadgeTone(tone: "primary" | "stable" | "watch" | "soft" | "risk" | "muted"): string {
  if (tone === "primary") return "border-cyan-500/25 bg-cyan-950/30 text-cyan-100";
  if (tone === "stable") return "border-emerald-500/25 bg-emerald-950/30 text-emerald-100";
  if (tone === "watch") return "border-amber-500/25 bg-amber-950/30 text-amber-100";
  if (tone === "soft") return "border-fuchsia-500/25 bg-fuchsia-950/30 text-fuchsia-100";
  if (tone === "risk") return "border-rose-500/25 bg-rose-950/30 text-rose-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

function patternConfidenceTone(score: number): string {
  if (score >= 0.82) return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (score >= 0.64) return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (score >= 0.48) return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function normalizePatternScope(scope: unknown): string {
  const key = String(scope || "").trim();
  if (key === "natal") return "原局";
  if (key === "luck_background") return "大运背景";
  if (key === "luck_only") return "大运触发";
  if (key === "flow_trigger") return "流年引动";
  if (key === "flow_only") return "流年主导";
  if (key === "runtime_pair") return "运流联动";
  if (key === "mixed") return "混合来源";
  return key || "来源待定";
}

function patternFamilyByName(name: string): string {
  return classicalPatternCatalog.find((item) => item.name === name)?.family || "格局候选";
}

type LivePatternCandidate = {
  key: string;
  name: string;
  family: string;
  confidence: number;
  scope: string;
  source: string;
  target: string;
  projectionText: string;
  profileText: string;
  manifestation: string;
  scopeWeights: Array<{ label: string; ratio: number }>;
  gate: string;
  gateReason: string;
  breakRisks: string[];
  statusLabel: string;
};

type TopicHubItem = {
  key: string;
  title: string;
  subtitle: string;
  status: string;
  tone: "primary" | "stable" | "watch" | "soft" | "risk" | "muted";
  details: string[];
  badges: string[];
};

function AuxiliarySection({
  title,
  subtitle,
  badge,
  open,
  onToggle,
  children,
}: {
  title: string;
  subtitle: string;
  badge?: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-cyan-500/18 bg-[linear-gradient(180deg,rgba(9,9,11,0.9),rgba(16,24,39,0.72))]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left transition hover:bg-cyan-950/10"
      >
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">{title}</p>
          <p className="mt-1 text-[11px] leading-5 text-zinc-400">{subtitle}</p>
        </div>
        <div className="flex items-center gap-2 pt-0.5">
          {badge ? (
            <span className="rounded-full border border-cyan-500/20 bg-cyan-950/30 px-2 py-1 text-[10px] text-cyan-100">
              {badge}
            </span>
          ) : null}
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 p-1.5 text-zinc-300">
            {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </span>
        </div>
      </button>
      {open ? <div className="border-t border-zinc-800/80 px-3 pb-3 pt-3">{children}</div> : null}
    </section>
  );
}

function normalizeManifestation(value: unknown): string {
  const key = String(value || "").trim();
  if (key === "manifested") return "成格";
  if (key === "supported") return "候选成立";
  if (key === "latent") return "潜势待成";
  if (key === "contested") return "受扰待核";
  return "观察中";
}

function patternStatusToneForRuntime(status: string): string {
  if (status === "成格") return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (status === "候选成立") return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (status === "受扰待核") return "border-rose-500/25 bg-rose-950/35 text-rose-100";
  if (status === "潜势待成") return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function normalizeScopeWeights(value: unknown): Array<{ label: string; ratio: number }> {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([key, raw]) => ({ label: normalizePatternScope(key), ratio: Number(raw || 0) }))
    .filter((item) => Number.isFinite(item.ratio) && item.ratio > 0)
    .sort((a, b) => b.ratio - a.ratio)
    .slice(0, 4);
}

function normalizePluginKey(value: unknown): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_");
}

function decisionPluginLabel(row: Record<string, unknown>): string {
  return String(row.plugin_label || row.plugin_name || row.label || row.source || row.plugin_id || "")
    .trim()
    .replace(/^classical\./, "");
}

function compactProjection(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return "";
      const entry = item as Record<string, unknown>;
      const label = String(entry.label || entry.name || entry.family || "").trim();
      const percent = Number(entry.percent ?? entry.ratio ?? 0);
      if (!label) return "";
      return `${label}${percent > 0 ? ` ${Math.round(percent)}%` : ""}`;
    })
    .filter(Boolean)
    .slice(0, 3)
    .join(" / ");
}

function deriveLivePatternCandidates(
  allRows: Array<Record<string, unknown>>,
  pluginClaims: Array<Record<string, unknown>>,
): LivePatternCandidate[] {
  const candidates = new Map<string, LivePatternCandidate>();
  let globalGate = "";
  let globalGateReason = "";
  let globalBreakRisks: string[] = [];
  const ingest = (row: Record<string, unknown>, source: string) => {
    const name = String(row.pattern_candidate || row.pattern_name || "").trim();
    if (!name) return;
    const confidenceRaw = row.pattern_confidence_percent ?? row.pattern_confidence ?? row.match_ratio ?? 0;
    let confidence = Number(confidenceRaw || 0);
    if (confidence > 1) confidence = confidence / 100;
    confidence = Number.isFinite(confidence) ? confidence : 0;
    const target = String(row.target_god || "").trim();
    const scope = String(row.pattern_scope_label || normalizePatternScope(row.pattern_scope)).trim();
    const projectionText = compactProjection(row.cluster_projection);
    const manifestation = normalizeManifestation(row.manifestation_state);
    const scopeWeights = normalizeScopeWeights(row.scope_weights);
    const profile = Array.isArray(row.pattern_profile) ? row.pattern_profile : [];
    const profileText = profile
      .slice(0, 3)
      .map((item) => {
        if (!item || typeof item !== "object") return "";
        const family = String((item as { family?: string }).family || "").trim();
        const percent = Number((item as { percent?: number }).percent || 0);
        if (!family) return "";
        return `${family}${percent > 0 ? ` ${Math.round(percent)}%` : ""}`;
      })
      .filter(Boolean)
      .join(" / ");
    const key = `${name}::${target || "na"}`;
    const current = candidates.get(key);
    const next: LivePatternCandidate = {
      key,
      name,
      family: patternFamilyByName(name),
      confidence,
      scope: scope || "来源待定",
      source,
      target: target || "未定目标",
      projectionText,
      profileText,
      manifestation,
      scopeWeights,
      gate: globalGate,
      gateReason: globalGateReason,
      breakRisks: globalBreakRisks,
      statusLabel: manifestation,
    };
    if (!current || next.confidence > current.confidence) {
      candidates.set(key, next);
      return;
    }
    if (current && !current.scopeWeights.length && scopeWeights.length) current.scopeWeights = scopeWeights;
    if (current && !current.profileText && profileText) current.profileText = profileText;
    if (current && !current.projectionText && projectionText) current.projectionText = projectionText;
    if (current && current.statusLabel === "观察中" && manifestation !== "观察中") current.statusLabel = manifestation;
  };

  for (const row of [...pluginClaims, ...allRows]) {
    const pluginId = String(row.plugin_id || row.source || "").trim();
    if (pluginId === "classical.pattern.formation_gate.v1") {
      globalGate = String(row.pattern_gate || "").trim();
      globalGateReason = String(row.pattern_gate_reason || "").trim();
    }
    if (pluginId === "classical.pattern.break_guard.v1") {
      globalBreakRisks = Array.isArray(row.pattern_break_risks)
        ? (row.pattern_break_risks as unknown[]).map((item) => String(item || "").trim()).filter(Boolean)
        : [];
    }
  }

  for (const row of pluginClaims) ingest(row, "claim");
  for (const row of allRows) ingest(row, "decision");

  return Array.from(candidates.values())
    .map((item) => {
      const statusLabel = item.breakRisks.length
        ? "受扰待核"
        : item.gate === "月令成格" || item.gate === "强轴成格" || item.gate === "双线成格"
          ? "成格"
          : item.manifestation;
      return { ...item, gate: globalGate, gateReason: globalGateReason, breakRisks: globalBreakRisks, statusLabel };
    })
    .sort((a, b) => b.confidence - a.confidence);
}

export default function OraclePage() {
  const router = useRouter();
  const { language, user, authLoading, logout, access, ui, term, termList } = useV17Runtime();
  const s = useOracleSession({ uiLanguage: language });
  const [focusedDecisionId, setFocusedDecisionId] = useState<string>("");
  const [activeSurfaceTab, setActiveSurfaceTab] = useState<OracleSurfaceTab>("core");
  const [lastContentSurfaceTab, setLastContentSurfaceTab] = useState<ContentSurfaceTab>("core");
  const [auxiliarySections, setAuxiliarySections] = useState<Record<AuxiliarySectionKey, boolean>>({
    structure: true,
    runtime: true,
    authority: false,
    patterns: false,
    collaboration: true,
  });
  const [authUsers, setAuthUsers] = useState<AdminAuthUser[]>([]);
  const [authUsersLoading, setAuthUsersLoading] = useState(false);
  const [authUsersMessage, setAuthUsersMessage] = useState("");

  const payload = (s.physicsSnapshot?.payload || {}) as Record<string, unknown>;
  const energyMeta = payload.energy_meta && typeof payload.energy_meta === "object"
    ? (payload.energy_meta as Record<string, unknown>)
    : {};
  const fourPillars =
    payload.four_pillars && typeof payload.four_pillars === "object"
      ? (payload.four_pillars as { year?: string; month?: string; day?: string; hour?: string })
      : undefined;
  const luckPillarSnap = payload.luck_pillar;
  const flowPillarSnap = payload.flow_pillar;
  const godRingInfo =
    payload.god_rings && typeof payload.god_rings === "object"
        ? (payload.god_rings as {
            god_of_use?: string[];
            god_of_taboo?: string[];
            tongguan_gods?: string[];
            source?: string;
            mode?: string;
            display_mode?: string;
          label_of_use?: string;
          label_of_taboo?: string;
          confidence?: number;
          core_path_count?: number;
          core_use_candidates?: Array<Record<string, unknown>>;
          core_taboo_candidates?: Array<Record<string, unknown>>;
          dual_role_candidates?: Array<Record<string, unknown>>;
          judgement_bias?: {
            use_bias?: Record<string, number>;
            taboo_bias?: Record<string, number>;
          };
          judgement_bias_entries?: Array<Record<string, unknown>>;
          judgement_bias_protocol?: Record<string, unknown>;
          blind_theme?: Record<string, unknown>;
          blind_bias?: Record<string, unknown>;
          blind_bias_protocol?: Record<string, unknown>;
          stage_bias?: Record<string, Record<string, number>>;
          stage_bias_protocol?: Record<string, unknown>;
          effect_scores?: Record<string, unknown>;
          core_graph_meta?: Record<string, unknown>;
          core_paths_preview?: Array<Record<string, unknown>>;
          positive_work?: Record<string, unknown>;
          negative_work?: Record<string, unknown>;
        })
      : undefined;
  const allRows = Array.isArray(payload.all_decisions) ? payload.all_decisions as Array<Record<string, unknown>> : [];
  const meta = payload.meta && typeof payload.meta === "object" ? payload.meta as Record<string, unknown> : {};
  const pluginClaims = Array.isArray(meta.plugin_claims) ? meta.plugin_claims as Array<Record<string, unknown>> : [];
  const relationFormationSummary = Array.isArray(energyMeta.relation_formation_summary)
    ? energyMeta.relation_formation_summary as Array<Record<string, unknown>>
    : [];
  const relationDynamicsSummary = Array.isArray(energyMeta.relation_dynamics_summary)
    ? energyMeta.relation_dynamics_summary as Array<Record<string, unknown>>
    : [];
  const climateField = energyMeta.climate_field && typeof energyMeta.climate_field === "object"
    ? energyMeta.climate_field as Record<string, unknown>
    : {};
  const climateModifierLayer = energyMeta.climate_modifier_layer && typeof energyMeta.climate_modifier_layer === "object"
    ? energyMeta.climate_modifier_layer as Record<string, unknown>
    : {};
  const climateTheme = meta.climate_theme && typeof meta.climate_theme === "object"
    ? meta.climate_theme as Record<string, unknown>
    : {};
  const xiangfaTheme = meta.xiangfa_theme && typeof meta.xiangfa_theme === "object"
    ? meta.xiangfa_theme as Record<string, unknown>
    : {};
  const livePatternCandidates = deriveLivePatternCandidates(allRows, pluginClaims);
  const patternLeader = livePatternCandidates[0];
  const patternRunners = livePatternCandidates.slice(1, 4);
  const activePatternScopes = Array.from(new Set(livePatternCandidates.map((item) => item.scope).filter(Boolean))).slice(0, 5);
  const leaderBreakRisks = patternLeader?.breakRisks || [];
  const patternJudgement = (() => {
    if (!patternLeader) {
      return ui(
        "当前盘面尚未形成稳定格局候选，系统仍在等待更多结构证据完成聚合。",
        "No stable pattern candidate has formed yet. The system is still waiting for more structural evidence.",
        "현재 명식에는 안정적인 격국 후보가 아직 형성되지 않았고, 시스템은 구조 증거가 더 모이기를 기다리고 있습니다.",
      );
    }
    const parts: string[] = [];
    const leadScope = term(patternLeader.scope || "来源待定");
    const leadStatus = term(patternLeader.statusLabel || "观察中");
    parts.push(
      ui(
        `当前以「${patternLeader.name}」为主格局，处于${leadStatus}态势`,
        `The leading pattern is ${term(patternLeader.name)}, currently in ${leadStatus} state`,
        `현재 주격은 ${term(patternLeader.name)}이며 ${leadStatus} 상태입니다`,
      ),
    );
    parts.push(
      ui(
        `主要证据来自${leadScope}`,
        `main evidence comes from ${leadScope}`,
        `주요 근거는 ${leadScope}에서 나옵니다`,
      ),
    );
    if (patternLeader.target && patternLeader.target !== "未定目标") {
      parts.push(
        ui(
          `主落点聚焦在${term(patternLeader.target)}`,
          `the main focus is ${term(patternLeader.target)}`,
          `주요 초점은 ${term(patternLeader.target)}입니다`,
        ),
      );
    }
    if (patternRunners.length) {
      const topRunners = patternRunners
        .slice(0, 2)
        .map((item) => `${term(item.name)} ${Math.round(item.confidence * 100)}%`)
        .join(language === "zh" ? "、" : " / ");
      if (topRunners) {
        parts.push(
          ui(
            `次格局候选包括${topRunners}`,
            `secondary candidates include ${topRunners}`,
            `보조 격국 후보는 ${topRunners}입니다`,
          ),
        );
      }
    }
    if (patternLeader.breakRisks.length) {
      parts.push(
        ui(
          `但当前受${patternLeader.breakRisks.slice(0, 2).map(term).join("、")}牵制，仍需继续核验是否破格`,
          `but current break risks ${patternLeader.breakRisks.slice(0, 2).map(term).join(" / ")} still need verification`,
          `다만 현재 ${patternLeader.breakRisks.slice(0, 2).map(term).join(" / ")}의 견제를 받아 파격 여부를 계속 확인해야 합니다`,
        ),
      );
    } else if (patternLeader.gateReason) {
      parts.push(patternLeader.gateReason);
    }
    return `${parts.join(language === "zh" ? "，" : ". ")}${language === "zh" ? "。" : "."}`;
  })();
  const useGods = asStringList(godRingInfo?.god_of_use);
  const tabooGods = asStringList(godRingInfo?.god_of_taboo);
  const tongguanGods = asStringList(godRingInfo?.tongguan_gods);
  const coreUseCandidates = Array.isArray(godRingInfo?.core_use_candidates) ? godRingInfo.core_use_candidates : [];
  const coreTabooCandidates = Array.isArray(godRingInfo?.core_taboo_candidates) ? godRingInfo.core_taboo_candidates : [];
  const blindTheme = asLooseRecord(godRingInfo?.blind_theme);
  const blindBiasProtocol = asLooseRecord(godRingInfo?.blind_bias_protocol);
  const blindBias = asLooseRecord(godRingInfo?.blind_bias);
  const blindUseBias = Object.keys(asLooseRecord(blindBias.use_bias));
  const blindTabooBias = Object.keys(asLooseRecord(blindBias.taboo_bias));
  const climateFavored = asStringList(climateTheme.favored_gods);
  const climateStrained = asStringList(climateTheme.strained_gods);
  const xiangfaSemantic = asStringList(xiangfaTheme.semantic_mapping);
  const xiangfaEvidence = asStringList(xiangfaTheme.evidence);
  const xiangfaTopics = asStringList(xiangfaTheme.source_topics);
  const riskRows = [...pluginClaims, ...allRows].filter((row) => {
    const key = normalizePluginKey(row.plugin_id || row.source);
    const label = decisionPluginLabel(row);
    return key.includes("risk") || key.includes("break_guard") || label.includes("风险") || label.includes("破格");
  });
  const judgementBiasEntries = Array.isArray(godRingInfo?.judgement_bias_entries)
    ? godRingInfo.judgement_bias_entries as Array<Record<string, unknown>>
    : [];
  const runtimeTenGodCount =
    payload.ten_gods_runtime && typeof payload.ten_gods_runtime === "object"
      ? Object.keys(payload.ten_gods_runtime as Record<string, unknown>).length
      : 0;
  const runtimeLedgerSignalCount =
    runtimeTenGodCount +
    judgementBiasEntries.length +
    pluginClaims.length +
    relationDynamicsSummary.length;
  const relationStressCount = relationDynamicsSummary.filter((row) => asNumberValue(row.stability_delta_ratio) < -0.05).length;
  const structureSignalCount =
    relationFormationSummary.length + relationDynamicsSummary.length + Object.keys(climateField).length;
  const authoritySignalCount = useGods.length + tabooGods.length + tongguanGods.length;
  const collaborationUserCount = authUsers.length;
  const topicHubItems: TopicHubItem[] = [
    {
      key: "ziping",
      title: ui("子平主裁决", "ZiPing Authority", "자평 주판정"),
      subtitle: ui(
        "月令 / 旺衰 / 调候桥 / 格局桥 / 体用",
        "Month order / balance / climate bridge / pattern bridge / body-use",
        "월령 / 왕쇠 / 조후 브리지 / 격국 브리지 / 체용",
      ),
      status: godRingInfo ? ui("硬约束已接通", "Hard constraint online", "하드 제약 연결됨") : ui("等待权威源", "Waiting for authority source", "권위 출처 대기"),
      tone: godRingInfo ? "primary" : "muted",
      details: [
        useGods.length ? `${ui("用神", "Useful gods", "용신")} ${termList(useGods.slice(0, 3)).join(" / ")}` : ui("用神待定", "Useful gods pending", "용신 대기"),
        tabooGods.length ? `${ui("忌神", "Taboo gods", "기신")} ${termList(tabooGods.slice(0, 3)).join(" / ")}` : ui("忌神待定", "Taboo gods pending", "기신 대기"),
        `${ui("候选", "Candidates", "후보")} ${coreUseCandidates.length + coreTabooCandidates.length}`,
      ],
      badges: [
        `${ui("置信", "Confidence", "신뢰도")} ${Math.round(asNumberValue(godRingInfo?.confidence) * 100)}%`,
        String(godRingInfo?.mode || godRingInfo?.display_mode || "authority"),
      ].filter(Boolean),
    },
    {
      key: "pattern",
      title: ui("格局专题", "Pattern Topic", "격국 주제"),
      subtitle: ui("古典格局 / 成局度 / 破格风险", "Classical pattern / formation / break risk", "고전 격국 / 성국도 / 파격 위험"),
      status: patternLeader ? `${term(patternLeader.name)} ${Math.round(patternLeader.confidence * 100)}%` : ui("暂无主格局", "No primary pattern", "주격 없음"),
      tone: patternLeader ? (leaderBreakRisks.length ? "watch" : "stable") : "muted",
      details: [
        patternLeader ? `${ui("状态", "State", "상태")} ${term(patternLeader.statusLabel)}` : ui("等待候选聚合", "Waiting for candidates", "후보 집계 대기"),
        patternLeader ? `${ui("来源", "Source", "출처")} ${term(patternLeader.scope)}` : `${ui("候选", "Candidates", "후보")} ${livePatternCandidates.length}`,
        leaderBreakRisks.length ? `${ui("风险", "Risk", "위험")} ${leaderBreakRisks.slice(0, 2).map(term).join(" / ")}` : ui("破格风险未显著", "No major break risk", "큰 파격 위험 없음"),
      ],
      badges: activePatternScopes.length ? activePatternScopes.map(term) : ["pattern"],
    },
    {
      key: "climate",
      title: ui("调候专题", "Climate Topic", "조후 주제"),
      subtitle: ui("寒热轴 / 燥湿轴 / 效率稳定修正", "Thermal axis / moisture axis / efficiency-stability modifier", "한열축 / 조습축 / 효율·안정 보정"),
      status: term(String(climateTheme.state || climateField.state || "调候观察")),
      tone: Object.keys(climateField).length || Object.keys(climateTheme).length ? "stable" : "muted",
      details: [
        `${ui("寒热", "Thermal", "한열")} ${asNumberValue(climateTheme.thermal_index ?? climateField.thermal_index).toFixed(2)}`,
        `${ui("燥湿", "Moisture", "조습")} ${asNumberValue(climateTheme.moisture_index ?? climateField.moisture_index).toFixed(2)}`,
        `${ui("张力", "Tension", "장력")} ${asNumberValue(climateTheme.climate_tension ?? climateField.climate_tension).toFixed(2)}`,
      ],
      badges: [
        ...climateFavored.slice(0, 2).map((god) => `${ui("顺", "Favors", "순응")} ${term(god)}`),
        ...climateStrained.slice(0, 2).map((god) => `${ui("压", "Strains", "압박")} ${term(god)}`),
      ].slice(0, 4),
    },
    {
      key: "blind",
      title: ui("盲派专题", "Blind-School Topic", "맹파 주제"),
      subtitle: ui("体用主线 / 家里家外 / 运行换挡", "Body-use route / inner-outer roles / runtime shift", "체용 주선 / 안팎 역할 / 운행 전환"),
      status: term(String(blindTheme.primary_route || "盲派未显性")),
      tone: Object.keys(blindTheme).length ? "soft" : "muted",
      details: [
        `${ui("体态", "Body mode", "체태")} ${term(String(blindTheme.body_mode || "未定"))}`,
        `${ui("桥接", "Bridge", "브리지")} ${String(blindBiasProtocol.authority_bridge_mode || "bias_only")}`,
        `${ui("推用/推忌", "Use/Taboo bias", "용/기신 편향")} ${blindUseBias.length}/${blindTabooBias.length}`,
      ],
      badges: ["bias-only", ...termList(asStringList(blindTheme.runtime_switches).slice(0, 2))],
    },
    {
      key: "xiangfa",
      title: ui("象法专题", "Image-Semantic Topic", "상법 주제"),
      subtitle: ui("语义映射 / 证据串 / 事件框架", "Semantic mapping / evidence chain / event framing", "의미 매핑 / 근거 사슬 / 사건 프레임"),
      status: xiangfaSemantic.length || xiangfaEvidence.length ? ui("semantic-only 已接通", "semantic-only online", "semantic-only 연결됨") : ui("语义等待", "Semantic pending", "의미 대기"),
      tone: xiangfaSemantic.length || xiangfaEvidence.length ? "soft" : "muted",
      details: [
        `${ui("语义", "Semantic", "의미")} ${xiangfaSemantic.length}`,
        `${ui("证据", "Evidence", "근거")} ${xiangfaEvidence.length}`,
        `${ui("主题", "Topics", "주제")} ${xiangfaTopics.length}`,
      ],
      badges: xiangfaTopics.length ? termList(xiangfaTopics.slice(0, 4)) : [ui("不入 bias", "No bias entry", "bias 미진입")],
    },
    {
      key: "risk",
      title: ui("风险专题", "Risk Topic", "위험 주제"),
      subtitle: ui("风险放大 / 破格提示 / 判定偏置", "Risk amplification / break warning / judgement bias", "위험 증폭 / 파격 경고 / 판정 편향"),
      status: riskRows.length || relationStressCount ? ui("风险链已观测", "Risk chain observed", "위험 체인 관측") : ui("无显著风险", "No major risk", "주요 위험 없음"),
      tone: riskRows.length || relationStressCount ? "risk" : "muted",
      details: [
        `${ui("风险来源", "Risk sources", "위험 출처")} ${riskRows.length}`,
        `${ui("判定偏置", "Judgement bias", "판정 편향")} ${judgementBiasEntries.length}`,
        `${ui("稳定承压", "Stability strain", "안정 압박")} ${relationStressCount}`,
      ],
      badges: riskRows.length ? Array.from(new Set(riskRows.map(decisionPluginLabel).filter(Boolean))).slice(0, 3) : ["risk guard"],
    },
  ];
  const auxiliarySignalCount =
    livePatternCandidates.length +
    relationFormationSummary.length +
    relationDynamicsSummary.length +
    topicHubItems.filter((item) => item.tone !== "muted").length;
  const traceSignalCount =
    s.traceHits.length +
    s.traceFacts.length +
    s.heartbeatHistory.length +
    (s.fullTrace ? 1 : 0);
  const canAccessAuxiliarySurface = access.canAccessOracleSurface("auxiliary");
  const canAccessTraceSurface = access.canAccessOracleSurface("trace");
  const canManageUsers = access.canManageUsers;
  const surfaceTabs = resolveFeatureTabs(ORACLE_FEATURE_MODULES, {
    language,
    access,
    context: {
      decisionCount: s.pendingDecisionWorkCount,
      auxiliarySignalCount,
      traceSignalCount,
    },
  });
  const toggleAuxiliarySection = (section: AuxiliarySectionKey) => {
    setAuxiliarySections((current) => ({
      ...current,
      [section]: !current[section],
    }));
  };

  const loadAuthUsers = useCallback(async () => {
    if (!canManageUsers) return;
    setAuthUsersLoading(true);
    setAuthUsersMessage("");
    try {
      const { data: payload, ok } = await requestJson<Record<string, unknown>>("/api/auth/users", noStoreInit());
      if (!ok) {
        throw new Error(String(payload.detail || ui("用户列表加载失败。", "Failed to load users.", "사용자 목록을 불러오지 못했습니다.")));
      }
      const rows = Array.isArray(payload.users) ? payload.users : [];
      setAuthUsers(
        rows.map((row) => {
          const item = asLooseRecord(row);
          return {
            id: Number(item.id || 0),
            username: String(item.username || "").trim(),
            display_name: String(item.display_name || "").trim(),
            email: String(item.email || "").trim(),
            role: (String(item.role || "user").trim().toLowerCase() as AdminAuthUser["role"]),
            is_active: Boolean(item.is_active),
            created_at: String(item.created_at || "").trim(),
            last_login_at: String(item.last_login_at || "").trim(),
            latest_ip_address: String(item.latest_ip_address || "").trim(),
            latest_user_agent: String(item.latest_user_agent || "").trim(),
            latest_seen_at: String(item.latest_seen_at || "").trim(),
          };
        }),
      );
    } catch (error) {
      setAuthUsersMessage(error instanceof Error ? error.message : ui("用户列表加载失败。", "Failed to load users.", "사용자 목록을 불러오지 못했습니다."));
    } finally {
      setAuthUsersLoading(false);
    }
  }, [canManageUsers, ui]);

  const updateAuthUserRole = useCallback(
    async (userId: number, role: AdminAuthUser["role"]) => {
      const { data: payload, ok } = await requestJson<Record<string, unknown>>(`/api/auth/users/${userId}/role`, jsonPostInit({ role }));
      if (!ok || payload.ok === false) {
        throw new Error(String(payload.detail || ui("角色更新失败。", "Failed to update role.", "역할을 업데이트하지 못했습니다.")));
      }
      setAuthUsersMessage(ui(`角色已更新为 ${role}。`, `Role updated to ${role}.`, `역할이 ${role}(으)로 변경되었습니다.`));
      await loadAuthUsers();
    },
    [loadAuthUsers, ui],
  );

  const verdictTriggerPrompt = ui(
    "请基于当前已通过的决策，生成新的八字断言。",
    "Generate a new BaZi verdict based on the currently approved decisions.",
    "현재 승인된 결정을 바탕으로 새로운 사주 단언을 생성하세요.",
  );

  const switchContentSurface = (tab: ContentSurfaceTab) => {
    if (tab === "auxiliary" && !canAccessAuxiliarySurface) return;
    setActiveSurfaceTab(tab);
    setLastContentSurfaceTab(tab);
    s.setTraceOpen(false);
  };

  const openTraceSurface = () => {
    if (!canAccessTraceSurface) return;
    setActiveSurfaceTab("trace");
    s.setTraceOpen(true);
  };

  const closeTraceSurface = () => {
    setActiveSurfaceTab(lastContentSurfaceTab);
    s.setTraceOpen(false);
  };

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (activeSurfaceTab === "trace" && !canAccessTraceSurface) {
      const fallbackTab: ContentSurfaceTab = canAccessAuxiliarySurface ? "auxiliary" : "core";
      setActiveSurfaceTab(fallbackTab);
      setLastContentSurfaceTab(fallbackTab);
      s.setTraceOpen(false);
      return;
    }
    if (activeSurfaceTab === "auxiliary" && !canAccessAuxiliarySurface) {
      setActiveSurfaceTab("core");
      setLastContentSurfaceTab("core");
      s.setTraceOpen(false);
    }
  }, [activeSurfaceTab, authLoading, canAccessAuxiliarySurface, canAccessTraceSurface, router, s, user]);

  useEffect(() => {
    if (!authLoading && user && canManageUsers) {
      void loadAuthUsers();
    }
  }, [authLoading, canManageUsers, loadAuthUsers, user]);

  async function handleLogout() {
    await logout();
    router.replace("/login");
    router.refresh();
  }

  if (authLoading || !user) {
    return (
      <V17_AppShell
        language={language}
        user={user}
        loading={authLoading}
        onLogout={() => void handleLogout()}
        maxWidthClassName="max-w-3xl"
      >
        {null}
      </V17_AppShell>
    );
  }

  return (
    <V17_AppShell
      language={language}
      user={user}
      loading={authLoading}
      running={s.running}
      onRetry={s.resetRun}
      onLogout={() => void handleLogout()}
    >
        {/* ── 排盘输入 ── */}
        <div className="relative">
          {s.running ? (
            <div className="absolute inset-0 z-20 animate-[fadeOut_280ms_ease-out_forwards] rounded-2xl bg-black/50 backdrop-blur-[1px]" />
          ) : null}
          {!s.running ? <V17_NatalInput onStart={s.startRun} lang={language} /> : null}
        </div>

        {/* ── 运行态主体 ── */}
        {s.running ? (
          <div className="min-h-[60vh]">
            <div className="w-full space-y-3">
              <V17_SurfaceTabs
                items={surfaceTabs}
                activeId={activeSurfaceTab}
                onChange={(tab) => {
                  if (tab === "trace") {
                    openTraceSurface();
                  } else {
                    switchContentSurface(tab);
                  }
                }}
              />

              {activeSurfaceTab === "core" ? (
                <>
                  <V17_SixPillarsPanel
                    fourPillars={fourPillars}
                    luckPillarFromServer={typeof luckPillarSnap === "string" ? luckPillarSnap : undefined}
                    flowPillarFromServer={typeof flowPillarSnap === "string" ? flowPillarSnap : undefined}
                    godRingInfo={godRingInfo}
                    tenGodDecomposition={
                      payload.ten_gods_decomposition_l0 && typeof payload.ten_gods_decomposition_l0 === "object"
                        ? (payload.ten_gods_decomposition_l0 as Record<
                            string,
                            {
                              manifest?: number;
                              root?: number;
                              momentum?: number;
                              momentum_month_order?: number;
                              momentum_stage?: number;
                              momentum_stage_lu?: number;
                              momentum_stage_blade?: number;
                              momentum_stage_general?: number;
                              momentum_structure?: number;
                              momentum_auxiliary?: number;
                              momentum_other?: number;
                              hidden?: number;
                              total?: number;
                            }
                          >)
                        : undefined
                    }
                    tenGodLedger={
                      payload.ten_gods_ledger && typeof payload.ten_gods_ledger === "object"
                        ? (payload.ten_gods_ledger as Record<string, Array<{ step?: string; reason?: string; delta?: number; val?: number }>>)
                        : undefined
                    }
                    climateField={climateField}
                    climateModifierLayer={climateModifierLayer}
                    climateTheme={climateTheme}
                    xiangfaTheme={xiangfaTheme}
                    patternLeader={
                      patternLeader
                        ? {
                            name: patternLeader.name,
                            confidence: patternLeader.confidence,
                            statusLabel: patternLeader.statusLabel,
                            scope: patternLeader.scope,
                          }
                        : undefined
                    }
                    projectionBridgeProtocol={
                      payload.projection_bridge_protocol && typeof payload.projection_bridge_protocol === "object"
                        ? (payload.projection_bridge_protocol as Record<string, unknown>)
                        : undefined
                    }
                    relationFormationSummary={relationFormationSummary}
                    relationDynamicsSummary={relationDynamicsSummary}
                    birthTimeISO={s.birthTimeISO}
                    gender={s.natalGender}
                    calendarType={s.natalCalendar}
                    lunarIsLeapMonth={s.lunarIsLeapMonth}
                    selectedYear={s.selectedLuckYear}
                    onYearChange={s.setSelectedLuckYear}
                    detailMode="core"
                    lang={language}
                  />
                  <V17_PurpleVerdictCard
                    frames={s.frames}
                    connectTickMs={s.connectTickMs}
                    running={s.running}
                    llmStatusText={s.llmStatusText}
                    llmStatusDetail={s.llmStatusDetail}
                    llmLifecyclePhase={s.llmLifecyclePhase}
                    lang={language}
                  />
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-2.5">
                    <p className="text-xs text-zinc-400">
                      {t(language, "oracle.core.decision_notice")}
                      {s.canAutoGenerateVerdict ? ` ${t(language, "oracle.core.ready_for_verdict")}` : ""}
                    </p>
                    <button
                      type="button"
                      onClick={() => s.triggerVerdict(verdictTriggerPrompt)}
                      className="inline-flex items-center gap-1 rounded-md border border-cyan-500/30 bg-cyan-950/25 px-2 py-1 text-xs text-cyan-100 hover:bg-cyan-900/35"
                    >
                      <Sparkles className="h-3.5 w-3.5" />
                      {t(language, "oracle.action.show_verdict")}
                    </button>
                  </div>
                  <V17_DecisionInbox
                    frames={s.frames}
                    adoptedIds={s.adoptedDecisions.map((x) => x.id).filter((id): id is string => !!id)}
                    focusedDecisionId={focusedDecisionId}
                    viewMode="manual_only"
                    locked={s.decisionInboxLocked}
                    lockMessage={s.decisionInboxLockMessage}
                    onAdopted={s.handleAdopted}
                    onAdoptedBatch={s.handleAdoptedBatch}
                    onPlanAction={s.handlePlanAction}
                    lang={language}
                  />
                  {!s.hasNarrative ? (
                    <p className="mt-3 text-xs text-violet-200/80">{t(language, "oracle.core.weaving")}</p>
                  ) : null}
                </>
              ) : activeSurfaceTab === "trace" ? (
                <>
                  <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/15 p-3 text-[12px] leading-6 text-cyan-50">
                    {t(language, "oracle.trace.notice")}
                  </div>
                  <V17_TracePanel
                    surfaceMode="tab"
                    contentMode="debug_only"
                    collapsed={false}
                    onToggle={closeTraceSurface}
                    focusedDecisionId={focusedDecisionId}
                    llmMeta={s.llmMeta}
                    llmLifecyclePhase={s.llmLifecyclePhase}
                    llmStatusText={s.llmStatusText}
                    llmStatusDetail={s.llmStatusDetail}
                    modelLabel={s.modelLabel}
                    connectTickMs={s.connectTickMs}
                    lastHeartbeatStep={s.lastHeartbeatStep}
                    heartbeatHistory={s.heartbeatHistory}
                    streamClosed={s.streamClosed}
                    fullTrace={s.fullTrace}
                    llmAuditSnapshot={s.llmAuditSnapshot}
                    latestNarrator={s.latestNarrator as { payload?: Record<string, unknown> } | undefined}
                    traceHits={s.traceHits}
                    traceFacts={s.traceFacts}
                    birthTimeISO={s.birthTimeISO}
                    natalGender={s.natalGender}
                    natalCalendar={s.natalCalendar}
                    selectedLuckYear={s.selectedLuckYear}
                    streamEndpoint={s.streamEndpoint}
                    streamBody={s.streamBody}
                    streamQuery={s.streamQuery}
                    physicsSnapshot={s.physicsSnapshot as { payload?: Record<string, unknown> } | undefined}
                  />
                  <div className="rounded-xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(8,47,73,0.28),rgba(9,9,11,0.84))] p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">{t(language, "oracle.trace.console.title")}</p>
                        <p className="mt-1 text-[12px] leading-6 text-cyan-50">
                          {t(language, "oracle.trace.console.desc")}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-1.5 text-[10px]">
                        <span className="rounded-full border border-cyan-500/25 bg-cyan-950/30 px-2 py-1 text-cyan-100">
                          {t(language, "oracle.trace.console.badge.backend")}
                        </span>
                        <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-2 py-1 text-zinc-200">
                          {t(language, "oracle.trace.console.badge.full")}
                        </span>
                      </div>
                    </div>
                  </div>
                  <V17_DecisionInbox
                    frames={s.frames}
                    adoptedIds={s.adoptedDecisions.map((x) => x.id).filter((id): id is string => !!id)}
                    focusedDecisionId={focusedDecisionId}
                    locked={s.decisionInboxLocked}
                    lockMessage={s.decisionInboxLockMessage}
                    onAdopted={s.handleAdopted}
                    onAdoptedBatch={s.handleAdoptedBatch}
                    onPlanAction={s.handlePlanAction}
                    lang={language}
                  />
                </>
              ) : (
                <>
                  <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/15 p-3 text-[12px] leading-6 text-cyan-50">
                    {t(language, "oracle.aux.notice")}
                  </div>
                  <div className="rounded-2xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.13),transparent_34%),linear-gradient(180deg,rgba(9,9,11,0.92),rgba(24,24,27,0.74))] p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-300">{t(language, "oracle.topic_hub.title")}</p>
                        <h2 className="mt-1 text-sm font-semibold text-zinc-100">{t(language, "oracle.topic_hub.heading")}</h2>
                        <p className="mt-1 max-w-2xl text-[11px] leading-5 text-zinc-400">
                          {t(language, "oracle.topic_hub.desc")}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-1.5 text-[10px]">
                        <span className="rounded-full border border-cyan-500/25 bg-cyan-950/25 px-2 py-1 text-cyan-100">
                          {t(language, "oracle.topic_hub.active")} {topicHubItems.filter((item) => item.tone !== "muted").length}
                        </span>
                        <span className="rounded-full border border-emerald-500/25 bg-emerald-950/25 px-2 py-1 text-emerald-100">
                          {t(language, "oracle.topic_hub.hard")}
                        </span>
                        <span className="rounded-full border border-fuchsia-500/25 bg-fuchsia-950/25 px-2 py-1 text-fuchsia-100">
                          {t(language, "oracle.topic_hub.soft")}
                        </span>
                      </div>
                    </div>
                    <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                      {topicHubItems.map((item) => (
                        <div key={item.key} className={`rounded-xl border p-3 ${topicHubTone(item.tone)}`}>
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="text-[12px] font-semibold">{item.title}</div>
                              <p className="mt-1 text-[10px] leading-4 text-zinc-400">{item.subtitle}</p>
                            </div>
                            <span className={`rounded-full border px-2 py-0.5 text-[9px] ${topicHubBadgeTone(item.tone)}`}>
                              {item.status}
                            </span>
                          </div>
                          <div className="mt-3 grid gap-1.5 text-[10px]">
                            {item.details.map((detail) => (
                              <div key={`${item.key}_${detail}`} className="rounded-lg border border-white/10 bg-black/20 px-2 py-1 text-zinc-300">
                                {detail}
                              </div>
                            ))}
                          </div>
                          {item.badges.length ? (
                            <div className="mt-3 flex flex-wrap gap-1.5">
                              {item.badges.slice(0, 4).map((badge) => (
                                <span key={`${item.key}_${badge}`} className={`rounded-full border px-2 py-0.5 text-[9px] ${topicHubBadgeTone(item.tone)}`}>
                                  {badge}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>
                  <AuxiliarySection
                    title={t(language, "oracle.section.structure.title")}
                    subtitle={t(language, "oracle.section.structure.subtitle")}
                    badge={`${structureSignalCount} ${ui("信号", "signals", "신호")}`}
                    open={auxiliarySections.structure}
                    onToggle={() => toggleAuxiliarySection("structure")}
                  >
                    <V17_SixPillarsPanel
                      fourPillars={fourPillars}
                      luckPillarFromServer={typeof luckPillarSnap === "string" ? luckPillarSnap : undefined}
                      flowPillarFromServer={typeof flowPillarSnap === "string" ? flowPillarSnap : undefined}
                      godRingInfo={godRingInfo}
                      tenGodDecomposition={
                        payload.ten_gods_decomposition_l0 && typeof payload.ten_gods_decomposition_l0 === "object"
                          ? (payload.ten_gods_decomposition_l0 as Record<
                              string,
                              {
                                manifest?: number;
                                root?: number;
                                momentum?: number;
                                momentum_month_order?: number;
                                momentum_stage?: number;
                                momentum_stage_lu?: number;
                                momentum_stage_blade?: number;
                                momentum_stage_general?: number;
                                momentum_structure?: number;
                                momentum_auxiliary?: number;
                                momentum_other?: number;
                                hidden?: number;
                                total?: number;
                              }
                            >)
                          : undefined
                      }
                      tenGodLedger={
                        payload.ten_gods_ledger && typeof payload.ten_gods_ledger === "object"
                          ? (payload.ten_gods_ledger as Record<string, Array<{ step?: string; reason?: string; delta?: number; val?: number }>>)
                          : undefined
                      }
                      climateField={climateField}
                      climateModifierLayer={climateModifierLayer}
                      climateTheme={climateTheme}
                      xiangfaTheme={xiangfaTheme}
                      projectionBridgeProtocol={
                        payload.projection_bridge_protocol && typeof payload.projection_bridge_protocol === "object"
                          ? (payload.projection_bridge_protocol as Record<string, unknown>)
                          : undefined
                      }
                      relationFormationSummary={relationFormationSummary}
                      relationDynamicsSummary={relationDynamicsSummary}
                      birthTimeISO={s.birthTimeISO}
                      gender={s.natalGender}
                      calendarType={s.natalCalendar}
                      lunarIsLeapMonth={s.lunarIsLeapMonth}
                      selectedYear={s.selectedLuckYear}
                      onYearChange={s.setSelectedLuckYear}
                      detailMode="auxiliary"
                      lang={language}
                    />
                  </AuxiliarySection>

                  <AuxiliarySection
                    title={t(language, "oracle.section.runtime.title")}
                    subtitle={t(language, "oracle.section.runtime.subtitle")}
                    badge={`${runtimeLedgerSignalCount} ${ui("账本", "ledger", "장부")}`}
                    open={auxiliarySections.runtime}
                    onToggle={() => toggleAuxiliarySection("runtime")}
                  >
                    <V17_TracePanel
                      surfaceMode="tab"
                      contentMode="insight_only"
                      showChrome={false}
                      collapsed={false}
                      onToggle={() => {}}
                      focusedDecisionId={focusedDecisionId}
                      llmMeta={s.llmMeta}
                      llmLifecyclePhase={s.llmLifecyclePhase}
                      llmStatusText={s.llmStatusText}
                      llmStatusDetail={s.llmStatusDetail}
                      modelLabel={s.modelLabel}
                      connectTickMs={s.connectTickMs}
                      lastHeartbeatStep={s.lastHeartbeatStep}
                      heartbeatHistory={s.heartbeatHistory}
                      streamClosed={s.streamClosed}
                      fullTrace={s.fullTrace}
                      llmAuditSnapshot={s.llmAuditSnapshot}
                      latestNarrator={s.latestNarrator as { payload?: Record<string, unknown> } | undefined}
                      traceHits={s.traceHits}
                      traceFacts={s.traceFacts}
                      birthTimeISO={s.birthTimeISO}
                      natalGender={s.natalGender}
                      natalCalendar={s.natalCalendar}
                      selectedLuckYear={s.selectedLuckYear}
                      streamEndpoint={s.streamEndpoint}
                      streamBody={s.streamBody}
                      streamQuery={s.streamQuery}
                      physicsSnapshot={s.physicsSnapshot as { payload?: Record<string, unknown> } | undefined}
                      lang={language}
                    />
                  </AuxiliarySection>

                  <AuxiliarySection
                    title={t(language, "oracle.section.authority.title")}
                    subtitle={t(language, "oracle.section.authority.subtitle")}
                    badge={`${authoritySignalCount} ${ui("神", "gods", "신")}`}
                    open={auxiliarySections.authority}
                    onToggle={() => toggleAuxiliarySection("authority")}
                  >
                    <V17_GodRingExplainCard
                      godRings={godRingInfo}
                      focusedDecisionId={focusedDecisionId}
                      onFocusDecision={(decisionId) => {
                        setFocusedDecisionId(decisionId);
                        openTraceSurface();
                      }}
                      lang={language}
                    />
                  </AuxiliarySection>

                  <AuxiliarySection
                    title={t(language, "oracle.section.pattern.title")}
                    subtitle={t(language, "oracle.section.pattern.subtitle")}
                    badge={`${livePatternCandidates.length} ${ui("格局", "patterns", "격국")}`}
                    open={auxiliarySections.patterns}
                    onToggle={() => toggleAuxiliarySection("patterns")}
                  >
                    <div className="rounded-xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(12,74,110,0.32),rgba(9,9,11,0.76))] p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">
                            {ui("格局总览", "Pattern Overview", "격국 총람")}
                          </p>
                          <p className="mt-1 text-sm text-cyan-50">
                            {ui(
                              "当前盘面的主格局、次格局、动态来源、置信度与系统判读",
                              "Primary pattern, secondary candidates, runtime sources, confidence, and system reading.",
                              "현재 명식의 주격, 보조 격국, 동적 출처, 신뢰도와 시스템 판독입니다.",
                            )}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-1.5 text-[10px]">
                          <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">
                            {ui("候选", "Candidates", "후보")} {livePatternCandidates.length}
                          </span>
                          {activePatternScopes.map((scope) => (
                            <span key={`pattern_scope_${scope}`} className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">
                              {term(scope)}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="mt-3 rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">
                          {ui("系统判读", "System Reading", "시스템 판독")}
                        </p>
                        <p className="mt-2 text-[12px] leading-6 text-cyan-50">{patternJudgement}</p>
                      </div>

                      {patternLeader ? (
                        <div className="mt-3 grid gap-3 xl:grid-cols-[1.05fr_0.95fr]">
                          <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div>
                                <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">
                                  {ui("主格局", "Primary Pattern", "주격")}
                                </p>
                                <p className="mt-1 text-lg text-cyan-50">{term(patternLeader.name)}</p>
                                <p className="mt-1 text-[11px] text-zinc-400">{term(patternLeader.family)}</p>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                <span className={`rounded-full border px-2 py-1 text-[10px] ${patternStatusToneForRuntime(patternLeader.statusLabel)}`}>
                                  {term(patternLeader.statusLabel)}
                                </span>
                                <span className={`rounded-full border px-2 py-1 text-[10px] ${patternConfidenceTone(patternLeader.confidence)}`}>
                                  {ui("置信", "Confidence", "신뢰도")} {Math.round(patternLeader.confidence * 100)}%
                                </span>
                              </div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
                              <span className="rounded-full border border-cyan-500/20 bg-cyan-950/30 px-2 py-1 text-cyan-100">{term(patternLeader.scope)}</span>
                              <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-200">
                                {ui("主落点", "Focus", "초점")} {term(patternLeader.target)}
                              </span>
                              <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                {patternLeader.source === "claim" ? ui("来自 Claim 层", "From Claim layer", "Claim 계층") : ui("来自 Decision 层", "From Decision layer", "Decision 계층")}
                              </span>
                            </div>
                            {(patternLeader.gate || patternLeader.gateReason) ? (
                              <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/45 p-2">
                                <p className="text-[10px] uppercase tracking-[0.16em] text-emerald-300">
                                  {ui("成格门槛", "Formation Gate", "성격 관문")}
                                </p>
                                <p className="mt-1 text-[11px] text-emerald-100">
                                  {patternLeader.gate ? term(patternLeader.gate) : ui("候选审计", "Candidate audit", "후보 감사")}
                                </p>
                                {patternLeader.gateReason ? <p className="mt-1 text-[10px] leading-relaxed text-zinc-400">{patternLeader.gateReason}</p> : null}
                              </div>
                            ) : null}
                            {patternLeader.scopeWeights.length ? (
                              <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/45 p-2">
                                <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-300">
                                  {ui("来源证据", "Scope Evidence", "출처 근거")}
                                </p>
                                <div className="mt-2 grid gap-1.5">
                                  {patternLeader.scopeWeights.map((item) => (
                                    <div key={`${patternLeader.key}_${item.label}`} className="grid gap-1">
                                      <div className="flex items-center justify-between text-[10px]">
                                        <span className="text-zinc-300">{term(item.label)}</span>
                                        <span className="text-cyan-200">{Math.round(item.ratio * 100)}%</span>
                                      </div>
                                      <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                                        <div className="h-full rounded-full bg-[linear-gradient(90deg,rgba(34,211,238,0.95),rgba(45,212,191,0.95))]" style={{ width: `${Math.max(6, Math.round(item.ratio * 100))}%` }} />
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                            {patternLeader.profileText ? (
                              <p className="mt-3 text-[11px] leading-relaxed text-zinc-300">
                                {ui("家族混合", "Family mixture", "계열 혼합")}：<span className="text-cyan-100">{patternLeader.profileText}</span>
                              </p>
                            ) : null}
                            {patternLeader.projectionText ? (
                              <p className="mt-2 text-[11px] leading-relaxed text-zinc-400">
                                {ui("投影焦点", "Projection focus", "투영 초점")}：{patternLeader.projectionText}
                              </p>
                            ) : null}
                            {leaderBreakRisks.length ? (
                              <div className="mt-3 rounded-lg border border-rose-500/20 bg-rose-950/20 p-2">
                                <p className="text-[10px] uppercase tracking-[0.16em] text-rose-300">
                                  {ui("破格风险", "Break Risks", "파격 위험")}
                                </p>
                                <div className="mt-2 flex flex-wrap gap-1.5">
                                  {leaderBreakRisks.map((risk) => (
                                    <span key={`${patternLeader.key}_${risk}`} className="rounded-full border border-rose-500/20 bg-zinc-950/50 px-2 py-1 text-[10px] text-rose-100">
                                      {term(risk)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                          </div>

                          <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                            <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">
                              {ui("次格局", "Secondary Patterns", "보조 격국")}
                            </p>
                            <div className="mt-2 grid gap-2">
                              {patternRunners.length ? (
                                patternRunners.map((item) => (
                                  <div key={item.key} className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2">
                                    <div className="flex items-start justify-between gap-2">
                                      <div>
                                        <p className="text-[11px] text-cyan-50">{term(item.name)}</p>
                                        <p className="text-[9px] text-zinc-500">{term(item.family)} · {term(item.scope)}</p>
                                      </div>
                                      <div className="flex flex-wrap gap-1">
                                        <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternStatusToneForRuntime(item.statusLabel)}`}>
                                          {term(item.statusLabel)}
                                        </span>
                                        <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternConfidenceTone(item.confidence)}`}>
                                          {Math.round(item.confidence * 100)}%
                                        </span>
                                      </div>
                                    </div>
                                    <p className="mt-1 text-[10px] text-zinc-300">
                                      {ui("主落点", "Focus", "초점")} {term(item.target)}{item.profileText ? ` · ${item.profileText}` : ""}
                                    </p>
                                    {item.scopeWeights.length ? (
                                      <div className="mt-1 flex flex-wrap gap-1">
                                        {item.scopeWeights.map((scope) => (
                                          <span key={`${item.key}_${scope.label}`} className="rounded-full border border-zinc-700 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                                            {term(scope.label)} {Math.round(scope.ratio * 100)}%
                                          </span>
                                        ))}
                                      </div>
                                    ) : null}
                                    {item.projectionText ? <p className="mt-1 text-[9px] text-zinc-500">{item.projectionText}</p> : null}
                                  </div>
                                ))
                              ) : (
                                <div className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2 text-[10px] text-zinc-500">
                                  {ui(
                                    "当前尚未形成明确的次格局分层，系统只识别到一个主候选。",
                                    "No clear secondary pattern layer has formed yet; the system currently sees only one primary candidate.",
                                    "아직 명확한 보조 격국 층이 형성되지 않았고, 시스템은 현재 하나의 주 후보만 인식했습니다.",
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-3 rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3 text-[11px] text-zinc-400">
                          {ui(
                            "当前盘面还没有显式格局候选，系统会随着插件命中和 Claim 聚合继续补全。",
                            "No explicit pattern candidate has appeared yet; the system will keep completing this as plugins and claims aggregate.",
                            "현재 명식에는 명시적 격국 후보가 없으며, 플러그인 명중과 Claim 집계에 따라 계속 보완됩니다.",
                          )}
                        </div>
                      )}
                    </div>
                  </AuxiliarySection>

                  {canManageUsers && user.role === "manager" ? (
                    <AuxiliarySection
                      title={t(language, "oracle.section.collab.title")}
                      subtitle={t(language, "oracle.section.collab.subtitle")}
                      badge={collaborationUserCount ? `${collaborationUserCount} ${ui("用户", "users", "사용자")}` : "sync"}
                      open={auxiliarySections.collaboration}
                      onToggle={() => toggleAuxiliarySection("collaboration")}
                    >
                      <div className="rounded-2xl border border-amber-500/20 bg-amber-950/10 p-3">
                        {authUsersMessage ? (
                          <p className="mb-3 rounded-lg border border-amber-500/20 bg-black/20 px-3 py-2 text-[11px] text-amber-100">
                            {authUsersMessage}
                          </p>
                        ) : null}
                        <V17_AdminUsersPanel
                          users={authUsers}
                          loading={authUsersLoading}
                          onRefresh={() => void loadAuthUsers()}
                          onUpdateRole={updateAuthUserRole}
                          operatorRole={user.role}
                          compact
                          title={t(language, "oracle.section.collab.title")}
                          description={t(language, "oracle.collab.desc")}
                        />
                      </div>
                    </AuxiliarySection>
                  ) : null}
                </>
              )}
            </div>
          </div>
        ) : null}
    </V17_AppShell>
  );
}
