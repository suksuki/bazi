import type { ReadOnlySixPillarCanvas } from "./contracts";
import { dreamRequest } from "./dream_api";


export const DREAM_GAME_BANNER = "V50结构验证场｜正式命盘快照｜不计入真人果实";

export type DreamGameLens =
  | "overview"
  | "five_element"
  | "combination_conflict"
  | "roots_reveal"
  | "timing"
  | "work_path";

export type DreamGameState =
  | "ROUND_OBSERVING"
  | "QUESTION_FLOWER_OPEN"
  | "OPTIONAL_DIVINATION"
  | "JUDGMENT_DRAFTING"
  | "USER_JUDGMENT_SEALED"
  | "BOTH_JUDGMENTS_SEALED"
  | "OUTCOME_REVEALABLE"
  | "OUTCOME_REVEALED"
  | "EVALUATED"
  | "KNOWLEDGE_SEED_ISSUED"
  | "ROUND_COMPLETE"
  | "AUTHORIZATION_REVOKED"
  | "PROJECTION_INVALID"
  | "SEAL_CONFLICT"
  | "FAIL_CLOSED";

export type DreamLearningQuestionKind =
  | "LEAF_BASIC_01"
  | "LEAF_BASIC_02"
  | "TRUNK_BACKBONE_01";

export type DreamLearningQuestionStatus =
  | "NOT_STARTED"
  | "RETRY_REQUIRED"
  | "COMPLETED";

export interface DreamGameContentGate {
  schema_version: "deepbazi.dream_game_content_gate.v1";
  development_content: "V50_CANONICAL_ONLY";
  simulated_round_count: 0;
  v50_canonical_round_count: number;
  verified_real_content_count: number;
  verified_real_content_required: 3;
  verified_real_content_gate: string;
  verified_real_launch: "LOCKED" | "ELIGIBLE_FOR_REVIEW";
  banner: string;
}

export interface DreamGameRoundCard {
  round_id: string;
  resident_scene_ref: string;
  resident_label: string;
  anonymous_label: string;
  event_family: "V50_STRUCTURE_PATH" | string;
  question_preview: string;
  selection_whisper: string;
  evidence_class: "V50_CANONICAL";
  development_only: false;
  banner: string;
  content_state: "PUBLISHABLE";
  knowledge_cutoff: string;
}

export interface DreamGameNodeOption {
  node_ref: string;
  label: string;
  pillar_label: string;
  layer: "stem" | "branch" | "hidden_stem" | "timing" | "unknown";
}

export interface DreamGameRelationOption {
  relation_ref: string;
  label: string;
  source_node_ref: string;
  target_node_ref: string;
  formal: boolean;
  evidence_class: "formal_pre_cutoff";
}

export interface DreamGameQuestion {
  question_id: string;
  subject_label: string;
  neutral_question_text: string;
  known_context: string[];
  knowledge_cutoff: string;
  outcome_window_start: string;
  outcome_window_end: string;
  outcome_options: Record<"yes" | "no" | "partial_or_unclear", string>;
  resolution_criteria: string[];
  disconfirmation_definition: string;
  liuyao_permitted: boolean;
}

export interface DreamGameLearningQuestionPublic {
  question_id: string;
  kind: DreamLearningQuestionKind;
  title: string;
  prompt: string;
  target_lens: DreamGameLens;
  answer_type: "single_choice";
  options: Array<{ option_id: string; label: string }>;
  available: boolean;
  organ_role:
    | "OBSERVATION_LEAF"
    | "RULE_LEAF"
    | "TRUNK_FRAMEWORK"
    | null;
  depends_on: string[];
  difficulty: "FOUNDATION" | "INTERMEDIATE" | "ADVANCED";
}

export interface DreamGameQuestionSetProjection {
  schema_version: "deepbazi.dream_question_set_projection.v1";
  question_set_id: string;
  question_set_version: string;
  source_snapshot_id: string;
  cutoff_at: string;
  domain: "BAZI";
  content_status: "DRAFT" | "VALIDATED" | "GOLDEN" | "ACTIVE" | "RETIRED";
  story_script_ref:
    | "RECOGNIZE_THIS_TREE"
    | "FIND_MAIN_TRUNK"
    | "SEASONAL_VARIATION"
    | null;
  target_lens: DreamGameLens | null;
  reveal_policy: "ASSERTION_REVEAL" | "REALITY_REVEAL";
  questions: DreamGameLearningQuestionPublic[];
}

