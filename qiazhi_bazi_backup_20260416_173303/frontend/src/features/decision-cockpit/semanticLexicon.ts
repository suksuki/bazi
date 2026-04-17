/**
 * 裁决者可读：插件 ID、判语血统码、时序枚举等 → 中文语义标题 / 句子。
 */

export const PLUGIN_DISPLAY_NAMES: Record<string, string> = {
  "classical.blind_school.v1": "盲派初级规则库",
  "classical.wangshuai.v1": "子平旺衰模型",
  "modern.wealth_risk.v1": "现代财富风险模块",
  "base.chronos": "大运流年时空轴（Chronos）",
  "sys.core.physics": "物理引擎（L1 总线）",
  "l1_branch_sanhe": "L1 · 地支三合局",
  "l1_branch_liuhe": "L1 · 地支六合",
  "l1_branch_liuchong": "L1 · 地支六冲",
  "l1_branch_gov_kill_mix": "L1 · 官杀混杂",
};

/** 判语 / 证据行内可能出现的英文码 → 人话标题（作 Item Title） */
export const PROVENANCE_CODE_TITLES: Record<string, string> = {
  BRANCH_CLASH_HARM: "[冲突审计] 地支相害影响评估",
  DEITY_ABS_LEAKAGE: "[能量流转] 十神泄气深度诊断",
  L1_SGJG: "[结构对抗] 伤官见官张力评估",
  L1_STRUCTURE: "[结构登记] 地支合成场登记",
  PATTERN_SOVEREIGNTY: "[格局主权] 格局优先于单点 L1 对抗",
  SANHE_CLUSTER: "[合成场] 三合聚能登记",
  STEM_FUSION_LOCK: "[天干锁相] 五合不化对十神轴的冻结",
  POLARITY_FLIP: "[路由极性] 多插件对同一十神轴符号相反",
};

/** 时序 / 日志中的裸枚举 token → 不出现原文时的替换句 */
export const TIMELINE_ENUM_PHRASES: Array<{ re: RegExp; zh: string }> = [
  {
    re: /\bNEGOTIATE_IMPACT\b|negotiate_impact|negotiate impact/gi,
    zh: "正在平衡多插件冲突，最终结论已按路由策略融合（若启用流派主权则优先采纳盲派高权建议）",
  },
  { re: /\bstrategy_applied\b\s*[:=]\s*weighted_sum/gi, zh: "路由策略：加权求和（保守融合）" },
  { re: /\bstrategy_applied\b\s*[:=]\s*school_priority/gi, zh: "路由策略：流派优先（盲派向量覆盖重叠轴）" },
  { re: /\bstrategy_applied\b\s*[:=]\s*manual_arbitration/gi, zh: "路由策略：人工仲裁（等待裁决人）" },
  { re: /\bclassical\.blind_school\.v1\b/g, zh: "盲派初级规则库" },
  { re: /\bclassical\.wangshuai\.v1\b/g, zh: "子平旺衰模型" },
  { re: /\bPlugin mount:\s*/gi, zh: "插件挂载：" },
];

export function humanizePluginId(pluginId: string): string {
  const k = String(pluginId || "").trim();
  if (PLUGIN_DISPLAY_NAMES[k]) return PLUGIN_DISPLAY_NAMES[k];
  return k
    .replace(/^classical\./, "")
    .replace(/^modern\./, "")
    .replace(/\.v\d+$/i, "")
    .replace(/\./g, " · ");
}

/**
 * physics_tensor.evidence 等处的单行 `key=value`（与 physics_engine 写入一致）→ 具象中文。
 * 命中则返回标题 + 说明；未命中返回 null，交由上层继续处理。
 */
export function humanizeEvidenceKvLine(raw: string): { title: string; body: string } | null {
  const s = String(raw || "").trim();
  if (!s || /[\n\r]/.test(s)) return null;

  let m = /^solar_term=(.+)$/.exec(s);
  if (m) {
    const v = m[1].trim();
    const explain =
      v === "derived_from_month_branch"
        ? "未写入精确交节节气名时，由月支推导季节上下文，用于气候矩阵（与完整节气表略有近似）。"
        : `当前节气键为「${v}」，参与季节向量与气候权重。`;
    return { title: "节气 / 季节上下文", body: `${explain} 技术字段：${s}` };
  }

  m = /^conflict_count=(\d+)$/.exec(s);
  if (m) {
    const n = Number.parseInt(m[1], 10);
    const explain =
      n === 0
        ? "物理层登记的结构冲突点数量为 0；不会因「多插件对同一十神轴符号相反」在路由里额外打折。"
        : `已登记 ${n} 个结构冲突点，会通过 conflict_gamma 参与整体强度折扣。`;
    return { title: "结构冲突计数（物理登记）", body: `${explain} 技术字段：${s}` };
  }

  m = /^root\.no_root=(True|False|true|false)$/.exec(s);
  if (m) {
    const noRoot = /^true$/i.test(m[1]);
    const explain = noRoot
      ? "判定日主无强根：比劫等帮身支点偏弱，「浮动十神」类衰减策略可能启用。"
      : "判定存在可识别根气支点，不因无根单独施加浮动衰减。";
    return { title: "日主根气（无根判定）", body: `${explain} 技术字段：${s}` };
  }

  m = /^根气\.no_root=(.+)$/.exec(s);
  if (m) {
    const v = String(m[1]).toLowerCase();
    const noRoot = v === "true" || v === "1";
    const explain = noRoot
      ? "根气审计：日主无根（与 root.no_root 同源信号）。"
      : "根气审计：未标为无根。";
    return { title: "根气审计（日主）", body: `${explain} 技术字段：${s}` };
  }

  m = /^param_version=(.+)$/.exec(s);
  if (m) {
    const vid = m[1].trim();
    return {
      title: "物理参数版本锚点",
      body: `本次张量与下列参数版本绑定，便于机房复现与对齐：${vid}。技术字段：${s}`,
    };
  }

  m = /^climate\.enabled=(True|False|true|false)$/.exec(s);
  if (m) {
    const on = /^true$/i.test(m[1]);
    return {
      title: "气候修正层",
      body: `${on ? "气候修正模块已参与调节五行向量。" : "气候修正未启用，向量不经气候层二次缩放。"} 技术字段：${s}`,
    };
  }

  m = /^climate\.factors=(.+)$/.exec(s);
  if (m) {
    const payload = m[1].trim();
    const short = payload.length > 220 ? `${payload.slice(0, 220)}…` : payload;
    return {
      title: "气候修正因子",
      body: `各气候因子对向量的贡献权重（摘要）：${short}。完整见技术字段：${s}`,
    };
  }

  return null;
}

/** 将文本中的已知英文码替换为中文标题（用于判语血统 Item 标题） */
export function humanizeProvenanceSnippet(text: string): { title: string; body: string } {
  const raw = String(text || "").trim();
  if (!raw) return { title: "（空条目）", body: "" };

  const kv = humanizeEvidenceKvLine(raw);
  if (kv) return kv;

  for (const [code, title] of Object.entries(PROVENANCE_CODE_TITLES)) {
    if (raw.includes(code)) {
      return { title, body: raw };
    }
  }
  const head = raw.split(/[。；\n]/)[0]?.slice(0, 48) || raw.slice(0, 48);
  return { title: head.length < raw.length ? `${head}…` : head, body: raw };
}

export function stripTimelineEnumJargon(line: string): string {
  let s = String(line || "");
  for (const { re, zh } of TIMELINE_ENUM_PHRASES) {
    s = s.replace(re, zh);
  }
  return s;
}
