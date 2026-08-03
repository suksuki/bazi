import { useEffect, useState } from "react";

import type { RuntimeMediaCue } from "../api";
import type { MingliLayerNarrationProjection } from "../mingliLayerNarrationProjection";
import type {
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "../mingliStageTypes";
import { MingliCharacterPerformance } from "./MingliCharacterPerformance";

export function MingliLayerRehearsal({
  actorCue,
  actorRef,
  onClock,
  onClose,
  projection,
  stage,
}: {
  actorCue: RuntimeMediaCue;
  actorRef: MingliStageProjection["narrator_actor_id"];
  onClock: (clock: MingliNarrationVisualClock) => void;
  onClose: () => void;
  projection: MingliLayerNarrationProjection;
  stage: MingliStageProjection;
}) {
  const [chapterIndex, setChapterIndex] = useState(0);
  const chapter = projection.chapters[chapterIndex] ?? projection.chapters[0];
  const narrator = actorRef === "DUODUO_NARRATOR_V1" ? "多多" : "阿布";

  useEffect(() => setChapterIndex(0), [projection.graphRef, projection.layer]);

  useEffect(() => {
    onClock({
      phase: "PAUSED",
      currentTimeMs: chapterIndex * 1000,
      activeCueId: null,
      cueProgress: 1,
      semanticAction: chapter?.semanticAction ?? "PILLARS_PRESENT",
    });
  }, [chapter?.semanticAction, chapterIndex, onClock]);

  if (!chapter) return null;
  const move = (offset: number) => {
    setChapterIndex((current) =>
      Math.max(0, Math.min(projection.chapters.length - 1, current + offset)),
    );
  };

  return (
    <section
      aria-label={`${narrator}陪你看${projection.layerLabel}`}
      className="mingli-layer-rehearsal"
      data-claim-ref={chapter.claimRef}
      data-graph-hash={projection.graphHash}
      data-graph-ref={projection.graphRef}
      data-layer={projection.layer}
    >
      <div className="mingli-rehearsal-brand">
        <small>阿布说 · 讲述预览</small>
        <strong>{narrator}带你看 · {projection.layerLabel}</strong>
        <span>{projection.notice ?? "先校对判断，再生成声音"}</span>
      </div>
      <button className="mingli-rehearsal-close" onClick={onClose} type="button">
        回到命理阅读 <span aria-hidden="true">↗</span>
      </button>
      <MingliCharacterPerformance
        activeCue={null}
        attentionLabel={`正在看：${chapter.eyebrow}`}
        actorRef={actorRef}
        cue={actorCue}
        performanceMode="REHEARSAL"
        phase="PAUSED"
        stage={stage}
      />
      <article className="mingli-rehearsal-caption" aria-live="polite">
        <small>{chapter.eyebrow} · {chapter.statusLabel}</small>
        <h2>{chapter.title}</h2>
        <p>{chapter.text}</p>
        {chapter.evidenceLine && <span>{chapter.evidenceLine}</span>}
        {chapter.condition && <em>成立条件：{chapter.condition}</em>}
      </article>
      <nav className="mingli-rehearsal-rail" aria-label="讲述章节">
        <button
          disabled={chapterIndex === 0}
          onClick={() => move(-1)}
          type="button"
        >
          上一段
        </button>
        <div>
          <small>{projection.layerLabel}</small>
          <span aria-label={`第 ${chapterIndex + 1} 段，共 ${projection.chapters.length} 段`}>
            {projection.chapters.map((item, index) => (
              <button
                aria-label={`查看第 ${index + 1} 段：${item.eyebrow}`}
                aria-pressed={index === chapterIndex}
                key={item.chapterId}
                onClick={() => setChapterIndex(index)}
                type="button"
              />
            ))}
          </span>
        </div>
        <button
          disabled={chapterIndex === projection.chapters.length - 1}
          onClick={() => move(1)}
          type="button"
        >
          下一段
        </button>
      </nav>
    </section>
  );
}
