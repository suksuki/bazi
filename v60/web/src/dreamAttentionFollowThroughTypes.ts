import {
  arraysEqual,
  hasOnlyKeys,
  isHash,
  isNonNegativeInteger,
  isOneOf,
  isRecord,
  isRef,
  isUniqueRefArray,
} from "./projectionValidation";

export const DREAM_PENDING_ATTENTION_VERSION =
  "v60.dream-pending-attention.001" as const;
export const DREAM_ATTENTION_FOLLOW_THROUGH_VERSION =
  "v60.dream-attention-follow-through.001" as const;

export type DreamAttentionFollowThroughStatus =
  | "OBSERVING"
  | "OBSERVATIONS_COMPLETE"
  | "AWAITING_WORLD_RESPONSE"
  | "WORLD_RESPONSE_READY_HIDDEN"
  | "WORLD_RESPONSE_AVAILABLE"
  | "RECONCILED_NOT_EVALUATED"
  | "RETURNED_NOT_EVALUATED";

export interface DreamPendingAttention {
  contract_version: typeof DREAM_PENDING_ATTENTION_VERSION;
  attention_ref: string;
  attention_hash: string;
  source_encounter_ref: string;
  source_encounter_version: number;
  source_echo_ref: string;
  source_echo_hash: string;
  source_candidate_ref: string;
  source_candidate_hash: string;
  tree_ref: string;
  observation_ref: string;
  label: string;
  summary: string;
  status: "PENDING_SAME_TREE_RETURN";
  semantics: "DREAM_RETURN_ATTENTION_ONLY";
  evidence_role: "NOT_EVIDENCE";
  tree_candidate_set_or_order_changed: false;
  question_changed: false;
  answer_changed: false;
  npc_choice_changed: false;
  outcome_changed: false;
  mingli_write_allowed: false;
  decision_write_allowed: false;
  knowledge_write_allowed: false;
  read_only: true;
}

export interface DreamAttentionFollowThroughProgress {
  required_count: 3;
  observed_count: number;
  required_organ_refs: string[];
  observed_organ_refs: string[];
}

export interface DreamAttentionFollowThroughWorldResponse {
  actual_event: string;
  evidence_refs: string[];
  evidence_summaries: string[];
  material_count: number;
}

export interface DreamAttentionFollowThrough {
  contract_version: typeof DREAM_ATTENTION_FOLLOW_THROUGH_VERSION;
  application_ref: string;
  application_hash: string;
  attention_ref: string;
  attention_hash: string;
  source_encounter_ref: string;
  source_encounter_version: number;
  source_echo_ref: string;
  source_echo_hash: string;
  source_candidate_ref: string;
  source_candidate_hash: string;
  source_tree_ref: string;
  target_tree_ref: string;
  target_encounter_ref: string;
  observation_ref: string;
  label: string;
  summary: string;
  status: DreamAttentionFollowThroughStatus;
  progress: DreamAttentionFollowThroughProgress;
  world_response: DreamAttentionFollowThroughWorldResponse | null;
  semantic_match_status:
    | "NOT_AVAILABLE_BEFORE_REVEAL"
    | "SEMANTIC_MATCH_NOT_EVALUATED";
  answer_status: "NOT_EVALUATED";
  semantics: "DREAM_ATTENTION_FOLLOW_THROUGH_ONLY";
  evidence_role: "NOT_EVIDENCE";
  tree_candidate_set_or_order_changed: false;
  question_changed: false;
  answer_changed: false;
  npc_choice_changed: false;
  outcome_changed: false;
  mingli_write_allowed: false;
  decision_write_allowed: false;
  knowledge_write_allowed: false;
  read_only: true;
}

const PENDING_KEYS = [
  "contract_version",
  "attention_ref",
  "attention_hash",
  "source_encounter_ref",
  "source_encounter_version",
  "source_echo_ref",
  "source_echo_hash",
  "source_candidate_ref",
  "source_candidate_hash",
  "tree_ref",
  "observation_ref",
  "label",
  "summary",
  "status",
  "semantics",
  "evidence_role",
  "tree_candidate_set_or_order_changed",
  "question_changed",
  "answer_changed",
  "npc_choice_changed",
  "outcome_changed",
  "mingli_write_allowed",
  "decision_write_allowed",
  "knowledge_write_allowed",
  "read_only",
] as const;

const FOLLOW_THROUGH_KEYS = [
  "contract_version",
  "application_ref",
  "application_hash",
  "attention_ref",
  "attention_hash",
  "source_encounter_ref",
  "source_encounter_version",
  "source_echo_ref",
  "source_echo_hash",
  "source_candidate_ref",
  "source_candidate_hash",
  "source_tree_ref",
  "target_tree_ref",
  "target_encounter_ref",
  "observation_ref",
  "label",
  "summary",
  "status",
  "progress",
  "world_response",
  "semantic_match_status",
  "answer_status",
  "semantics",
  "evidence_role",
  "tree_candidate_set_or_order_changed",
  "question_changed",
  "answer_changed",
  "npc_choice_changed",
  "outcome_changed",
  "mingli_write_allowed",
  "decision_write_allowed",
  "knowledge_write_allowed",
  "read_only",
] as const;

