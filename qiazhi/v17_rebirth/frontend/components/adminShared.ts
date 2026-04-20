"use client";

export type ArbiterRole = "system" | "llm" | "user";
export type LooseObject = Record<string, unknown>;

export type PluginCardRow = {
  layer?: string;
  plugin_id: string;
  display_name?: string;
  definition_text?: string;
  display_definition?: string;
  function_summary?: string;
  display_description?: string;
  detail_description?: string;
  design_rationale?: string;
  family_label?: string;
  causal_tier: number;
  execution_order?: number;
};

export type PluginClaimLike = {
  target_god?: string;
  projection_share?: number;
  cluster_projection?: Record<string, unknown>;
  match_ratio?: number;
};

export type PluginConflictLike = {
  conflict_id: string;
  conflict_type?: string;
  severity?: string;
  conflict_score?: number;
  plugins?: string[];
  target_god?: string;
  why_conflict?: string;
  recommended_arbiter?: string;
  resolution_status?: string;
  routing_reason?: string;
  routing_policy?: string;
  routing_scores?: Record<string, number>;
};

export type PluginConflictResolutionLike = {
  conflict_id: string;
  status?: string;
};

export type PluginPanelRowLike<TPlugin extends PluginCardRow = PluginCardRow> = {
  plugin: TPlugin;
  runtime?: {
    fact_count?: number;
    proposal_count?: number;
    decision_count?: number;
    status?: string;
    target_god?: string;
    reason?: string;
  };
  relatedClaims: PluginClaimLike[];
  relatedConflicts: PluginConflictLike[];
};

export type PluginCategoryBucketLike<TPlugin extends PluginCardRow = PluginCardRow> = {
  key: string;
  label: string;
  rows: PluginPanelRowLike<TPlugin>[];
};

export type PluginTierBucketLike<TPlugin extends PluginCardRow = PluginCardRow> = {
  tier: string;
  title: string;
  rows: PluginPanelRowLike<TPlugin>[];
  categories: PluginCategoryBucketLike<TPlugin>[];
};

export type ConflictMergeGroupLike = {
  key: string;
  conflict_type: string;
  severity: string;
  target_god: string;
  recommended_arbiter: string;
  conflicts: PluginConflictLike[];
  conflict_ids: string[];
  max_conflict_score: number;
};

export const ADMIN_GHOST_BTN =
  "cursor-pointer rounded-md border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm font-semibold text-zinc-200 transition hover:border-zinc-500 hover:bg-zinc-800 disabled:opacity-50";
export const ADMIN_SOLID_BTN =
  "cursor-pointer rounded-md bg-zinc-100 px-4 py-2 text-sm font-semibold text-zinc-900 transition hover:bg-white disabled:opacity-60";

export function pluginCardTitle<T extends PluginCardRow>(row: T): string {
  return String(row.display_name || row.definition_text || row.plugin_id || "未命名插件").trim();
}

export function pluginCardDefinition<T extends PluginCardRow>(row: T): string {
  return String(row.display_definition || row.definition_text || row.function_summary || row.plugin_id || "").trim();
}

export function pluginCardDescription<T extends PluginCardRow>(row: T): string {
  return String(row.display_description || row.detail_description || row.design_rationale || "暂无补充说明。").trim();
}

export function asLooseObject(value: unknown): LooseObject {
  return typeof value === "object" && value !== null ? (value as LooseObject) : {};
}

export function asLooseRecord<T>(value: unknown, fallback: T[] = [] as T[]): T[] {
  return Array.isArray(value) ? (value as T[]) : fallback;
}

export function asNumber(value: unknown, fallback = 0): number {
  const raw = Number(value);
  return Number.isFinite(raw) ? raw : fallback;
}

export function asString(value: unknown, fallback = ""): string {
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return fallback;
}

export function normalizePluginKey(value: string | undefined): string {
  return String(value || "").trim().toLowerCase();
}

export function conflictTone(severity: string | undefined): string {
  const value = String(severity || "").trim().toUpperCase();
  if (value === "P1") return "bg-rose-900/40 text-rose-300";
  if (value === "P2") return "bg-amber-900/40 text-amber-300";
  return "bg-cyan-900/40 text-cyan-300";
}

