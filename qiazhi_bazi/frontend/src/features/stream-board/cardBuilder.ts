import type { BaziMetadata } from "@/types/bazi";
import { inferDecisionSkillId } from "@/features/decision-inbox/skillInference";
import type { InboxCard, LogicProposal } from "./models";

export function buildInboxCards(params: {
  metadata: BaziMetadata | null;
  firstPromptText: string;
  auditorProposalCards: InboxCard[];
  resolvedCardIds: string[];
  t: (text: string) => string;
}): InboxCard[] {
  const { metadata, firstPromptText, auditorProposalCards, resolvedCardIds, t } = params;
  if (!metadata) return [];
  const conflictPoints = metadata.conflict_matrix?.points ?? [];

  const sentenceItems = firstPromptText
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

  return mergedCards.filter((card) => !resolvedCardIds.includes(card.id));
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
