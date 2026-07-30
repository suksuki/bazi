import type { DreamReadingObservationLensModel } from "../homeDreamObservationLens";
import "../styles/dream-reading-observation-lens.css";

type DreamReadingObservationLensMode = "grove" | "encounter";

export function DreamReadingObservationLens({
  lens,
  mode = "grove",
}: {
  lens: DreamReadingObservationLensModel;
  mode?: DreamReadingObservationLensMode;
}) {
  const encounter = mode === "encounter";

  return (
    <aside
      aria-label="命理 Reading 的只读现实观察"
      className="dream-reading-observation-lens"
      data-attention-order-recorded={lens.attention_order_recorded}
      data-canonical-write-allowed={lens.canonical_write_allowed}
      data-decision-role={lens.decision_role}
      data-dream-answer-or-outcome-input={false}
      data-dream-outcome-admitted-as-owner-evidence={false}
      data-future-evidence-included={lens.future_evidence_included}
      data-mode={mode}
      data-semantics={lens.semantics}
      data-tree-candidate-set-or-order-changed={
        lens.tree_candidate_set_or_order_changed
      }
    >
      <header>
        <span>
          <small>Reading 观察镜片</small>
          <strong>
            {encounter ? "把三个现实问题留在树边" : "带着三个问题进入雾林"}
          </strong>
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
        {encounter
          ? "这三条只属于你的现实观察；系统不把它们写入树中问题、封印或结果，也不用梦中结果验证你的命理，不预测、不回写。"
          : "只用于留意现实；系统不会据此改动三棵树的候选或顺序，也不预测结果、不回写命理。"}
      </p>
    </aside>
  );
}
