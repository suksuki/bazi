import type { DreamReadingObservationLensModel } from "../homeDreamObservationLens";
import "../styles/dream-reading-observation-lens.css";

export function DreamReadingObservationLens({
  lens,
}: {
  lens: DreamReadingObservationLensModel;
}) {
  return (
    <aside
      aria-label="命理 Reading 的只读现实观察"
      className="dream-reading-observation-lens"
      data-attention-order-recorded={lens.attention_order_recorded}
      data-canonical-write-allowed={lens.canonical_write_allowed}
      data-decision-role={lens.decision_role}
      data-future-evidence-included={lens.future_evidence_included}
      data-semantics={lens.semantics}
      data-tree-candidate-set-or-order-changed={
        lens.tree_candidate_set_or_order_changed
      }
    >
      <header>
        <span>
          <small>Reading 观察镜片</small>
          <strong>带着三个问题进入雾林</strong>
        </span>
        <em>三条等权</em>
      </header>

      <div className="dream-reading-observation-list">
        {lens.observations.map((observation) => (
          <section data-domain={observation.domain} key={observation.domain}>
            <strong>{observation.label}</strong>
            <p>{observation.question}</p>
          </section>
        ))}
      </div>

      <p className="dream-reading-observation-boundary">
        只用于留意现实；系统不会据此改动三棵树的候选或顺序，也不预测结果、不回写命理。
      </p>
    </aside>
  );
}
