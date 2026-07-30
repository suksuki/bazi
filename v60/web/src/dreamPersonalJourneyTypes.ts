import {
  hasOnlyKeys,
  isHash,
  isNonNegativeInteger,
  isOneOf,
  isRecord,
  isRef,
} from "./projectionValidation";

export const DREAM_PERSONAL_JOURNEY_VERSION =
  "v60.dream-personal-journey.001" as const;
export const DREAM_PRIVATE_INQUIRY_VERSION =
  "v60.dream-private-inquiry.001" as const;
export const DREAM_PERSONAL_OBSERVATION_VERSION =
  "v60.dream-personal-observation.001" as const;
export const DREAM_PERSONAL_CHECKIN_VERSION =
  "v60.dream-personal-check-in.001" as const;

export type DreamLifeDomain = "career" | "wealth" | "relationship";
export type DreamPersonalCheckInStatus =
  | "OBSERVED"
  | "NOT_OBSERVED"
  | "STILL_OBSERVING";

export interface DreamPrivateInquiry {
  contract_version: typeof DREAM_PRIVATE_INQUIRY_VERSION;
  inquiry_ref: string;
  inquiry_hash: string;
  domain: DreamLifeDomain;
  question: string;
  candidate_ref: string;
  candidate_hash: string;
  public_alias: string;
  tree_ref: string;
  encounter_ref: string;
  episode_question_ref: string;
  private_to_account: true;
  owner_self_report_only: true;
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE";
  reading_used_to_select_candidate: false;
  llm_interpretation_used: false;
  dream_answers_owner_question: false;
}

export interface DreamPersonalObservationOption {
  option_ref: string;
  inquiry_ref: string;
  domain: DreamLifeDomain;
  label: string;
  summary: string;
  checkpoint_days: 7;
}

export interface DreamPersonalObservation {
  contract_version: typeof DREAM_PERSONAL_OBSERVATION_VERSION;
  task_ref: string;
  task_hash: string;
  inquiry_ref: string;
  inquiry_hash: string;
  encounter_ref: string;
  option: DreamPersonalObservationOption;
  checkpoint_on: string;
  semantics: "PRIVATE_REALITY_OBSERVATION_ONLY";
  private_to_account: true;
  owner_self_report_only: true;
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE";
  dream_result_validates_owner_question: false;
}

export interface DreamPersonalCheckIn {
  contract_version: typeof DREAM_PERSONAL_CHECKIN_VERSION;
  checkin_ref: string;
  checkin_hash: string;
  task_ref: string;
  task_hash: string;
  status: DreamPersonalCheckInStatus;
  note: string | null;
  checked_in_on: string;
  semantics: "PRIVATE_SELF_REPORTED_CHECK_IN";
  private_to_account: true;
  owner_self_report_only: true;
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE";
  validates_dream_or_mingli: false;
}

export interface DreamPersonalJourney {
  contract_version: typeof DREAM_PERSONAL_JOURNEY_VERSION;
  status:
    | "IN_DREAM"
    | "DREAM_INTERRUPTED"
    | "AWAITING_OBSERVATION"
    | "OBSERVING"
    | "FOLLOWED_UP";
  inquiry: DreamPrivateInquiry;
  observation_options: DreamPersonalObservationOption[];
  observation: DreamPersonalObservation | null;
  latest_checkin: DreamPersonalCheckIn | null;
  checkin_count: number;
  private_to_account: true;
  owner_self_report_only: true;
  mingli_evidence_role: "NOT_MINGLI_EVIDENCE";
  dream_answers_owner_question: false;
  tree_candidate_set_or_order_changed: false;
  chapter_route_changed: false;
  episode_question_changed: false;
  answer_changed: false;
  npc_choice_changed: false;
  world_outcome_changed: false;
  mingli_write_allowed: false;
  decision_write_allowed: false;
  knowledge_write_allowed: false;
}

interface JourneyBindings {
  candidateRef?: string;
  candidateHash?: string;
  encounterRef?: string;
  treeRef?: string;
}

const INQUIRY_KEYS = [
  "contract_version",
  "inquiry_ref",
  "inquiry_hash",
  "domain",
  "question",
  "candidate_ref",
  "candidate_hash",
  "public_alias",
  "tree_ref",
  "encounter_ref",
  "episode_question_ref",
  "private_to_account",
  "owner_self_report_only",
  "mingli_evidence_role",
  "reading_used_to_select_candidate",
  "llm_interpretation_used",
  "dream_answers_owner_question",
] as const;

