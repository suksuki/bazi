import type { MingliReadingClaim } from "./mingliClaimGraphTypes";

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
