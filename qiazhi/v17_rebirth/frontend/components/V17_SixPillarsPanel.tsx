"use client";

import type { ReactNode } from "react";
import { t, translateTerm, translateTermList, type AppLanguage } from "@/lib/i18n";

type Pillar = { stem: string; branch: string };

type FourPillars = {
  year?: string;
  month?: string;
  day?: string;
  hour?: string;
};

type GodRingInfo = {
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
  dual_role_candidates?: Array<Record<string, unknown>>;
  judgement_bias?: {
    use_bias?: Record<string, number>;
    taboo_bias?: Record<string, number>;
  };
  judgement_bias_entries?: Array<Record<string, unknown>>;
  judgement_bias_protocol?: Record<string, unknown>;
  blind_theme?: Record<string, unknown>;
  blind_bias?: {
    use_bias?: Record<string, number>;
    taboo_bias?: Record<string, number>;
  };
  blind_bias_protocol?: Record<string, unknown>;
  stage_bias?: Record<string, Record<string, number>>;
  stage_bias_protocol?: Record<string, unknown>;
  effect_scores?: Record<string, unknown>;
};

type ClimateThemeInfo = {
  state?: string;
  thermal_index?: number;
  moisture_index?: number;
  climate_tension?: number;
  favored_gods?: string[];
  strained_gods?: string[];
  pattern_survival?: Array<Record<string, unknown>>;
  source_focus?: Array<Record<string, unknown>>;
  narrative_focus?: string[];
  prompt_digest?: string;
};

type XiangfaThemeInfo = {
  semantic_mapping?: string[];
  evidence?: string[];
  narrative_hint?: string[];
  event_framing?: string[];
  prompt_digest?: string;
  source_topics?: string[];
};

type TenGodDecompositionRow = {
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
};

type ProjectionBridgeProtocol = {
  tonggen_direction?: string;
  tougan_direction?: string;
  same_element_first?: boolean;
  polarity_second?: boolean;
  exact_root_support_factor?: number;
  cross_polarity_root_support_factor?: number;
  exact_exposed_hidden_gain?: number;
  same_element_visible_relief?: number;
  rooted_gain_cap?: number;
  single_pass_coupling?: boolean;
  recursive_feedback?: boolean;
  protocol?: string;
};

type ClimateFieldInfo = {
  state?: string;
  thermal_index?: number;
  moisture_index?: number;
  climate_tension?: number;
  heat?: number;
  cold?: number;
  humidity?: number;
  dryness?: number;
  source_by_scope?: Record<string, { thermal?: number; moisture?: number }>;
};

type ClimateModifierLayer = {
  ten_god_efficiency?: Record<string, number>;
  ten_god_stability?: Record<string, number>;
  yongshen_priority_delta?: Record<string, number>;
  pattern_survival_delta?: Record<string, number>;
};

type PatternLeaderInfo = {
  name?: string;
  confidence?: number;
  statusLabel?: string;
  scope?: string;
};

type LedgerEntry = {
  step?: string;
  reason?: string;
  delta?: number;
  val?: number;
};

type PractitionerChoiceKind = "pattern" | "use_god" | "taboo_god";
type PractitionerChoiceState = Partial<Record<PractitionerChoiceKind, string>>;

/** 解析后端/表单传来的出生时刻：无时区后缀时按本地墙钟理解，与 NatalInput 一致。 */
export function parseBirthTimeLocal(iso: string | undefined): Date | null {
  const raw = String(iso || "").trim();
  if (!raw) return null;
  if (raw.endsWith("Z") || /[+-]\d{2}:?\d{2}$/.test(raw)) {
    return new Date(raw);
  }
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?/.exec(raw);
  if (!m) return new Date(raw);
  return new Date(
    Number(m[1]),
    Number(m[2]) - 1,
    Number(m[3]),
    Number(m[4]),
    Number(m[5]),
    m[6] ? Number(m[6]) : 0,
    0,
  );
}

const STEM_META: Record<string, { element: string; yinYang: "阳" | "阴" }> = {
  甲: { element: "木", yinYang: "阳" },
  乙: { element: "木", yinYang: "阴" },
  丙: { element: "火", yinYang: "阳" },
  丁: { element: "火", yinYang: "阴" },
  戊: { element: "土", yinYang: "阳" },
  己: { element: "土", yinYang: "阴" },
  庚: { element: "金", yinYang: "阳" },
  辛: { element: "金", yinYang: "阴" },
  壬: { element: "水", yinYang: "阳" },
  癸: { element: "水", yinYang: "阴" },
};

const BRANCH_META: Record<string, { element: string; yinYang: "阳" | "阴" }> = {
  子: { element: "水", yinYang: "阳" },
  丑: { element: "土", yinYang: "阴" },
  寅: { element: "木", yinYang: "阳" },
  卯: { element: "木", yinYang: "阴" },
  辰: { element: "土", yinYang: "阳" },
  巳: { element: "火", yinYang: "阴" },
  午: { element: "火", yinYang: "阳" },
  未: { element: "土", yinYang: "阴" },
  申: { element: "金", yinYang: "阳" },
  酉: { element: "金", yinYang: "阴" },
  戌: { element: "土", yinYang: "阳" },
  亥: { element: "水", yinYang: "阴" },
};

const BRANCH_MAIN_HIDDEN_STEM: Record<string, string> = {
  子: "癸",
  丑: "己",
  寅: "甲",
  卯: "乙",
  辰: "戊",
  巳: "丙",
  午: "丁",
  未: "己",
  申: "庚",
  酉: "辛",
  戌: "戊",
  亥: "壬",
};

const BRANCH_HIDDEN_STEMS: Record<string, string[]> = {
  子: ["癸"],
  丑: ["己", "癸", "辛"],
  寅: ["甲", "丙", "戊"],
  卯: ["乙"],
  辰: ["戊", "乙", "癸"],
  巳: ["丙", "庚", "戊"],
  午: ["丁", "己"],
  未: ["己", "丁", "乙"],
  申: ["庚", "壬", "戊"],
  酉: ["辛"],
  戌: ["戊", "辛", "丁"],
  亥: ["壬", "甲"],
};

const ELEMENT_CYCLE = ["木", "火", "土", "金", "水"] as const;

function tenGodFromStems(dayMasterStem: string, targetStem: string): string {
  const dm = STEM_META[dayMasterStem];
  const tg = STEM_META[targetStem];
  if (!dm || !tg) return "";
  const dmIdx = ELEMENT_CYCLE.indexOf(dm.element as (typeof ELEMENT_CYCLE)[number]);
  const tgIdx = ELEMENT_CYCLE.indexOf(tg.element as (typeof ELEMENT_CYCLE)[number]);
  if (dmIdx < 0 || tgIdx < 0) return "";
  const samePolarity = dm.yinYang === tg.yinYang;
  if (dmIdx === tgIdx) return samePolarity ? "比肩" : "劫财";
  if (tgIdx === (dmIdx + 1) % 5) return samePolarity ? "食神" : "伤官";
  if (tgIdx === (dmIdx + 2) % 5) return samePolarity ? "偏财" : "正财";
  if (tgIdx === (dmIdx + 3) % 5) return samePolarity ? "七杀" : "正官";
  return samePolarity ? "偏印" : "正印";
}

type BranchLayerGod = {
  level: "主" | "中" | "余";
  stem: string;
  god: string;
};

function branchLayerGods(dayMasterStem: string, branch: string): BranchLayerGod[] {
  const stems = BRANCH_HIDDEN_STEMS[branch] || [];
  const labels: Array<"主" | "中" | "余"> = ["主", "中", "余"];
  return stems
    .slice(0, 3)
    .map((stem, idx) => {
      const god = tenGodFromStems(dayMasterStem, stem);
      if (!god) return null;
      return { level: labels[idx] || "余", stem, god };
    })
    .filter(Boolean) as BranchLayerGod[];
}

