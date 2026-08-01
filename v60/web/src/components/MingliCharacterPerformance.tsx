import type { RuntimeMediaCue } from "../api";
import type {
  MingliNarrationCue,
  MingliNarrationPhase,
  MingliStageProjection,
} from "../mingliStageTypes";
import { TransparentCharacterMedia } from "./TransparentCharacterMedia";

const ATTENTION_LABELS: Record<MingliNarrationCue["cue_id"], string> = {
  STRUCTURE: "正在看完整柱位",
  RELATION_BOUNDARY: "正在看关系成员",
  EVIDENCE_GAP: "正在守住证据边界",
  TIME_LAYER: "正在看大运与流年",
};

export function MingliCharacterPerformance({
  activeCue,
  cue,
  phase,
  stage,
}: {
  activeCue: MingliNarrationCue | null;
  cue: RuntimeMediaCue;
  phase: MingliNarrationPhase | null;
  stage: MingliStageProjection;
}) {
  const isDodo = stage.narrator_actor_id === "DUODUO_NARRATOR_V1";
  const name = isDodo ? "多多" : "阿布";
  const state = performanceState(phase);
  const poster = cue.deliveries.REDUCED_MOTION_POSTER;
  const video = cue.deliveries.VP9_ALPHA_WEBM;
  const webp = cue.deliveries.ANIMATED_WEBP;
  return (
    <div
      className="mingli-character-performance"
      data-actor-ref={stage.narrator_actor_id}
      data-character-state={state}
      data-performance-fidelity="IDLE_MEDIA_WITH_AUDIO_BOUND_STATE"
    >
      <TransparentCharacterMedia
        active={phase === "PLAYING"}
        alt={`${name}${state === "SPEAKING" ? "正在讲述" : "正在陪你看命理舞台"}`}
        className="mingli-character-media"
        cueRef={cue.cue_ref}
        poster={poster}
        video={video}
        webp={webp}
      />
      <div>
        <strong>{name}</strong>
        <span>{stateLabel(state)}</span>
        <small>{activeCue ? ATTENTION_LABELS[activeCue.cue_id] : "等待舞台与声音就绪"}</small>
      </div>
    </div>
  );
}

type CharacterState =
  | "IDLE"
  | "LISTENING"
  | "SPEAKING"
  | "PAUSED"
  | "BUFFERING"
  | "ENDED"
  | "ERROR";

function performanceState(phase: MingliNarrationPhase | null): CharacterState {
  if (phase === "PLAYING") return "SPEAKING";
  if (phase === "PAUSED") return "PAUSED";
  if (phase === "BUFFERING") return "BUFFERING";
  if (phase === "ENDED") return "ENDED";
  if (phase === "FAILED") return "ERROR";
  if (phase === "PREPARING" || phase === "READY") return "LISTENING";
  return "IDLE";
}

function stateLabel(state: CharacterState): string {
  if (state === "SPEAKING") return "正在讲述";
  if (state === "PAUSED") return "讲述已暂停";
  if (state === "BUFFERING") return "声音正在等待";
  if (state === "ENDED") return "这一段讲完了";
  if (state === "ERROR") return "声音没有准备好";
  if (state === "LISTENING") return "在等声音和舞台一起就绪";
  return "安静陪在舞台旁";
}
