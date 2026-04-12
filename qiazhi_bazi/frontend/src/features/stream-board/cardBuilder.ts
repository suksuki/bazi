import type { BaziMetadata } from "@/types/bazi";
import { inferDecisionSkillId } from "@/features/decision-inbox/skillInference";
import type { DecisionSignalToNoiseMeta, InboxCard, LogicProposal } from "./models";
import { sysCorePhysicsPayload } from "./sysCorePhysics";

export type { DecisionSignalToNoiseMeta };

/** 与后端 SANHE_GROUPS 一致：地支 Unicode 排序后的拼接键 → 局名 */
const SANHE_SORTED_KEY_TO_TITLE: Record<string, string> = {
  午寅戌: "寅午戌火局",
  子申辰: "申子辰水局",
  卯亥未: "亥卯未木局",
  丑巳酉: "巳酉丑金局",
};

function _sortedBranchKey(branches: string[]): string {
  return [...new Set(branches)].sort().join("");
}

function _sanheBureauTitle(branches: string[]): string {
  const key = _sortedBranchKey(branches);
  return SANHE_SORTED_KEY_TO_TITLE[key] || `地支三合（${branches.join("、")}）`;
}

function _sanheTendencyMarkdown(bureauTitle: string): string {
  const stability =
    "三合聚轴会抬高对应五行的**场强权重**，使参与支位在冲合刑害叙事中更「成局」、更难被单点冲散；请在终判中结合根气、透干与岁运评估地支结构的稳定性。";
  if (bureauTitle.includes("金局")) {
    return (
      `${bureauTitle}已在 L1 聚能登记（plugin_outputs.sys.core.physics）。**能量增益**：金气聚轴带来肃杀、规则与收敛做功；` +
      `**稳定性**：${stability}若木火为喜用，需评估合局对食伤透发与柔性的压制；若金为喜用，则利于决断与资源固化。`
    );
  }
  if (bureauTitle.includes("火局")) {
    return `${bureauTitle}已登记。**能量增益**：火气聚轴增强表达、动能与「炎上」做功；**稳定性**：${stability}注意过燥对金水体的抽干。`;
  }
  if (bureauTitle.includes("水局")) {
    return `${bureauTitle}已登记。**能量增益**：水气聚轴增强智略、渗透与「润下」做功；**稳定性**：${stability}注意过寒对火土的抑制。`;
  }
  if (bureauTitle.includes("木局")) {
    return `${bureauTitle}已登记。**能量增益**：木气聚轴增强条达、进取与「曲直」做功；**稳定性**：${stability}注意过旺对土的克伐。`;
  }
  return `${bureauTitle}已登记。**能量增益**：合局抬升该五行场强；**稳定性**：${stability}请结合全局向量与十神轴评估格调抬升或偏枯。`;
}

/** 由 physics_tensor 装配地支三合 Decision 卡片（不受 Inbox 信噪比门控清空判词观察项的影响）。 */
export function buildSanheStructureCards(physicsTensor: Record<string, unknown> | null | undefined): InboxCard[] {
  if (!physicsTensor || typeof physicsTensor !== "object") return [];
  const po = physicsTensor.plugin_outputs as Record<string, unknown> | undefined;
  const payload = sysCorePhysicsPayload(po);
  const raw = payload && Array.isArray(payload.sanhe_clusters) ? payload.sanhe_clusters : [];
  const clusters: unknown[] = Array.isArray(raw) ? raw : [];
  const out: InboxCard[] = [];
  clusters.forEach((cl, idx) => {
    if (!cl || typeof cl !== "object") return;
    const row = cl as Record<string, unknown>;
    const brs = Array.isArray(row.branches) ? row.branches.map((x) => String(x)) : [];
    if (brs.length < 3) return;
    const bureauTitle = _sanheBureauTitle(brs);
    const stat = String(row.energy_vault_status || "AGGREGATED");
    const nodes = Array.isArray(row.nodes) ? row.nodes : [];
    const nodeLine = nodes
      .map((n) => {
        if (!n || typeof n !== "object") return "";
        const o = n as Record<string, unknown>;
        const p = String(o.pillar || "");
        const b = String(o.branch || "");
        return p && b ? `${p}:${b}` : "";
      })
      .filter(Boolean)
      .join("，");
    const id = `inbox-sanhe-${idx}`;
    const base: InboxCard = {
      id,
      title: "地支三合局锁定",
      displayText: `${bureauTitle} · ${stat}`,
      conflictDetail: `nodes=${nodeLine || "—"}`,
      markdown: _sanheTendencyMarkdown(bureauTitle),
      cardType: "L1_STRUCTURE",
      pluginAuditAnchorId: "sys.core.physics",
    };
    out.push({ ...base, skillId: inferDecisionSkillId(base, []) });
  });
  return out;
}

