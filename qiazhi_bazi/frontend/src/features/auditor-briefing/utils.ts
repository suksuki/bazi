import { LogicProposal } from "./types";

export function formatVal(value: number | undefined) {
  if (typeof value !== "number" || Number.isNaN(value)) return "—";
  return value.toFixed(2);
}

export function getAuditorBriefingState(args: {
  logicProposal?: LogicProposal | null;
  currentParams?: Record<string, number>;
  alignmentScore?: number;
  structuredHit?: boolean;
  autoConverted?: boolean;
  alreadyAdded?: boolean;
}) {
  const key = args.logicProposal?.param_key || "";
  const currentValue = key ? args.currentParams?.[key] : undefined;
  const nextValue = args.logicProposal?.suggested_value;
  const hasSqlPatch = Boolean(args.logicProposal?.sql_patch);
  const aligned = Boolean(args.structuredHit) && typeof args.alignmentScore === "number" && args.alignmentScore >= 60;
  const disableByState = Boolean(args.alreadyAdded || args.autoConverted);
  return { key, currentValue, nextValue, hasSqlPatch, aligned, disableByState };
}
