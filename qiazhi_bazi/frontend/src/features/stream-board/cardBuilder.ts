import type { BaziMetadata } from "@/types/bazi";
import { inferDecisionSkillId } from "@/features/decision-inbox/skillInference";
import type { DecisionSignalToNoiseMeta, InboxCard, LogicProposal } from "./models";

export type { DecisionSignalToNoiseMeta };

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
  } = params;
  if (!metadata) return [];
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
  return withSovereignty.filter((card) => !resolvedCardIds.includes(card.id));
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
