import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { cueAtAudioTime } from "./mingliNarrationMachine";
import { prepareMingliNarration } from "./mingliStageApi";
import type {
  MingliNarrationPhase,
  MingliNarrationReadyResponse,
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "./mingliStageTypes";

export type MingliMediaWaitStatus = "WAITING" | "STALLED" | null;

function releaseAudioElement(audio: HTMLAudioElement) {
  audio.pause();
  audio.removeAttribute("src");
  audio.load();
}

export function useMingliNarrationDirector({
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
  const [mediaWait, setMediaWait] = useState<MingliMediaWaitStatus>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  const frameRef = useRef<number | null>(null);
  const activeCue = useMemo(
    () => cueAtAudioTime(ready?.asset ?? null, currentTimeMs, phase),
    [currentTimeMs, phase, ready?.asset],
  );
  const cueProgress = useMemo(() => {
    if (!activeCue) return 0;
    if (phase === "ENDED") return 1;
    return Math.max(
      0,
      Math.min(
        1,
        (currentTimeMs - activeCue.start_ms) /
          Math.max(1, activeCue.end_ms - activeCue.start_ms),
      ),
    );
  }, [activeCue, currentTimeMs, phase]);

  useEffect(() => {
    onClock({
      phase,
      currentTimeMs,
      activeCueId: activeCue?.cue_id ?? null,
      cueProgress,
      semanticAction: activeCue?.semantic_action ?? null,
    });
  }, [activeCue, cueProgress, currentTimeMs, onClock, phase]);

  useEffect(() => {
    requestRef.current?.abort();
    if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    setReady(null);
    setPhase(null);
    setCurrentTimeMs(0);
    setError(null);
    setMediaWait(null);
  }, [stage.projection_ref]);

  useEffect(
    () => () => {
      requestRef.current?.abort();
      if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
      if (audioRef.current) releaseAudioElement(audioRef.current);
    },
    [],
  );

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

  const prepare = useCallback(async () => {
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
      if (!controller.signal.aborted) setReady(response);
    } catch (caught) {
      if (controller.signal.aborted) return;
      setError(caught instanceof Error ? caught.message : String(caught));
      setPhase("FAILED");
    }
  }, [stage]);

  const togglePlayback = useCallback(async () => {
    if (phase === null || phase === "FAILED") {
      await prepare();
      return;
    }
    const audio = audioRef.current;
    if (!audio || phase === "PREPARING") return;
    if (phase === "PLAYING" || phase === "BUFFERING") {
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
  }, [phase, prepare]);

  return {
    activeCue,
    audioRef,
    currentTimeMs,
    error,
    mediaWait,
    phase,
    prepare,
    ready,
    togglePlayback,
    playerEvents: {
      onCanPlay: () => {
        setMediaWait(null);
        setPhase((current) => (current === "PREPARING" ? "READY" : current));
      },
      onEnded: () => {
        if (ready) setCurrentTimeMs(ready.asset.duration_ms);
        setMediaWait(null);
        setPhase("ENDED");
      },
      onError: (audio: HTMLAudioElement) => {
        if (!audio.getAttribute("src")) return;
        setError("同源音频未能完成加载");
        setPhase("FAILED");
      },
      onPause: (audio: HTMLAudioElement) => {
        setCurrentTimeMs(Math.round(audio.currentTime * 1000));
        if (!audio.ended) {
          setPhase((current) =>
            current === "PLAYING" || current === "BUFFERING"
              ? "PAUSED"
              : current,
          );
        }
      },
      onPlaying: () => {
        setMediaWait(null);
        setPhase("PLAYING");
      },
      onStalled: (audio: HTMLAudioElement) => {
        setCurrentTimeMs(Math.round(audio.currentTime * 1000));
        setMediaWait("STALLED");
        setPhase("BUFFERING");
      },
      onWaiting: (audio: HTMLAudioElement) => {
        setCurrentTimeMs(Math.round(audio.currentTime * 1000));
        setMediaWait("WAITING");
        setPhase("BUFFERING");
      },
    },
  };
}