export function compactRoutingScores(scores: Record<string, number> | undefined): string {
  if (!scores) return "";
  return Object.entries(scores)
    .map(([name, value]) => `${name} ${(Number(value) || 0).toFixed(2)}`)
    .filter(Boolean)
    .sort()
    .join(" · ");
}

export function formatArbiterLabel(value: string | undefined): string {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "system") return "系统";
  if (normalized === "llm") return "LLM";
  if (normalized === "user") return "用户";
  if (!normalized) return "待定";
  if (normalized.includes("manual")) return "手动";
  return value || "待定";
}

export function formatQueueLabel(value: string | undefined): string {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return "待处理";
  if (normalized === "llm") return "LLM";
  if (normalized === "system") return "系统";
  if (normalized.includes("manual")) return "手动";
  if (normalized.includes("auto")) return "自动";
  if (normalized.includes("user")) return "用户";
  return String(value);
}

export function resolveRoutingPolicy(conflict: Pick<PluginConflictLike, "routing_policy" | "routing_reason">): string {
  const policy = String(conflict.routing_policy || "").trim();
  if (policy) return policy;
  const reason = String(conflict.routing_reason || "").trim();
  if (reason) return "显式";
  return "优先级+冲突等级";
}

export function pickAutoArbiter(severity: string | undefined): ArbiterRole {
  const normalized = String(severity || "P3").trim().toUpperCase();
  if (normalized === "P1") return "system";
  if (normalized === "P2") return "llm";
  return "user";
}

export function brainStepTone(kind: string | undefined): string {
  const value = String(kind || "").trim().toLowerCase();
  if (value.includes("manual") || value === "user") return "text-violet-300";
  if (value.includes("system")) return "text-amber-300";
  if (value.includes("llm")) return "text-cyan-300";
  return "text-zinc-400";
}

function isConflictPending(
  conflict: PluginConflictLike,
  resolution?: PluginConflictResolutionLike | undefined,
) {
  const status = String(conflict.resolution_status || "").trim().toLowerCase();
  if (status) {
    if (status === "approved" || status === "resolved_system") return false;
    if (status.startsWith("queued_")) return false;
  }

  const resolutionStatus = String(resolution?.status || "").trim().toLowerCase();
  if (resolutionStatus) {
    if (resolutionStatus === "approved" || resolutionStatus === "resolved_system") return false;
    if (resolutionStatus.startsWith("queued_")) return false;
  }
  return true;
}

function conflictMergeKey(row: PluginConflictLike) {
  const target = String(row.target_god || "未定目标").trim();
  const severity = String(row.severity || "P3").trim().toUpperCase();
  const type = String(row.conflict_type || "unknown").trim().toLowerCase();
  const arbiter = String(row.recommended_arbiter || "system").trim().toLowerCase();
  return `${type}#${target}#${severity}#${arbiter}`;
}

export function buildConflictGroups(
  conflicts: PluginConflictLike[],
  resolutions: PluginConflictResolutionLike[],
): ConflictMergeGroupLike[] {
  const resolutionByConflict = new Map<string, PluginConflictResolutionLike>();
  for (const resolution of resolutions || []) {
    const conflictId = String(resolution.conflict_id || "").trim();
    if (conflictId) resolutionByConflict.set(conflictId, resolution);
  }

  const bucket: Record<string, ConflictMergeGroupLike> = {};
  for (const row of conflicts || []) {
    const conflictId = String(row.conflict_id || "").trim();
    if (!conflictId) continue;
    const resolution = resolutionByConflict.get(conflictId);
    if (!isConflictPending(row, resolution)) continue;
    const key = conflictMergeKey(row);
    if (!bucket[key]) {
      bucket[key] = {
        key,
        conflict_type: String(row.conflict_type || "unknown").trim(),
        severity: String(row.severity || "P3").trim(),
        target_god: String(row.target_god || "未定目标").trim(),
        recommended_arbiter: String(row.recommended_arbiter || "system").trim().toLowerCase(),
        conflicts: [],
        conflict_ids: [],
        max_conflict_score: 0,
      };
    }
    bucket[key].conflicts.push(row);
    bucket[key].conflict_ids.push(conflictId);
    bucket[key].max_conflict_score = Math.max(bucket[key].max_conflict_score, Number(row.conflict_score || 0));
  }

  return Object.values(bucket).sort((a, b) => {
    const severityValue = { P1: 3, P2: 2, P3: 1 };
    const score = (value: string) => severityValue[value as keyof typeof severityValue] || 0;
    return (
      score(String(b.severity || "P3").toUpperCase()) - score(String(a.severity || "P3").toUpperCase()) ||
      b.max_conflict_score - a.max_conflict_score ||
      b.conflict_ids.length - a.conflict_ids.length ||
      b.target_god.localeCompare(a.target_god)
    );
  });
}

