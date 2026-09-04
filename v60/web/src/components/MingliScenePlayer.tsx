import { lazy, Suspense, useCallback, useRef, useState } from "react";

import type { MingliSceneFrame } from "../mingliSceneDirector";
import type {
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "../mingliStageTypes";
import { MingliPillarStage } from "./MingliPillarStage";

const MingliSceneCanvas = lazy(() => import("./MingliSceneCanvas"));

export function MingliScenePlayer({
  daylight = false,
  fallbackClock,
  frame,
  stage,
}: {
  daylight?: boolean;
  fallbackClock: MingliNarrationVisualClock;
  frame: MingliSceneFrame;
  stage: MingliStageProjection;
}) {
  const instanceId = useRef(
    `mingli-scene-${Math.random().toString(36).slice(2, 10)}`,
  );
  const [fallbackReason, setFallbackReason] = useState<string | null>(() =>
    supportsWebGl2() ? null : "WEBGL2_UNAVAILABLE",
  );
  const handleContextLost = useCallback(() => {
    setFallbackReason("WEBGL_CONTEXT_LOST");
  }, []);

  return (
    <section
      className="mingli-scene-player"
      data-active-column-refs={frame.activeColumnRefs.join(",")}
      data-column-count={stage.columns.length}
      data-cue-progress={frame.cueProgress.toFixed(6)}
      data-projection-hash={stage.projection_hash}
      data-projection-ref={stage.projection_ref}
      data-scene-instance-id={instanceId.current}
      data-scene-phase={frame.phase}
      data-scene-surface={frame.surface}
      data-stage-mode={stage.stage_mode}
      aria-label={`${stage.display_name}的${stage.columns.length}柱命理舞台`}
    >
      <div className="mingli-scene-player-field">
        {fallbackReason ? (
          <div className="mingli-scene-fallback" data-fallback-reason={fallbackReason}>
            <MingliPillarStage clock={fallbackClock} stage={stage} />
          </div>
        ) : (
          <Suspense
            fallback={
              <div className="mingli-scene-fallback" data-fallback-reason="THREE_LOADING">
                <MingliPillarStage clock={fallbackClock} stage={stage} />
              </div>
            }
          >
            <MingliSceneCanvas
              daylight={daylight}
              frame={frame}
              onContextLost={handleContextLost}
              stage={stage}
            />
          </Suspense>
        )}
        <div className="mingli-scene-vignette" aria-hidden="true" />
        <div className="mingli-scene-column-labels" aria-label="命理柱位">
          {stage.columns.map((column) => (
            <span
              data-column-ref={column.column_ref}
              data-column-role={column.slot}
              data-narrated={frame.activeColumnRefs.includes(column.column_ref)
                ? "true"
                : undefined}
              data-source-layer={column.source_layer}
              key={column.column_ref}
            >
              <strong>{column.label}</strong>
              <small>
                {column.slot === "DAYUN"
                  ? `${column.start_date?.slice(0, 4)}—${column.end_date?.slice(0, 4)}`
                  : column.slot === "ANNUAL"
                    ? `${stage.selected_year} 年`
                    : column.pillar}
              </small>
            </span>
          ))}
        </div>
      </div>
      <div className="mingli-scene-truth-line">
        <span>{stage.columns.length} 柱 · {stage.bodies.length} 个本体球</span>
        <small>场景只表现确定坐标与已准入的关系成员，不演算关系作用。</small>
      </div>
    </section>
  );
}

function supportsWebGl2() {
  if (typeof window === "undefined") return false;
  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("webgl2");
    const loseContext = context?.getExtension("WEBGL_lose_context");
    loseContext?.loseContext();
    return Boolean(context);
  } catch {
    return false;
  }
}
