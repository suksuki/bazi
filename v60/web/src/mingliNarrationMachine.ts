import type {
  MingliNarrationAsset,
  MingliNarrationCue,
  MingliNarrationPhase,
} from "./mingliStageTypes";

export function cueAtAudioTime(
  asset: MingliNarrationAsset | null,
  currentTimeMs: number,
  phase: MingliNarrationPhase | null,
): MingliNarrationCue | null {
  if (
    !asset ||
    !["PLAYING", "BUFFERING", "PAUSED", "ENDED"].includes(phase ?? "")
  ) {
    return null;
  }
  if (phase === "ENDED") return asset.cues.at(-1) ?? null;
  return (
    asset.cues.find(
      (cue) => currentTimeMs >= cue.start_ms && currentTimeMs < cue.end_ms,
    ) ?? asset.cues.at(-1) ?? null
  );
}

export function narrationCommandLabel(phase: MingliNarrationPhase | null): string {
  if (phase === "PREPARING") return "正在准备声音";
  if (phase === "READY") return "开始播放";
  if (phase === "PLAYING") return "暂停讲述";
  if (phase === "BUFFERING") return "暂停等待";
  if (phase === "PAUSED") return "继续播放";
  if (phase === "ENDED") return "重新播放";
  if (phase === "FAILED") return "重新准备";
  return "请角色讲述";
}
