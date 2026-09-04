import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";

import type { RuntimeMediaManifest } from "../publicRuntimeTypes";
import type { HomeWorldLight } from "../homeWorldLight";
import type {
  MingliLeafEntry,
  MingliReadingLayer,
} from "../mingliStageNavigation";
import type { MingliStageProjection } from "../mingliStageTypes";
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

const LAYER_REVEAL_AT = [0.45, 3.32, 4.58, 5.32] as const;

export function MingliBranchJourney({
  agentError,
  agentGenerating,
  entry,
  layer,
  light,
  media,
  onClose,
  onEntryConsumed,
  onActivateLayer,
  stage,
}: {
  agentError: string | null;
  agentGenerating: boolean;
  entry: MingliLeafEntry | null;
  layer: MingliReadingLayer;
  light: HomeWorldLight;
  media: RuntimeMediaManifest;
  onClose: () => void;
  onEntryConsumed: () => void;
  onActivateLayer: (layer: MingliReadingLayer) => void;
  stage: MingliStageProjection;
}) {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const shouldGrow = entry !== null && !reducedMotion;
  const [entryState, setEntryState] = useState<EntryState>(
    shouldGrow ? "opening" : "entered",
  );
  const [growthState, setGrowthState] = useState<GrowthState>(
    shouldGrow ? "growing" : "static",
  );
  const [revealedCount, setRevealedCount] = useState(
    shouldGrow ? 0 : LAYERS.length,
  );
  const [replayNonce, setReplayNonce] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timerRef = useRef<number | null>(null);
  const entryTimerRef = useRef<number | null>(null);
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
      entryTimerRef.current = null;
      setEntryState("entered");
      onEntryConsumed();
    }, 1080);
    return () => {
      if (entryTimerRef.current !== null) {
        window.clearTimeout(entryTimerRef.current);
        entryTimerRef.current = null;
      }
    };
  }, [onEntryConsumed, shouldGrow]);

  useEffect(() => {
    if (entry === null || shouldGrow) return;
    onEntryConsumed();
  }, [entry, onEntryConsumed, shouldGrow]);

  useEffect(() => {
    if (entryState !== "entered" || growthState !== "growing") return;
    void videoRef.current?.play().catch(() => {
      setGrowthState("static");
      setRevealedCount(LAYERS.length);
    });
  }, [entryState, growthState, replayNonce]);

  useEffect(
    () => () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current);
    },
    [],
  );

  const close = useCallback(() => {
    if (entryState === "closing") return;
    if (entryTimerRef.current !== null) {
      window.clearTimeout(entryTimerRef.current);
      entryTimerRef.current = null;
    }
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
    videoRef.current?.pause();
    setGrowthState("growing");
    setRevealedCount(0);
    setReplayNonce((current) => current + 1);
  };

  const updateGrowthTimeline = () => {
    const currentTime = videoRef.current?.currentTime ?? 0;
    const nextCount = LAYER_REVEAL_AT.filter(
      (threshold) => currentTime >= threshold,
    ).length;
    setRevealedCount((current) => Math.max(current, nextCount));
  };

  const completeGrowth = () => {
    setGrowthState("ready");
    setRevealedCount(LAYERS.length);
  };

  const showStaticGrowth = () => {
    setGrowthState("static");
    setRevealedCount(LAYERS.length);
  };

  const ready = growthState !== "growing";
  return (
    <section
      aria-busy={!ready || agentGenerating}
      aria-label={`${stage.display_name}的命理枝`}
      aria-modal="true"
      className="mingli-growth-world"
      data-entry-state={entryState}
      data-growth-state={growthState}
      data-layer={layer}
      data-light={light}
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
            onEnded={completeGrowth}
            onError={showStaticGrowth}
            onTimeUpdate={updateGrowthTimeline}
            playsInline
            poster={film.start.url}
            preload="auto"
            ref={videoRef}
            src={film.video.url}
          />
        )}
      </div>

      <nav aria-label="命理四层" className="mingli-growth-nodes">
        {LAYERS.map((item, index) => {
          const revealed = growthState !== "growing" || index < revealedCount;
          return (
            <button
              aria-label={`点${item.organ}，让阿布说${item.product}`}
              aria-pressed={layer === item.id}
              className={`mingli-growth-node is-${item.id} ${revealed ? "is-revealed" : ""}`}
              disabled={!ready || !revealed || agentGenerating}
              key={item.id}
              onClick={() => onActivateLayer(item.id)}
              type="button"
            >
              <span>{item.organ}</span>
              <b><small>{item.professional}</small>{item.product}</b>
            </button>
          );
        })}
      </nav>

      <div className="mingli-growth-controls">
        <button onClick={close} type="button"><span aria-hidden="true">←</span> 回到整棵树</button>
        {ready && !reducedMotion && (
          <button onClick={replay} type="button"><span aria-hidden="true">↺</span> 重看生长</button>
        )}
      </div>

      {ready && (
        <>
          <div
            aria-live="polite"
            className={`mingli-growth-guide ${guideIsDodo ? "is-dodo" : "is-abu"}`}
            data-speaking-state={agentGenerating ? "preparing" : agentError ? "retry" : "ready"}
            role="status"
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
            <span>{agentGenerating
              ? "阿布正在准备这一层……"
              : agentError
                ? "刚才没讲完整，再点一次重试"
                : "点枝、叶、花、果，直接听阿布说"}</span>
          </div>
        </>
      )}
    </section>
  );
}