export function isInboxRuntimeStatus(status: string | undefined): boolean {
  const value = String(status || "").trim().toLowerCase();
  return new Set([
    "manual_pending",
    "manual_committed",
    "manual_rejected",
    "await_review",
    "context_pending",
    "context_consumed",
    "proposal_pending",
    "auto_applied",
  ]).has(value);
}

export function isHitRuntimeStatus(status: string | undefined): boolean {
  const value = String(status || "").trim().toLowerCase();
  return value !== "" && value !== "unknown";
}

export function runtimeStatusTone(status: string | undefined): string {
  const value = String(status || "").trim().toLowerCase();
  if (value === "auto_applied") return "bg-emerald-900/40 text-emerald-300";
  if (value === "manual_committed") return "bg-cyan-900/40 text-cyan-300";
  if (value === "manual_pending" || value === "await_review" || value === "proposal_pending") return "bg-amber-900/40 text-amber-300";
  if (value === "context_pending" || value === "context_consumed") return "bg-sky-900/40 text-sky-300";
  if (value === "manual_rejected") return "bg-rose-900/40 text-rose-300";
  if (value === "clamped") return "bg-fuchsia-900/40 text-fuchsia-300";
  if (value.startsWith("skipped")) return "bg-rose-900/40 text-rose-300";
  return "bg-zinc-800 text-zinc-400";
}

export function compactProjection(projection: unknown): string {
  if (!projection || typeof projection !== "object") return "";
  const entries = Object.entries(projection as Record<string, unknown>)
    .map(([key, value]) => [key, Number(value || 0)] as const)
    .filter(([, value]) => Number.isFinite(value) && value > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);
  return entries.map(([key, value]) => `${key} ${Math.round(value * 100)}%`).join(" · ");
}

export function runtimeStatusLabel(status: string | undefined): string {
  const value = String(status || "").trim().toLowerCase();
  if (value === "manual_pending") return "待手动处理";
  if (value === "manual_committed") return "已人工结算";
  if (value === "manual_rejected") return "已人工否决";
  if (value === "await_review") return "等待复核";
  if (value === "context_pending") return "上下文待消化";
  if (value === "context_consumed") return "上下文已消化";
  if (value === "proposal_pending") return "提案待裁决";
  if (value === "auto_applied") return "自动已结算";
  if (value === "fact_only") return "仅命中事实";
  if (value === "clamped") return "护栏钳制";
  if (value === "skipped_dedup") return "重复跳过";
  if (value === "skipped_no_target") return "无目标跳过";
  return String(status || "未知");
}

export function normalizePluginTier(row: PluginCardRow): string {
  const direct = String(row.layer || "").trim().toUpperCase();
  if (/^L[0-4]$/.test(direct)) return direct;
  const causalTier = Number.isFinite(Number(row.causal_tier)) ? Math.round(row.causal_tier) : 0;
  const fromCausal = { 5: "L0", 4: "L1", 3: "L2", 2: "L3", 1: "L4" };
  if (causalTier >= 1 && causalTier <= 5 && Object.prototype.hasOwnProperty.call(fromCausal, causalTier)) {
    return String(fromCausal[causalTier as keyof typeof fromCausal]);
  }
  return "L?";
}

