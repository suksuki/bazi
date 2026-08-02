import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";

import type { RuntimeMediaManifest } from "../api";
import type { HomeWorldLight } from "../homeWorldLight";
import type {
  MingliLeafEntry,
  MingliReadingLayer,
} from "../mingliStageNavigation";
import type {
  MingliReadingSummaryProjection,
  MingliStageProjection,
} from "../mingliStageTypes";
import {
  MingliReadingLayerContent,
  summaryMatchesStage,
} from "./MingliReadingJourney";
import { TransparentCharacterMedia } from "./TransparentCharacterMedia";

type EntryState = "opening" | "entered" | "closing";
type GrowthState = "growing" | "ready" | "static";

const LAYERS: Array<{
  id: MingliReadingLayer;
  professional: string;
  product: string;
  organ: string;
}> = [
  { id: "principle", professional: "理法", product: "命局原理", organ: "枝" },
  { id: "image", professional: "象法", product: "生命意象", organ: "叶" },
  { id: "themes", professional: "应事", product: "人生主题", organ: "花" },
  { id: "timing", professional: "应期", product: "时间趋势", organ: "果" },
];

export function MingliBranchJourney({
  agentError,
  agentGenerating,
  entry,
  layer,
  light,
  media,
  onClose,
  onEntryConsumed,
  onLayerChange,
  onGenerateAgent,
  onOpenStage,
  stage,
  summary,
}: {
  agentError: string | null;
  agentGenerating: boolean;
  entry: MingliLeafEntry | null;
  layer: MingliReadingLayer;
  light: HomeWorldLight;
  media: RuntimeMediaManifest;
  onClose: () => void;
  onEntryConsumed: () => void;
  onLayerChange: (layer: MingliReadingLayer) => void;
  onGenerateAgent: () => void;
  onOpenStage: (expandTime: boolean) => void;
  stage: MingliStageProjection;
  summary: MingliReadingSummaryProjection | null;
}) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const shouldGrow = entry !== null && !reducedMotion;
  const [entryState, setEntryState] = useState<EntryState>(
    shouldGrow ? "opening" : "entered",
  );
  const [growthState, setGrowthState] = useState<GrowthState>(
    shouldGrow ? "growing" : "static",
  );
  const [replayNonce, setReplayNonce] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<number | null>(null);
  const entryTimerRef = useRef<number | null>(null);
  const hasFormalReading = summaryMatchesStage(summary, stage);
  const hasClaimGraph = hasFormalReading && summary?.claim_graph !== null;
  const guideIsDodo = light === "day";
  const guideCue = guideIsDodo ? media.cues.dodo_idle : media.cues.abu_idle;
  const film = light === "day"
    ? {
        video: media.assets.mingli_growth_day_video,
        start: media.assets.mingli_growth_day_start,
        poster: media.assets.mingli_growth_day_poster,
      }
    : {
        video: media.assets.mingli_growth_night_video,
        start: media.assets.mingli_growth_night_start,
        poster: media.assets.mingli_growth_night_poster,
      };
  const anchor = entry ?? {
    light,
    viewportX: 34,
    viewportY: 46,
    sceneX: 34,
    sceneY: 46,
  };
  const style = {
    "--mingli-entry-x": `${anchor.viewportX}%`,
    "--mingli-entry-y": `${anchor.viewportY}%`,
    "--mingli-scene-entry-x": `${anchor.sceneX}%`,
    "--mingli-scene-entry-y": `${anchor.sceneY}%`,
  } as CSSProperties;

  useEffect(() => {
    if (!shouldGrow) return;
    entryTimerRef.current = window.setTimeout(() => {
      setEntryState("entered");
      onEntryConsumed();
    }, 1080);
    return () => {
      if (entryTimerRef.current !== null) window.clearTimeout(entryTimerRef.current);
    };
  }, [onEntryConsumed, shouldGrow]);

  useEffect(() => {
    if (entry === null || shouldGrow) return;
    onEntryConsumed();
  }, [entry, onEntryConsumed, shouldGrow]);

  useEffect(() => {
    if (entryState !== "entered" || growthState !== "growing") return;
    void videoRef.current?.play().catch(() => setGrowthState("static"));
  }, [entryState, growthState, replayNonce]);

  useEffect(
    () => () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    },
    [],
  );

  const close = useCallback(() => {
    if (entryState === "closing") return;
    videoRef.current?.pause();
    if (reducedMotion) {
      onClose();
      return;
    }
    setEntryState("closing");
    timerRef.current = window.setTimeout(onClose, 620);
  }, [entryState, onClose, reducedMotion]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [close]);

  const replay = () => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = 0;
    setGrowthState("growing");
    setReplayNonce((current) => current + 1);
  };

  const ready = growthState !== "growing";
  return (
    <section
      aria-busy={!ready}
      aria-label={`${stage.display_name}的命理枝`}
      aria-modal="true"
      className="mingli-growth-world"
      data-entry-state={entryState}
      data-growth-state={growthState}
      data-layer={layer}
      data-light={light}
      data-claim-graph-ref={hasClaimGraph ? summary?.claim_graph?.graph_ref : undefined}
      role="dialog"
      style={style}
    >
      <span className="mingli-entry-leaf-light" aria-hidden="true" />
      <div className="mingli-growth-scene" aria-hidden="true">
        {growthState === "static" ? (
          <img
            className="mingli-growth-film"
            data-asset-ref={film.poster.asset_ref}
            src={film.poster.url}
            alt=""
          />
        ) : (
          <video
            className="mingli-growth-film"
            data-asset-ref={film.video.asset_ref}
            key={`${film.video.asset_ref}:${replayNonce}`}
            muted
            onEnded={() => setGrowthState("ready")}
            onError={() => setGrowthState("static")}
            playsInline
            poster={film.start.url}
            preload="auto"
            ref={videoRef}
            src={film.video.url}
          />
        )}
      </div>

      <nav aria-label="命理四层" className="mingli-growth-nodes">
        {LAYERS.map((item) => (
          <button
            aria-label={`${item.professional}：${item.product}`}
            aria-pressed={layer === item.id}
            className={`mingli-growth-node is-${item.id}`}
            disabled={!ready}
            key={item.id}
            onClick={() => onLayerChange(item.id)}
            type="button"
          >
            <span>{item.organ}</span>
            <b><small>{item.professional}</small>{item.product}</b>
          </button>
        ))}
      </nav>

      <div className="mingli-growth-controls">
        <button onClick={close} type="button"><span aria-hidden="true">←</span> 回到整棵树</button>
        {ready && !reducedMotion && (
          <button onClick={replay} type="button"><span aria-hidden="true">↺</span> 重看生长</button>
        )}
      </div>

      {ready && (
        <>
          <button
            aria-label={`进入${guideIsDodo ? "多多" : "阿布"}陪伴的命理舞台`}
            className={`mingli-growth-guide ${guideIsDodo ? "is-dodo" : "is-abu"}`}
            onClick={() => onOpenStage(false)}
            type="button"
          >
            <TransparentCharacterMedia
              active
              alt=""
              className="mingli-growth-guide-motion"
              cueRef={guideCue.cue_ref}
              poster={guideCue.deliveries.REDUCED_MOTION_POSTER}
              video={guideCue.deliveries.VP9_ALPHA_WEBM}
              webp={guideCue.deliveries.ANIMATED_WEBP}
            />
            <span>{guideIsDodo ? "多多" : "阿布"} · 进入命理舞台</span>
          </button>
          <article aria-live="polite" className="mingli-growth-whisper">
            <header className="mingli-growth-identity">
              <span>{stage.identity_badge}</span>
              <strong>{stage.display_name}的命理枝</strong>
              <small>{hasClaimGraph ? "阿布初断 · 可以继续校准" : "等待阿布整盘初断"}</small>
            </header>
            <MingliReadingLayerContent
              agentError={agentError}
              agentGenerating={agentGenerating}
              hasFormalReading={hasFormalReading}
              layer={layer}
              onExpandTime={() => onOpenStage(true)}
              onGenerateAgent={onGenerateAgent}
              stage={stage}
              summary={summary}
            />
            <div className="mingli-growth-actions">
              <span>轻触枝、叶、花、果，继续看这份命局</span>
              <button onClick={() => onOpenStage(layer === "timing")} type="button">
                {layer === "timing" ? "进入六柱时间舞台" : "查看本命四柱舞台"}
              </button>
            </div>
          </article>
        </>
      )}
    </section>
  );
}
