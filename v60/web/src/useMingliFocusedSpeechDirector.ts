import { useEffect, useMemo, useRef, useState } from "react";

import type {
  MingliFocusedPassRecord,
  MingliNarrationCue,
  MingliNarrationVisualClock,
  MingliStageProjection,
} from "./mingliStageTypes";
import type {
  MingliLayerNarrationChapter,
  MingliLayerNarrationProjection,
} from "./mingliLayerNarrationProjection";
import {
  focusedSubtitle,
  type MingliFocusedSubtitle,
} from "./mingliFocusedSpeechTimeline";
import {
  loadFocusedPassSpeech,
  type MingliFocusedSpeechAsset,
} from "./publicSpeechApi";

export type MingliFocusedSpeechState =
  | "IDLE"
  | "PREPARING"
  | "PLAYING"
  | "BUFFERING"
  | "PAUSED"
  | "FALLBACK"
  | "ENDED";

interface FocusedSpeechSegment {
  chapter: MingliLayerNarrationChapter;
  record: MingliFocusedPassRecord;
}

interface PreparedFocusedSpeechSegment extends FocusedSpeechSegment {
  asset: MingliFocusedSpeechAsset;
  url: string;
}

interface PreparedFocusedSpeech {
  segments: PreparedFocusedSpeechSegment[];
}

function cueIdForAction(
  action: MingliNarrationCue["semantic_action"],
): MingliNarrationCue["cue_id"] {
  if (action === "RELATIONS_PRESENT") return "RELATION_BOUNDARY";
  if (action === "BOUNDARY_HOLD") return "EVIDENCE_GAP";
  if (action === "TIME_COORDINATES_PRESENT") return "TIME_LAYER";
  return "STRUCTURE";
}

function releaseAudio(audio: HTMLAudioElement) {
  audio.onended = null;
  audio.onerror = null;
  audio.onpause = null;
  audio.onplaying = null;
  audio.onstalled = null;
  audio.onwaiting = null;
  audio.pause();
  audio.removeAttribute("src");
  audio.load();
}

