/**
 * physics_tensor.meta 中参与物理收敛对比的键（数值/结构/节气等），不含 LLM 叙事。
 */
const META_CONVERGENCE_KEYS = new Set([
  "params",
  "solar_term",
  "climate_season",
  "global_entropy",
  "l1_junction_flags",
  "pattern_profile",
  "energy_flow_audit",
  "causal_routing",
]);

/** 顶层物理数值/结构字段（排除 audit_log、evidence 文本、plugin 内 LLM 块等） */
const TENSOR_TOP_CONVERGENCE_KEYS = ["normalized", "deity_scores", "deity_energy_axes", "deity_components", "confidence"] as const;

/**
 * 从 physics_tensor 抽出「物理收敛」子树：仅能量矩阵、神煞分、轴/组件、置信度及 meta 白名单。
 * 严格排除 diagnosis、causal_reasoning、tuning_suggestions、判词遥测等一切易随 LLM 抖动的字段。
 */
export function extractPhysicsTensorConvergenceCore(tensor: unknown): Record<string, unknown> | null {
  if (!tensor || typeof tensor !== "object" || Array.isArray(tensor)) return null;
  const t = tensor as Record<string, unknown>;
  const out: Record<string, unknown> = {};
  for (const k of TENSOR_TOP_CONVERGENCE_KEYS) {
    if (t[k] !== undefined) out[k] = t[k];
  }
  const metaRaw = t.meta;
  if (metaRaw && typeof metaRaw === "object" && !Array.isArray(metaRaw)) {
    const m = metaRaw as Record<string, unknown>;
    const slim: Record<string, unknown> = {};
    const keys = Object.keys(m).filter((k) => META_CONVERGENCE_KEYS.has(k)).sort();
    for (const k of keys) {
      slim[k] = m[k];
    }
    if (Object.keys(slim).length > 0) out.meta = slim;
  }
  return Object.keys(out).length > 0 ? out : null;
}

/**
 * 稳定序列化 physics_tensor 用于「前后两次是否完全一致」对比（键排序、深度上限防环）。
 */
export function stableStringifyForHash(value: unknown, depth = 0): string {
  if (depth > 48) return '"[max-depth]"';
  if (value === null) return "null";
  const t = typeof value;
  if (t === "number") return Number.isFinite(value as number) ? String(value) : '"NaN"';
  if (t === "boolean") return value ? "true" : "false";
  if (t === "string") return JSON.stringify(value);
  if (t === "bigint") return `"bigint:${String(value)}"`;
  if (t === "undefined") return "undefined";
  if (t !== "object") return JSON.stringify(String(value));
  if (Array.isArray(value)) {
    return `[${value.map((x) => stableStringifyForHash(x, depth + 1)).join(",")}]`;
  }
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringifyForHash(obj[k], depth + 1)}`).join(",")}}`;
}

/**
 * 与「掐指一算」成功后 `lastSuccessfulInputBundle` 对齐：仅含 analyze-seed 实际依赖的输入
 *（生辰、插件权重、流年、physics_config 来源的 lab）。
 * 不包含 Inbox `decision_selection_ids`：该状态会随快照回灌、Inbox 重挂载而波动，若纳入指纹会误触发档位复位（再算 → 一算）。
 * `labConfig` 使用稳定键序序列化，避免与 `useMemo` 快照逐字节不一致。
 */
export function buildFullRecalcInputBundle(input: {
  seedSignature: string;
  paramSignature: string;
  referenceYear: number;
  labConfig: unknown;
}): string {
  return JSON.stringify({
    s: input.seedSignature,
    p: input.paramSignature,
    y: input.referenceYear,
    l: stableStringifyForHash(input.labConfig),
  });
}

/**
 * 物理收敛指纹：仅对 {@link extractPhysicsTensorConvergenceCore} 子树哈希。
 * LLM 诊断/因果叙事等不参与对比，避免断言文案随机性误判「物理未收敛」。
 */
export function physicsTensorFingerprint(tensor: unknown): string {
  const core = extractPhysicsTensorConvergenceCore(tensor);
  if (!core) return "";
  try {
    const s = stableStringifyForHash(core);
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return (h >>> 0).toString(16).padStart(8, "0");
  } catch {
    return "";
  }
}
