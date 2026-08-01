import { useEffect, type RefObject } from "react";

import type { MingliNarrationReadyResponse } from "../mingliStageTypes";

export function MingliAudioPlayer({
  audioRef,
  events,
  ready,
}: {
  audioRef: RefObject<HTMLAudioElement | null>;
  events: {
    onCanPlay: () => void;
    onEnded: () => void;
    onError: (audio: HTMLAudioElement) => void;
    onPause: (audio: HTMLAudioElement) => void;
    onPlaying: () => void;
    onStalled: (audio: HTMLAudioElement) => void;
    onWaiting: (audio: HTMLAudioElement) => void;
  };
  ready: MingliNarrationReadyResponse | null;
}) {
  useEffect(() => {
    const audio = audioRef.current;
    return () => {
      if (!audio) return;
      audio.pause();
      audio.removeAttribute("src");
      audio.load();
    };
  }, [audioRef, ready?.asset.narration_ref]);

  if (!ready) return null;
  return (
    <audio
      key={ready.asset.narration_ref}
      preload="auto"
      ref={audioRef}
      src={ready.audio_url}
      onCanPlay={events.onCanPlay}
      onEnded={events.onEnded}
      onError={(event) => events.onError(event.currentTarget)}
      onPause={(event) => events.onPause(event.currentTarget)}
      onPlaying={events.onPlaying}
      onStalled={(event) => events.onStalled(event.currentTarget)}
      onWaiting={(event) => events.onWaiting(event.currentTarget)}
    />
  );
}
