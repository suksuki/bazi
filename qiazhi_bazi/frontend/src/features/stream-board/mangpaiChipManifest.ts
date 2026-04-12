/**
 * 盲派芯片（MANGPAI_CHIP）语义模板：与日志行中的物理信号解耦，供 UI/叙事/教示统一引用。
 * 后端仍输出 `[MANGPAI_CHIP] …` 技术行；此处仅提供「人读」短锚，不参与力学计算。
 */
export const MANGPAI_CHIP_MANIFEST = {
  id: "mp_v1",
  semantic_templates: {
    tomb_locked: "墓库势能闭锁，才华难以施展",
    pierce_active: "六穿剧烈，根基存在物理损耗",
    gain_positive: "做功路径清晰，宜顺势而为",
  },
} as const;

export type MangpaiChipSemanticTemplateKey = keyof typeof MANGPAI_CHIP_MANIFEST.semantic_templates;

/** 按模板键取中文短句；未知键返回 undefined */
export function mangpaiChipSemanticLine(key: string): string | undefined {
  const row = MANGPAI_CHIP_MANIFEST.semantic_templates;
  if (key in row) return row[key as MangpaiChipSemanticTemplateKey];
  return undefined;
}

/**
 * 从单条 chip 日志粗分类到模板键（启发式，与 ResultInterpretation.inferSkillHintFromAssertionLine 互补）。
 */
export function inferMangpaiChipTemplateKey(line: string): MangpaiChipSemanticTemplateKey | null {
  const t = String(line || "");
  if (t.includes("墓库") || t.includes("闭库") || t.includes("闭锁")) return "tomb_locked";
  if (t.includes("穿局") || t.includes("六穿") || /子未|丑午|寅巳|卯辰|申亥|酉戌/.test(t)) return "pierce_active";
  if (t.includes("宾主") || t.includes("红利") || t.includes("做功路径")) return "gain_positive";
  return null;
}

/** 从 work_vector 单条（type/detail/direction）推断语义短锚，供「盲派做功链路」展示。 */
export function semanticAnchorForBlindWorkVectorItem(item: Record<string, unknown>): string | null {
  const blob = [item.type, item.detail, item.direction, item.summary].map((x) => String(x || "")).join(" ");
  const k = inferMangpaiChipTemplateKey(blob);
  if (!k) return null;
  return mangpaiChipSemanticLine(k) ?? null;
}

/** 由芯片日志 + 诊断正文汇总「金句」前缀（无则空串）。 */
export function mangpaiDiagnosisSemanticPrefix(chipLogs: readonly string[], diagnosis: string): string {
  const keys = new Set<MangpaiChipSemanticTemplateKey>();
  for (const line of chipLogs) {
    const k = inferMangpaiChipTemplateKey(line);
    if (k) keys.add(k);
  }
  if (keys.size === 0) {
    const k = inferMangpaiChipTemplateKey(diagnosis);
    if (k) keys.add(k);
  }
  const parts = [...keys].map((k) => mangpaiChipSemanticLine(k)).filter(Boolean) as string[];
  if (!parts.length) return "";
  return `${parts.join("；")}｜`;
}

/** 在 diagnosis 头部拼接盲派语义金句（已带头则跳过）。 */
export function augmentDiagnosisWithMangpaiManifest(diagnosis: string, chipLogs: readonly string[]): string {
  const head = mangpaiDiagnosisSemanticPrefix(chipLogs, diagnosis);
  if (!head) return String(diagnosis || "").trim();
  const d = String(diagnosis || "").trim();
  if (d.startsWith(head)) return d;
  const core = head.replace(/｜$/, "");
  if (core && (d.startsWith(core) || core.split("；").some((p) => p && d.startsWith(p)))) return d;
  return head + d;
}
