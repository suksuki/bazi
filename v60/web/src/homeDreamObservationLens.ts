import type { HomeSnapshot } from "./homeApi";

export const DREAM_OBSERVATION_DOMAINS = [
  "career",
  "wealth",
  "relationship",
] as const;

export type DreamObservationDomain =
  (typeof DREAM_OBSERVATION_DOMAINS)[number];

type ReadingBriefSource = Pick<
  HomeSnapshot["mingli"]["reading_brief"],
  "life_domains"
>;

type MechanismComparisonSource = Pick<
  HomeSnapshot["lab"]["mechanism_comparison"],
  "decision_ref" | "status"
>;

export interface DreamReadingObservationLensSource {
  reading_brief: ReadingBriefSource;
  mechanism_comparison: MechanismComparisonSource;
}

export interface DreamReadingObservation {
  domain: DreamObservationDomain;
  label: string;
  question: string;
}

export interface DreamReadingObservationLensModel {
  observations: [
    DreamReadingObservation,
    DreamReadingObservation,
    DreamReadingObservation,
  ];
  semantics: "ATTENTION_WINDOW_ONLY";
  decision_role: "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER";
  attention_order_recorded: boolean;
  tree_candidate_set_or_order_changed: false;
  future_evidence_included: false;
  canonical_write_allowed: false;
}

function projectObservation(
  readingBrief: ReadingBriefSource,
  domain: DreamObservationDomain,
): DreamReadingObservation {
  const matches = readingBrief.life_domains.filter(
    (observation) => observation.domain === domain,
  );
  if (matches.length !== 1) {
    throw new Error("dream_observation_domain_contract_invalid");
  }

  const label = matches[0].label.trim();
  const question = matches[0].question.trim();
  if (!label || !question) {
    throw new Error("dream_observation_copy_contract_invalid");
  }

  return { domain, label, question };
}

export function buildDreamReadingObservationLens(
  source: DreamReadingObservationLensSource,
): DreamReadingObservationLensModel {
  const { mechanism_comparison: comparison, reading_brief: readingBrief } =
    source;

  return {
    observations: [
      projectObservation(readingBrief, "career"),
      projectObservation(readingBrief, "wealth"),
      projectObservation(readingBrief, "relationship"),
    ],
    semantics: "ATTENTION_WINDOW_ONLY",
    decision_role: "NOT_APPLIED_TO_TREE_CANDIDATES_OR_ORDER",
    attention_order_recorded:
      comparison.status === "RESOLVED" && comparison.decision_ref !== null,
    tree_candidate_set_or_order_changed: false,
    future_evidence_included: false,
    canonical_write_allowed: false,
  };
}