function colorForElement(el: string, yinYang: "阳" | "阴") {
  const palette: Record<string, string> = {
    木:
      yinYang === "阳"
        ? "text-lime-200 bg-gradient-to-br from-lime-500/45 to-lime-300/25 shadow-[0_0_14px_rgba(163,230,53,0.4)]"
        : "text-emerald-100 bg-gradient-to-br from-emerald-800/50 to-emerald-500/20 shadow-[0_0_12px_rgba(16,185,129,0.28)]",
    火:
      yinYang === "阳"
        ? "text-orange-50 bg-gradient-to-br from-orange-500/50 to-red-400/25 shadow-[0_0_14px_rgba(249,115,22,0.45)]"
        : "text-pink-100 bg-gradient-to-br from-rose-800/45 to-rose-500/20 shadow-[0_0_12px_rgba(244,63,94,0.28)]",
    土:
      yinYang === "阳"
        ? "text-amber-50 bg-gradient-to-br from-amber-500/45 to-yellow-300/25 shadow-[0_0_14px_rgba(245,158,11,0.4)]"
        : "text-orange-100 bg-gradient-to-br from-amber-800/45 to-amber-500/20 shadow-[0_0_12px_rgba(251,191,36,0.25)]",
    金:
      yinYang === "阳"
        ? "text-slate-100 bg-gradient-to-br from-slate-200/35 to-zinc-300/15 shadow-[0_0_14px_rgba(226,232,240,0.42)]"
        : "text-zinc-200 bg-gradient-to-br from-zinc-700/45 to-zinc-500/20 shadow-[0_0_12px_rgba(212,212,216,0.28)]",
    水:
      yinYang === "阳"
        ? "text-sky-50 bg-gradient-to-br from-sky-500/45 to-cyan-300/20 shadow-[0_0_14px_rgba(56,189,248,0.42)]"
        : "text-cyan-100 bg-gradient-to-br from-cyan-800/45 to-cyan-500/20 shadow-[0_0_12px_rgba(34,211,238,0.26)]",
  };
  return palette[el] || "text-zinc-200 bg-zinc-700/20";
}

function parsePillar(raw: string | undefined): Pillar {
  const text = String(raw || "").trim();
  if (text.length < 2) return { stem: "—", branch: "" };
  return { stem: text.slice(0, 1), branch: text.slice(1, 2) };
}

function topDecompositionRows(raw?: Record<string, TenGodDecompositionRow>) {
  return Object.entries(raw || {})
    .map(([god, row]) => ({
      god: String(god || "").trim(),
      manifest: Number(row?.manifest || 0),
      root: Number(row?.root || 0),
      momentum: Number(row?.momentum || 0),
      momentumMonthOrder: Number(row?.momentum_month_order || 0),
      momentumStage: Number(row?.momentum_stage || 0),
      momentumStageLu: Number(row?.momentum_stage_lu || 0),
      momentumStageBlade: Number(row?.momentum_stage_blade || 0),
      momentumStageGeneral: Number(row?.momentum_stage_general || 0),
      momentumStructure: Number(row?.momentum_structure || 0),
      momentumAuxiliary: Number(row?.momentum_auxiliary || 0),
      momentumOther: Number(row?.momentum_other || 0),
      hidden: Number(row?.hidden || 0),
      total: Number(row?.total || 0),
    }))
    .filter((row) => row.god && Number.isFinite(row.total) && row.total > 0)
    .sort((left, right) => right.total - left.total)
    .slice(0, 4);
}

function bridgeDirectionLabel(raw: string | undefined): string {
  const text = String(raw || "").trim();
  if (text === "stem<-branch_hidden") return "天干 <- 地支藏干";
  if (text === "branch_hidden->visible_stem") return "地支藏干 -> 天干";
  return text || "未定义";
}

function decompositionEvidenceTags(
  god: string,
  row: {
    manifest: number;
    root: number;
    hidden: number;
  },
  ledger?: Record<string, LedgerEntry[]>,
): string[] {
  const entries = Array.isArray(ledger?.[god]) ? ledger?.[god] || [] : [];
  const reasons = entries.map((entry) => String(entry?.reason || ""));
  const tags: string[] = [];

  if (reasons.some((reason) => reason.includes("本根×"))) {
    tags.push("本根通根");
  } else if (reasons.some((reason) => reason.includes("异阴阳根×"))) {
    tags.push("异阴阳通根");
  } else if (row.root > 0.01) {
    tags.push("有根支撑");
  }

  if (reasons.some((reason) => reason.includes("透干×1.2"))) {
    tags.push("精确透干");
  } else if (row.manifest > 0.01) {
    tags.push("天干明透");
  }

  if (row.hidden > 0.01 && row.manifest <= 0.01) {
    tags.push("潜藏未透");
  } else if (row.hidden > 0.01) {
    tags.push("兼带潜藏");
  }

  if (row.manifest > 0.01 && row.root <= 0.01) {
    tags.push("明透无根");
  }

  return [...new Set(tags)].slice(0, 3);
}

function num(value: unknown): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : 0;
}

function signed(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function asLooseRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function practitionerChoiceRows(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object" && !Array.isArray(item)))
    : [];
}

function choiceConfidencePercent(row: Record<string, unknown>): number {
  const direct = Number(row.confidence_percent);
  if (Number.isFinite(direct) && direct > 0) return Math.round(direct);
  const confidence = Number(row.confidence || 0);
  if (!Number.isFinite(confidence) || confidence <= 0) return 0;
  return Math.round(confidence <= 1 ? confidence * 100 : confidence);
}

function selectedPractitionerChoice(
  rows: Array<Record<string, unknown>>,
  selectedId: string | undefined,
): Record<string, unknown> | undefined {
  if (!rows.length) return undefined;
  if (selectedId) {
    const found = rows.find((row) => String(row.id || "").trim() === selectedId);
    if (found) return found;
  }
  return rows.find((row) => row.selected_by_system === true) || rows[0];
}

type RelationFormationRow = {
  formationLabel: string;
  formationPercent: number;
  familyFactor: number;
  status: string;
  projectionPreview: string[];
  summary: string;
};

type RelationDynamicsRow = {
  label: string;
  energyAxis: string;
  energyEffectRatio: number;
  stabilityDeltaRatio: number;
  freeEnergyLockRatio: number;
  pillars: string[];
  note: string;
};

function relationFormationTone(status: string): string {
  const text = String(status || "").trim();
  if (text === "强成局") return "border-emerald-500/25 bg-emerald-950/20 text-emerald-200";
  if (text === "受扰成局") return "border-amber-500/25 bg-amber-950/20 text-amber-200";
  if (text === "候选未全") return "border-fuchsia-500/25 bg-fuchsia-950/20 text-fuchsia-200";
  return "border-cyan-500/25 bg-cyan-950/20 text-cyan-200";
}

function relationFormationRows(value: unknown): RelationFormationRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = item && typeof item === "object" && !Array.isArray(item)
        ? (item as Record<string, unknown>)
        : {};
      return {
        formationLabel: String(row.formation_label || "").trim(),
        formationPercent: num(row.formation_percent),
        familyFactor: num(row.family_factor),
        status: String(row.status || "").trim(),
        projectionPreview: Array.isArray(row.projection_preview)
          ? row.projection_preview.map((entry) => String(entry || "").trim()).filter(Boolean)
          : [],
        summary: String(row.summary || "").trim(),
      };
    })
    .filter((row) => row.formationLabel && row.formationPercent > 0)
    .sort((left, right) => right.formationPercent - left.formationPercent)
    .slice(0, 4);
}

function relationDynamicsTone(axis: string, stabilityDeltaRatio: number): string {
  const text = String(axis || "").trim();
  if (text === "激发" || text === "解构") return "border-rose-500/25 bg-rose-950/20 text-rose-200";
  if (text === "内耗" || text === "暗损" || stabilityDeltaRatio < 0) return "border-amber-500/25 bg-amber-950/20 text-amber-200";
  if (text === "绑定" || text === "组织化" || text === "转化") return "border-cyan-500/25 bg-cyan-950/20 text-cyan-200";
  return "border-zinc-700 bg-zinc-950/60 text-zinc-300";
}

function pillarLabel(value: string): string {
  const map: Record<string, string> = {
    year: "年柱",
    month: "月柱",
    day: "日柱",
    hour: "时柱",
    luck: "大运",
    flow: "流年",
  };
  return map[value] || value || "未定";
}

function relationDynamicsRows(value: unknown): RelationDynamicsRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      const row = item && typeof item === "object" && !Array.isArray(item)
        ? (item as Record<string, unknown>)
        : {};
      return {
        label: String(row.label || "").trim(),
        energyAxis: String(row.energy_axis || "").trim(),
        energyEffectRatio: num(row.energy_effect_ratio),
        stabilityDeltaRatio: num(row.stability_delta_ratio),
        freeEnergyLockRatio: num(row.free_energy_lock_ratio),
        pillars: Array.isArray(row.pillars)
          ? row.pillars.map((entry) => String(entry || "").trim()).filter(Boolean)
          : [],
        note: String(row.note || "").trim(),
      };
    })
    .filter((row) => row.label)
    .sort(
      (left, right) =>
        Math.abs(right.stabilityDeltaRatio) + right.energyEffectRatio - (Math.abs(left.stabilityDeltaRatio) + left.energyEffectRatio),
    )
    .slice(0, 6);
}

function climateGodRows(value: unknown): Array<{ god: string; delta: number }> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([god, raw]) => ({ god: String(god || "").trim(), delta: num(raw) }))
    .filter((row) => row.god && Math.abs(row.delta) > 0.001)
    .sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta))
    .slice(0, 4);
}