const PROGRESS_KEYS = [
  "required_count",
  "observed_count",
  "required_organ_refs",
  "observed_organ_refs",
] as const;

const WORLD_RESPONSE_KEYS = [
  "actual_event",
  "evidence_refs",
  "evidence_summaries",
  "material_count",
] as const;

const FOLLOW_THROUGH_STATUSES = [
  "OBSERVING",
  "OBSERVATIONS_COMPLETE",
  "AWAITING_WORLD_RESPONSE",
  "WORLD_RESPONSE_READY_HIDDEN",
  "WORLD_RESPONSE_AVAILABLE",
  "RECONCILED_NOT_EVALUATED",
  "RETURNED_NOT_EVALUATED",
] as const;

const RESPONSE_VISIBLE_STATUSES = [
  "WORLD_RESPONSE_AVAILABLE",
  "RECONCILED_NOT_EVALUATED",
  "RETURNED_NOT_EVALUATED",
] as const;

interface PendingBindings {
  candidateRefs?: readonly string[];
}

export function isDreamPendingAttentionSupplied(candidate: unknown): boolean {
  return candidate !== null && candidate !== undefined;
}

export function isDreamPendingAttentionDisplayable(
  candidate: unknown,
  bindings: PendingBindings = {},
): candidate is DreamPendingAttention {
  if (!isRecord(candidate) || !hasOnlyKeys(candidate, PENDING_KEYS)) {
    return false;
  }
  return (
    candidate.contract_version === DREAM_PENDING_ATTENTION_VERSION &&
    isRef(candidate.attention_ref) &&
    isHash(candidate.attention_hash) &&
    isRef(candidate.source_encounter_ref) &&
    Number.isInteger(candidate.source_encounter_version) &&
    Number(candidate.source_encounter_version) >= 1 &&
    isRef(candidate.source_echo_ref) &&
    isHash(candidate.source_echo_hash) &&
    isRef(candidate.source_candidate_ref) &&
    isHash(candidate.source_candidate_hash) &&
    isRef(candidate.tree_ref) &&
    isRef(candidate.observation_ref) &&
    isRef(candidate.label) &&
    isRef(candidate.summary) &&
    candidate.status === "PENDING_SAME_TREE_RETURN" &&
    candidate.semantics === "DREAM_RETURN_ATTENTION_ONLY" &&
    candidate.evidence_role === "NOT_EVIDENCE" &&
    candidate.tree_candidate_set_or_order_changed === false &&
    candidate.question_changed === false &&
    candidate.answer_changed === false &&
    candidate.npc_choice_changed === false &&
    candidate.outcome_changed === false &&
    candidate.mingli_write_allowed === false &&
    candidate.decision_write_allowed === false &&
    candidate.knowledge_write_allowed === false &&
    candidate.read_only === true &&
    (bindings.candidateRefs === undefined ||
      bindings.candidateRefs.includes(candidate.source_candidate_ref))
  );
}

interface FollowThroughBindings {
  targetEncounterRef?: string;
  targetTreeRef?: string;
  requiredOrganRefs?: readonly string[];
  observedOrganRefs?: readonly string[];
  expectedStatus?: DreamAttentionFollowThroughStatus;
  worldResponse?: DreamAttentionFollowThroughWorldResponse | null;
  candidateRefs?: readonly string[];
}

