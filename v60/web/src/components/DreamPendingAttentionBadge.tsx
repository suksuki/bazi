import {
  isDreamPendingAttentionDisplayable,
  type DreamPendingAttention,
} from "../dreamAttentionFollowThroughTypes";

export function DreamPendingAttentionBadge({
  candidateRef,
  pending,
}: {
  candidateRef: string;
  pending: DreamPendingAttention | null | undefined;
}) {
  if (
    !isDreamPendingAttentionDisplayable(pending, {
      candidateRefs: [candidateRef],
    }) ||
    pending.source_candidate_ref !== candidateRef
  ) {
    return null;
  }

  return (
    <span
      className="dream-pending-attention-badge"
      data-pending-attention-status={pending.status}
      data-attention-ref={pending.attention_ref}
      data-attention-hash={pending.attention_hash}
      data-source-encounter-ref={pending.source_encounter_ref}
      data-source-encounter-version={pending.source_encounter_version}
      data-source-echo-ref={pending.source_echo_ref}
      data-source-echo-hash={pending.source_echo_hash}
      data-source-candidate-ref={pending.source_candidate_ref}
      data-source-candidate-hash={pending.source_candidate_hash}
      data-tree-ref={pending.tree_ref}
      data-observation-ref={pending.observation_ref}
      data-semantics={pending.semantics}
      data-evidence-role={pending.evidence_role}
      data-tree-candidate-set-or-order-changed={
        pending.tree_candidate_set_or_order_changed
      }
      data-question-changed={pending.question_changed}
      data-answer-changed={pending.answer_changed}
      data-npc-choice-changed={pending.npc_choice_changed}
      data-outcome-changed={pending.outcome_changed}
      data-mingli-write-allowed={pending.mingli_write_allowed}
      data-decision-write-allowed={pending.decision_write_allowed}
      data-knowledge-write-allowed={pending.knowledge_write_allowed}
      data-read-only={pending.read_only}
      aria-label={`世界还记得${pending.label}`}
    >
      <small>上次留下的观察</small>
      <strong>{pending.label}</strong>
      <span>{pending.summary}</span>
      <em>回到这棵树继续</em>
    </span>
  );
}