function climatePatternRows(value: unknown): Array<{ label: string; delta: number; bucket: string }> {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        const row = item && typeof item === "object" && !Array.isArray(item)
          ? (item as Record<string, unknown>)
          : {};
        return {
          label: String(row.label || row.key || "").trim(),
          delta: num(row.delta),
          bucket: String(row.bucket || "").trim(),
        };
      })
      .filter((row) => row.label)
      .sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta))
      .slice(0, 4);
  }
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([label, raw]) => ({ label: String(label || "").trim(), delta: num(raw), bucket: "" }))
    .filter((row) => row.label && Math.abs(row.delta) > 0.001)
    .sort((left, right) => Math.abs(right.delta) - Math.abs(left.delta))
    .slice(0, 4);
}

function climateSourceRows(value: unknown): Array<{ scopeLabel: string; thermal: number; moisture: number; dominance: number }> {
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        const row = item && typeof item === "object" && !Array.isArray(item)
          ? (item as Record<string, unknown>)
          : {};
        const thermal = num(row.thermal);
        const moisture = num(row.moisture);
        return {
          scopeLabel: String(row.scope_label || row.scope || "").trim(),
          thermal,
          moisture,
          dominance: Number.isFinite(Number(row.dominance))
            ? num(row.dominance)
            : Math.abs(thermal) + Math.abs(moisture),
        };
      })
      .filter((row) => row.scopeLabel)
      .sort((left, right) => right.dominance - left.dominance)
      .slice(0, 4);
  }
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([scope, raw]) => {
      const row = raw && typeof raw === "object" && !Array.isArray(raw)
        ? (raw as Record<string, unknown>)
        : {};
      const thermal = num(row.thermal);
      const moisture = num(row.moisture);
      return {
        scopeLabel: pillarLabel(String(scope || "").trim()),
        thermal,
        moisture,
        dominance: Math.abs(thermal) + Math.abs(moisture),
      };
    })
    .filter((row) => row.scopeLabel)
    .sort((left, right) => right.dominance - left.dominance)
    .slice(0, 4);
}

function asEffectRow(value: unknown): Record<string, unknown> | undefined {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : undefined;
}

