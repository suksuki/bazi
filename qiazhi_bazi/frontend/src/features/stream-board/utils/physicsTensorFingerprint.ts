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

/** 返回十六进制指纹；tensor 缺失时为 "" */
export function physicsTensorFingerprint(tensor: unknown): string {
  if (!tensor || typeof tensor !== "object") return "";
  try {
    const s = stableStringifyForHash(tensor);
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
