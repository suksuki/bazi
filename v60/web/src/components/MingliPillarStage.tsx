import type { CSSProperties } from "react";

import type {
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "../mingliStageTypes";

export function MingliPillarStage({
  clock,
  stage,
}: {
  clock: MingliNarrationVisualClock;
  stage: MingliStageProjection;
}) {
  const columnWidth = 600 / stage.columns.length;
  const columnIndex = new Map(
    stage.columns.map((column, index) => [column.column_ref, index]),
  );
  const clockBound = ["PLAYING", "PAUSED", "ENDED"].includes(clock.phase ?? "");
  const clockWave = clockBound
    ? (Math.sin((clock.currentTimeMs / 1200) * Math.PI * 2) + 1) / 2
    : 0;
  const visualStyle = {
    "--mingli-column-count": stage.columns.length,
    "--mingli-clock-wave": clockWave.toFixed(4),
    "--mingli-relation-offset": `${clockBound ? -((clock.currentTimeMs / 45) % 18) : 0}px`,
  } as CSSProperties;
  return (
    <div
      className="mingli-pillar-stage"
      data-active-cue-id={clock.activeCueId ?? "NONE"}
      data-column-count={stage.columns.length}
      data-narration-phase={clock.phase ?? "IDLE"}
      style={visualStyle}
    >
      <div className="mingli-stage-plot">
        <div className="mingli-stage-aura" aria-hidden="true" />
        <div className="mingli-stage-coordinate-plane">
          <svg
            className="mingli-relation-lines"
            aria-hidden="true"
            viewBox="0 0 600 250"
            preserveAspectRatio="none"
          >
            {stage.relations.map((relation, index) => {
              const left = columnIndex.get(relation.left_column_ref) ?? 0;
              const right = columnIndex.get(relation.right_column_ref) ?? 0;
              const startX = (left + 0.5) * columnWidth;
              const endX = (right + 0.5) * columnWidth;
              const arch =
                188 -
                Math.min(76, Math.abs(endX - startX) * 0.18 + index * 8);
              return (
                <path
                  key={relation.relation_ref}
                  data-left-column-ref={relation.left_column_ref}
                  data-relation-type={relation.relation_type}
                  data-right-column-ref={relation.right_column_ref}
                  d={`M ${startX} 207 Q ${(startX + endX) / 2} ${arch} ${endX} 207`}
                />
              );
            })}
          </svg>

          <div className="mingli-stage-columns">
            {stage.columns.map((column) => {
              const bodies = stage.bodies.filter(
                (body) => body.column_ref === column.column_ref,
              );
              return (
                <article
                  className="mingli-stage-column"
                  data-column-ref={column.column_ref}
                  data-column-role={column.slot}
                  data-source-layer={column.source_layer}
                  key={column.column_ref}
                >
                  <header>
                    <span>{column.label}</span>
                    {column.slot === "ANNUAL" && (
                      <small>{stage.selected_year}</small>
                    )}
                    {column.slot === "DAYUN" && (
                      <small>
                        {column.start_date?.slice(0, 4)}–
                        {column.end_date?.slice(0, 4)}
                      </small>
                    )}
                  </header>
                  <div className="mingli-stage-body-stack">
                    {bodies.map((body) => (
                      <span
                        className="mingli-stage-body"
                        data-body-role={body.role}
                        data-body-ref={body.body_ref}
                        key={body.body_ref}
                      >
                        <i aria-hidden="true" />
                        <strong>{body.glyph}</strong>
                        <small>{body.role === "STEM" ? "天干" : "地支"}</small>
                      </span>
                    ))}
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mingli-relation-key" aria-label="当前关系成员事实">
        {stage.relations.length ? (
          stage.relations.map((relation) => (
            <span data-relation-type={relation.relation_type} key={relation.relation_ref}>
              {relation.left_branch}—{relation.right_branch} · {relation.label}
              <small>作用待定</small>
            </span>
          ))
        ) : (
          <span>当前柱位没有命中已准入的六冲／六合成员关系</span>
        )}
      </div>
    </div>
  );
}
