import { NarrationTimeline } from "./audio";
import type { NarrationManifest, NarrationStatus } from "./contracts";
import type { UiAction } from "./state";


export function createNarrationTimeline(
  caseId: string,
  manifest: NarrationManifest,
  statuses: Record<string, NarrationStatus>,
  dispatch: (action: UiAction) => void,
  focusAnchor: (anchor: string, scroll?: boolean) => void,
  humanizeError: (message: string) => string,
): NarrationTimeline {
  return new NarrationTimeline(caseId, manifest, statuses, {
    onPreparing(segment, index) {
      dispatch({ type: "narration", status: "preparing", index, message: `我正在准备“${segment.title}”。页面可以先看，不用等我。` });
    },
    onPlaying(segment, index) {
      dispatch({ type: "narration", status: "playing", index, message: segment.text });
      focusAnchor(segment.visual_anchor_ids[0] || "baseline-summary", false);
    },
    onPaused(segment, index) {
      dispatch({ type: "narration", status: "paused", index, message: `停在“${segment.title}”。你可以先看页面，也可以继续听。` });
    },
    onComplete() {
      dispatch({ type: "narration", status: "complete", index: -1, message: "这次先讲到这里。你可以点四柱、路径或未决项继续问。" });
    },
    onError(error) {
      dispatch({ type: "narration", status: "error", message: `声音暂时没有准备好：${humanizeError(error.message)}。文字内容仍然完整可读。` });
    },
    onCue(anchor) {
      focusAnchor(anchor, false);
    },
  });
}
