import { useEffect, useState } from "react";

import type { RuntimeMediaCue } from "./api";
import { useReducedMotion } from "./AbuIdle";

type CompanionMotion = "IDLE" | "GUIDE_LEFT";

function cueStorageKey(cueKey: string) {
  return `abu-v60:presentation-cue:guide-left:${cueKey}`;
}

function wasGuideShown(cueKey: string): boolean {
  try {
    return sessionStorage.getItem(cueStorageKey(cueKey)) === "shown";
  } catch {
    return false;
  }
}

function rememberGuide(cueKey: string) {
  try {
    sessionStorage.setItem(cueStorageKey(cueKey), "shown");
  } catch {
    // Presentation memory is optional and never owns encounter state.
  }
}

export function AbuCompanionMotion({
  className,
  cueKey,
  guideLeft,
  guideLeftCue,
  idleCue,
  label,
}: {
  className?: string;
  cueKey: string;
  guideLeft: boolean;
  guideLeftCue: RuntimeMediaCue;
  idleCue: RuntimeMediaCue;
  label: string;
}) {
  const reducedMotion = useReducedMotion();
  const [motion, setMotion] = useState<CompanionMotion>("IDLE");
  const activeCue = motion === "GUIDE_LEFT" ? guideLeftCue : idleCue;
  const activeVideo = activeCue.deliveries.VP9_ALPHA_WEBM;
  const activePoster = activeCue.deliveries.REDUCED_MOTION_POSTER;

  useEffect(() => {
    if (!guideLeft || wasGuideShown(cueKey)) {
      setMotion("IDLE");
      return;
    }
    rememberGuide(cueKey);
    setMotion("GUIDE_LEFT");
  }, [cueKey, guideLeft]);

  if (reducedMotion) {
    return (
      <img
        className={className}
        data-abu-motion={motion}
        data-media-cue={activeCue.cue_ref}
        data-asset-ref={activePoster.asset_ref}
        src={activePoster.url}
        alt={label}
      />
    );
  }

  if (motion === "GUIDE_LEFT") {
    return (
      <video
        className={className}
        data-abu-motion="GUIDE_LEFT"
        data-media-cue={guideLeftCue.cue_ref}
        data-asset-ref={activeVideo.asset_ref}
        aria-label={label}
        role="img"
        autoPlay
        muted
        playsInline
        preload="auto"
        onEnded={() => setMotion("IDLE")}
      >
        <source src={activeVideo.url} type={activeVideo.media_type} />
      </video>
    );
  }

  return (
    <video
      className={className}
      data-abu-motion="IDLE"
      data-media-cue={idleCue.cue_ref}
      data-asset-ref={activeVideo.asset_ref}
      aria-label={label}
      role="img"
      autoPlay
      loop
      muted
      playsInline
      preload="metadata"
    >
      <source src={activeVideo.url} type={activeVideo.media_type} />
    </video>
  );
}
