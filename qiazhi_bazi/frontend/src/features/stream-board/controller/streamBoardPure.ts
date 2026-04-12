import type { PhysicsLabConfig, PluginSwitches, SeedPayload } from "@/features/stream-board/models";
import type { MetricSnapshot } from "./streamBoardTypes";

/** 与 persistSnapshot / mergeSnapshot 使用的 seed 签名一致（不含 reference_year） */
export function seedPayloadSignature(seed: SeedPayload | null | undefined): string | null {
  if (!seed) return null;
  return JSON.stringify({
    date: seed.date,
    time: seed.time,
    calendar: seed.calendar,
    gender: seed.gender,
  });
}

export function normalizeDecisionIds(list: string[]): string[] {
  return [...new Set(list.map((item) => String(item || "").trim()).filter(Boolean))].sort();
}

export function normalizedSnapshotDecisionIds(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return normalizeDecisionIds(value.map((item) => String(item)));
}

export function decisionIdsSignature(list: string[]): string {
  return JSON.stringify(normalizeDecisionIds(list));
}

/**
 * 合并快照中的 decision_selection_ids 与本地勾选：若快照缺少任一本地 id，视为陈旧回灌，保留本地；
 * 否则与快照做并集，以吸收服务端新增的勾选。
 */
export function mergeDecisionIdsPreferLocal(prev: string[], snapshot: string[]): string[] {
  const prevN = normalizeDecisionIds(prev);
  const snapN = normalizeDecisionIds(snapshot);
  const snapSet = new Set(snapN);
  for (const id of prevN) {
    if (!snapSet.has(id)) {
      return prevN;
    }
  }
  return normalizeDecisionIds([...prevN, ...snapN]);
}

export function buildBlindSchoolFeaturesPayload(sw: PluginSwitches) {
  return {
    enable_pierce_harm: sw.blindSchoolPierceHarm !== false,
    enable_tomb_vault: sw.blindSchoolTombVault !== false,
    enable_host_guest_bonus: sw.blindSchoolHostGuest !== false,
  };
}

const ALLOWED_USER_DIRECTIONS = new Set(["东", "南", "西", "北", "中"]);

/** analyze-seed / 静默重算：仅合法方位写入 physics_config，避免后端校验噪声 */
export function buildPhysicsConfigPayload(lab: PhysicsLabConfig): Record<string, unknown> {
  const cfg: Record<string, unknown> = { ...lab };
  const dir = String(cfg.user_target_direction || "").trim();
  if (!dir || !ALLOWED_USER_DIRECTIONS.has(dir)) {
    delete cfg.user_target_direction;
  } else {
    cfg.user_target_direction = dir;
  }
  return cfg;
}

export function extractMetricSnapshotFromPhysics(physicsTensor: Record<string, unknown> | null | undefined): MetricSnapshot {
  const auditLog = (physicsTensor?.audit_log as Record<string, unknown> | undefined) || {};
  const trace = (auditLog.trace as Record<string, unknown> | undefined) || {};
  const meta = (physicsTensor?.meta as Record<string, unknown> | undefined) || {};
  const absRaw = trace.clash_abs_loss_total ?? auditLog.clash_abs_loss_total ?? meta.clash_abs_loss_total ?? meta.abs_loss_total;
  const entropyRaw = meta.global_entropy;
  return {
    absLossTotal: typeof absRaw === "number" && Number.isFinite(absRaw) ? absRaw : null,
    entropy: typeof entropyRaw === "number" && Number.isFinite(entropyRaw) ? entropyRaw : null,
  };
}

/** 后端 meta.interaction_hub_mangpai → 并入实验室 interaction_hub（主权占优金标等） */
export function extractInteractionHubMangpai(physicsTensor: Record<string, unknown> | null | undefined): Record<string, unknown> {
  if (!physicsTensor || typeof physicsTensor !== "object") return {};
  const meta = physicsTensor.meta as Record<string, unknown> | undefined;
  const m = meta?.interaction_hub_mangpai;
  if (!m || typeof m !== "object" || Array.isArray(m)) return {};
  return m as Record<string, unknown>;
}

export function interpolateColor(startHex: string, endHex: string, ratio: number): string {
  const normalized = Math.max(0, Math.min(1, ratio));
  const parse = (hex: string) => {
    const v = hex.replace("#", "");
    const full = v.length === 3 ? v.split("").map((x) => `${x}${x}`).join("") : v;
    return {
      r: parseInt(full.slice(0, 2), 16),
      g: parseInt(full.slice(2, 4), 16),
      b: parseInt(full.slice(4, 6), 16),
    };
  };
  const a = parse(startHex);
  const b = parse(endHex);
  const toHex = (v: number) => Math.round(v).toString(16).padStart(2, "0");
  const r = a.r + (b.r - a.r) * normalized;
  const g = a.g + (b.g - a.g) * normalized;
  const bVal = a.b + (b.b - a.b) * normalized;
  return `#${toHex(r)}${toHex(g)}${toHex(bVal)}`;
}