export function useMingliFocusedSpeechDirector({
  onClock,
  projection,
  speechRecords,
  stage,
}: {
  onClock: (clock: MingliNarrationVisualClock) => void;
  projection: MingliLayerNarrationProjection;
  speechRecords: MingliFocusedPassRecord[];
  stage: MingliStageProjection;
}) {
  const segments = useMemo(() => {
    const recordsByPass = new Map(
      speechRecords.map((record) => [record.pass_result.pass_ref, record]),
    );
    return projection.chapters.flatMap((chapter) => {
      const record = recordsByPass.get(chapter.sourceItemRef);
      return record ? [{ chapter, record }] : [];
    });
  }, [projection.chapters, speechRecords]);
  const firstChapter = projection.chapters[0] ?? null;
  const initialClock = (): MingliNarrationVisualClock => ({
    phase: "PAUSED",
    currentTimeMs: 0,
    activeCueId: firstChapter
      ? cueIdForAction(firstChapter.semanticAction)
      : null,
    cueProgress: 0,
    semanticAction: firstChapter?.semanticAction ?? "PILLARS_PRESENT",
    activeColumnRefs: [],
  });
  const [speechState, setSpeechState] =
    useState<MingliFocusedSpeechState>("IDLE");
  const [speechNote, setSpeechNote] = useState<string | null>(null);
  const [visualClock, setVisualClock] =
    useState<MingliNarrationVisualClock>(initialClock);
  const [activeChapterId, setActiveChapterId] = useState<string | null>(
    firstChapter?.chapterId ?? null,
  );
  const [activeSubtitle, setActiveSubtitle] =
    useState<MingliFocusedSubtitle | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const preparedRef = useRef<PreparedFocusedSpeech | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const frameRef = useRef<number | null>(null);
  const completedTimeMsRef = useRef(0);
  const playbackNonceRef = useRef(0);
  const fallbackNonceRef = useRef(0);
  const activeSubtitleKeyRef = useRef<string | null>(null);

  const publishClock = (next: MingliNarrationVisualClock) => {
    setVisualClock(next);
    onClock(next);
  };
  const stopSampling = () => {
    if (frameRef.current !== null) window.cancelAnimationFrame(frameRef.current);
    frameRef.current = null;
  };
  const publishSubtitle = (next: MingliFocusedSubtitle | null) => {
    const key = next ? `${next.chapterId}:${next.cueIndex}` : null;
    if (key === activeSubtitleKeyRef.current) return;
    activeSubtitleKeyRef.current = key;
    setActiveSubtitle(next);
  };
  const clockAtAudio = (
    audio: HTMLAudioElement,
    segment: PreparedFocusedSpeechSegment,
    phase: MingliNarrationVisualClock["phase"],
    completed = false,
  ): MingliNarrationVisualClock => {
    const localTimeMs = completed
      ? segment.asset.durationMs
      : Math.max(
          0,
          Math.min(segment.asset.durationMs, Math.round(audio.currentTime * 1000)),
        );
    const subtitle = focusedSubtitle(
      segment.asset,
      segment.chapter.chapterId,
      localTimeMs,
      stage,
    );
    publishSubtitle(subtitle);
    const cueDurationMs = Math.max(1, subtitle.endMs - subtitle.startMs);
    const progress = Math.max(
      0,
      Math.min(1, (localTimeMs - subtitle.startMs) / cueDurationMs),
    );
    return {
      phase,
      currentTimeMs: completedTimeMsRef.current + localTimeMs,
      activeCueId: cueIdForAction(segment.chapter.semanticAction),
      cueProgress: progress,
      semanticAction: segment.chapter.semanticAction,
      activeColumnRefs: subtitle.activeColumnRefs,
    };
  };
  const startSampling = (
    audio: HTMLAudioElement,
    segment: PreparedFocusedSpeechSegment,
    nonce: number,
  ) => {
    stopSampling();
    const sample = () => {
      if (
        nonce !== playbackNonceRef.current
        || audioRef.current !== audio
        || audio.paused
        || audio.ended
      ) return;
      publishClock(clockAtAudio(audio, segment, "PLAYING"));
      frameRef.current = window.requestAnimationFrame(sample);
    };
    sample();
  };

  const speakWithBrowser = (text: string, chapter: MingliLayerNarrationChapter | null) => {
    stopSampling();
    publishSubtitle(null);
    if (!("speechSynthesis" in window)) {
      setSpeechState("IDLE");
      setSpeechNote("声音暂时不可用，断语仍可正常阅读。");
      publishClock(initialClock());
      return;
    }
    const fallbackNonce = fallbackNonceRef.current + 1;
    fallbackNonceRef.current = fallbackNonce;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "zh-CN";
    utterance.rate = 0.92;
    utterance.pitch = 1.03;
    utterance.onstart = () => {
      if (fallbackNonce === fallbackNonceRef.current) setSpeechState("FALLBACK");
    };
    utterance.onend = () => {
      if (fallbackNonce !== fallbackNonceRef.current) return;
      setSpeechState("IDLE");
      publishClock(initialClock());
    };
    utterance.onerror = () => {
      if (fallbackNonce !== fallbackNonceRef.current) return;
      setSpeechState("IDLE");
      setSpeechNote("声音暂时不可用，断语仍可正常阅读。");
      publishClock(initialClock());
    };
    setActiveChapterId(chapter?.chapterId ?? firstChapter?.chapterId ?? null);
    setSpeechNote("专属声音暂未接通，已改用设备中文语音；粒子保持环境动画。");
    publishClock({
      phase: "READY",
      currentTimeMs: 0,
      activeCueId: chapter ? cueIdForAction(chapter.semanticAction) : null,
      cueProgress: 0,
      semanticAction: chapter?.semanticAction ?? "PILLARS_PRESENT",
      activeColumnRefs: [],
    });
    window.speechSynthesis.speak(utterance);
  };

  const playSegment = async (
    prepared: PreparedFocusedSpeech,
    index: number,
    nonce: number,
  ): Promise<void> => {
    if (nonce !== playbackNonceRef.current) return;
    if (index >= prepared.segments.length) {
      audioRef.current = null;
      setSpeechState("ENDED");
      return;
    }
    const segment = prepared.segments[index];
    const audio = new Audio(segment.url);
    audioRef.current = audio;
    setActiveChapterId(segment.chapter.chapterId);
    const openingSubtitle = focusedSubtitle(
      segment.asset,
      segment.chapter.chapterId,
      0,
      stage,
    );
    publishSubtitle(openingSubtitle);
    publishClock({
      phase: "READY",
      currentTimeMs: completedTimeMsRef.current,
      activeCueId: cueIdForAction(segment.chapter.semanticAction),
      cueProgress: 0,
      semanticAction: segment.chapter.semanticAction,
      activeColumnRefs: openingSubtitle.activeColumnRefs,
    });
    audio.onplaying = () => {
      if (nonce !== playbackNonceRef.current) return;
      setSpeechState("PLAYING");
      setSpeechNote(null);
      startSampling(audio, segment, nonce);
    };
    audio.onpause = () => {
      if (nonce !== playbackNonceRef.current || audio.ended) return;
      stopSampling();
      setSpeechState("PAUSED");
      publishClock(clockAtAudio(audio, segment, "PAUSED"));
    };
    const holdForBuffer = () => {
      if (nonce !== playbackNonceRef.current || audio.paused || audio.ended) return;
      stopSampling();
      setSpeechState("BUFFERING");
      setSpeechNote("声音正在等待，粒子停在同一讲述位置。");
      publishClock(clockAtAudio(audio, segment, "BUFFERING"));
    };
    audio.onwaiting = holdForBuffer;
    audio.onstalled = holdForBuffer;
    audio.onended = () => {
      if (nonce !== playbackNonceRef.current) return;
      stopSampling();
      const completedClock = clockAtAudio(audio, segment, "PLAYING", true);
      publishClock(completedClock);
      completedTimeMsRef.current = completedClock.currentTimeMs;
      releaseAudio(audio);
      audioRef.current = null;
      if (index + 1 < prepared.segments.length) {
        void playSegment(prepared, index + 1, nonce);
      } else {
        setSpeechState("ENDED");
        publishClock({ ...completedClock, phase: "ENDED" });
      }
    };
    audio.onerror = () => {
      if (nonce !== playbackNonceRef.current) return;
      releaseAudio(audio);
      audioRef.current = null;
      const remaining = prepared.segments
        .slice(index)
        .map((item) => item.chapter.text)
        .join("\n");
      speakWithBrowser(remaining, segment.chapter);
    };
    try {
      await audio.play();
    } catch {
      if (nonce === playbackNonceRef.current) audio.onerror?.(new Event("error"));
    }
  };

  const prepareAndPlay = async () => {
    if (
      segments.length === 0
      || segments.length !== projection.chapters.length
    ) {
      speakWithBrowser(
        projection.chapters.map((chapter) => chapter.text).join("\n"),
        firstChapter,
      );
      return;
    }
    const nonce = playbackNonceRef.current + 1;
    playbackNonceRef.current = nonce;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setSpeechState("PREPARING");
    setSpeechNote("阿布正在准备声音，断语不用等。");
    publishClock({ ...initialClock(), phase: "PREPARING" });
    try {
      const assets = await Promise.all(
        segments.map(({ record }) => loadFocusedPassSpeech(stage, record, controller.signal)),
      );
      if (controller.signal.aborted || nonce !== playbackNonceRef.current) return;
      preparedRef.current?.segments.forEach(({ url }) => URL.revokeObjectURL(url));
      const prepared = {
        segments: segments.map((segment, index) => ({
          ...segment,
          asset: assets[index],
          url: URL.createObjectURL(assets[index].blob),
        })),
      };
      preparedRef.current = prepared;
      completedTimeMsRef.current = 0;
      setSpeechNote(null);
      await playSegment(prepared, 0, nonce);
    } catch {
      if (!controller.signal.aborted && nonce === playbackNonceRef.current) {
        speakWithBrowser(
          projection.chapters.map((chapter) => chapter.text).join("\n"),
          firstChapter,
        );
      }
    }
  };

  const toggleSpeech = async () => {
    const audio = audioRef.current;
    if (audio) {
      if (audio.paused) {
        try {
          await audio.play();
        } catch {
          audio.onerror?.(new Event("error"));
        }
      } else {
        audio.pause();
      }
      return;
    }
    if (speechState === "FALLBACK") {
      fallbackNonceRef.current += 1;
      window.speechSynthesis.cancel();
      setSpeechState("IDLE");
      publishClock(initialClock());
      return;
    }
    const prepared = preparedRef.current;
    if (prepared) {
      const nonce = playbackNonceRef.current + 1;
      playbackNonceRef.current = nonce;
      completedTimeMsRef.current = 0;
      await playSegment(prepared, 0, nonce);
      return;
    }
    await prepareAndPlay();
  };

  useEffect(() => {
    playbackNonceRef.current += 1;
    fallbackNonceRef.current += 1;
    controllerRef.current?.abort();
    stopSampling();
    if (audioRef.current) releaseAudio(audioRef.current);
    audioRef.current = null;
    preparedRef.current?.segments.forEach(({ url }) => URL.revokeObjectURL(url));
    preparedRef.current = null;
    completedTimeMsRef.current = 0;
    window.speechSynthesis?.cancel();
    setSpeechState("IDLE");
    setSpeechNote(null);
    activeSubtitleKeyRef.current = null;
    setActiveSubtitle(null);
    setActiveChapterId(firstChapter?.chapterId ?? null);
    const resetClock = initialClock();
    setVisualClock(resetClock);
    onClock(resetClock);
    return () => {
      playbackNonceRef.current += 1;
      fallbackNonceRef.current += 1;
      controllerRef.current?.abort();
      stopSampling();
      if (audioRef.current) releaseAudio(audioRef.current);
      audioRef.current = null;
      preparedRef.current?.segments.forEach(({ url }) => URL.revokeObjectURL(url));
      preparedRef.current = null;
      window.speechSynthesis?.cancel();
    };
  }, [projection.layer, projection.sourceHash, projection.sourceRef, stage.projection_hash]);

  return {
    activeChapterId,
    activeSubtitle,
    speechNote,
    speechState,
    toggleSpeech,
    visualClock,
  };
}
