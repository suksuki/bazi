import { mapConflictDetail } from "@/constants/termMap";
import type { BaziMetadata, Lang } from "@/types/bazi";
import type { InboxCard, LogicProposal } from "./models";

export function buildInboxCards(params: {
  metadata: BaziMetadata | null;
  firstPromptText: string;
  auditorProposalCards: InboxCard[];
  resolvedCardIds: string[];
  lang: Lang;
  t: (text: string) => string;
}): InboxCard[] {
  const { metadata, firstPromptText, auditorProposalCards, resolvedCardIds, lang, t } = params;
  if (!metadata) return [];

  const detected = metadata.conflict_matrix.points.map((point, index) => ({
    id: `conflict-${index}-${point.detail}`,
    title: `冲突确认：${point.detail}`,
    conflictDetail: point.detail,
    markdown: mapConflictDetail(`系统检测到 ${point.detail}。请选择是否深入分析该局部。`, lang),
    displayText: mapConflictDetail(point.detail, lang),
    cardType: "conflict" as const,
  }));

  const sentenceItems = firstPromptText
    .replace(/\r/g, "")
    .split(/\n+/)
    .flatMap((line) => line.split(/(?<=[。！？!?])/))
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 4)
    .map((text, index) => ({
      id: `llm-observe-${index}`,
      title: `判词观察项 ${index + 1}`,
      conflictDetail: text,
      markdown: text,
      displayText: text,
      cardType: "conflict" as const,
    }));

  const proposalCards = auditorProposalCards.map((card, index) => ({
    ...card,
    id: card.id || `auditor-proposal-${index}-${card.title}`,
    cardType: "auditor-proposal" as const,
  }));

  const mergedCards = detected.length > 0 || sentenceItems.length > 0 || proposalCards.length > 0
    ? [...proposalCards, ...detected, ...sentenceItems]
    : [{
        id: "fallback-deep-scan",
        title: "继续深度扫描",
        conflictDetail: "未见明显冲合，进入深层扫描",
        markdown: "当前未检测到六冲/六合，是否继续执行深层结构扫描？",
        displayText: t("未见明显冲合，进入深层扫描"),
        cardType: "conflict" as const,
      }];

  return mergedCards.filter((card) => !resolvedCardIds.includes(card.id));
}

export function createAuditorProposalCard(proposal: LogicProposal): InboxCard | null {
  const paramKey = proposal?.param_key || "";
  if (!paramKey) return null;
  return {
    id: `auditor-proposal-${Date.now()}`,
    title: proposal.title?.trim() ? proposal.title : "参数校准",
    markdown: `${proposal.reason || ""}\n预期影响：${proposal.expected_impact || ""}`.trim(),
    conflictDetail: proposal.reason || "",
    displayText: proposal.param_key ? `参数校准：${proposal.param_key}` : "Auditor 提案参数校准",
    cardType: "auditor-proposal",
    proposal,
  };
}