export function isDreamAttentionFollowThroughDisplayable(
  candidate: unknown,
  bindings: FollowThroughBindings = {},
): candidate is DreamAttentionFollowThrough {
  if (
    !isRecord(candidate) ||
    !hasOnlyKeys(candidate, FOLLOW_THROUGH_KEYS) ||
    !isRecord(candidate.progress) ||
    !hasOnlyKeys(candidate.progress, PROGRESS_KEYS)
  ) {
    return false;
  }

  const progress = candidate.progress;
  if (
    progress.required_count !== 3 ||
    !isNonNegativeInteger(progress.observed_count) ||
    Number(progress.observed_count) > 3 ||
    !isUniqueRefArray(progress.required_organ_refs) ||
    progress.required_organ_refs.length !== 3 ||
    !isUniqueRefArray(progress.observed_organ_refs)
  ) {
    return false;
  }
  const requiredOrganRefs = progress.required_organ_refs;
  const observedOrganRefs = progress.observed_organ_refs;
  if (
    observedOrganRefs.length !== progress.observed_count ||
    !arraysEqual(
      observedOrganRefs,
      requiredOrganRefs.filter((ref) => observedOrganRefs.includes(ref)),
    )
  ) {
    return false;
  }

  const status = candidate.status;
  const responseVisible = isOneOf(status, RESPONSE_VISIBLE_STATUSES);
  if (
    !isOneOf(status, FOLLOW_THROUGH_STATUSES) ||
    (status === "OBSERVING" && progress.observed_count >= 3) ||
    (status !== "OBSERVING" && progress.observed_count !== 3) ||
    !isWorldResponseValid(candidate.world_response, responseVisible) ||
    candidate.semantic_match_status !==
      (responseVisible
        ? "SEMANTIC_MATCH_NOT_EVALUATED"
        : "NOT_AVAILABLE_BEFORE_REVEAL")
  ) {
    return false;
  }

  return (
    candidate.contract_version === DREAM_ATTENTION_FOLLOW_THROUGH_VERSION &&
    isRef(candidate.application_ref) &&
    isHash(candidate.application_hash) &&
    isRef(candidate.attention_ref) &&
    isHash(candidate.attention_hash) &&
    isRef(candidate.source_encounter_ref) &&
    Number.isInteger(candidate.source_encounter_version) &&
    Number(candidate.source_encounter_version) >= 1 &&
    isRef(candidate.source_echo_ref) &&
    isHash(candidate.source_echo_hash) &&
    isRef(candidate.source_candidate_ref) &&
    isHash(candidate.source_candidate_hash) &&
    isRef(candidate.source_tree_ref) &&
    isRef(candidate.target_tree_ref) &&
    candidate.source_tree_ref === candidate.target_tree_ref &&
    isRef(candidate.target_encounter_ref) &&
    isRef(candidate.observation_ref) &&
    isRef(candidate.label) &&
    isRef(candidate.summary) &&
    candidate.answer_status === "NOT_EVALUATED" &&
    candidate.semantics === "DREAM_ATTENTION_FOLLOW_THROUGH_ONLY" &&
    candidate.evidence_role === "NOT_EVIDENCE" &&
    candidate.tree_candidate_set_or_order_changed === false &&
    candidate.question_changed === false &&
    candidate.answer_changed === false &&
    candidate.npc_choice_changed === false &&
    candidate.outcome_changed === false &&
    candidate.mingli_write_allowed === false &&
    candidate.decision_write_allowed === false &&
    candidate.knowledge_write_allowed === false &&
    candidate.read_only === true &&
    (bindings.targetEncounterRef === undefined ||
      candidate.target_encounter_ref === bindings.targetEncounterRef) &&
    (bindings.targetTreeRef === undefined ||
      candidate.target_tree_ref === bindings.targetTreeRef) &&
    (bindings.requiredOrganRefs === undefined ||
      arraysEqual(progress.required_organ_refs, bindings.requiredOrganRefs)) &&
    (bindings.observedOrganRefs === undefined ||
      arraysEqual(progress.observed_organ_refs, bindings.observedOrganRefs)) &&
    (bindings.expectedStatus === undefined ||
      status === bindings.expectedStatus) &&
    (bindings.worldResponse === undefined ||
      worldResponsesEqual(candidate.world_response, bindings.worldResponse)) &&
    (bindings.candidateRefs === undefined ||
      bindings.candidateRefs.includes(candidate.source_candidate_ref))
  );
}

function isWorldResponseValid(
  candidate: unknown,
  responseVisible: boolean,
): candidate is DreamAttentionFollowThroughWorldResponse | null {
  if (!responseVisible) return candidate === null;
  if (!isRecord(candidate) || !hasOnlyKeys(candidate, WORLD_RESPONSE_KEYS)) {
    return false;
  }
  return (
    isRef(candidate.actual_event) &&
    isUniqueRefArray(candidate.evidence_refs) &&
    arraysEqual(candidate.evidence_refs, [...candidate.evidence_refs].sort()) &&
    Array.isArray(candidate.evidence_summaries) &&
    candidate.evidence_summaries.every(isRef) &&
    isNonNegativeInteger(candidate.material_count) &&
    Number(candidate.material_count) > 0 &&
    candidate.evidence_refs.length === candidate.material_count &&
    candidate.evidence_summaries.length === candidate.material_count
  );
}

function worldResponsesEqual(
  left: unknown,
  right: DreamAttentionFollowThroughWorldResponse | null,
): boolean {
  if (left === null || right === null) return left === right;
  if (!isRecord(left)) return false;
  return (
    left.actual_event === right.actual_event &&
    arraysEqual(left.evidence_refs, right.evidence_refs) &&
    arraysEqual(left.evidence_summaries, right.evidence_summaries) &&
    left.material_count === right.material_count
  );
}