function buildPatternSovereigntyCard(
  patternProfile: Record<string, unknown> | null | undefined,
  l1JunctionFlags: Record<string, unknown> | null | undefined,
): InboxCard | null {
  if (!patternProfile || typeof patternProfile !== "object") return null;
  if (!patternProfile.sovereignty_priority) return null;
  if (!l1JunctionFlags || typeof l1JunctionFlags !== "object") return null;
  if (!Boolean(l1JunctionFlags.SHANG_GUAN_JIAN_GUAN)) return null;
  const rawLines = patternProfile.xi_ji_reversal_lines;
  const lines = Array.isArray(rawLines)
    ? rawLines.filter((x): x is string => typeof x === "string" && x.trim().length > 0)
    : [];
  const md = [
    "**格局优先（Pattern Sovereignty）**",
    "格局判定与 L1「伤官见官」同时成立：已执行「格局优先」，合并域 η 对顺势管道做反转增强；L1 对抗叙事不单独接管结论域。",
    ...lines.map((l) => `- ${l}`),
  ].join("\n");
  return {
    id: "inbox-pattern-sovereignty",
    title: "格局优先 · 主权覆盖 L1",
    displayText: "PATTERN_SOVEREIGNTY：从格主权下「被克泄」可转为顺势增益",
    conflictDetail: "格局优先：从格主权压制 L1 伤官见官的对抗解读",
    markdown: md,
    cardType: "conflict",
    skillId: "PATTERN_SOVEREIGNTY",
    sovereigntyMark: "PATTERN_SOVEREIGNTY",
  };
}

export function buildInboxCards(params: {
  metadata: BaziMetadata | null;
  firstPromptText: string;
  auditorProposalCards: InboxCard[];
  resolvedCardIds: string[];
  t: (text: string) => string;
  /** physics_tensor.meta.decision_signal_to_noise：低信噪且无 CRITICAL 时不生成判词观察项 */
  decisionSignalToNoise?: DecisionSignalToNoiseMeta | null;
  /** physics_tensor.meta.pattern_profile */
  patternProfile?: Record<string, unknown> | null;
  /** physics_tensor.meta.l1_junction_flags：与格局主权冲突检测 */
  l1JunctionFlags?: Record<string, unknown> | null;
  /** physics_tensor：装配三合 L1_STRUCTURE 卡片 */
  physicsTensor?: Record<string, unknown> | null;
}): InboxCard[] {
  const {
    metadata,
    firstPromptText,
    auditorProposalCards,
    resolvedCardIds,
    t,
    decisionSignalToNoise,
    patternProfile,
    l1JunctionFlags,
    physicsTensor,
  } = params;
  const sanheCards = buildSanheStructureCards(physicsTensor ?? null);
  if (!metadata) {
    return sanheCards.filter((card) => !resolvedCardIds.includes(card.id));
  }
  const conflictPoints = metadata.conflict_matrix?.points ?? [];

  let sentenceItems = firstPromptText
    .replace(/\r/g, "")
    .split(/\n+/)
    .flatMap((line) => line.split(/(?<=[。！？!?])/))
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 4)
    .map((text, index) => {
      const base = {
        id: `llm-observe-${index}`,
        title: `判词观察项 ${index + 1}`,
        conflictDetail: text,
        markdown: text,
        displayText: text,
        cardType: "conflict" as const,
      };
      return { ...base, skillId: inferDecisionSkillId(base, conflictPoints) };
    });

  if (decisionSignalToNoise?.inbox_conflict_cards_eligible === false) {
    sentenceItems = [];
  }

  const proposalCards = auditorProposalCards.map((card, index) => {
    const id = card.id || `auditor-proposal-${index}-${card.title}`;
    const merged = { ...card, id, cardType: "auditor-proposal" as const };
    return { ...merged, skillId: inferDecisionSkillId(merged, conflictPoints) };
  });

  const byId = new Map<string, InboxCard>();
  for (const item of sentenceItems) {
    byId.set(item.id, item);
  }
  proposalCards.forEach((card, index) => {
    const id = card.id || `auditor-proposal-${index}-${card.title}`;
    byId.set(id, { ...card, id });
  });

  const mergedList =
    sentenceItems.length > 0 || proposalCards.length > 0 ? Array.from(byId.values()) : [];
  const mergedCards =
    mergedList.length > 0
      ? [
          ...mergedList.filter((c) => c.cardType === "auditor-proposal"),
          ...mergedList.filter((c) => c.cardType !== "auditor-proposal"),
        ]
      : (() => {
          const fb = {
            id: "fallback-deep-scan",
            title: "继续深度扫描",
            conflictDetail: "进入深层扫描",
            markdown: "当前无可展示决策项，是否继续执行深层结构扫描？",
            displayText: t("进入深层扫描"),
            cardType: "conflict" as const,
          };
          return [{ ...fb, skillId: inferDecisionSkillId(fb, conflictPoints) }];
        })();

  const patternCard = buildPatternSovereigntyCard(patternProfile, l1JunctionFlags);
  const withSovereignty = patternCard
    ? [patternCard, ...mergedCards.filter((c) => c.id !== patternCard.id)]
    : mergedCards;
  return [...sanheCards, ...withSovereignty].filter((card) => !resolvedCardIds.includes(card.id));
}

export function createAuditorProposalCard(proposal: LogicProposal): InboxCard | null {
  const paramKey = proposal?.param_key || "";
  if (!paramKey) return null;
  const base: InboxCard = {
    id: `auditor-proposal-${Date.now()}`,
    title: proposal.title?.trim() ? proposal.title : "参数校准",
    markdown: `${proposal.reason || ""}\n预期影响：${proposal.expected_impact || ""}`.trim(),
    conflictDetail: proposal.reason || "",
    displayText: proposal.param_key ? `参数校准：${proposal.param_key}` : "Auditor 提案参数校准",
    cardType: "auditor-proposal",
    proposal,
  };
  return { ...base, skillId: inferDecisionSkillId(base, []) };
}