const OPTION_KEYS = [
  "option_ref",
  "inquiry_ref",
  "domain",
  "label",
  "summary",
  "checkpoint_days",
] as const;

const OBSERVATION_KEYS = [
  "contract_version",
  "task_ref",
  "task_hash",
  "inquiry_ref",
  "inquiry_hash",
  "encounter_ref",
  "option",
  "checkpoint_on",
  "semantics",
  "private_to_account",
  "owner_self_report_only",
  "mingli_evidence_role",
  "dream_result_validates_owner_question",
] as const;

const CHECKIN_KEYS = [
  "contract_version",
  "checkin_ref",
  "checkin_hash",
  "task_ref",
  "task_hash",
  "status",
  "note",
  "checked_in_on",
  "semantics",
  "private_to_account",
  "owner_self_report_only",
  "mingli_evidence_role",
  "validates_dream_or_mingli",
] as const;

const JOURNEY_KEYS = [
  "contract_version",
  "status",
  "inquiry",
  "observation_options",
  "observation",
  "latest_checkin",
  "checkin_count",
  "private_to_account",
  "owner_self_report_only",
  "mingli_evidence_role",
  "dream_answers_owner_question",
  "tree_candidate_set_or_order_changed",
  "chapter_route_changed",
  "episode_question_changed",
  "answer_changed",
  "npc_choice_changed",
  "world_outcome_changed",
  "mingli_write_allowed",
  "decision_write_allowed",
  "knowledge_write_allowed",
] as const;

const DOMAINS = ["career", "wealth", "relationship"] as const;
const STATUSES = [
  "IN_DREAM",
  "DREAM_INTERRUPTED",
  "AWAITING_OBSERVATION",
  "OBSERVING",
  "FOLLOWED_UP",
] as const;
const CHECKIN_STATUSES = [
  "OBSERVED",
  "NOT_OBSERVED",
  "STILL_OBSERVING",
] as const;

function isDate(value: unknown): value is string {
  if (
    typeof value !== "string" ||
    !/^\d{4}-\d{2}-\d{2}$/.test(value)
  ) {
    return false;
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  return (
    !Number.isNaN(parsed.getTime()) &&
    parsed.toISOString().slice(0, 10) === value
  );
}

function isInquiry(
  value: unknown,
  bindings: JourneyBindings,
): value is DreamPrivateInquiry {
  if (!isRecord(value) || !hasOnlyKeys(value, INQUIRY_KEYS)) {
    return false;
  }
  return (
    value.contract_version === DREAM_PRIVATE_INQUIRY_VERSION &&
    isRef(value.inquiry_ref) &&
    isHash(value.inquiry_hash) &&
    isOneOf(value.domain, DOMAINS) &&
    typeof value.question === "string" &&
    value.question.length >= 4 &&
    value.question.length <= 120 &&
    isRef(value.candidate_ref) &&
    isHash(value.candidate_hash) &&
    isRef(value.public_alias) &&
    isRef(value.tree_ref) &&
    isRef(value.encounter_ref) &&
    isRef(value.episode_question_ref) &&
    value.private_to_account === true &&
    value.owner_self_report_only === true &&
    value.mingli_evidence_role === "NOT_MINGLI_EVIDENCE" &&
    value.reading_used_to_select_candidate === false &&
    value.llm_interpretation_used === false &&
    value.dream_answers_owner_question === false &&
    (bindings.candidateRef === undefined ||
      value.candidate_ref === bindings.candidateRef) &&
    (bindings.candidateHash === undefined ||
      value.candidate_hash === bindings.candidateHash) &&
    (bindings.encounterRef === undefined ||
      value.encounter_ref === bindings.encounterRef) &&
    (bindings.treeRef === undefined ||
      value.tree_ref === bindings.treeRef)
  );
}

function isOption(
  value: unknown,
  inquiry: DreamPrivateInquiry,
): value is DreamPersonalObservationOption {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, OPTION_KEYS) &&
    isRef(value.option_ref) &&
    value.inquiry_ref === inquiry.inquiry_ref &&
    value.domain === inquiry.domain &&
    isRef(value.label) &&
    isRef(value.summary) &&
    value.checkpoint_days === 7
  );
}

