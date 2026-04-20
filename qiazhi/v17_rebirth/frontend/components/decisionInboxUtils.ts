import type { Decision } from "@/hooks/useOracleSession";

export type DecisionWithId = Decision & { _ui_id: string };

export type DecisionBatchGroup = {
  key: string;
  target: string;
  source: string;
  exclusivityKey: string;
  decisions: DecisionWithId[];
};

export type DecisionBatch = {
  batch_id: string;
  batch_ids?: string[];
  bucket: "manual" | "system" | "llm";
  target: string;
  source_anchor: string;
  source_families: string[];
  decisions: DecisionWithId[];
  decision_count: number;
  net_impact_ratio: number;
  max_priority: number;
  direction_key?: string;
  direction_label?: string;
  prompt_line: string;
  labels: string[];
};

export function sourceLabel(decision: Decision): string {
  const explicit = String(decision.source_label || "").trim();
  if (explicit) return explicit;
  const raw = String(decision.source || decision.plugin_id || "unknown").trim();
  if (!raw) return "未知规则";
  if (raw.includes("op_branch_sanhe")) return "三合成局";
  if (raw.includes("risk_matrix")) return "官伤风险矩阵";
  if (raw.includes("liuchong")) return "六冲";
  if (raw.includes("liuhe")) return "六合";
  if (raw.includes("liupo")) return "六破";
  if (raw.includes("sanxing")) return "三刑";
  if (raw.includes("op_status")) return "状态机节律";
  if (raw.includes("three_harmony")) return "三合";
  if (raw.includes("muku")) return "墓库";
  if (raw.includes("stem_fusion")) return "天干五合";
  if (raw.includes("chang_sheng")) return "长生状态";
  if (raw.includes("geometry")) return "几何关系";
  if (raw.includes("manifest")) return "插件命中";
  if (raw.startsWith("l2.")) return raw.replace(/^l2\./, "L2:");
  return raw;
}

export function normalizeDecisionId(decision: Decision, idx: number): string {
  return String(decision.id || decision.label || `manual_${idx}`).trim() || `manual_${idx}`;
}

export function resolveDecisionLookupKeys(decision: DecisionWithId): string[] {
  const keys = new Set<string>();
  if (decision.id) keys.add(String(decision.id).trim());
  if (decision._ui_id) keys.add(String(decision._ui_id).trim());
  if (decision.label) keys.add(String(decision.label).trim());
  if (decision.title) keys.add(String(decision.title).trim());
  keys.delete("");
  return Array.from(keys);
}

function manualDecisionKey(decision: DecisionWithId): string {
  const target = String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim();
  const source = String(sourceLabel(decision)).trim() || "unknown";
  const impact = decision.physical_impact || {};
  const level = Number(impact.intensity_level || 0);
  const ratio = Number(impact.impact_ratio || 0);
  const ratioBucket = ratio >= 0.08 ? "high" : ratio <= -0.08 ? "low" : "mid";
  const exclusivityKey = String(
    decision.exclusivity_key || decision.source_event || `${decision.source || decision.plugin_id || "manual"}::${target}`,
  ).trim();
  const stableTag = exclusivityKey || "fallback";
  return `${target}::${source}::${stableTag}::L${level}::${ratioBucket}`;
}

export function buildManualDecisionGroups(decisions: DecisionWithId[]): DecisionBatchGroup[] {
  const bucket: Record<string, DecisionBatchGroup> = {};
  for (const decision of decisions) {
    const key = manualDecisionKey(decision);
    if (!bucket[key]) {
      bucket[key] = {
        key,
        target: String(decision.target_god || decision.physical_impact?.target_god || "未定目标").trim() || "未定目标",
        source: String(sourceLabel(decision)).trim() || "未知规则",
        exclusivityKey: String(
          decision.exclusivity_key ||
            decision.source_event ||
            `${decision.source || decision.plugin_id || "manual"}::${decision.target_god || ""}`.trim(),
        ).trim() || "manual",
        decisions: [],
      };
    }
    bucket[key].decisions.push(decision);
  }

  return Object.values(bucket).sort((a, b) => {
    const aLevel = Number(a.decisions[0]?.physical_impact?.intensity_level || 0);
    const bLevel = Number(b.decisions[0]?.physical_impact?.intensity_level || 0);
    return bLevel - aLevel || b.decisions.length - a.decisions.length || a.key.localeCompare(b.key);
  });
}

export function buildDecisionCatalog(
  decisions: DecisionWithId[],
  source: Decision[],
): DecisionWithId[] {
  if (!source.length) return decisions;
  const catalog = new Map<string, DecisionWithId>();
  const seenIds = new Set<string>();
  const seenLookup = new Set<string>();

  const addDecision = (raw: Decision, fallbackIdx: number) => {
    const candidate: DecisionWithId = {
      ...raw,
      _ui_id: normalizeDecisionId(raw, fallbackIdx),
    };
    const rawId = String(candidate.id || "").trim();
    const lookupKeys = resolveDecisionLookupKeys(candidate);
    if (!lookupKeys.length) {
      if (!rawId || seenIds.has(rawId)) return fallbackIdx;
    }
    if (rawId && seenIds.has(rawId)) return fallbackIdx;
    if (lookupKeys.some((key) => seenLookup.has(key))) return fallbackIdx;
    if (rawId) seenIds.add(rawId);
    for (const key of lookupKeys) {
      seenLookup.add(key);
      catalog.set(`lookup:${key}`, candidate);
    }
    if (candidate._ui_id) catalog.set(`ui:${candidate._ui_id}`, candidate);
    catalog.set(`fallback:${fallbackIdx}`, candidate);
    return fallbackIdx + 1;
  };

  let nextIdx = 0;
  for (const row of decisions) {
    nextIdx = addDecision(row, nextIdx);
  }
  for (const row of source) {
    nextIdx = addDecision(row, nextIdx);
  }

  return Array.from(new Set(catalog.values())).filter(
    (row): row is DecisionWithId => Boolean(row && (row as DecisionWithId)._ui_id),
  );
}

export function buildDecisionIndex(allDecisionCatalog: DecisionWithId[]): Map<string, DecisionWithId> {
  const idx = new Map<string, DecisionWithId>();
  for (const decision of allDecisionCatalog) {
    for (const key of resolveDecisionLookupKeys(decision)) {
      idx.set(key, decision);
    }
    idx.set(decision._ui_id, decision);
    if (decision.id) {
      idx.set(String(decision.id), decision);
    }
  }
  return idx;
}

export function normalizeBatchBucket(rawBucket?: string): "manual" | "system" | "llm" {
  const normalized = String(rawBucket || "manual").trim().toLowerCase();
  if (normalized === "manual") return "manual";
  if (normalized === "llm" || normalized === "narrative" || normalized === "story" || normalized === "context") return "llm";
  if (normalized === "system" || normalized === "auto" || normalized === "auto_apply") return "system";
  return "system";
}

export function directionGroupLabel(ratio: number, rawLabel?: string): string {
  const explicit = String(rawLabel || "").trim();
  if (explicit) return explicit;
  if (ratio > 0) return "增强组";
  if (ratio < 0) return "抑制组";
  return "观察组";
}
