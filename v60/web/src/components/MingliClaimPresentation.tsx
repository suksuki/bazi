import type { MingliReadingClaim } from "../mingliClaimGraphTypes";

export function claimIsAdmitted(item: MingliReadingClaim): boolean {
  return item.status !== "WITHHELD";
}

export function claimStatusLabel(item: MingliReadingClaim): string {
  if (item.status === "WITHHELD") return "本条未采用";
  if (item.assessment_codes.includes("MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION")) {
    return "初断 · 机制待裁决";
  }
  if (item.assessment_codes.includes("PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE")) {
    return "初断 · 论据待补齐";
  }
  if (item.status === "NEEDS_RECONCILIATION") return "初断 · 待经历校准";
  if (item.status === "OPEN_QUESTION") return "待你回答";
  return "整盘初断";
}

export function visibleClaimAssessmentCodes(item: MingliReadingClaim) {
  if (item.status !== "WITHHELD") return item.assessment_codes;
  return item.assessment_codes.filter((code) => ![
    "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE",
    "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION",
    "CONFIDENCE_EXCEEDS_PACKET",
    "DEPENDENCY_WITHHELD",
  ].includes(code));
}

export function ClaimReviewNotice({
  context,
  item,
}: {
  context?: string;
  item: MingliReadingClaim;
}) {
  const visibleCodes = visibleClaimAssessmentCodes(item);
  const messages = visibleCodes.map((code) => {
    if (code === "CLAIM_EVIDENCE_MISSING") {
      return "这条没有绑定可复核的命盘依据，暂不采用。";
    }
    if (code === "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE") {
      return "这条初断仍然保留，但整盘命据需要继续补齐。";
    }
    if (code === "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION") {
      return "这条保留为当前最佳解释，但候选机制尚未完成逐项专业裁决。";
    }
    if (code === "CONFIDENCE_EXCEEDS_PACKET") {
      return "原回答的高置信度超出了当前卷宗，系统已降为中等置信。";
    }
    if (code === "DEPENDENCY_WITHHELD") {
      return "局部支撑路径已撤下；总纲仍作为初断保留，但不能视为定论。";
    }
    if (code === "NATAL_CLAIM_CITES_TIMING_EVIDENCE"
      || code === "NATAL_CLAIM_USES_SELECTED_TIMING") {
      return "这条把大运或流年反写成了原局，暂不采用。";
    }
    if (code === "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT") {
      return "这条把关系成员直接当成了确定作用，暂不采用。";
    }
    if (code === "TIMING_COORDINATE_EVIDENCE_MISSING") {
      return "这条岁运判断没有绑定对应时间坐标，暂不采用。";
    }
    if (code === "TIMING_NATAL_BASIS_MISSING") {
      return "这条岁运判断缺少原局依据，先作为待校准判断保留。";
    }
    if (code === "TIMING_RELATION_EVIDENCE_MISSING") {
      return "这条点名了岁运关系，却没有绑定对应关系证据，暂不采用。";
    }
    if (code === "WORK_PATH_CLOSURE_EXCEEDS_PACKET") {
      return "这条把仍有条件的做功路径说成已经闭合，暂不采用。";
    }
    if (code === "ROOT_ASSERTION_CONFLICTS_WITH_PACKET") {
      return "这条把并不存在的地支根位写进了解释，暂不采用。";
    }
    if (code === "NAMED_COORDINATE_CONFLICTS_WITH_PACKET") {
      return "这条写错了干支与藏干位置，暂不采用。";
    }
    if (code === "TEN_GOD_MANIFESTATION_CONFLICTS_WITH_PACKET") {
      return "这条把藏干误写成天干透出，暂不采用。";
    }
    if (code === "PEER_COUNT_CONFLICTS_WITH_PACKET") {
      return "这条写错了明干比肩数量，暂不采用。";
    }
    if (code === "UNSELECTED_TIMING_LAYER_ASSERTION") {
      return "当前卷宗没有流月，这条时间判断暂不采用。";
    }
    if (code === "UNLISTED_RELATION_COORDINATE_ASSERTION") {
      return "这条使用了卷宗中不存在的地支关系，暂不采用。";
    }
    if (code === "UNADMITTED_CLASSICAL_ASSERTION") {
      return "这条使用了尚未完成专业判定的传统标签，暂不采用。";
    }
    if (code === "MODEL_FIELD_INVALID") {
      return "这条原始回答没有形成完整判断，已单独撤下；其余命局结论不受影响。";
    }
    if (code === "NON_READING_LANGUAGE" || code === "LOW_INFORMATION_LANGUAGE") {
      return "这条没有给出具体命理判断，暂不采用。";
    }
    if (code === "TIMING_LAYER_PROSE_CONFLICT") {
      return "这条混用了大运与流年内容，暂不采用。";
    }
    if (code === "EXACT_ROLE_PATH_MISSING") {
      return "这条没有说清具体是哪一种十神路径，暂不采用。";
    }
    if (code === "DOMAIN_METHOD_AXES_INCOMPLETE") {
      return "这条关系或家庭判断没有同时完成专题所需的两条命盘轴，暂不采用。";
    }
    if (code === "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED") {
      return "关系与家庭的正向判法还没有完成专业准入，这条先不采用。";
    }
    if (code === "TEN_GOD_TO_LIFE_STORY_SHORTCUT") {
      return "这条从单枚十神直接跳到了关系或家庭故事，暂不采用。";
    }
    if (code === "UNSUPPORTED_SOCIAL_RESOURCE_INFERENCE") {
      return "这条把比劫直接写成人脉或团队支持，暂不采用。";
    }
    if (code === "DOMAIN_PRIMARY_PATH_MISSING") {
      return "这条先作为待经历校准的初断保留；它还没有从整盘主线完整推出，不能先当定论。";
    }
    return "这条包含不应由命盘直接断定的高风险事件，暂不采用。";
  });
  return (
    <p className="mingli-claim-review-note" data-claim-status={item.status}>
      {context ? `${context}：` : ""}
      {[...new Set(messages)].join(" ") || "这条初断需要重新落回整盘主线。"}
    </p>
  );
}
