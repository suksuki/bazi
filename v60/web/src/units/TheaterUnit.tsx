import type { DreamSnapshot } from "../api";
import type {
  FocusSourcesHandler,
  SemanticFocus,
} from "../semanticFocus";

export function TheaterUnit({
  focus,
  onFocusSources,
  snapshot,
}: {
  focus: SemanticFocus | null;
  onFocusSources: FocusSourcesHandler;
  snapshot: DreamSnapshot;
}) {
  const visibleEvidence = focus
    ? focus.theaterEvidence
    : snapshot.public_evidence.filter((item) =>
        snapshot.projections.theater.evidence_refs.includes(item.evidence_ref),
      );

  return (
    <>
      <p className="rail-kicker">正史片段</p>
      <h2>这一幕已经发生</h2>
      <p className="story-beat">{snapshot.projections.theater.beat}</p>
      {visibleEvidence.length > 0 ? (
        <div className="evidence-thread">
          {visibleEvidence.map((evidence, index) => (
            <button
              key={evidence.evidence_ref}
              type="button"
              onClick={() =>
                onFocusSources(
                  [evidence.evidence_ref],
                  ["EVIDENCE_LEAF", "OUTCOME_FRUIT"],
                )
              }
            >
              <i>{index + 1}</i>
              {evidence.summary}
            </button>
          ))}
        </div>
      ) : (
        <p className="projection-empty">当前焦点没有独立的已提交剧场证据。</p>
      )}
      <p className="unit-boundary">只演已经发生或明确标记的分支，不补写正史。</p>
    </>
  );
}
