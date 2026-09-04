import type { CSSProperties } from "react";

import type { MingliSceneSurface } from "./mingliSceneDirector";

export function buildMingliSceneHostStyle({
  labStageUrl,
  rehearsalArtUrl,
  rehearsalVisible,
  surface,
}: {
  labStageUrl: string;
  rehearsalArtUrl: string;
  rehearsalVisible: boolean;
  surface: MingliSceneSurface;
}): CSSProperties {
  return {
    ...(surface === "LAB"
      ? { "--mingli-lab-stage-art": `url("${labStageUrl}")` }
      : {}),
    ...(rehearsalVisible
      ? { "--mingli-rehearsal-art": `url("${rehearsalArtUrl}")` }
      : {}),
  } as CSSProperties;
}
