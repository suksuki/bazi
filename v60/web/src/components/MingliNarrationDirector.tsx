import { useEffect } from "react";

import type { RuntimeMediaCue } from "../api";
import { narrationCommandLabel } from "../mingliNarrationMachine";
import type {
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "../mingliStageTypes";
import { useMingliNarrationDirector } from "../useMingliNarrationDirector";
import { MingliAudioPlayer } from "./MingliAudioPlayer";
import { MingliCharacterPerformance } from "./MingliCharacterPerformance";

export function MingliNarrationDirector({
  actorCue,
  onClock,
  onClose,
  returnLabel,
  stage,
}: {
  actorCue: RuntimeMediaCue;
  onClock: (clock: MingliNarrationVisualClock) => void;
  onClose: () => void;
  returnLabel: string;
  stage: MingliStageProjection;
}) {
  const director = useMingliNarrationDirector({ onClock, stage });

  useEffect(() => {
    void director.prepare();
  }, [director.prepare]);

  return (
    <section
      className="mingli-narration-director"
      data-active-cue-id={director.activeCue?.cue_id ?? "NONE"}
      data-audio-time-ms={director.currentTimeMs}
      data-media-wait={director.mediaWait ?? "STABLE"}
      data-narration-phase={director.phase ?? "IDLE"}
      aria-label="阿布说共享讲述层"
    >
      <MingliAudioPlayer
        audioRef={director.audioRef}
        events={director.playerEvents}
        ready={director.ready}
      />
      <button className="mingli-narration-close" onClick={onClose} type="button">
        <span aria-hidden="true">←</span>
        {returnLabel}
      </button>
      <MingliCharacterPerformance
        activeCue={director.activeCue}
        cue={actorCue}
        phase={director.phase}
        stage={stage}
      />
      <div className="mingli-narration-subtitle" aria-live="polite">
        {director.phase === "PREPARING" ? (
          <p>脚本、投影、声音与提示正在一起锁定……</p>
        ) : director.activeCue ? (
          <p>{director.activeCue.text}</p>
        ) : (
          <p>声音就绪前，字幕、角色和舞台不会抢跑。</p>
        )}
      </div>
      {director.mediaWait && (
        <p className="mingli-narration-wait" role="status">
          声音正在缓冲；字幕、角色与舞台冻结在同一音频时间。
        </p>
      )}
      {director.error && (
        <p className="mingli-narration-error">声音未能准备：{director.error}</p>
      )}
      <div className="mingli-narration-controls">
        <button
          disabled={director.phase === "PREPARING"}
          onClick={() => void director.togglePlayback()}
          type="button"
        >
          <span aria-hidden="true">{director.phase === "PLAYING" ? "Ⅱ" : "▶"}</span>
          {narrationCommandLabel(director.phase)}
        </button>
        {director.ready && (
          <small>
            {(director.currentTimeMs / 1000).toFixed(1)} /{" "}
            {(director.ready.asset.duration_ms / 1000).toFixed(1)} 秒
          </small>
        )}
      </div>
    </section>
  );
}