export function V17_SixPillarsPanel({
  fourPillars,
  luckPillarFromServer,
  flowPillarFromServer,
  godRingInfo,
  tenGodDecomposition,
  tenGodLedger,
  climateField,
  climateModifierLayer,
  climateTheme,
  xiangfaTheme,
  patternLeader,
  projectionBridgeProtocol,
  relationFormationSummary,
  relationDynamicsSummary,
  practitionerChoiceCandidates,
  practitionerChoices = {},
  canSelectPractitionerChoices = false,
  onPractitionerChoiceSelect,
  birthTimeISO,
  gender,
  calendarType,
  lunarIsLeapMonth,
  selectedYear,
  onYearChange,
  detailMode = "core",
  lang = "zh",
}: {
  fourPillars?: FourPillars;
  /** 后端 lunar_python 大运（与所选流年对应） */
  luckPillarFromServer?: string;
  flowPillarFromServer?: string;
  godRingInfo?: GodRingInfo;
  tenGodDecomposition?: Record<string, TenGodDecompositionRow>;
  tenGodLedger?: Record<string, LedgerEntry[]>;
  climateField?: ClimateFieldInfo;
  climateModifierLayer?: ClimateModifierLayer;
  climateTheme?: ClimateThemeInfo;
  xiangfaTheme?: XiangfaThemeInfo;
  patternLeader?: PatternLeaderInfo;
  projectionBridgeProtocol?: ProjectionBridgeProtocol;
  relationFormationSummary?: Array<Record<string, unknown>>;
  relationDynamicsSummary?: Array<Record<string, unknown>>;
  practitionerChoiceCandidates?: Record<string, unknown>;
  practitionerChoices?: PractitionerChoiceState;
  canSelectPractitionerChoices?: boolean;
  onPractitionerChoiceSelect?: (kind: PractitionerChoiceKind, id: string) => void;
  birthTimeISO?: string;
  gender?: "male" | "female";
  calendarType?: "solar" | "lunar";
  lunarIsLeapMonth?: boolean;
  selectedYear: number;
  onYearChange: (year: number) => void;
  detailMode?: "core" | "auxiliary";
  lang?: AppLanguage;
}) {
  const ui = (zh: string, en: string, ko: string) =>
    lang === "en" ? en : lang === "ko" ? ko : zh;
  const birth = parseBirthTimeLocal(birthTimeISO);

  const yearP = parsePillar(fourPillars?.year);
  const monthP = parsePillar(fourPillars?.month);
  const dayP = parsePillar(fourPillars?.day);
  const hourP = parsePillar(fourPillars?.hour);
  const luckP = parsePillar(luckPillarFromServer);
  const flowP = parsePillar(flowPillarFromServer);
  const authorityMode = String(godRingInfo?.display_mode || "").trim() === "authority";
  const patternLeaderRow = patternLeader || {};
  const relationRows = relationFormationRows(relationFormationSummary);
  const relationDynamics = relationDynamicsRows(relationDynamicsSummary);
  const useGods = Array.isArray(godRingInfo?.god_of_use)
    ? godRingInfo?.god_of_use.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const tabooGods = Array.isArray(godRingInfo?.god_of_taboo)
    ? godRingInfo?.god_of_taboo.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const tongguanGods = Array.isArray(godRingInfo?.tongguan_gods)
    ? godRingInfo?.tongguan_gods.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const choiceSelections = asLooseRecord(practitionerChoiceCandidates?.selections);
  const canChoosePractitionerCandidate = canSelectPractitionerChoices && Boolean(onPractitionerChoiceSelect);
  const practitionerChoiceRowsByKind: Record<PractitionerChoiceKind, Array<Record<string, unknown>>> = {
    pattern: practitionerChoiceRows(choiceSelections.pattern),
    use_god: practitionerChoiceRows(choiceSelections.use_god),
    taboo_god: practitionerChoiceRows(choiceSelections.taboo_god),
  };
  const selectedChoicesByKind: Partial<Record<PractitionerChoiceKind, Record<string, unknown> | undefined>> = {
    pattern: selectedPractitionerChoice(practitionerChoiceRowsByKind.pattern, practitionerChoices.pattern),
    use_god: selectedPractitionerChoice(practitionerChoiceRowsByKind.use_god, practitionerChoices.use_god),
    taboo_god: selectedPractitionerChoice(practitionerChoiceRowsByKind.taboo_god, practitionerChoices.taboo_god),
  };
  const activeUseGodName = String(selectedChoicesByKind.use_god?.name || selectedChoicesByKind.use_god?.label || useGods[0] || "").trim();
  const activeTabooGodName = String(selectedChoicesByKind.taboo_god?.name || selectedChoicesByKind.taboo_god?.label || tabooGods[0] || "").trim();
  const activePatternName = String(selectedChoicesByKind.pattern?.name || selectedChoicesByKind.pattern?.label || patternLeaderRow.name || "").trim();
  const confidence = Number(godRingInfo?.confidence || 0);
  const pathCount = Number(godRingInfo?.core_path_count || 0);
  const mode = String(godRingInfo?.mode || "").trim();
  const dualRoleCandidates = Array.isArray(godRingInfo?.dual_role_candidates)
    ? godRingInfo?.dual_role_candidates
        .map((item) => {
          const god = String((item as Record<string, unknown>)?.god || "").trim();
          const benefit = Number((item as Record<string, unknown>)?.benefit || 0);
          const risk = Number((item as Record<string, unknown>)?.risk || 0);
          if (!god) return "";
          return `${translateTerm(lang, god)} ${ui("利", "benefit", "이익")}${benefit.toFixed(2)} / ${ui("害", "risk", "위험")}${risk.toFixed(2)}`;
        })
        .filter(Boolean)
    : [];
  const effectScores = godRingInfo?.effect_scores || {};
  const decompositionRows = topDecompositionRows(tenGodDecomposition);
  const climateThemeRow = climateTheme || {};
  const xiangfaThemeRow = xiangfaTheme || {};
  const climateFieldRow = climateField || {};
  const climateModifierRow = climateModifierLayer || {};
  const climateFavored = Array.isArray(climateThemeRow.favored_gods)
    ? climateThemeRow.favored_gods.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const climateStrained = Array.isArray(climateThemeRow.strained_gods)
    ? climateThemeRow.strained_gods.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const climateFocus = climateSourceRows(climateThemeRow.source_focus || climateFieldRow.source_by_scope);
  const climatePattern = climatePatternRows(
    climateThemeRow.pattern_survival || climateModifierRow.pattern_survival_delta,
  );
  const climateEfficiency = climateGodRows(climateModifierRow.ten_god_efficiency);
  const climateStability = climateGodRows(climateModifierRow.ten_god_stability);
  const climatePriority = climateGodRows(climateModifierRow.yongshen_priority_delta);
  const xiangfaSemantic = Array.isArray(xiangfaThemeRow.semantic_mapping)
    ? xiangfaThemeRow.semantic_mapping.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const xiangfaEvidence = Array.isArray(xiangfaThemeRow.evidence)
    ? xiangfaThemeRow.evidence.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const xiangfaHints = Array.isArray(xiangfaThemeRow.narrative_hint)
    ? xiangfaThemeRow.narrative_hint.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const xiangfaFraming = Array.isArray(xiangfaThemeRow.event_framing)
    ? xiangfaThemeRow.event_framing.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const xiangfaSourceTopics = Array.isArray(xiangfaThemeRow.source_topics)
    ? xiangfaThemeRow.source_topics.map((item) => String(item || "").trim()).filter(Boolean)
    : [];
  const bridgeProtocol = projectionBridgeProtocol || {};
  const bridgeReady = Object.keys(bridgeProtocol).length > 0;
  const dayMasterStem = dayP.stem && dayP.stem !== "—" ? dayP.stem : "";
  const showCoreSections = detailMode === "core";
  const showAuxiliarySections = detailMode === "auxiliary";
  const buildAuthorityMetricChips = (god?: string) => {
    const row = asEffectRow(god ? effectScores[god] : undefined);
    if (!row) return [] as Array<{ label: string; tone: string }>;
    const resolvedFlux = num(row.resolved_utility_flux ?? row.resolved_utility);
    const tension = num(row.flux_tension_load);
    const reinforce = num(row.flux_reinforce_load);
    const chips: Array<{ label: string; tone: string }> = [];
    if (Math.abs(resolvedFlux) > 0.001) {
      chips.push({
        label: `${ui("净效", "Net", "순효")} ${signed(resolvedFlux)}`,
        tone: resolvedFlux >= 0 ? "text-emerald-100 border-emerald-400/20 bg-emerald-950/35" : "text-rose-100 border-rose-400/20 bg-rose-950/35",
      });
    }
    if (Math.abs(tension) > 0.001) {
      chips.push({
        label: `${ui("张力", "Tension", "장력")} ${tension.toFixed(2)}`,
        tone: "text-amber-100 border-amber-400/20 bg-amber-950/35",
      });
    }
    if (Math.abs(reinforce) > 0.001) {
      chips.push({
        label: `${ui("放大", "Amplify", "증폭")} ${reinforce.toFixed(2)}`,
        tone: "text-cyan-100 border-cyan-400/20 bg-cyan-950/35",
      });
    }
    return chips.slice(0, 3);
  };
  const useMetricChips = authorityMode ? buildAuthorityMetricChips(activeUseGodName) : [];
  const tabooMetricChips = authorityMode ? buildAuthorityMetricChips(activeTabooGodName) : [];
  const tongguanMetricChips = authorityMode ? buildAuthorityMetricChips(tongguanGods[0]) : [];
  const patternChoiceRow = selectedChoicesByKind.pattern;
  const patternMetricChips = activePatternName
    ? [
        {
          label: `${ui("置信", "Confidence", "신뢰도")} ${choiceConfidencePercent(patternChoiceRow || { confidence: patternLeaderRow.confidence || 0 })}%`,
          tone: "text-amber-100 border-amber-400/20 bg-amber-950/35",
        },
        ...(String(patternChoiceRow?.status || patternLeaderRow.statusLabel || "").trim()
          ? [
              {
                label: translateTerm(lang, String(patternChoiceRow?.status || patternLeaderRow.statusLabel || "")),
                tone: "text-zinc-100 border-zinc-700 bg-zinc-950/70",
              },
            ]
          : []),
        ...(String(patternChoiceRow?.scope || patternLeaderRow.scope || "").trim()
          ? [
              {
                label: translateTerm(lang, String(patternChoiceRow?.scope || patternLeaderRow.scope || "")),
                tone: "text-zinc-200 border-zinc-700 bg-black/20",
              },
            ]
          : []),
      ]
    : [];

  const rows: Array<{ label: string; pillar: Pillar }> = [
    { label: "年柱", pillar: yearP },
    { label: "月柱", pillar: monthP },
    { label: "日柱", pillar: dayP },
    { label: "时柱", pillar: hourP },
    { label: "大运", pillar: luckP },
    { label: "流年", pillar: flowP },
  ];
  const layerLevelLabel = (level: string) => {
    if (level === "主") return ui("主", "main", "주");
    if (level === "中") return ui("中", "middle", "중");
    return ui("余", "residual", "여");
  };

  const yearChoices = Array.from({ length: 111 }, (_, i) => selectedYear - 80 + i);

  const birthLabel =
    birth != null
      ? `${birth.getFullYear()}-${String(birth.getMonth() + 1).padStart(2, "0")}-${String(birth.getDate()).padStart(2, "0")} ${String(birth.getHours()).padStart(2, "0")}:${String(birth.getMinutes()).padStart(2, "0")}`
      : "—";
  const genderLabel =
    gender === "male" ? t(lang, "natal.gender.male") : gender === "female" ? t(lang, "natal.gender.female") : "—";
  const calendarLabel =
    calendarType === "lunar"
      ? `${t(lang, "natal.calendar.lunar")}${lunarIsLeapMonth ? ` · ${t(lang, "natal.leap_month.badge")}` : ""}`
      : calendarType === "solar"
        ? t(lang, "natal.calendar.solar")
        : "—";
  const practitionerChoiceCount =
    practitionerChoiceRowsByKind.pattern.length +
    practitionerChoiceRowsByKind.use_god.length +
    practitionerChoiceRowsByKind.taboo_god.length;
  const renderFallbackGodChips = (
    gods: string[],
    tone: "emerald" | "rose" | "cyan" | "amber",
    emptyLabel: string,
  ) => {
    const toneClass =
      tone === "emerald"
        ? "border-emerald-300/25 bg-emerald-950/35 text-emerald-100"
        : tone === "rose"
          ? "border-rose-300/25 bg-rose-950/35 text-rose-100"
          : tone === "cyan"
            ? "border-cyan-300/25 bg-cyan-950/35 text-cyan-100"
            : "border-amber-300/25 bg-amber-950/35 text-amber-100";
    if (authorityMode && gods.length) {
      return gods.map((god) => (
        <span key={god} className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${toneClass}`}>
          {translateTerm(lang, god)}
        </span>
      ));
    }
    return (
      <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-2 py-0.5 text-[10px] text-zinc-300">
        {translateTerm(lang, emptyLabel)}
      </span>
    );
  };
  const renderPractitionerChoiceChips = (
    kind: PractitionerChoiceKind,
    rowsForKind: Array<Record<string, unknown>>,
    tone: "emerald" | "rose" | "amber",
    fallback: () => ReactNode,
  ) => {
    if (!canChoosePractitionerCandidate || !rowsForKind.length || !onPractitionerChoiceSelect) {
      return fallback();
    }
    const selectedRow = selectedChoicesByKind[kind];
    const selectedId = practitionerChoices[kind];
    return rowsForKind.map((row) => {
      const id = String(row.id || "").trim();
      const name = String(row.label || row.name || "").trim();
      if (!id || !name) return null;
      const active = String(selectedRow?.id || "").trim() === id;
      const manuallySelected = selectedId === id;
      const systemSelected = row.selected_by_system === true;
      const toneClass =
        tone === "emerald"
          ? active
            ? "border-emerald-200/55 bg-emerald-300/15 text-emerald-50"
            : "border-emerald-300/20 bg-emerald-950/25 text-emerald-100 hover:border-emerald-200/45 hover:bg-emerald-400/12"
          : tone === "rose"
            ? active
              ? "border-rose-200/55 bg-rose-300/15 text-rose-50"
              : "border-rose-300/20 bg-rose-950/25 text-rose-100 hover:border-rose-200/45 hover:bg-rose-400/12"
            : active
              ? "border-amber-200/55 bg-amber-300/15 text-amber-50"
              : "border-amber-300/20 bg-amber-950/25 text-amber-100 hover:border-amber-200/45 hover:bg-amber-400/12";
      return (
        <button
          key={id}
          type="button"
          aria-pressed={active}
          title={String(row.reason || row.source || "").trim() || undefined}
          onClick={() => onPractitionerChoiceSelect(kind, id)}
          className={`inline-flex min-h-7 max-w-full items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-semibold transition ${toneClass}`}
        >
          <span className="truncate">{translateTerm(lang, name)}</span>
          <span className="rounded-full border border-white/10 bg-black/25 px-1.5 py-0 text-[9px] font-medium text-current/80">
            {choiceConfidencePercent(row)}%
          </span>
          {manuallySelected || systemSelected ? (
            <span className="rounded-full border border-white/10 bg-white/[0.06] px-1.5 py-0 text-[9px] font-medium text-current/75">
              {manuallySelected ? ui("已选", "Chosen", "선택") : ui("系统", "System", "시스템")}
            </span>
          ) : null}
        </button>
      );
    });
  };

  return (
    <section className="relative overflow-hidden rounded-2xl border border-violet-500/35 bg-gradient-to-br from-violet-900/20 via-zinc-950/90 to-zinc-900/80 p-4 shadow-[0_0_24px_rgba(124,58,237,0.25)]">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-400/70 to-transparent" />
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-violet-600/30 bg-zinc-900/60 px-2.5 py-2 text-[11px] text-zinc-300">
        <span className="text-zinc-500">{t(lang, "six_pillars.birth")} </span>
        <span className="text-violet-100">{birthLabel}</span>
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-zinc-500">{t(lang, "six_pillars.gender")} </span>
        <span className="text-violet-100">{genderLabel}</span>
        <span className="mx-1.5 text-zinc-600">·</span>
        <span className="text-zinc-500">{t(lang, "six_pillars.calendar")} </span>
        <span className="text-violet-100">{calendarLabel}</span>
      </div>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-semibold tracking-wide text-violet-100">{t(lang, "six_pillars.title")}</p>
        <p className="text-[11px] text-violet-200/80">{t(lang, "six_pillars.subtitle")}</p>
        <label className="inline-flex items-center gap-2 text-xs text-zinc-300">
          <span>{t(lang, "six_pillars.year")}</span>
          <select
            value={selectedYear}
            onChange={(e) => onYearChange(Number(e.target.value))}
            className="rounded border border-violet-500/40 bg-zinc-900 px-2 py-1.5 text-xs text-zinc-100 transition-colors hover:border-violet-300/60"
          >
            {yearChoices.map((y) => (
              <option key={y} value={y}>
                {y}
              </option>
            ))}
          </select>
        </label>
      </div>
      {showCoreSections ? (
      <>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 xl:grid-cols-6">
        {rows.map((row) => {
          const stemMeta = STEM_META[row.pillar.stem] || { element: "土", yinYang: "阳" as const };
          const branchMeta = BRANCH_META[row.pillar.branch] || { element: "土", yinYang: "阳" as const };
          const stemColor = colorForElement(stemMeta.element, stemMeta.yinYang);
          const branchColor = colorForElement(branchMeta.element, branchMeta.yinYang);
          const stemGod =
            row.label === "日柱" && row.pillar.stem === dayMasterStem
              ? "日主"
              : tenGodFromStems(dayMasterStem, row.pillar.stem) || "十神";
          const branchMainStem = BRANCH_MAIN_HIDDEN_STEM[row.pillar.branch] || "";
          const branchGod = tenGodFromStems(dayMasterStem, branchMainStem) || "十神";
          const branchLayers = branchLayerGods(dayMasterStem, row.pillar.branch);
          const branchLayerText = branchLayers.map((layer) => `${layerLevelLabel(layer.level)}${translateTerm(lang, layer.god)}`).join(" · ");
          return (
            <div
              key={row.label}
              className="group rounded-xl border border-zinc-700/35 bg-zinc-900/45 p-2.5 text-center transition duration-150 hover:border-violet-400/70"
            >
              <p className="mb-2 text-[10px] font-semibold tracking-wide text-zinc-300">{translateTerm(lang, row.label)}</p>
              <div className="flex flex-col items-stretch gap-1.5">
                <div className={`rounded-md px-2 py-1.5 text-center text-lg font-bold ${stemColor}`}>
                  <span className="block text-[10px] font-semibold tracking-wide text-zinc-200/85">{translateTerm(lang, stemGod)}</span>
                  <span className="leading-none">{row.pillar.stem || "—"}</span>
                </div>
                <div className={`rounded-md px-2 py-1.5 text-center text-lg font-bold ${branchColor}`}>
                  <span className="block text-[10px] font-semibold tracking-wide text-zinc-200/85">{translateTerm(lang, branchGod)}</span>
                  <span className="leading-none">{row.pillar.branch || "—"}</span>
                  {branchLayers.length > 1 ? (
                    <span className="mt-1 block break-words text-[9px] font-medium tracking-wide text-zinc-200/80">
                      {branchLayerText}
                    </span>
                  ) : null}
                </div>
              </div>
              <div className="mt-2 text-[10px] text-zinc-400">
                {row.pillar.stem && row.pillar.branch ? (
                  <>
                    <span className="font-medium text-zinc-200">{row.pillar.stem + row.pillar.branch}</span>
                    <span className="ml-1 text-zinc-500">·</span>
                    <span className="ml-1 text-violet-200">
                      {translateTerm(lang, stemGod)} / {branchLayers.length > 1 ? branchLayerText : translateTerm(lang, branchGod)}
                    </span>
                  </>
                ) : (
                  <span>{translateTerm(lang, "待重算")}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-3 rounded-lg border border-violet-500/30 bg-zinc-950/55 p-2 text-xs text-zinc-400">
        <p className="text-violet-200/90">{t(lang, "six_pillars.tip")}</p>
        <p className="mt-1 text-zinc-400">{t(lang, "six_pillars.tip.body")}</p>
      </div>
      </>
      ) : null}
      {showCoreSections ? (
      <div className="mb-3 overflow-hidden rounded-2xl border border-violet-400/30 bg-[linear-gradient(135deg,rgba(76,29,149,0.22),rgba(17,24,39,0.88))]">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-violet-400/15 px-3 py-2">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-violet-50">{t(lang, "god_ring.title")}</p>
            <span className={`rounded-full border px-2 py-0.5 text-[10px] ${authorityMode ? "border-emerald-400/25 bg-emerald-500/10 text-emerald-200" : "border-amber-400/25 bg-amber-500/10 text-amber-200"}`}>
              {authorityMode ? t(lang, "god_ring.active") : t(lang, "god_ring.pending")}
            </span>
          </div>
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            <span className="rounded-full border border-violet-300/20 bg-black/20 px-2 py-0.5 text-violet-100/80">
              {t(lang, "god_ring.mode", { mode: mode || (authorityMode ? "authority" : "pending") })}
            </span>
            <span className="rounded-full border border-violet-300/20 bg-black/20 px-2 py-0.5 text-violet-100/80">
              {t(lang, "god_ring.confidence", { percent: Math.round(confidence * 100) })}
            </span>
            {authorityMode ? (
              <span className="rounded-full border border-violet-300/20 bg-black/20 px-2 py-0.5 text-violet-100/80">
                {t(lang, "god_ring.path", { count: pathCount })}
              </span>
            ) : null}
            {canChoosePractitionerCandidate && practitionerChoiceCount > 0 ? (
              <span className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-2 py-0.5 text-cyan-100/90">
                {ui("可点选本次断语前提", "Selectable premise", "전제 선택 가능")}
              </span>
            ) : null}
          </div>
        </div>
        <div className="grid gap-2 px-3 py-2.5 md:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg border border-emerald-400/20 bg-emerald-500/10 p-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-emerald-200/80">{t(lang, "god_ring.use")}</p>
            <div className="mt-1.5 flex min-h-[28px] flex-wrap gap-1.5">
              {renderPractitionerChoiceChips("use_god", practitionerChoiceRowsByKind.use_god, "emerald", () =>
                renderFallbackGodChips(useGods, "emerald", "等待裁决"),
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {useMetricChips.slice(0, 3).map((chip) => (
                <span key={`use_chip_${chip.label}`} className={`rounded-full border px-1.5 py-0.5 text-[9px] ${chip.tone}`}>
                  {chip.label}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-rose-400/20 bg-rose-500/10 p-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-rose-200/80">{t(lang, "god_ring.taboo")}</p>
            <div className="mt-1.5 flex min-h-[28px] flex-wrap gap-1.5">
              {renderPractitionerChoiceChips("taboo_god", practitionerChoiceRowsByKind.taboo_god, "rose", () =>
                renderFallbackGodChips(tabooGods, "rose", "等待裁决"),
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {tabooMetricChips.slice(0, 3).map((chip) => (
                <span key={`taboo_chip_${chip.label}`} className={`rounded-full border px-1.5 py-0.5 text-[9px] ${chip.tone}`}>
                  {chip.label}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-cyan-400/20 bg-cyan-500/10 p-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-cyan-200/80">{t(lang, "god_ring.tongguan")}</p>
            <div className="mt-1.5 flex min-h-[28px] flex-wrap gap-1.5">
              {authorityMode && tongguanGods.length ? (
                tongguanGods.map((god) => (
                  <span key={god} className="rounded-full border border-cyan-300/25 bg-cyan-950/35 px-2 py-0.5 text-[11px] font-semibold text-cyan-100">
                    {translateTerm(lang, god)}
                  </span>
                ))
              ) : (
                <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-2 py-0.5 text-[10px] text-zinc-300">
                  {authorityMode ? translateTerm(lang, "未形成通关链") : translateTerm(lang, "等待裁决")}
                </span>
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {tongguanMetricChips.slice(0, 3).map((chip) => (
                <span key={`tongguan_chip_${chip.label}`} className={`rounded-full border px-1.5 py-0.5 text-[9px] ${chip.tone}`}>
                  {chip.label}
                </span>
              ))}
            </div>
          </div>
          <div className="rounded-lg border border-amber-400/20 bg-amber-500/10 p-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-amber-200/80">{t(lang, "god_ring.pattern")}</p>
            <div className="mt-1.5 flex min-h-[28px] flex-wrap gap-1.5">
              {renderPractitionerChoiceChips("pattern", practitionerChoiceRowsByKind.pattern, "amber", () =>
                activePatternName
                  ? (
                      <span className="rounded-full border border-amber-300/25 bg-amber-950/35 px-2 py-0.5 text-[11px] font-semibold text-amber-100">
                        {translateTerm(lang, activePatternName)}
                      </span>
                    )
                  : (
                      <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-2 py-0.5 text-[10px] text-zinc-300">
                        {translateTerm(lang, "等待稳定格局")}
                      </span>
                    ),
              )}
            </div>
            <div className="mt-1.5 flex flex-wrap gap-1">
              {patternMetricChips.slice(0, 3).map((chip) => (
                <span key={`pattern_chip_${chip.label}`} className={`rounded-full border px-1.5 py-0.5 text-[9px] ${chip.tone}`}>
                  {chip.label}
                </span>
              ))}
            </div>
          </div>
        </div>
        {authorityMode && dualRoleCandidates.length ? (
          <div className="border-t border-violet-400/15 px-3 py-2">
            <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-950/25 px-2 py-0.5 text-[10px] text-fuchsia-100">
              {t(lang, "god_ring.dual_role", {
                value: translateTermList(lang, dualRoleCandidates.slice(0, 2)),
              })}
            </span>
          </div>
        ) : null}
      </div>
      ) : null}
      {showAuxiliarySections ? (
      <div className="mb-3 rounded-xl border border-emerald-500/25 bg-emerald-950/10 p-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-300/80">{ui("调候专题", "Climate Theme", "조후 테마")}</p>
            <p className="mt-1 text-sm text-emerald-50">{ui("调候专题", "Climate Topic", "조후 주제")}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-[10px]">
            <span className="rounded-full border border-emerald-400/20 bg-emerald-950/35 px-3 py-1 text-emerald-100">
              {translateTerm(lang, String(climateThemeRow.state || climateFieldRow.state || "未定"))}
            </span>
            <span className="rounded-full border border-amber-400/20 bg-amber-950/35 px-3 py-1 text-amber-100">
              {ui("寒热", "Thermal", "한열")} {signed(num(climateThemeRow.thermal_index ?? climateFieldRow.thermal_index))}
            </span>
            <span className="rounded-full border border-cyan-400/20 bg-cyan-950/35 px-3 py-1 text-cyan-100">
              {ui("燥湿", "Moisture", "조습")} {signed(num(climateThemeRow.moisture_index ?? climateFieldRow.moisture_index))}
            </span>
            <span className="rounded-full border border-rose-400/20 bg-rose-950/35 px-3 py-1 text-rose-100">
              {ui("张力", "Tension", "장력")} {num(climateThemeRow.climate_tension ?? climateFieldRow.climate_tension).toFixed(2)}
            </span>
          </div>
        </div>
        {String(climateThemeRow.prompt_digest || "").trim() ? (
          <p className="mt-2 text-[11px] leading-5 text-zinc-300">
            {String(climateThemeRow.prompt_digest || "").trim()}
          </p>
        ) : null}
        <div className="mt-3 grid gap-2 xl:grid-cols-2">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 p-3">
            <p className="text-[11px] font-semibold text-emerald-100">{ui("十神调候适配", "Ten-God Climate Fit", "십신 조후 적합도")}</p>
            <div className="mt-2 flex flex-wrap gap-2">
              {climateFavored.slice(0, 3).map((god) => (
                <span key={`climate_favored_${god}`} className="rounded-full border border-emerald-400/20 bg-emerald-950/35 px-3 py-1 text-[10px] text-emerald-100">
                  {ui("顺势", "Favored", "순응")} {translateTerm(lang, god)}
                </span>
              ))}
              {climateStrained.slice(0, 3).map((god) => (
                <span key={`climate_strained_${god}`} className="rounded-full border border-rose-400/20 bg-rose-950/35 px-3 py-1 text-[10px] text-rose-100">
                  {ui("承压", "Strained", "압박")} {translateTerm(lang, god)}
                </span>
              ))}
            </div>
            <div className="mt-3 grid gap-2 text-[10px] text-zinc-300 md:grid-cols-3">
              <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-2">
                <div className="text-zinc-400">{ui("效率修正", "Efficiency Delta", "효율 보정")}</div>
                {climateEfficiency.length ? (
                  <div className="mt-1 space-y-1">
                    {climateEfficiency.slice(0, 3).map((row) => (
                      <div key={`climate_eff_${row.god}`} className="font-mono text-cyan-100">
                        {translateTerm(lang, row.god)} {signed(row.delta)}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-1 text-zinc-500">{ui("暂无", "None", "없음")}</div>
                )}
              </div>
              <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-2">
                <div className="text-zinc-400">{ui("稳定修正", "Stability Delta", "안정성 보정")}</div>
                {climateStability.length ? (
                  <div className="mt-1 space-y-1">
                    {climateStability.slice(0, 3).map((row) => (
                      <div key={`climate_stab_${row.god}`} className="font-mono text-amber-100">
                        {translateTerm(lang, row.god)} {signed(row.delta)}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-1 text-zinc-500">{ui("暂无", "None", "없음")}</div>
                )}
              </div>
              <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-2">
                <div className="text-zinc-400">{ui("用神优先级", "Use Priority", "용신 우선순위")}</div>
                {climatePriority.length ? (
                  <div className="mt-1 space-y-1">
                    {climatePriority.slice(0, 3).map((row) => (
                      <div key={`climate_pri_${row.god}`} className="font-mono text-emerald-100">
                        {translateTerm(lang, row.god)} {signed(row.delta)}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-1 text-zinc-500">{ui("暂无", "None", "없음")}</div>
                )}
              </div>
            </div>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 p-3">
            <p className="text-[11px] font-semibold text-emerald-100">{ui("来源与格局存续", "Source & Pattern Survival", "출처와 격국 존속")}</p>
            <div className="mt-2 space-y-2">
              {climateFocus.length ? (
                <div className="grid gap-2 text-[10px] text-zinc-300 sm:grid-cols-2">
                  {climateFocus.map((row) => (
                    <div key={`climate_scope_${row.scopeLabel}`} className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-2">
                      <div className="text-zinc-400">{translateTerm(lang, row.scopeLabel)}</div>
                      <div className="mt-1 font-mono text-cyan-100">{ui("热", "Heat", "열")} {signed(row.thermal)}</div>
                      <div className="font-mono text-emerald-100">{ui("湿", "Moisture", "습")} {signed(row.moisture)}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-zinc-500">{ui("暂无主要来源焦点。", "No dominant source focus yet.", "주요 출처 초점이 아직 없습니다.")}</p>
              )}
              {climatePattern.length ? (
                <div className="space-y-1.5">
                  {climatePattern.map((row) => (
                    <p key={`climate_pattern_${row.label}`} className="text-[11px] leading-5 text-zinc-300">
                      {translateTerm(lang, row.label)}
                      <span className="ml-2 text-emerald-200/90">{translateTerm(lang, row.bucket || "存续观察")}</span>
                      <span className="ml-2 font-mono text-amber-100">{signed(row.delta)}</span>
                    </p>
                  ))}
                </div>
              ) : null}
            </div>
            {Array.isArray(climateThemeRow.narrative_focus) && climateThemeRow.narrative_focus.length ? (
              <div className="mt-3 rounded border border-emerald-400/10 bg-emerald-950/15 px-2 py-2 text-[10px] text-zinc-300">
                {climateThemeRow.narrative_focus
                  .map((item) => String(item || "").trim())
                  .filter(Boolean)
                  .slice(0, 3)
                  .join(" · ")}
              </div>
            ) : null}
          </div>
        </div>
        <p className="mt-2 text-[11px] leading-5 text-zinc-400">
          {ui(
            "调候专题只解释 climate field，不直接改写 L0 原始总量；当前主要影响十神效率、稳定性、用神优先级与格局存续。",
            "The climate topic only interprets the climate field. It does not rewrite the raw L0 totals and currently affects ten-god efficiency, stability, use-priority, and pattern survival.",
            "조후 주제는 climate field 만 해석합니다. L0 원시 총량은 다시 쓰지 않으며, 현재 십신 효율·안정성·용신 우선순위·격국 존속에만 영향을 줍니다.",
          )}
        </p>
      </div>
      ) : null}
      {showAuxiliarySections ? (
      <div className="mb-3 rounded-xl border border-fuchsia-500/25 bg-fuchsia-950/10 p-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.2em] text-fuchsia-300/80">{ui("象法专题", "Xiangfa Theme", "상법 테마")}</p>
            <p className="mt-1 text-sm text-fuchsia-50">{ui("象法专题", "Xiangfa Topic", "상법 주제")}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-[10px]">
            <span className="rounded-full border border-fuchsia-400/20 bg-fuchsia-950/35 px-3 py-1 text-fuchsia-100">
              {ui("语义专题", "Semantic topic", "의미 주제")}
            </span>
            <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
              {ui("不入 bias", "No bias", "bias 미포함")}
            </span>
            <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
              {ui("不改能量", "No energy rewrite", "에너지 미수정")}
            </span>
          </div>
        </div>
        {String(xiangfaThemeRow.prompt_digest || "").trim() ? (
          <p className="mt-2 text-[11px] leading-5 text-zinc-300">
            {String(xiangfaThemeRow.prompt_digest || "").trim()}
          </p>
        ) : null}
        <div className="mt-3 grid gap-2 xl:grid-cols-2">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 p-3">
            <p className="text-[11px] font-semibold text-fuchsia-100">{ui("语义映射 / 事件框架", "Semantic Mapping / Event Framing", "의미 매핑 / 사건 프레이밍")}</p>
            <div className="mt-2 space-y-2 text-[11px] leading-5 text-zinc-300">
              {xiangfaSemantic.length ? (
                <div>
                  <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Semantic</div>
                  {xiangfaSemantic.slice(0, 3).map((row) => (
                    <p key={`xiangfa_sem_${row}`}>{row}</p>
                  ))}
                </div>
              ) : null}
              {xiangfaFraming.length ? (
                <div>
                  <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Framing</div>
                  {xiangfaFraming.slice(0, 3).map((row) => (
                    <p key={`xiangfa_frame_${row}`}>{row}</p>
                  ))}
                </div>
              ) : null}
              {!xiangfaSemantic.length && !xiangfaFraming.length ? (
                <p className="text-[10px] text-zinc-500">{ui("当前尚未形成稳定的象法语义映射。", "No stable Xiangfa semantic mapping has formed yet.", "안정적인 상법 의미 매핑이 아직 형성되지 않았습니다.")}</p>
              ) : null}
            </div>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 p-3">
            <p className="text-[11px] font-semibold text-fuchsia-100">{ui("证据与叙事提示", "Evidence & Narrative Hints", "증거와 서사 힌트")}</p>
            <div className="mt-2 space-y-2 text-[11px] leading-5 text-zinc-300">
              {xiangfaEvidence.length ? (
                <div>
                  <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Evidence</div>
                  {xiangfaEvidence.slice(0, 3).map((row) => (
                    <p key={`xiangfa_evi_${row}`}>{row}</p>
                  ))}
                </div>
              ) : null}
              {xiangfaHints.length ? (
                <div>
                  <div className="mb-1 text-[10px] uppercase tracking-[0.16em] text-zinc-500">Hint</div>
                  {xiangfaHints.slice(0, 2).map((row) => (
                    <p key={`xiangfa_hint_${row}`}>{row}</p>
                  ))}
                </div>
              ) : null}
              {xiangfaSourceTopics.length ? (
                <div className="rounded border border-fuchsia-400/10 bg-fuchsia-950/15 px-2 py-2 text-[10px] text-zinc-300">
                  {ui("来源", "Sources", "출처")}：{translateTermList(lang, xiangfaSourceTopics.slice(0, 4), " · ")}
                </div>
              ) : null}
              {!xiangfaEvidence.length && !xiangfaHints.length ? (
                <p className="text-[10px] text-zinc-500">{ui("当前尚未形成稳定的象法证据串。", "No stable Xiangfa evidence chain has formed yet.", "안정적인 상법 증거 연쇄가 아직 형성되지 않았습니다.")}</p>
              ) : null}
            </div>
          </div>
        </div>
        <p className="mt-2 text-[11px] leading-5 text-zinc-400">
          {ui(
            "象法专题当前只做 semantic mapping、evidence、narrative hint、event framing，不进入 bias，不覆盖 authority，也不改写底层物理。",
            "The Xiangfa topic currently produces only semantic mapping, evidence, narrative hints, and event framing. It does not enter bias, override authority, or rewrite the physical base.",
            "상법 주제는 현재 semantic mapping, evidence, narrative hint, event framing 만 제공합니다. bias 에 들어가지 않고 authority 를 덮지 않으며 물리 기반도 다시 쓰지 않습니다.",
          )}
        </p>
      </div>
      ) : null}
      {showAuxiliarySections ? (
      <div className="mb-3 rounded-xl border border-cyan-500/20 bg-cyan-950/10 p-3">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <p className="text-[10px] uppercase tracking-[0.2em] text-cyan-300/80">{ui("根透协议", "Projection Bridge", "근투 프로토콜")}</p>
            <p className="mt-1 text-sm text-cyan-50">{ui("根透协议", "Projection Bridge", "근투 프로토콜")}</p>
          </div>
          <div className="flex flex-wrap gap-2 text-[10px]">
            <span className="rounded-full border border-cyan-400/20 bg-cyan-950/35 px-3 py-1 text-cyan-100">
              {ui("通根", "Rooting", "통근")} {translateTerm(lang, bridgeDirectionLabel(bridgeProtocol.tonggen_direction))}
            </span>
            <span className="rounded-full border border-violet-400/20 bg-violet-950/35 px-3 py-1 text-violet-100">
              {ui("透干", "Exposure", "투간")} {translateTerm(lang, bridgeDirectionLabel(bridgeProtocol.tougan_direction))}
            </span>
            <span className="rounded-full border border-emerald-400/20 bg-emerald-950/35 px-3 py-1 text-emerald-100">
              {ui("同五行先", "Same element first", "동오행 우선")} {bridgeProtocol.same_element_first ? "ON" : "OFF"}
            </span>
            <span className="rounded-full border border-amber-400/20 bg-amber-950/35 px-3 py-1 text-amber-100">
              {ui("阴阳后判", "Polarity second", "음양 후판")} {bridgeProtocol.polarity_second ? "ON" : "OFF"}
            </span>
            <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-200">
              {bridgeProtocol.single_pass_coupling ? ui("单次耦合", "Single-pass coupling", "단회 결합") : ui("未声明", "Undeclared", "미선언")}
            </span>
            <span className="rounded-full border border-rose-400/20 bg-rose-950/35 px-3 py-1 text-rose-100">
              {bridgeProtocol.recursive_feedback ? ui("允许递归", "Recursive allowed", "재귀 허용") : ui("禁止递归", "Recursive forbidden", "재귀 금지")}
            </span>
          </div>
        </div>
        <div className="mt-3 grid gap-2 text-[11px] text-zinc-300 md:grid-cols-2 xl:grid-cols-5">
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 px-3 py-2">
            {ui("本根", "Exact root", "정근")} <span className="ml-1 font-mono text-cyan-100">{Number(bridgeProtocol.exact_root_support_factor || 1).toFixed(2)}</span>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 px-3 py-2">
            {ui("异阴阳根", "Cross-polarity root", "이극 근")} <span className="ml-1 font-mono text-emerald-100">{Number(bridgeProtocol.cross_polarity_root_support_factor || 0).toFixed(2)}</span>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 px-3 py-2">
            {ui("精确透干", "Exact exposure", "정확 투간")} <span className="ml-1 font-mono text-violet-100">{Number(bridgeProtocol.exact_exposed_hidden_gain || 0).toFixed(2)}</span>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 px-3 py-2">
            {ui("同五行可见", "Same-element visible", "동오행 가시")} <span className="ml-1 font-mono text-amber-100">{Number(bridgeProtocol.same_element_visible_relief || 0).toFixed(2)}</span>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-950/55 px-3 py-2">
            {ui("通根上限", "Rooting cap", "통근 상한")} <span className="ml-1 font-mono text-fuchsia-100">{Number(bridgeProtocol.rooted_gain_cap || 0).toFixed(2)}</span>
          </div>
        </div>
        <p className="mt-2 text-[11px] leading-5 text-zinc-400">
          {bridgeReady
            ? ui(
                "规则口径：通根只服务天干，透干只服务地支显影。二者允许互证，但都只读取冻结盘面证据一次，不会递归放大。",
                "Rule scope: rooting serves stems, exposure serves branch-hidden manifestation. They may corroborate each other, but each reads frozen-chart evidence only once and never recursively amplifies.",
                "규칙 범위: 통근은 천간을, 투간은 지지 장간의 현현을 보조합니다. 둘은 상호 증거가 될 수 있지만 동결된 명식 증거를 한 번만 읽고 재귀 증폭하지 않습니다.",
              )
            : ui("等待后端下发根透协议。", "Waiting for backend projection-bridge protocol.", "백엔드 근투 프로토콜 대기 중입니다.")}
        </p>
      </div>
      ) : null}
      {showAuxiliarySections && relationRows.length ? (
        <div className="mb-3 rounded-xl border border-amber-500/20 bg-amber-950/10 p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-amber-300/80">Relation Formation</p>
              <p className="mt-1 text-sm text-amber-50">{ui("合化成局摘要", "Relation Formation Summary", "합화 성국 요약")}</p>
            </div>
            <p className="max-w-xl text-[11px] leading-5 text-zinc-400">
              {ui(
                "百分比表示成局度，不直接等于十神能量；请结合基准倍数、十神绝对强度和做功链条一起看。",
                "The percentage means formation degree, not direct ten-god energy. Read it together with base factor, absolute ten-god strength, and work-flow chains.",
                "퍼센트는 성국도를 뜻하며 십신 에너지와 직접 동일하지 않습니다. 기준 배수, 십신 절대 강도, 작용 사슬과 함께 보세요.",
              )}
            </p>
          </div>
          <div className="mt-3 grid gap-2 xl:grid-cols-2">
            {relationRows.map((row) => (
              <div key={row.formationLabel} className="rounded-lg border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="text-sm text-amber-50">{translateTerm(lang, row.formationLabel)}</p>
                    <p className="mt-1 text-[11px] text-zinc-400">{ui("家族基准", "Family factor", "계열 기준")} x{row.familyFactor.toFixed(2)}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-mono text-lg text-amber-100">{row.formationPercent.toFixed(1)}%</p>
                    <span className={`inline-flex rounded-full border px-2 py-1 text-[10px] ${relationFormationTone(row.status)}`}>
                      {translateTerm(lang, row.status || "成局观察")}
                    </span>
                  </div>
                </div>
                {row.projectionPreview.length ? (
                  <p className="mt-2 text-[11px] text-cyan-200/90">
                    {ui("主投影", "Main projection", "주 투영")}：{translateTermList(lang, row.projectionPreview)}
                  </p>
                ) : null}
                {row.summary ? (
                  <p className="mt-2 text-[11px] leading-5 text-zinc-400">{row.summary}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {showAuxiliarySections && relationDynamics.length ? (
        <div className="mb-3 rounded-xl border border-cyan-500/20 bg-cyan-950/10 p-3">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-cyan-300/80">Relation Dynamics</p>
              <p className="mt-1 text-sm text-cyan-50">{ui("关系动力学 / 能量-稳定性双轴", "Relation Dynamics / Energy-Stability Axes", "관계 동역학 / 에너지-안정성 이중축")}</p>
            </div>
            <p className="max-w-xl text-[11px] leading-5 text-zinc-400">
              {ui(
                "这里看的是关系如何改变能量运行方式与结构稳定性，不直接等于十神总分；合偏组织化/绑定，冲刑害破偏激发/内耗/暗损/解构。",
                "This shows how relations change energy operation and structural stability. It is not a direct ten-god total; combinations lean toward organization/binding, while clash/penalty/harm/break lean toward activation, drag, hidden drain, or deconstruction.",
                "여기는 관계가 에너지 운행 방식과 구조 안정성을 어떻게 바꾸는지 보여 줍니다. 십신 총점과 직접 동일하지 않으며, 합은 조직화/결속 쪽이고 충·형·해·파는 격발/내모/암손/해체 쪽입니다.",
              )}
            </p>
          </div>
          <div className="mt-3 grid gap-2 xl:grid-cols-2">
            {relationDynamics.map((row) => (
              <div key={row.label} className="rounded-lg border border-zinc-800 bg-zinc-950/55 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="text-sm text-cyan-50">{translateTerm(lang, row.label)}</p>
                    <p className="mt-1 text-[11px] text-zinc-400">
                      {ui("作用柱", "Active pillars", "작용 기둥")}：{row.pillars.length ? row.pillars.map((pillar) => translateTerm(lang, pillarLabel(pillar))).join(" / ") : translateTerm(lang, "未定")}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex rounded-full border px-2 py-1 text-[10px] ${relationDynamicsTone(row.energyAxis, row.stabilityDeltaRatio)}`}>
                      {translateTerm(lang, row.energyAxis || "动力学观察")}
                    </span>
                  </div>
                </div>
                <div className="mt-2 grid gap-2 text-[11px] text-zinc-300 sm:grid-cols-3">
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    {ui("能量效应", "Energy effect", "에너지 효과")} <span className="ml-1 font-mono text-cyan-100">{(row.energyEffectRatio * 100).toFixed(1)}%</span>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    {ui("稳定变化", "Stability delta", "안정 변화")} <span className="ml-1 font-mono text-amber-100">{signed(row.stabilityDeltaRatio * 100)}%</span>
                  </div>
                  <div className="rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                    {ui("自由能锁定", "Free-energy lock", "자유에너지 잠금")} <span className="ml-1 font-mono text-violet-100">{(row.freeEnergyLockRatio * 100).toFixed(1)}%</span>
                  </div>
                </div>
                {row.note ? (
                  <p className="mt-2 text-[11px] leading-5 text-zinc-400">{row.note}</p>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {showAuxiliarySections && decompositionRows.length ? (
        <div className="mt-3 rounded-xl border border-violet-500/25 bg-zinc-950/60 p-3">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-violet-300/80">Ten Gods Decomposition</p>
              <p className="mt-1 text-sm text-violet-50">{ui("十神来源分解", "Ten-God Source Decomposition", "십신 출처 분해")}</p>
            </div>
            <span className="rounded-full border border-violet-400/20 bg-violet-950/30 px-2 py-1 text-[10px] text-violet-100/80">
              {ui("显化 / 根气 / 势能细项 / 潜藏", "Manifest / Root / Momentum Detail / Hidden", "현출 / 근기 / 세력 세목 / 잠장")}
            </span>
          </div>
          <div className="mt-3 grid gap-2 md:grid-cols-2">
            {decompositionRows.map((row) => (
              <div key={row.god} className="min-w-0 rounded-lg border border-violet-400/15 bg-black/20 p-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="min-w-0 break-words text-sm font-semibold text-violet-100">{translateTerm(lang, row.god)}</span>
                  <span className="font-mono text-[11px] text-cyan-200">{row.total.toFixed(2)}</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {decompositionEvidenceTags(row.god, row, tenGodLedger).map((tag) => (
                    <span
                      key={`${row.god}_${tag}`}
                      className="rounded-full border border-violet-400/15 bg-violet-950/20 px-2 py-0.5 text-[10px] text-violet-100/90"
                    >
                      {translateTerm(lang, tag)}
                    </span>
                  ))}
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-[10px] text-zinc-300">
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("显化", "Manifest", "현출")} <span className="ml-1 font-mono text-violet-100">{row.manifest.toFixed(2)}</span>
                  </div>
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("根气", "Root", "근기")} <span className="ml-1 font-mono text-emerald-100">{row.root.toFixed(2)}</span>
                  </div>
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("势能", "Momentum", "세력")} <span className="ml-1 font-mono text-amber-100">{row.momentum.toFixed(2)}</span>
                  </div>
                  <div className="rounded border border-zinc-800 bg-zinc-950/60 px-2 py-1">
                    {ui("潜藏", "Hidden", "잠장")} <span className="ml-1 font-mono text-zinc-100">{row.hidden.toFixed(2)}</span>
                  </div>
                </div>
                <div className="mt-2 break-words rounded border border-violet-400/10 bg-violet-950/10 px-2 py-1.5 text-[10px] text-zinc-300">
                  {ui("势能细项", "Momentum details", "세력 세목")}：
                  <span className="ml-1 text-amber-100">{ui("月令", "Month", "월령")} {row.momentumMonthOrder.toFixed(2)}</span>
                  <span className="ml-2 text-orange-100">{ui("阶段", "Stage", "단계")} {row.momentumStage.toFixed(2)}</span>
                  <span className="ml-2 text-fuchsia-100">{ui("结构", "Structure", "구조")} {row.momentumStructure.toFixed(2)}</span>
                  <span className="ml-2 text-cyan-100">{ui("辅助", "Auxiliary", "보조")} {row.momentumAuxiliary.toFixed(2)}</span>
                  <span className="ml-2 text-zinc-200">{ui("其他", "Other", "기타")} {row.momentumOther.toFixed(2)}</span>
                </div>
                <div className="mt-2 break-words rounded border border-orange-400/10 bg-orange-950/10 px-2 py-1.5 text-[10px] text-zinc-300">
                  {ui("阶段分层", "Stage layers", "단계 분층")}：
                  <span className="ml-1 text-emerald-100">{ui("禄", "Lu", "록")} {row.momentumStageLu.toFixed(2)}</span>
                  <span className="ml-2 text-rose-100">{ui("刃", "Blade", "인")} {row.momentumStageBlade.toFixed(2)}</span>
                  <span className="ml-2 text-amber-100">{ui("长生", "Growth", "장생")} {row.momentumStageGeneral.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
