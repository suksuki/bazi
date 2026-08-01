import { useEffect, useRef, useState } from "react";

import { useReducedMotion } from "../AbuIdle";
import type { RuntimeAssetDelivery } from "../api";

type CharacterMediaMode = "poster" | "webm" | "webp";

function needsAppleAlphaFallback() {
  const userAgent = window.navigator.userAgent;
  const isAppleTouchDevice =
    /iPad|iPhone|iPod/.test(userAgent) ||
    (/Macintosh/.test(userAgent) && window.navigator.maxTouchPoints > 1);
  const isSafari =
    /Safari/.test(userAgent) &&
    !/Chrome|Chromium|CriOS|Edg|OPR|Firefox|FxiOS/.test(userAgent);
  return isAppleTouchDevice || isSafari;
}

export function TransparentCharacterMedia({
  active,
  alt,
  className,
  cueRef,
  poster,
  video,
  webp,
}: {
  active: boolean;
  alt: string;
  className: string;
  cueRef: string;
  poster: RuntimeAssetDelivery;
  video: RuntimeAssetDelivery;
  webp: RuntimeAssetDelivery;
}) {
  const reducedMotion = useReducedMotion();
  const [mode, setMode] = useState<CharacterMediaMode>("poster");
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (reducedMotion) {
      setMode("poster");
      return;
    }
    const frame = window.requestAnimationFrame(() => {
      setMode(needsAppleAlphaFallback() ? "webp" : "webm");
    });
    return () => window.cancelAnimationFrame(frame);
  }, [reducedMotion, video.url, webp.url]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (!active) {
      video.pause();
      return;
    }
    void video.play().catch(() => undefined);
  }, [active, mode]);

  if (reducedMotion || mode === "poster") {
    return (
      <img
        alt={alt}
        className={className}
        data-asset-ref={poster.asset_ref}
        data-media-cue={cueRef}
        src={poster.url}
      />
    );
  }
  if (mode === "webp") {
    return (
      <img
        className={className}
        data-asset-ref={active ? webp.asset_ref : poster.asset_ref}
        data-media-cue={cueRef}
        src={active ? webp.url : poster.url}
        alt={alt}
        onError={() => setMode("poster")}
      />
    );
  }
  return (
    <video
      aria-label={alt}
      className={className}
      data-asset-ref={video.asset_ref}
      data-media-cue={cueRef}
      loop
      muted
      playsInline
      poster={poster.url}
      preload="metadata"
      ref={videoRef}
      onError={() => setMode("webp")}
    >
      <source src={video.url} type={video.media_type} />
    </video>
  );
}
