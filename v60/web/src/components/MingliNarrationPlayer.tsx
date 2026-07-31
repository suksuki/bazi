import { useEffect, useMemo, useRef, useState } from "react";

import {
  cueAtAudioTime,
  narrationCommandLabel,
} from "../mingliNarrationMachine";
import { prepareMingliNarration } from "../mingliStageApi";
import type {
  MingliNarrationPhase,
  MingliNarrationReadyResponse,
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "../mingliStageTypes";

type MediaWaitStatus = "WAITING" | "STALLED" | null;

function releaseAudioElement(audio: HTMLAudioElement) {
  audio.pause();
  audio.removeAttribute("src");
  audio.load();
}

export function MingliNarrationPlayer({
  onClock,
  stage,
}: {
  onClock: (clock: MingliNarrationVisualClock) => void;
  stage: MingliStageProjection;
}) {
  const [phase, setPhase] = useState<MingliNarrationPhase | null>(null);
  const [ready, setReady] = useState<MingliNarrationReadyResponse | null>(null);
  const [currentTimeMs, setCurrentTimeMs] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [mediaWait, setMediaWait] = useState<MediaWaitStatus>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const frameRef = useRef<number | null>(null);
  const activeCue = useMemo(
    () => cueAtAudioTime(ready?.asset ?? null, currentTimeMs, phase),
    [currentTimeMs, phase, ready?.asset],
  );

  useEffect(() => {
    onClock({
      phase,
      currentTimeMs,
      activeCueId: activeCue?.cue_id ?? null,
    });
  }, [activeCue?.cue_id, currentTimeMs, onClock, phase]);

  useEffect(() => {
    requestRef.current?.abort();
    if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    setReady(null);
    setPhase(null);
    setCurrentTimeMs(0);
    setError(null);
    setMediaWait(null);
    onClock({ phase: null, currentTimeMs: 0, activeCueId: null });
  }, [onClock, stage.projection_ref]);

  useEffect(
    () => () => {
      requestRef.current?.abort();
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    },
    [],
  );

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    return () => releaseAudioElement(audio);
  }, [ready?.asset.narration_ref]);

  useEffect(() => {
    if (phase !== "PLAYING") {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
      return;
    }
    const sample = () => {
      const audio = audioRef.current;
      if (!audio) return;
      setCurrentTimeMs(Math.round(audio.currentTime * 1000));
      frameRef.current = window.requestAnimationFrame(sample);
    };
    frameRef.current = window.requestAnimationFrame(sample);
    return () => {
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    };
  }, [phase]);

  const prepare = async () => {
    requestRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setError(null);
    setReady(null);
    setCurrentTimeMs(0);
    setPhase("PREPARING");
    setMediaWait(null);
    try {
      const response = await prepareMingliNarration(stage, controller.signal);
      setReady(response);
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError(caught instanceof Error ? caught.message : String(caught));
      setPhase("FAILED");
    }
  };

  const togglePlayback = async () => {
    if (phase === null || phase === "FAILED") {
      await prepare();
      return;
    }
    const audio = audioRef.current;
    if (!audio || phase === "PREPARING") return;
    if (phase === "PLAYING") {
      audio.pause();
      return;
    }
    if (phase === "ENDED") {
      audio.currentTime = 0;
      setCurrentTimeMs(0);
    }
    try {
      await audio.play();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : String(caught));
      setPhase("FAILED");
    }
  };

  const narrator = stage.narrator_actor_id === "DUODUO_NARRATOR_V1" ? "多多" : "阿布";
  return (
    <section
      className="mingli-narration"
      data-active-cue-id={activeCue?.cue_id ?? "NONE"}
      data-audio-time-ms={currentTimeMs}
      data-media-wait={mediaWait ?? "STABLE"}
      data-narration-phase={phase ?? "IDLE"}
    >
      {ready && (
        <audio
          key={ready.asset.narration_ref}
          preload="auto"
          ref={audioRef}
          src={ready.audio_url}
          onCanPlay={() => {
            setMediaWait(null);
            if (phase === "PREPARING") setPhase("READY");
          }}
          onEnded={() => {
            setCurrentTimeMs(ready.asset.duration_ms);
            setMediaWait(null);
            setPhase("ENDED");
          }}
          onError={(event) => {
            if (!event.currentTarget.getAttribute("src")) return;
            setError("同源音频未能完成加载");
            setPhase("FAILED");
          }}
          onPause={(event) => {
            setCurrentTimeMs(Math.round(event.currentTarget.currentTime * 1000));
            if (!event.currentTarget.ended) {
              setPhase((current) => (current === "PLAYING" ? "PAUSED" : current));
            }
          }}
          onPlaying={() => {
            setMediaWait(null);
            setPhase("PLAYING");
          }}
          onStalled={(event) => {
            setCurrentTimeMs(Math.round(event.currentTarget.currentTime * 1000));
            setMediaWait("STALLED");
          }}
          onWaiting={(event) => {
            setCurrentTimeMs(Math.round(event.currentTarget.currentTime * 1000));
            setMediaWait("WAITING");
          }}
        />
      )}
      <div className="mingli-narration-speaker">
        <span aria-hidden="true">{narrator === "阿布" ? "阿" : "多"}</span>
        <p>
          <strong>{narrator}讲述</strong>
          <small>
            卡通角色声线 ·{" "}
            {(ready?.asset.voice_profile_status ?? stage.narration_voice_status) ===
            "OWNER_SELECTED"
              ? "Owner 已选"
              : "试听候选"}
          </small>
        </p>
      </div>
      <div className="mingli-narration-subtitle" aria-live="polite">
        {phase === "PREPARING" ? (
          <p>脚本、投影、声音与提示正在一起锁定……</p>
        ) : activeCue ? (
          <p>{activeCue.text}</p>
        ) : (
          <p>声音就绪前，字幕和舞台强调不会抢跑。</p>
        )}
      </div>
      {mediaWait && (
        <p className="mingli-narration-wait" role="status">
          {mediaWait === "STALLED"
            ? "音频暂未取得新数据；可暂停后继续，舞台保持在当前音频时间。"
            : "声音正在缓冲；字幕与舞台强调冻结在当前音频时间。"}
        </p>
      )}
      {error && <p className="mingli-narration-error">声音未能准备：{error}</p>}
      <div className="mingli-narration-controls">
        <button
          disabled={phase === "PREPARING"}
          onClick={() => void togglePlayback()}
          type="button"
        >
          <span aria-hidden="true">{phase === "PLAYING" ? "Ⅱ" : "▶"}</span>
          {narrationCommandLabel(phase)}
        </button>
        {ready && (
          <small>
            {(currentTimeMs / 1000).toFixed(1)} / {(ready.asset.duration_ms / 1000).toFixed(1)} 秒
          </small>
        )}
      </div>
    </section>
  );
}
