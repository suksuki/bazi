import type { DreamReturnAttentionPrompt } from "../dreamAttentionTypes";
import { isDreamReturnAttentionDisplayable } from "../dreamAttentionTypes";
import type { DreamReturnEcho } from "../dreamReturnEchoTypes";

export function DreamNextAttentionCard({
  attention,
  busy,
  echo,
  onSelect,
}: {
  attention: DreamReturnAttentionPrompt | null | undefined;
  busy: boolean;
  echo: DreamReturnEcho;
  onSelect?: (observationRef: string) => void;
}) {
  if (!attention) return null;

  if (
    !isDreamReturnAttentionDisplayable(attention) ||
    attention.source_echo_ref !== echo.echo_ref ||
    attention.source_echo_hash !== echo.echo_hash
  ) {
    return (
      <section
        className="dream-next-attention dream-next-attention-withheld"
        data-next-attention-status="WITHHELD"
        aria-label="下一次观察目标暂不可选择"
      >
        <strong>下一次观察先留白</strong>
        <p>这份观察邀请与归来足迹没有完整对上，阿布不会替世界补选。</p>
      </section>
    );
  }

  if (attention.status === "SELECTED" && attention.selection) {
    return (
      <section
        className="dream-next-attention dream-next-attention-selected"
        data-next-attention-status="SELECTED"
        data-attention-ref={attention.selection.attention_ref}
        data-attention-hash={attention.selection.attention_hash}
        data-observation-ref={attention.selection.observation_ref}
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
        aria-label="世界已经记住下一次观察目标"
      >
        <small>世界已记住</small>
        <strong>{attention.selection.label}</strong>
        <p>{attention.selection.summary}</p>
        <span>再次进入{echo.public_alias}的生命树时，这个目标会出现在开场。</span>
      </section>
    );
  }

  return (
    <section
      className="dream-next-attention"
      data-next-attention-status="AWAITING_SELECTION"
      data-source-candidate-ref={attention.source_candidate_ref}
      data-source-candidate-hash={attention.source_candidate_hash}
      data-tree-ref={attention.tree_ref}
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
      aria-label="为下一次相遇选择观察目标"
    >
      <small>留给下一次相遇</small>
      <strong>你想继续观察什么？</strong>
      <p>这些方向由这次已提交的梦中经历整理。选择一个，林中会替你记住。</p>
      <div className="dream-next-attention-options">
        {attention.options.map((option) => (
          <button
            data-observation-ref={option.observation_ref}
            disabled={busy || !onSelect}
            key={option.observation_ref}
            onClick={() => onSelect?.(option.observation_ref)}
            type="button"
          >
            <span>{option.label}</span>
            <small>{option.summary}</small>
          </button>
        ))}
      </div>
      <em>它只影响这条梦中生命下次提醒你的观察目标，不改变三棵树，也不写入命理。</em>
    </section>
  );
}
