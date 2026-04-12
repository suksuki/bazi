import type { LogicProposal, LlmDiagnosticData, PhysicsLabConfig, PluginSwitches, SeedPayload } from "@/features/stream-board/models";
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

/** 比较两处 `seedPayloadSignature` 字符串是否指向同一生辰（容忍 JSON 键顺序等导致的 !==） */
export function seedPayloadSignaturesCompatible(
  a: string | null | undefined,
  b: string | null | undefined,
): boolean {
  if (!a || !b) return false;
  if (a === b) return true;
  try {
    const pa = JSON.parse(a) as Record<string, unknown>;
    const pb = JSON.parse(b) as Record<string, unknown>;
    return (
      String(pa.date ?? "") === String(pb.date ?? "") &&
      String(pa.time ?? "") === String(pb.time ?? "") &&
      String(pa.calendar ?? "") === String(pb.calendar ?? "") &&
      String(pa.gender ?? "") === String(pb.gender ?? "")
    );
  } catch {
    return false;
  }
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

/** 与后端 `audit_helpers.ALLOWED_LOGIC_PROPOSAL_PARAM_KEYS` 一致：物理审计可改参键白名单 */
export const PHYSICS_AUDIT_LOGIC_PROPOSAL_PARAM_KEYS = new Set([
  "CF_FLOATING_DECAY",
  "THROUGH_STEM_BOOST",
  "CONFLICT_PENALTY_GAMMA",
  "A_PROTRUSION",
  "OFFICER_RESTRAINT_ALPHA",
  "POWER_DISTRIBUTION_GAMMA",
]);

/**
 * 物理审计 diagnosis 是否足以支撑 Inbox 勾选（「空意志」预检）。
 * 注意：回退路径下 top_anomaly 常为「未拿到结构化审计结论…」，与 diagnosis 并存；
 * 若用 top_anomaly 判假，会把整卡误锁死。故仅以 diagnosis 为准。
 */
export function isTrustworthyPhysicsAuditDiagnosis(
  diagnosis: string | null | undefined,
  _topAnomaly: string | null | undefined = undefined,
): boolean {
  const d = String(diagnosis || "").trim();
  if (!d) return false;
  // 仅当 diagnosis 本身是「无结论」占位句时才拦截，不回看 top_anomaly
  if (/未拿到结论|未拿到结构化审计结论/.test(d)) return false;
  return true;
}

/** 与 `audit_helpers.fallback_audit_response` diagnosis 前缀对齐 */
const PHYSICS_AUDIT_FALLBACK_DIAGNOSIS_PREFIX = "结构化审计回退";

/**
 * 物理审计是否为后端「结构化回退」路径：此类不应占多源断言里的「待定」大卡片，
 * 也不宜把占位 diagnosis 写入 semantic Inbox（详情仍在 Debug / physics_auditor_llm）。
 */
export function isPhysicsAuditFallbackUi(data: { diagnosis?: unknown; structured_hit?: unknown } | null | undefined): boolean {
  if (!data || typeof data !== "object") return false;
  if (data.structured_hit === false) return true;
  return String(data.diagnosis ?? "").trim().startsWith(PHYSICS_AUDIT_FALLBACK_DIAGNOSIS_PREFIX);
}

const _STRUCTURE_AUDIT_PATTERNS: { kinds: string[]; pattern: RegExp }[] = [
  { kinds: ["sanhe"], pattern: /三合|三合局|sanhe|支池|金局|火局|水局|木局|土局|合金局/i },
  { kinds: ["clash"], pattern: /六冲|相冲|对冲|地支冲|clash|liuchong/i },
  { kinds: ["combine"], pattern: /六合|合绊|liuhe|combine/i },
  { kinds: ["harm"], pattern: /六害|六穿|相害|相穿|穿害|pierce|harm/i },
  { kinds: ["punish"], pattern: /三刑|自刑|刑|punish/i },
];

/**
 * 当 metadata.conflict_matrix 已登记关键结构（如三合、六冲），而审计正文完全未提及时，
 * 视为与物理事实不同步（常见于旧审计或空 conflict_matrix 时代的回流），不展示「待定」区。
 */
export function isPhysicsAuditDiagnosisStaleVsConflictMatrix(
  diagnosis: string,
  top_anomaly: string,
  causal_reasoning: string,
  points: readonly { kind?: string | null; detail?: string | null }[],
): boolean {
  if (!points.length) return false;
  const haystack = `${diagnosis}\n${top_anomaly}\n${causal_reasoning}`;
  if (!haystack.trim()) return false;

  const need = new Set<string>();
  for (const p of points) {
    const k = String(p.kind || "").trim().toLowerCase();
    const d = String(p.detail || "");
    if (k) need.add(k);
    if (!k || k === "unknown") {
      if (/三合|三合局|支池/.test(d)) need.add("sanhe");
      if (/六冲|相冲/.test(d)) need.add("clash");
      if (/六合/.test(d)) need.add("combine");
      if (/害|穿/.test(d)) need.add("harm");
      if (/刑/.test(d)) need.add("punish");
    }
  }

  const structural = new Set(["sanhe", "clash", "combine", "harm", "punish"]);
  for (const row of _STRUCTURE_AUDIT_PATTERNS) {
    const hitKind = row.kinds.some((g) => need.has(g));
    if (!hitKind) continue;
    if (!row.pattern.test(haystack)) return true;
  }
  return false;
}

/** 与后端 `physics_fallback` 写入的 verdict_body 摘要一致：终判处于救急模板时不叠「待定审计」 */
export function isFinalVerdictPhysicsFallbackBody(text: string | null | undefined): boolean {
  const s = String(text || "").replace(/\s+/g, " ").trim();
  if (!s) return false;
  if (
    s.includes("盘局物理层已收敛") &&
    (s.includes("润色辞章") || s.includes("相互参证") || s.includes("sys.core.physics"))
  ) {
    return true;
  }
  if (s.includes("llm_empty_or_error_physics_fallback")) return true;
  return false;
}

const _PARAM_KEY_FROM_SQL_RE = /WHERE\s+param_key\s*=\s*['"]([A-Za-z0-9_]+)['"]/i;

/** 将 LLM 返回的 param_key 限制在白名单（与 normalize_audit_result 对齐的客户端兜底） */
export function coerceLogicProposalParamKey(proposal: LogicProposal): LogicProposal {
  const raw = String(proposal.param_key || "").trim();
  if (PHYSICS_AUDIT_LOGIC_PROPOSAL_PARAM_KEYS.has(raw)) return proposal;
  const m = _PARAM_KEY_FROM_SQL_RE.exec(String(proposal.sql_patch || ""));
  const k = m?.[1];
  if (k && PHYSICS_AUDIT_LOGIC_PROPOSAL_PARAM_KEYS.has(k)) {
    return { ...proposal, param_key: k };
  }
  return { ...proposal, param_key: "CF_FLOATING_DECAY" };
}

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

/** 物理审计 JSON：顶层 diagnosis 缺省时，从 logic_proposal.diagnosis / reason 提拔（避免「只有 JSON 无正文」）。 */
export function hoistPhysicsAuditDiagnosis(audit: Record<string, unknown> | null | undefined): string {
  if (!audit || typeof audit !== "object") return "";
  const top = typeof audit.diagnosis === "string" ? audit.diagnosis.trim() : "";
  if (top) return top;
  const lp = audit.logic_proposal;
  if (lp && typeof lp === "object" && !Array.isArray(lp)) {
    const d = (lp as { diagnosis?: unknown }).diagnosis;
    if (typeof d === "string" && d.trim()) return d.trim();
    const r = (lp as { reason?: unknown }).reason;
    if (typeof r === "string" && r.trim()) return r.trim();
    const exp = (lp as { expected_impact?: unknown }).expected_impact;
    if (typeof exp === "string" && exp.trim()) return exp.trim();
  }
  return "";
}

/** 同 seed 静默重算时合并审计 LLM 结果（与 useSeedAnalysis 对齐） */
export function mergeLlmDiagnosticSameSeedPreserve(
  sameSeedResubmit: boolean,
  previous: LlmDiagnosticData | null,
  auditData: Record<string, unknown>,
): LlmDiagnosticData {
  const hoisted = hoistPhysicsAuditDiagnosis(auditData);
  const next: LlmDiagnosticData = {
    diagnosis: hoisted || (typeof auditData.diagnosis === "string" ? auditData.diagnosis : undefined),
    alignment_score: typeof auditData.alignment_score === "number" ? auditData.alignment_score : undefined,
    top_anomaly: typeof auditData.top_anomaly === "string" ? auditData.top_anomaly : undefined,
    causal_reasoning: typeof auditData.causal_reasoning === "string" ? auditData.causal_reasoning : undefined,
    tuning_suggestions: Array.isArray(auditData.tuning_suggestions)
      ? auditData.tuning_suggestions.map((x: unknown) => String(x))
      : undefined,
    sql_patch: typeof auditData.sql_patch === "string" ? auditData.sql_patch : undefined,
    refresh_hint: typeof auditData.refresh_hint === "string" ? auditData.refresh_hint : undefined,
    logic_proposal: auditData.logic_proposal as LogicProposal | undefined,
    structured_hit: typeof auditData.structured_hit === "boolean" ? auditData.structured_hit : undefined,
    repair_mode: auditData.repair_mode != null ? String(auditData.repair_mode) : undefined,
  };
  if (!sameSeedResubmit || !previous) {
    return next;
  }
  const preferNextStr = (n?: string, p?: string | undefined) => {
    if (String(n ?? "").trim()) return n;
    if (String(p ?? "").trim()) return p;
    return n;
  };
  return {
    ...previous,
    ...next,
    diagnosis: preferNextStr(next.diagnosis, previous.diagnosis),
    top_anomaly: preferNextStr(next.top_anomaly, previous.top_anomaly),
    causal_reasoning: preferNextStr(next.causal_reasoning, previous.causal_reasoning),
    sql_patch: preferNextStr(next.sql_patch, previous.sql_patch),
    refresh_hint: preferNextStr(next.refresh_hint, previous.refresh_hint),
    repair_mode: preferNextStr(next.repair_mode, previous.repair_mode),
    alignment_score:
      typeof next.alignment_score === "number" ? next.alignment_score : previous.alignment_score,
    structured_hit: typeof next.structured_hit === "boolean" ? next.structured_hit : previous.structured_hit,
    tuning_suggestions:
      Array.isArray(next.tuning_suggestions) && next.tuning_suggestions.length
        ? next.tuning_suggestions
        : previous.tuning_suggestions,
    logic_proposal: next.logic_proposal ?? previous.logic_proposal,
  };
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
