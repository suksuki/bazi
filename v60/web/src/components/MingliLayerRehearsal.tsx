import type { RuntimeMediaCue } from "../publicRuntimeTypes";
import type { MingliLayerNarrationProjection } from "../mingliLayerNarrationProjection";
import type {
  MingliFocusedPassRecord,
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "../mingliStageTypes";
import { useMingliFocusedSpeechDirector } from "../useMingliFocusedSpeechDirector";
import { MingliCharacterPerformance } from "./MingliCharacterPerformance";

export function MingliLayerRehearsal({
  actorCue,
  actorRef,
  onClock,
  onClose,
  projection,
  returnLabel,
  speechRecords,
  stage,
}: {
  actorCue: RuntimeMediaCue;
  actorRef: MingliStageProjection["narrator_actor_id"];
  onClock: (clock: MingliNarrationVisualClock) => void;
  onClose: () => void;
  projection: MingliLayerNarrationProjection;
  returnLabel: string;
  speechRecords: MingliFocusedPassRecord[];
  stage: MingliStageProjection;
}) {
  const firstChapter = projection.chapters[0];
  const narrator = actorRef === "DUODUO_NARRATOR_V1" ? "多多" : "阿布";
  const speech = useMingliFocusedSpeechDirector({
    onClock,
    projection,
    speechRecords,
    stage,
  });
  const activeChapter = projection.chapters.find(
    (chapter) => chapter.chapterId === speech.activeChapterId,
  ) ?? firstChapter;
  const subtitleMode = speech.activeSubtitle !== null && [
    "PLAYING",
    "BUFFERING",
    "PAUSED",
    "ENDED",
  ].includes(speech.speechState);

  const speechLabel = speech.speechState === "PREPARING"
    ? "准备声音…"
    : speech.speechState === "PLAYING"
        || speech.speechState === "BUFFERING"
        || speech.speechState === "FALLBACK"
      ? "暂停"
      : speech.speechState === "PAUSED"
        ? "继续"
        : `听${narrator}讲`;

  if (!firstChapter) return null;

  return (
    <section
      aria-label={`${narrator}陪你看${projection.layerLabel}`}
      className="mingli-layer-rehearsal"
      data-graph-hash={projection.graphHash ?? undefined}
      data-graph-ref={projection.graphRef ?? undefined}
      data-layer={projection.layer}
      data-active-chapter-id={speech.activeChapterId ?? "NONE"}
      data-active-column-refs={speech.activeSubtitle?.activeColumnRefs.join(",") ?? ""}
      data-active-subtitle-index={speech.activeSubtitle?.cueIndex ?? -1}
      data-active-subtitle-start-ms={speech.activeSubtitle?.startMs ?? -1}
      data-active-subtitle-end-ms={speech.activeSubtitle?.endMs ?? -1}
      data-subtitle-cue-count={speech.activeSubtitle?.cueCount ?? 0}
      data-audio-time-ms={speech.visualClock.currentTimeMs}
      data-caption-mode={subtitleMode ? "SUBTITLE" : "FULL_TEXT"}
      data-cue-progress={speech.visualClock.cueProgress.toFixed(6)}
      data-narration-phase={speech.visualClock.phase ?? "IDLE"}
      data-source-hash={projection.sourceHash}
      data-source-kind={projection.sourceKind}
      data-source-ref={projection.sourceRef}
    >
      <div className="mingli-rehearsal-brand">
        <small>阿布说 · 直接讲述</small>
        <strong>{narrator}带你看 · {projection.layerLabel}</strong>
        <span>{projection.notice ?? "这份讲述与当前命盘来源一一对应。"}</span>
      </div>
      <button className="mingli-rehearsal-close" onClick={onClose} type="button">
        {returnLabel} <span aria-hidden="true">↗</span>
      </button>
      <button
        className="mingli-rehearsal-speech"
        disabled={speech.speechState === "PREPARING"}
        onClick={() => void speech.toggleSpeech()}
        type="button"
      >
        <span aria-hidden="true">
          {speech.speechState === "PLAYING"
            || speech.speechState === "BUFFERING"
            || speech.speechState === "FALLBACK" ? "Ⅱ" : "▶"}
        </span>
        {speechLabel}
      </button>
      {speech.speechNote && (
        <p className="mingli-rehearsal-speech-note" role="status">
          {speech.speechNote}
        </p>
      )}
      <MingliCharacterPerformance
        activeCue={null}
        attentionLabel={speech.speechState === "PLAYING"
          ? `正在讲：${activeChapter.eyebrow}`
          : `正在看：${projection.layerLabel}`}
        actorRef={actorRef}
        cue={actorCue}
        performanceMode="AUDIO"
        phase={speech.visualClock.phase}
        stage={stage}
      />
      <article
        className="mingli-rehearsal-caption"
        aria-live="polite"
      >
        {subtitleMode && speech.activeSubtitle ? (
          <section
            aria-atomic="true"
            className="mingli-rehearsal-subtitle"
            data-chapter-id={activeChapter.chapterId}
            data-cue-index={speech.activeSubtitle.cueIndex}
            key={`${activeChapter.chapterId}:${speech.activeSubtitle.cueIndex}`}
          >
            <small>{activeChapter.eyebrow} · {activeChapter.statusLabel}</small>
            <h2>{activeChapter.title}</h2>
            <p>{speech.activeSubtitle.text}</p>
            <div className="mingli-rehearsal-subtitle-progress" aria-hidden="true">
              <i style={{ transform: `scaleX(${speech.visualClock.cueProgress})` }} />
            </div>
            <span>
              第 {speech.activeSubtitle.cueIndex + 1} / {speech.activeSubtitle.cueCount} 句
            </span>
          </section>
        ) : (
          projection.chapters.map((chapter) => (
            <section
              aria-current={chapter.chapterId === speech.activeChapterId
                ? "true"
                : undefined}
              className="mingli-rehearsal-chapter"
              data-active={chapter.chapterId === speech.activeChapterId}
              data-chapter-id={chapter.chapterId}
              data-claim-ref={chapter.claimRef ?? undefined}
              data-source-item-ref={chapter.sourceItemRef}
              key={chapter.chapterId}
            >
              <small>{chapter.eyebrow} · {chapter.statusLabel}</small>
              <h2>{chapter.title}</h2>
              <p>{chapter.text}</p>
              {chapter.evidenceLine && <span>{chapter.evidenceLine}</span>}
              {chapter.condition && <em>成立条件：{chapter.condition}</em>}
              {chapter.reviewNote && (
                <em className="mingli-rehearsal-review-note">{chapter.reviewNote}</em>
              )}
            </section>
          ))
        )}
      </article>
    </section>
  );
}
