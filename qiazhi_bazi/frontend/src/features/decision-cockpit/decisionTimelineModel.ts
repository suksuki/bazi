/**
 * 将快照中的审计痕迹装配为「决策时序」节点，并把后端指令 token 译为裁决者可读文案。
 */

import { humanizePluginId, stripTimelineEnumJargon } from "./semanticLexicon";

export type TimelineTier = "physics" | "plugin" | "router" | "llm" | "verdict" | "hub";

export type DecisionTimelineEvent = {
  id: string;
  /** 展示用时间序标签（部分来源无真实时间戳，用相对序号） */
  tsLabel: string;
  tier: TimelineTier;
  raw: string;
  titleZh: string;
  bodyZh: string;
};

const ROUTE_RULES: Array<{ re: RegExp; zh: string }> = [
  { re: /L1_SGJG|伤官见官|SHANG_GUAN_JIAN_GUAN/i, zh: "正在调和伤官见官与官杀结构的冲突权重（Junction / 旺衰枢纽）" },
  { re: /RECONCILE|school_priority|流派优先|流派主权|school_sov/i, zh: "正在执行 CausalRouter 仲裁：多插件十神极性分歧按策略融合" },
  { re: /weighted_sum|加权求和|保守模式/i, zh: "正在以加权求和（保守策略）融合各插件对十神轴的贡献" },
  { re: /manual_arbitration|人工仲裁/i, zh: "路由策略为人工仲裁：极性冲突已检出，等待裁决人裁定" },
  { re: /sanhe|三合|composite_field/i, zh: "正在登记或校正地支三合合成场对场强的贡献" },
  { re: /stem_fusion|天干五合|is_locked/i, zh: "正在应用天干五合锁相：冻结部分十神对外影响量" },
  { re: /wealth_seal|财.*印|财星破印/i, zh: "正在应用财星破印合并偏置：压低印、抬高财轴" },
  { re: /HARD_ROUTE|consensus|共识覆盖|Param\s+'/i, zh: "用户共识写入硬路径：关键 η 参数已按会话决议重绑定" },
  { re: /Polarity_Flip|极性/i, zh: "检测到两插件对同一十神轴符号相反，已纳入路由极性事件集" },
  { re: /PLUGIN_INTERVENE|插件介入/i, zh: "插件介入流水线：盲派 / 旺衰等 L2 算子输出已汇入物理张量" },
  { re: /FINAL_DECISION|终审|签发/i, zh: "终审断言已签发：因果链与版本指纹已固化" },
  { re: /MANGPAI|盲派|穿局|墓库/i, zh: "盲派语义层（穿害墓库等）已参与证据装配" },
];

export function translateBackendLine(line: string): string {
  const s = stripTimelineEnumJargon(String(line || "").trim());
  if (!s) return "（空指令）";
  for (const { re, zh } of ROUTE_RULES) {
    if (re.test(s)) return zh;
  }
  if (s.length <= 120) return `系统行为：${s}`;
  return `系统行为：${s.slice(0, 118)}…`;
}

function tierFromLine(line: string, hint?: TimelineTier): TimelineTier {
  if (hint) return hint;
  const s = line;
  if (/CausalRouter|causal_routing|routing_decision|negotiate|冲突事件|strategy_applied/i.test(s)) return "router";
  if (/llm|判词|prompt|观察项|Qwen/i.test(s)) return "llm";
  if (/classical\.|wangshuai|plugin|Skill|盲派|旺衰/i.test(s)) return "plugin";
  if (/终审|final_verdict|verdict_body|签发/i.test(s)) return "verdict";
  if (/audit_items|interaction_hub|Hub/i.test(s)) return "hub";
  return "physics";
}

export function buildDecisionTimelineEvents(snapshot: Record<string, unknown> | null): DecisionTimelineEvent[] {
  if (!snapshot || typeof snapshot !== "object") return [];
  const out: DecisionTimelineEvent[] = [];
  let seq = 0;
  const push = (tier: TimelineTier, raw: string, hintTier?: TimelineTier) => {
    const t = tierFromLine(raw, hintTier);
    const id = `tl-${seq++}`;
    out.push({
      id,
      tsLabel: `T${String(seq).padStart(2, "0")}`,
      tier: t,
      raw,
      titleZh: tierLabelZh(t),
      bodyZh: translateBackendLine(raw),
    });
  };

  const physics = snapshot.physics_tensor as Record<string, unknown> | undefined;
  const audit = (physics?.audit_log as Record<string, unknown> | undefined) || {};
  const trace = (audit.trace as Record<string, unknown> | undefined) || {};
  const hardLogs = Array.isArray(trace.hard_route_logs) ? trace.hard_route_logs : [];
  hardLogs.forEach((x) => push("physics", String(x)));

  const ev = Array.isArray(physics?.evidence) ? (physics!.evidence as unknown[]) : [];
  ev.forEach((x) => push("physics", `Evidence: ${String(x)}`));

  const conf =
    typeof physics?.confidence === "number" && Number.isFinite(physics.confidence as number)
      ? (physics.confidence as number)
      : null;
  if (conf != null) push("physics", `Physics confidence snapshot: ${(conf * 100).toFixed(1)}%`);

  const plugins = (physics?.plugin_outputs as Record<string, unknown> | undefined) || {};
  Object.keys(plugins).forEach((pid) => {
    const row = plugins[pid] && typeof plugins[pid] === "object" ? (plugins[pid] as Record<string, unknown>) : {};
    const topCs = typeof row.confidence_score === "number" && Number.isFinite(row.confidence_score) ? row.confidence_score : null;
    const pl = row.payload && typeof row.payload === "object" ? (row.payload as Record<string, unknown>) : null;
    const plConf =
      pl && typeof pl.confidence === "number" && Number.isFinite(pl.confidence) ? (pl.confidence as number) : null;
    const confP = topCs ?? plConf;
    const label = humanizePluginId(pid);
    push(
      "plugin",
      `插件挂载：${label}${confP != null ? ` · 匹配置信度 ${(confP * 100).toFixed(0)}%` : ""}（内部 ID 已脱敏）`,
    );
  });

  const cra = Array.isArray(audit.causal_routing_audit_items) ? audit.causal_routing_audit_items : [];
  cra.forEach((item, i) => {
    if (!item || typeof item !== "object") return;
    const row = item as Record<string, unknown>;
    const rd = String(row.routing_decision || row.strategy_applied || JSON.stringify(row)).slice(0, 600);
    push("router", `[CausalRouter#${i + 1}] ${rd}`, "router");
  });

  const hub = snapshot.interaction_hub as Record<string, unknown> | undefined;
  const auditItems = Array.isArray(hub?.audit_items) ? (hub.audit_items as Record<string, unknown>[]) : [];
  auditItems.forEach((item, i) => {
    const blob = `${String(item.step || "")} ${String(item.action || "")}`.trim();
    if (blob) push("hub", `[Hub#${i + 1}] ${blob}`, "hub");
  });

  const logs = Array.isArray(hub?.result_logs) ? (hub.result_logs as string[]) : [];
  logs.slice(-16).forEach((line) => {
    if (
      /\[MANGPAI_CHIP\]|\[FINAL_DECISION|语义裁决|PLUGIN_INTERVENE|CRITICAL|ENERGY_OVERLOAD/i.test(line)
    ) {
      push("hub", line, "hub");
    }
  });

  const llmPrompt = typeof snapshot.llm_prompt === "string" ? snapshot.llm_prompt : "";
  if (llmPrompt.trim()) {
    push("llm", `LLM 首条装配上下文（截断）: ${llmPrompt.slice(0, 240)}…`, "llm");
  }

  const fv = snapshot.final_verdict as Record<string, unknown> | undefined;
  const body = fv?.body ? String(fv.body).slice(0, 400) : "";
  if (body) push("verdict", `终审断言摘要: ${body}${String(fv?.body).length > 400 ? "…" : ""}`, "verdict");

  return out;
}

function tierLabelZh(tier: TimelineTier): string {
  switch (tier) {
    case "physics":
      return "物理层";
    case "plugin":
      return "插件介入";
    case "router":
      return "CausalRouter 仲裁";
    case "llm":
      return "LLM 证据装配";
    case "verdict":
      return "终审断言";
    case "hub":
      return "交互中枢";
    default:
      return "其它";
  }
}