export interface DreamGameQuestionProgressItem {
  question_id: string;
  kind: DreamLearningQuestionKind;
  status: DreamLearningQuestionStatus;
  attempts: number;
  last_selected_option_id: string;
  feedback: string;
  resolved_answer_ref_kind: "node" | "relation" | "path" | "none";
  resolved_answer_ref: string;
  resolved_evidence_refs: string[];
  completed_at: string | null;
}

export interface DreamGameQuestionProgress {
  schema_version: "deepbazi.dream_question_attempt_progress.v1";
  question_set_id: string;
  items: DreamGameQuestionProgressItem[];
  flower_unlocked: boolean;
  updated_at: string;
}

export interface DreamGameDivination {
  divination_id: string;
  server_timestamp: string;
  divination_temporality: "RETROSPECTIVE_BLIND" | "PROSPECTIVE";
  line_values_bottom_up: number[];
  moving_line_indexes: number[];
  interpretation_status: "not_generated";
}

export interface DreamFlowerLifecycleView {
  schema_version: "deepbazi.flower_lifecycle_view.v1";
  flower_id: string;
  state: "OPEN" | "CLOSED_NO_RESPONSE" | "SHARED_FRUIT_FORMED";
  answer_close_at: string;
  outcome_due_at: string;
  own_answer_sealed: boolean;
  answer_count_visible: boolean;
  answer_count: number | null;
  close_reason: "NATURAL_WITHER" | "OWNER_CLOSED" | "OUTCOME_CUTOFF" | null;
  shared_fruit_visible: boolean;
  revealable: boolean;
  neutral_message: string;
}

export interface DreamGameProjection {
  projection_ref: string;
  round_id: string;
  attempt_id: string;
  resident_scene_ref: string;
  resident_label: string;
  authorization_version: string;
  knowledge_cutoff: string;
  clock_domain: string;
  source_snapshot_id: string;
  cutoff_verification_status:
    | "VERIFIED_AS_OF_SOURCE_VERSION"
    | "LEGACY_CUTOFF_UNVERIFIABLE";
  expires_at: string;
  frozen_projection_hash: string;
  viewer_projection_hash: string;
  canvas: ReadOnlySixPillarCanvas;
  allowed_nodes: DreamGameNodeOption[];
  allowed_relations: DreamGameRelationOption[];
  available_lenses: DreamGameLens[];
  evidence_class: "V50_CANONICAL";
  development_only: false;
  banner: string;
}

export interface DreamGameAttemptView {
  attempt_id: string;
  round_id: string;
  state: DreamGameState;
  projection: DreamGameProjection;
  question_set: DreamGameQuestionSetProjection;
  question_progress: DreamGameQuestionProgress;
  flower_question: DreamGameQuestion | null;
  observed_lenses: DreamGameLens[];
  divination: DreamGameDivination | null;
  flower: DreamFlowerLifecycleView | null;
  sealed: boolean;
  revealable: boolean;
  completed: boolean;
  updated_at: string;
}

export interface DreamGameJudgmentPayload {
  selected_outcome_option_id: "yes" | "no" | "partial_or_unclear";
  confidence_basis_points: number;
  node_refs: string[];
  relation_refs: string[];
  interpretation: string;
  evidence_refs: string[];
  strongest_alternative: string;
  disconfirmation_condition: string;
  idempotency_key: string;
  confirmed: true;
}

