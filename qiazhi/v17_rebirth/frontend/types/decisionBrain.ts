export type PlanDecisionSignalValue = string | number | boolean;

export type PlanDecisionClaim = {
  claim_id?: string;
  severity?: string;
  confidence?: number;
  routing?: string;
  routing_reason?: string;
  rationale?: string;
  signals?: Record<string, PlanDecisionSignalValue>;
};

export type PlanDecisionRoutingFeatures = Record<string, PlanDecisionSignalValue>;
