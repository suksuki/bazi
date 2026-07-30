export const DREAM_RETURN_ATTENTION_VERSION =
  "v60.dream-return-attention.001" as const;
export const DREAM_OPENING_ATTENTION_VERSION =
  "v60.dream-opening-attention.001" as const;

export interface DreamAttentionOption {
  observation_ref: string;
  kind: "WORLD_RESPONSE" | "OUTCOME_EVIDENCE" | "OPEN_OBSERVATION";
  label: string;
  summary: string;
}

export interface DreamAttentionSelection {
  attention_ref: string;
  attention_hash: string;
  observation_ref: string;
  label: string;
  summary: string;
}

export interface DreamReturnAttentionPrompt {
  contract_version: typeof DREAM_RETURN_ATTENTION_VERSION;
  source_encounter_ref: string;
  source_encounter_version: number;
  source_echo_ref: string;
  source_echo_hash: string;
  source_candidate_ref: string;
  source_candidate_hash: string;
  tree_ref: string;
  status: "AWAITING_SELECTION" | "SELECTED";
  options: DreamAttentionOption[];
  selection: DreamAttentionSelection | null;
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
}

export interface DreamOpeningAttention {
  contract_version: typeof DREAM_OPENING_ATTENTION_VERSION;
  application_ref: string;
  application_hash: string;
  attention_ref: string;
  attention_hash: string;
  source_echo_ref: string;
  source_tree_ref: string;
  target_tree_ref: string;
  target_encounter_ref: string;
  observation_ref: string;
  label: string;
  summary: string;
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

export function isDreamReturnAttentionDisplayable(
  attention: DreamReturnAttentionPrompt | null | undefined,
): attention is DreamReturnAttentionPrompt {
  if (
    attention?.contract_version !== DREAM_RETURN_ATTENTION_VERSION ||
    !attention.source_encounter_ref ||
    !Number.isInteger(attention.source_encounter_version) ||
    attention.source_encounter_version < 1 ||
    !attention.source_echo_ref ||
    attention.source_echo_hash?.length !== 64 ||
    !attention.source_candidate_ref ||
    attention.source_candidate_hash?.length !== 64 ||
    !attention.tree_ref ||
    !Array.isArray(attention.options) ||
    attention.options.length < 2 ||
    attention.options.length > 3 ||
    attention.semantics !== "DREAM_RETURN_ATTENTION_ONLY" ||
    attention.evidence_role !== "NOT_EVIDENCE" ||
    attention.tree_candidate_set_or_order_changed !== false ||
    attention.question_changed !== false ||
    attention.answer_changed !== false ||
    attention.npc_choice_changed !== false ||
    attention.outcome_changed !== false ||
    attention.mingli_write_allowed !== false ||
    attention.decision_write_allowed !== false ||
    attention.knowledge_write_allowed !== false
  ) {
    return false;
  }

  const optionRefs = new Set<string>();
  for (const option of attention.options) {
    if (
      !option.observation_ref ||
      !["WORLD_RESPONSE", "OUTCOME_EVIDENCE", "OPEN_OBSERVATION"].includes(
        option.kind,
      ) ||
      !option.label ||
      !option.summary ||
      optionRefs.has(option.observation_ref)
    ) {
      return false;
    }
    optionRefs.add(option.observation_ref);
  }

  if (attention.status === "AWAITING_SELECTION") {
    return attention.selection === null;
  }
  if (attention.status !== "SELECTED" || attention.selection === null) {
    return false;
  }
  const selectedOption = attention.options.find(
    (option) =>
      option.observation_ref === attention.selection?.observation_ref,
  );
  return (
    Boolean(attention.selection.attention_ref) &&
    attention.selection.attention_hash?.length === 64 &&
    selectedOption?.label === attention.selection.label &&
    selectedOption.summary === attention.selection.summary
  );
}

export function isDreamOpeningAttentionDisplayable(
  attention: DreamOpeningAttention | null | undefined,
): attention is DreamOpeningAttention {
  return (
    attention?.contract_version === DREAM_OPENING_ATTENTION_VERSION &&
    Boolean(attention.application_ref) &&
    attention.application_hash?.length === 64 &&
    Boolean(attention.attention_ref) &&
    attention.attention_hash?.length === 64 &&
    Boolean(attention.source_echo_ref) &&
    Boolean(attention.source_tree_ref) &&
    Boolean(attention.target_tree_ref) &&
    attention.source_tree_ref === attention.target_tree_ref &&
    Boolean(attention.target_encounter_ref) &&
    Boolean(attention.observation_ref) &&
    Boolean(attention.label) &&
    Boolean(attention.summary) &&
    attention.semantics === "DREAM_RETURN_ATTENTION_ONLY" &&
    attention.evidence_role === "NOT_EVIDENCE" &&
    attention.tree_candidate_set_or_order_changed === false &&
    attention.question_changed === false &&
    attention.answer_changed === false &&
    attention.npc_choice_changed === false &&
    attention.outcome_changed === false &&
    attention.mingli_write_allowed === false &&
    attention.decision_write_allowed === false &&
    attention.knowledge_write_allowed === false &&
    attention.read_only === true
  );
}
