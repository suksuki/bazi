import type { DreamOpeningAttention as OpeningAttention } from "../dreamAttentionTypes";
import { isDreamOpeningAttentionDisplayable } from "../dreamAttentionTypes";

export function DreamOpeningAttention({
  attention,
}: {
  attention: OpeningAttention | null | undefined;
}) {
  if (!isDreamOpeningAttentionDisplayable(attention)) return null;

  return (
    <aside
      className="dream-opening-attention"
      data-opening-attention-status="REMEMBERED"
      data-application-ref={attention.application_ref}
      data-application-hash={attention.application_hash}
      data-attention-ref={attention.attention_ref}
      data-attention-hash={attention.attention_hash}
      data-source-tree-ref={attention.source_tree_ref}
      data-target-tree-ref={attention.target_tree_ref}
      data-target-encounter-ref={attention.target_encounter_ref}
      data-observation-ref={attention.observation_ref}
      data-semantics={attention.semantics}
      data-evidence-role={attention.evidence_role}
      data-tree-candidate-set-or-order-changed={
        attention.tree_candidate_set_or_order_changed
      }
      data-question-changed={attention.question_changed}
      data-answer-changed={attention.answer_changed}
      data-npc-choice-changed={attention.npc_choice_changed}
      data-outcome-changed={attention.outcome_changed}
      data-mingli-write-allowed={attention.mingli_write_allowed}
      data-decision-write-allowed={attention.decision_write_allowed}
      data-knowledge-write-allowed={attention.knowledge_write_allowed}
      data-read-only={attention.read_only}
      aria-label="上次留下的观察目标"
    >
      <small>上次留下的观察目标 · 世界已记住</small>
      <strong>{attention.label}</strong>
      <p>{attention.summary}</p>
      <span>它只提醒这条梦中生命接下来值得观察什么，不预告答案。</span>
    </aside>
  );
}
