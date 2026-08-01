import type { MingliStageProjection } from "../mingliStageTypes";

export function MingliLabSceneInspector({
  onAskGuide,
  onSelectRelation,
  selectedRelationRef,
  stage,
}: {
  onAskGuide: () => void;
  onSelectRelation: (relationRef: string | null) => void;
  selectedRelationRef: string | null;
  stage: MingliStageProjection;
}) {
  const selected =
    stage.relations.find(
      (relation) => relation.relation_ref === selectedRelationRef,
    ) ?? null;

  return (
    <aside className="mingli-lab-inspector" aria-label="命理 Lab 舞台观察">
      <header>
        <p>Lab · 观察同一个舞台</p>
        <h2>关系坐标复核</h2>
        <span>这里只选择与核对，不另建命盘，也不产生新的命理结论。</span>
      </header>
      <div className="mingli-lab-relation-list" role="list" aria-label="已准入关系成员">
        {stage.relations.length ? (
          stage.relations.map((relation) => (
            <button
              aria-pressed={selectedRelationRef === relation.relation_ref}
              data-relation-ref={relation.relation_ref}
              key={relation.relation_ref}
              onClick={() =>
                onSelectRelation(
                  selectedRelationRef === relation.relation_ref
                    ? null
                    : relation.relation_ref,
                )
              }
              type="button"
            >
              <strong>{relation.left_branch}—{relation.right_branch}</strong>
              <span>{relation.label}</span>
              <small>成员关系成立 · 作用待定</small>
            </button>
          ))
        ) : (
          <p>当前柱位没有命中已准入的六冲／六合成员关系。</p>
        )}
      </div>
      {selected && (
        <dl className="mingli-lab-evidence" data-selected-relation-ref={selected.relation_ref}>
          <div>
            <dt>来源柱位</dt>
            <dd>{selected.left_column_ref} ↔ {selected.right_column_ref}</dd>
          </div>
          <div>
            <dt>规则正本</dt>
            <dd>{selected.rule_ref}</dd>
          </div>
          <div>
            <dt>证据引用</dt>
            <dd>{selected.evidence_refs.join(" · ")}</dd>
          </div>
          <div>
            <dt>当前边界</dt>
            <dd>关系作用与来源可用性均为 UNRESOLVED。</dd>
          </div>
        </dl>
      )}
      <button className="mingli-lab-ask-guide" onClick={onAskGuide} type="button">
        请角色按当前舞台讲解
        <span aria-hidden="true">声画同步 →</span>
      </button>
    </aside>
  );
}