export function inferPluginSubCategory(plugin: PluginCardRow): string {
  const pluginId = String(plugin.plugin_id || "").trim();
  const tier = normalizePluginTier(plugin);
  if (tier === "L0") {
    if (pluginId.includes("l0.foundation")) return "基础五行基线";
    if (pluginId.includes("month_command")) return "月令主气";
    return "基础观测";
  }
  if (tier === "L1") {
    if (pluginId === "officer_see_hurt") return "官杀观测";
    if (pluginId.includes("op_status")) return "状态机观测";
    if (pluginId.includes("l1.physics.")) return "关系结构算子";
    if (pluginId.includes("narrative") || pluginId.includes("story")) return "叙事锚点";
    return "L1 插件";
  }
  if (tier === "L2") {
    if (pluginId.includes("classical.pattern")) return "格局专题";
    if (pluginId.includes("classical.ziping")) return "子平专题";
    if (pluginId.includes("classical.blind")) return "盲派专题";
    if (pluginId.includes("kong_wang") || pluginId.includes("shensha") || pluginId.includes("risk")) return "风险/象法观察";
    if (pluginId === "ten_god_pattern") return "十神主轴";
    if (pluginId === "narrative_clip") return "叙事剪辑";
    return "L2 逻辑插件";
  }
  if (tier === "L3") return "Narrative 观察";
  if (tier === "L4") return "战略叙事";
  if (plugin.family_label) return String(plugin.family_label).trim();
  return "未归类";
}

function pluginCategoryKey(value: string): string {
  const raw = String(value || "").trim().toLowerCase();
  const normalized = raw.replace(/[^a-z0-9\u4e00-\u9fff]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "");
  return normalized || "category";
}

export function buildPluginTierBuckets<TPlugin extends PluginCardRow>(
  rows: PluginPanelRowLike<TPlugin>[],
): PluginTierBucketLike<TPlugin>[] {
  const tierOrder = ["L0", "L1", "L2", "L3", "L4"];
  const byTier = new Map<string, Map<string, PluginPanelRowLike<TPlugin>[]>>();

  for (const row of rows) {
    const tier = normalizePluginTier(row.plugin);
    const category = inferPluginSubCategory(row.plugin);
    const tierBucket = byTier.get(tier) || new Map<string, PluginPanelRowLike<TPlugin>[]>();
    if (!byTier.has(tier)) byTier.set(tier, tierBucket);
    const key = pluginCategoryKey(category);
    const categoryBucket = tierBucket.get(key) || [];
    categoryBucket.push(row);
    tierBucket.set(key, categoryBucket);
  }

  const sortRows = (a: PluginPanelRowLike<TPlugin>, b: PluginPanelRowLike<TPlugin>): number => {
    const aOrder = Number(a.plugin.execution_order || 0);
    const bOrder = Number(b.plugin.execution_order || 0);
    if (aOrder !== bOrder) return aOrder - bOrder;
    return String(a.plugin.plugin_id || "").localeCompare(String(b.plugin.plugin_id || ""));
  };

  return tierOrder
    .map((tier) => {
      const categoryMap = byTier.get(tier);
      if (!categoryMap) return null;
      const rowsInTier: PluginPanelRowLike<TPlugin>[] = [];
      const categories: PluginCategoryBucketLike<TPlugin>[] = [];
      for (const [key, groupRows] of categoryMap.entries()) {
        const label = groupRows.length ? inferPluginSubCategory(groupRows[0]?.plugin) : "未归类";
        const sortedRows = [...groupRows].sort(sortRows);
        rowsInTier.push(...sortedRows);
        categories.push({ key, label, rows: sortedRows });
      }
      categories.sort((a, b) => b.rows.length - a.rows.length || a.label.localeCompare(b.label));
      return { tier, title: `L${tier.replace(/^L/, "")}层`, rows: rowsInTier.sort(sortRows), categories };
    })
    .filter((row): row is PluginTierBucketLike<TPlugin> => row !== null && row.rows.length > 0);
}
