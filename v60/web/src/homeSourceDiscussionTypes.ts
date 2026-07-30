import type { HomeSourceUsabilityRequirementId } from "./homeSourceUsabilityTypes";

export type HomeSourceDiscussionDisposition = "ABSTAIN";

export type HomeSourceDiscussionReason =
  "NO_ADMITTED_PROFESSIONAL_RULE_CHAIN";

export type HomeSourceDiscussionOutputMode = "FACTS_AND_GAPS_ONLY";

export type HomeSourceDiscussionAbstainedClaims = [
  "RELATION_EFFECT",
  "SOURCE_USABILITY",
];

export interface HomeSourceDiscussionAbstentionReceipt {
  receipt_ref: string;
  receipt_hash: string;
  receipt_version: "v60.mingli-source-discussion-abstention-receipt.001";
  case_ref: string;
  chart_version_ref: string;
  reading_ref: string;
  reading_hash: string;
  source_review_vector_ref: string;
  source_review_vector_hash: string;
  prerequisite_ref: string;
  prerequisite_hash: string;
  carrier_refs: string[];
  carrier_count: number;
  ready_carrier_count: 0;
  blocking_requirement_ids: HomeSourceUsabilityRequirementId[];
  non_triggered_requirement_ids: HomeSourceUsabilityRequirementId[];
  abstained_claims: HomeSourceDiscussionAbstainedClaims;
  disposition: HomeSourceDiscussionDisposition;
  reason: HomeSourceDiscussionReason;
  output_mode: HomeSourceDiscussionOutputMode;
  provider_invoked: false;
  decision_created: false;
  discussion_allowed: false;
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}
