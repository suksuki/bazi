import type { ChartStructureOk, PillarName } from "./chartStructureTypes";

export type IncomeStabilitySignalKey =
  | "self_capacity"
  | "wealth_presence"
  | "wealth_accessibility"
  | "volatility"
  | "structure_binding"
  | "income_stability";

export type IncomeStabilitySignalValue =
  | "none"
  | "low"
  | "medium"
  | "high"
  | "clear"
  | "bound"
  | "disrupted"
  | "conflicted"
  | "not_applicable"
  | "present"
  | "stable"
  | "unstable"
  | "mixed";

export type IncomeStabilitySourceBinding = {
  source: keyof Pick<
    ChartStructureOk,
    "day_master" | "ten_god_counts" | "branch_relations" | "simplified_strength" | "pillars"
  >;
  path: string;
};

export type IncomeStabilityInferenceSignal = {
  key: IncomeStabilitySignalKey;
  value: IncomeStabilitySignalValue;
  sources: IncomeStabilitySourceBinding[];
};

export type IncomeStabilityInferenceBundle = {
  status: "ok";
  supported_theme: "income_stability";
  signals: IncomeStabilityInferenceSignal[];
  touched_wealth_pillars: PillarName[];
};

