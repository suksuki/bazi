import {
  hasOnlyKeys,
  isHash,
  isNonNegativeInteger,
  isOneOf,
  isRecord,
  isRef,
} from "./projectionValidation";

export const DREAM_GROVE_CHAPTER_ROUTE_VERSION =
  "v60.dream-grove-chapter-route.001" as const;

export type DreamGroveChapterRouteStatus =
  | "AVAILABLE"
  | "STORY_CURRENTLY_COMPLETE";

export type DreamGroveChapterRouteBasis =
  | "ENTRYPOINT"
  | "CANONICAL_TRANSITION"
  | "TERMINAL_CHAPTER";

export interface DreamGroveChapterRoute {
  contract_version: typeof DREAM_GROVE_CHAPTER_ROUTE_VERSION;
  route_hash: string;
  status: DreamGroveChapterRouteStatus;
  basis: DreamGroveChapterRouteBasis;
  candidate_ref: string;
  candidate_hash: string;
  tree_ref: string;
  previous_source_question_ref: string | null;
  previous_source_episode_ref: string | null;
  target_source_question_ref: string;
  target_source_episode_ref: string;
  target_source_episode_version: number;
  target_chapter: "FIRST_VISIT" | "RETURN_VISIT";
  transition_ref: string | null;
  transition_hash: string | null;
  title: string;
  premise: string;
  chapter_label: string;
  routing_authority: "CANONICAL_EPISODE_GRAPH";
  attention_routing_allowed: false;
  attention_ref_used: false;
  tree_candidate_set_or_order_changed: false;
  question_changed: false;
  answer_changed: false;
  npc_choice_changed: false;
  outcome_changed: false;
  read_only: true;
}

const ROUTE_KEYS = [
  "contract_version",
  "route_hash",
  "status",
  "basis",
  "candidate_ref",
  "candidate_hash",
  "tree_ref",
  "previous_source_question_ref",
  "previous_source_episode_ref",
  "target_source_question_ref",
  "target_source_episode_ref",
  "target_source_episode_version",
  "target_chapter",
  "transition_ref",
  "transition_hash",
  "title",
  "premise",
  "chapter_label",
  "routing_authority",
  "attention_routing_allowed",
  "attention_ref_used",
  "tree_candidate_set_or_order_changed",
  "question_changed",
  "answer_changed",
  "npc_choice_changed",
  "outcome_changed",
  "read_only",
] as const;

const ROUTE_STATUSES = [
  "AVAILABLE",
  "STORY_CURRENTLY_COMPLETE",
] as const;

const ROUTE_BASES = [
  "ENTRYPOINT",
  "CANONICAL_TRANSITION",
  "TERMINAL_CHAPTER",
] as const;

const CHAPTERS = ["FIRST_VISIT", "RETURN_VISIT"] as const;

interface DreamGroveChapterRouteBindings {
  candidateRef: string;
  candidateHash: string;
  treeRef: string;
}

export function isDreamGroveChapterRouteDisplayable(
  candidate: unknown,
  bindings: DreamGroveChapterRouteBindings,
): candidate is DreamGroveChapterRoute {
  if (!isRecord(candidate) || !hasOnlyKeys(candidate, ROUTE_KEYS)) {
    return false;
  }

  if (
    candidate.contract_version !== DREAM_GROVE_CHAPTER_ROUTE_VERSION ||
    !isHash(candidate.route_hash) ||
    !isOneOf(candidate.status, ROUTE_STATUSES) ||
    !isOneOf(candidate.basis, ROUTE_BASES) ||
    !isRef(candidate.candidate_ref) ||
    !isHash(candidate.candidate_hash) ||
    !isRef(candidate.tree_ref) ||
    !nullableRef(candidate.previous_source_question_ref) ||
    !nullableRef(candidate.previous_source_episode_ref) ||
    !isRef(candidate.target_source_question_ref) ||
    !isRef(candidate.target_source_episode_ref) ||
    !isNonNegativeInteger(candidate.target_source_episode_version) ||
    Number(candidate.target_source_episode_version) < 1 ||
    !isOneOf(candidate.target_chapter, CHAPTERS) ||
    !nullableRef(candidate.transition_ref) ||
    !nullableHash(candidate.transition_hash) ||
    !isRef(candidate.title) ||
    !isRef(candidate.premise) ||
    !isRef(candidate.chapter_label) ||
    candidate.routing_authority !== "CANONICAL_EPISODE_GRAPH" ||
    candidate.attention_routing_allowed !== false ||
    candidate.attention_ref_used !== false ||
    candidate.tree_candidate_set_or_order_changed !== false ||
    candidate.question_changed !== false ||
    candidate.answer_changed !== false ||
    candidate.npc_choice_changed !== false ||
    candidate.outcome_changed !== false ||
    candidate.read_only !== true ||
    candidate.candidate_ref !== bindings.candidateRef ||
    candidate.candidate_hash !== bindings.candidateHash ||
    candidate.tree_ref !== bindings.treeRef
  ) {
    return false;
  }

  const previousRefsArePaired =
    (candidate.previous_source_question_ref === null) ===
    (candidate.previous_source_episode_ref === null);
  const transitionIdentityIsPaired =
    (candidate.transition_ref === null) ===
    (candidate.transition_hash === null);
  if (!previousRefsArePaired || !transitionIdentityIsPaired) {
    return false;
  }

  if (
    candidate.status === "AVAILABLE" &&
    candidate.basis === "ENTRYPOINT"
  ) {
    return (
      candidate.previous_source_question_ref === null &&
      candidate.previous_source_episode_ref === null &&
      candidate.transition_ref === null &&
      candidate.transition_hash === null &&
      candidate.target_chapter === "FIRST_VISIT"
    );
  }

  if (
    candidate.status === "AVAILABLE" &&
    candidate.basis === "CANONICAL_TRANSITION"
  ) {
    return (
      candidate.previous_source_question_ref !== null &&
      candidate.previous_source_episode_ref !== null &&
      candidate.transition_ref !== null &&
      candidate.transition_hash !== null &&
      candidate.target_chapter === "RETURN_VISIT" &&
      candidate.previous_source_question_ref !==
        candidate.target_source_question_ref &&
      candidate.previous_source_episode_ref !==
        candidate.target_source_episode_ref
    );
  }

  if (
    candidate.status === "STORY_CURRENTLY_COMPLETE" &&
    candidate.basis === "TERMINAL_CHAPTER"
  ) {
    return (
      candidate.previous_source_question_ref ===
        candidate.target_source_question_ref &&
      candidate.previous_source_episode_ref ===
        candidate.target_source_episode_ref &&
      candidate.transition_ref === null &&
      candidate.transition_hash === null
    );
  }

  return false;
}

function nullableRef(value: unknown): value is string | null {
  return value === null || isRef(value);
}

function nullableHash(value: unknown): value is string | null {
  return value === null || isHash(value);
}