function isObservation(
  value: unknown,
  inquiry: DreamPrivateInquiry,
  options: DreamPersonalObservationOption[],
): value is DreamPersonalObservation {
  if (!isRecord(value) || !hasOnlyKeys(value, OBSERVATION_KEYS)) {
    return false;
  }
  const option = value.option;
  if (
    value.contract_version !== DREAM_PERSONAL_OBSERVATION_VERSION ||
    !isRef(value.task_ref) ||
    !isHash(value.task_hash) ||
    value.inquiry_ref !== inquiry.inquiry_ref ||
    value.inquiry_hash !== inquiry.inquiry_hash ||
    value.encounter_ref !== inquiry.encounter_ref ||
    !isOption(option, inquiry) ||
    !options.some(
      (candidate) =>
        candidate.option_ref === option.option_ref &&
        candidate.label === option.label &&
        candidate.summary === option.summary,
    )
  ) {
    return false;
  }
  return (
    isDate(value.checkpoint_on) &&
    value.semantics === "PRIVATE_REALITY_OBSERVATION_ONLY" &&
    value.private_to_account === true &&
    value.owner_self_report_only === true &&
    value.mingli_evidence_role === "NOT_MINGLI_EVIDENCE" &&
    value.dream_result_validates_owner_question === false
  );
}

function isCheckIn(
  value: unknown,
  observation: DreamPersonalObservation,
): value is DreamPersonalCheckIn {
  return (
    isRecord(value) &&
    hasOnlyKeys(value, CHECKIN_KEYS) &&
    value.contract_version === DREAM_PERSONAL_CHECKIN_VERSION &&
    isRef(value.checkin_ref) &&
    isHash(value.checkin_hash) &&
    value.task_ref === observation.task_ref &&
    value.task_hash === observation.task_hash &&
    isOneOf(value.status, CHECKIN_STATUSES) &&
    (value.note === null ||
      (typeof value.note === "string" && value.note.length <= 160)) &&
    isDate(value.checked_in_on) &&
    value.semantics === "PRIVATE_SELF_REPORTED_CHECK_IN" &&
    value.private_to_account === true &&
    value.owner_self_report_only === true &&
    value.mingli_evidence_role === "NOT_MINGLI_EVIDENCE" &&
    value.validates_dream_or_mingli === false
  );
}

export function isDreamPersonalJourneyDisplayable(
  value: unknown,
  bindings: JourneyBindings = {},
): value is DreamPersonalJourney {
  if (
    !isRecord(value) ||
    !hasOnlyKeys(value, JOURNEY_KEYS) ||
    value.contract_version !== DREAM_PERSONAL_JOURNEY_VERSION ||
    !isOneOf(value.status, STATUSES) ||
    !isInquiry(value.inquiry, bindings) ||
    !Array.isArray(value.observation_options) ||
    value.private_to_account !== true ||
    value.owner_self_report_only !== true ||
    value.mingli_evidence_role !== "NOT_MINGLI_EVIDENCE" ||
    value.dream_answers_owner_question !== false ||
    value.tree_candidate_set_or_order_changed !== false ||
    value.chapter_route_changed !== false ||
    value.episode_question_changed !== false ||
    value.answer_changed !== false ||
    value.npc_choice_changed !== false ||
    value.world_outcome_changed !== false ||
    value.mingli_write_allowed !== false ||
    value.decision_write_allowed !== false ||
    value.knowledge_write_allowed !== false ||
    !isNonNegativeInteger(value.checkin_count)
  ) {
    return false;
  }

  const inquiry = value.inquiry;
  const options = value.observation_options;
  if (
    !options.every((option) => isOption(option, inquiry)) ||
    new Set(options.map(({ option_ref }) => option_ref)).size !==
      options.length
  ) {
    return false;
  }
  if (
    value.status === "IN_DREAM" ||
    value.status === "DREAM_INTERRUPTED"
  ) {
    return (
      options.length === 0 &&
      value.observation === null &&
      value.latest_checkin === null &&
      value.checkin_count === 0
    );
  }
  if (options.length !== 3) return false;
  if (value.status === "AWAITING_OBSERVATION") {
    return (
      value.observation === null &&
      value.latest_checkin === null &&
      value.checkin_count === 0
    );
  }
  if (!isObservation(value.observation, inquiry, options)) {
    return false;
  }
  if (value.status === "OBSERVING") {
    return value.latest_checkin === null && value.checkin_count === 0;
  }
  return (
    value.checkin_count >= 1 &&
    isCheckIn(value.latest_checkin, value.observation)
  );
}
