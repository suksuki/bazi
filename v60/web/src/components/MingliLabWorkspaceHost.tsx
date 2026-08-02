import { useCallback, useEffect, useState } from "react";
import type { RuntimeMediaManifest } from "../api";
import type { MingliSceneSurface } from "../mingliSceneDirector";
import {
  readMingliSyntheticLabRoute,
  type MingliSyntheticLabRoute,
  writeMingliSyntheticLabRoute,
} from "../mingliSyntheticLabNavigation";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { MingliSceneHost } from "./MingliSceneHost";
import { MingliSyntheticExperimentScene } from "./MingliSyntheticExperimentScene";

export function MingliLabWorkspaceHost({
  homeLineageKey,
  media,
  onContextChange,
  onExit,
  onSurfaceChange,
}: {
  homeLineageKey: string;
  media: RuntimeMediaManifest;
  onContextChange: (context: MingliStageViewContext) => void;
  onExit: () => void;
  onSurfaceChange: (surface: MingliSceneSurface) => void;
}) {
  const [route, setRoute] = useState<MingliSyntheticLabRoute>(
    readMingliSyntheticLabRoute,
  );

  useEffect(() => {
    const restore = () => setRoute(readMingliSyntheticLabRoute());
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, []);

  const navigate = useCallback((
    next: MingliSyntheticLabRoute,
    mode: "push" | "replace" = "push",
  ) => {
    setRoute(next);
    writeMingliSyntheticLabRoute(next, mode);
  }, []);

  if (route.mode === "synthetic") {
    return (
      <MingliSyntheticExperimentScene
        onBackToCurrent={() =>
          navigate({
            mode: "current",
            experimentRef: null,
            runRef: null,
            variant: "A",
          })
        }
        onContextChange={onContextChange}
        onExit={onExit}
        onOpenReading={() => onSurfaceChange("READING")}
        onRouteChange={navigate}
        route={route}
      />
    );
  }

  return (
    <MingliSceneHost
      homeLineageKey={homeLineageKey}
      media={media}
      onContextChange={onContextChange}
      onExit={onExit}
      onOpenSyntheticLab={() =>
        navigate({
          mode: "synthetic",
          experimentRef: null,
          runRef: null,
          variant: "A",
        })
      }
      onSurfaceChange={onSurfaceChange}
      surface="LAB"
    />
  );
}
