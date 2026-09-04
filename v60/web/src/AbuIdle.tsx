import { useEffect, useState } from "react";

import type { RuntimeMediaCue } from "./publicRuntimeTypes";

export function useReducedMotion() {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(query.matches);
    update();
    query.addEventListener("change", update);
    return () => query.removeEventListener("change", update);
  }, []);

  return reduced;
}

export function AbuIdle({
  className,
  cue,
  label,
}: {
  className?: string;
  cue: RuntimeMediaCue;
  label: string;
}) {
  const reducedMotion = useReducedMotion();
  const video = cue.deliveries.VP9_ALPHA_WEBM;
  const poster = cue.deliveries.REDUCED_MOTION_POSTER;

  if (reducedMotion) {
    return (
      <img
        className={className}
        data-media-cue={cue.cue_ref}
        data-asset-ref={poster.asset_ref}
        src={poster.url}
        alt={label}
      />
    );
  }

  return (
    <video
      className={className}
      data-media-cue={cue.cue_ref}
      data-asset-ref={video.asset_ref}
      aria-label={label}
      role="img"
      autoPlay
      loop
      muted
      playsInline
      preload="metadata"
    >
      <source src={video.url} type={video.media_type} />
    </video>
  );
}