export interface DreamGameResult {
  banner: string;
  evidence_class: "V50_CANONICAL";
  development_only: false;
  submission: {
    selected_outcome_option_id: "yes" | "no" | "partial_or_unclear";
    confidence_basis_points: number;
    strongest_alternative: string;
    disconfirmation_condition: string;
    user_path_hypothesis: {
      node_refs: string[];
      relation_refs: string[];
      interpretation: string;
      formal_status: "USER_HYPOTHESIS_ONLY";
    };
  };
  shared_fruit: {
    fruit_id: string;
    flower_id: string;
    round_id: string;
    closure_ref: string;
    answer_set_hash: string;
    answer_count: number;
    visual_state: "MIST_WHITE";
    formed_at: string;
    outcome_due_at: string;
  } | null;
  system_seal: {
    selected_outcome_option_id: "yes" | "no" | "partial_or_unclear";
    confidence_basis_points: number;
    reasoning_summary: string;
    strongest_alternative: string;
    disconfirmation_condition: string;
  };
  outcome_evidence: {
    resolved_option_id: "yes" | "no" | "partial_or_unclear";
    outcome_summary: string;
    evidence_items: string[];
    evidence_class: "V50_CANONICAL";
  };
  evaluation: {
    user_result: { option_match: boolean; decisive_node_omissions: string[] };
    system_result: { option_match: boolean };
    limitations: string[];
  };
  knowledge_seed: {
    issued_calibration_summary: string;
    observation_kept: string[];
    missed_or_overweighted: string[];
    applicable_boundary: string;
    formal_status: "PRIVATE_LEARNING_RECORD";
  };
}

function gamePath(visitId: string, suffix: string): string {
  return `/api/v50/dream/visits/${encodeURIComponent(visitId)}/game/${suffix}`;
}

export function loadDreamGameContentGate(visitId: string): Promise<DreamGameContentGate> {
  return dreamRequest(gamePath(visitId, "content-gate"), undefined, visitId);
}

export function loadDreamGameRounds(visitId: string): Promise<DreamGameRoundCard[]> {
  return dreamRequest(gamePath(visitId, "rounds"), undefined, visitId);
}

export function startDreamGameRound(visitId: string, roundId: string): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `rounds/${encodeURIComponent(roundId)}/start`),
    { method: "POST", body: "{}" },
    visitId,
  );
}

export function loadDreamGameAttempt(visitId: string, attemptId: string): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}`),
    undefined,
    visitId,
  );
}

export function answerDreamLearningQuestion(
  visitId: string,
  attemptId: string,
  questionId: string,
  optionId: string,
  idempotencyKey: string,
): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(
      visitId,
      `attempts/${encodeURIComponent(attemptId)}/learning/${encodeURIComponent(questionId)}/answer`,
    ),
    {
      method: "POST",
      body: JSON.stringify({
        option_id: optionId,
        idempotency_key: idempotencyKey,
      }),
    },
    visitId,
  );
}

export function observeDreamGameLens(
  visitId: string,
  attemptId: string,
  lens: DreamGameLens,
): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/lenses/${lens}`),
    { method: "POST", body: "{}" },
    visitId,
  );
}

export function openDreamProblemFlower(visitId: string, attemptId: string): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/question/open`),
    { method: "POST", body: "{}" },
    visitId,
  );
}

export function castDreamGameDivination(
  visitId: string,
  attemptId: string,
  idempotencyKey: string,
): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/divination`),
    {
      method: "POST",
      body: JSON.stringify({ explicit_user_intent: true, idempotency_key: idempotencyKey }),
    },
    visitId,
  );
}

export function beginDreamGameJudgment(visitId: string, attemptId: string): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/judgment/start`),
    { method: "POST", body: "{}" },
    visitId,
  );
}

export function sealDreamGameJudgment(
  visitId: string,
  attemptId: string,
  payload: DreamGameJudgmentPayload,
): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/judgment/seal`),
    { method: "POST", body: JSON.stringify(payload) },
    visitId,
  );
}

export function closeDreamProblemFlower(
  visitId: string,
  attemptId: string,
  idempotencyKey: string,
): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/flower/close`),
    {
      method: "POST",
      body: JSON.stringify({
        idempotency_key: idempotencyKey,
        confirmed: true,
      }),
    },
    visitId,
  );
}

export function revealDreamGameOutcome(
  visitId: string,
  attemptId: string,
  idempotencyKey: string,
): Promise<DreamGameResult> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/reveal`),
    { method: "POST", body: JSON.stringify({ idempotency_key: idempotencyKey }) },
    visitId,
  );
}

export function loadDreamGameResult(visitId: string, attemptId: string): Promise<DreamGameResult> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/result`),
    undefined,
    visitId,
  );
}

export function completeDreamGameRound(visitId: string, attemptId: string): Promise<DreamGameAttemptView> {
  return dreamRequest(
    gamePath(visitId, `attempts/${encodeURIComponent(attemptId)}/complete`),
    { method: "POST", body: "{}" },
    visitId,
  );
}
