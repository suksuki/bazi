import { useCallback, useEffect, useState } from "react";
import type { RuntimeMediaManifest } from "../api";
import type { MingliSceneSurface } from "../mingliSceneDirector";
import {
  readMingliStageRoute,
  writeMingliStageRoute,
} from "../mingliStageNavigation";
import {
  readMingliSyntheticLabRoute,
  type MingliSyntheticLabRoute,
  writeMingliSyntheticLabRoute,
} from "../mingliSyntheticLabNavigation";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { MingliSceneHost } from "./MingliSceneHost";
import { MingliResearchOverview } from "./MingliResearchOverview";
import { MingliSyntheticCatalogScene } from "./MingliSyntheticCatalogScene";
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

  useEffect(() => {
    if (route.mode === "overview" || route.mode === "catalog") {
      onContextChange({ subjectId: "current", status: "LOADING", projection: null });
    }
  }, [onContextChange, route.mode]);

  const enterCurrentRoom = (mode: "current" | "narration") => {
    const stageRoute = readMingliStageRoute();
    writeMingliStageRoute({
      ...stageRoute,
      mode: "NATAL_DAYUN_YEAR_6",
      year: null,
    }, "replace", "lab");
    navigate({
      mode,
      suiteRunRef: null,
      experimentRef: null,
      runRef: null,
      variant: "A",
    });
  };

  const overviewRoute: MingliSyntheticLabRoute = {
    mode: "overview",
    suiteRunRef: null,
    experimentRef: null,
    runRef: null,
    variant: "A",
  };

  if (route.mode === "overview") {
    return (
      <MingliResearchOverview
        media={media}
        onExit={onExit}
        onOpenNarration={() => enterCurrentRoom("narration")}
        onOpenSixPillar={() => enterCurrentRoom("current")}
        onOpenSynthesis={() => navigate({ ...overviewRoute, mode: "catalog" })}
      />
    );
  }

  if (route.mode === "catalog") {
    return (
      <MingliSyntheticCatalogScene
        media={media}
        onBack={() => navigate(overviewRoute)}
        onOpenExperiment={navigate}
      />
    );
  }

  if (route.mode === "synthetic") {
    return (
      <MingliSyntheticExperimentScene
        onBackToCurrent={() =>
          navigate({
            mode: "current",
            suiteRunRef: null,
            experimentRef: null,
            runRef: null,
            variant: "A",
          })
        }
        onContextChange={onContextChange}
        onExit={() => navigate(overviewRoute)}
        onOpenReading={() => onSurfaceChange("READING")}
        onRouteChange={navigate}
        route={route}
      />
    );
  }

  return (
    <MingliSceneHost
      autoOpenNarration={route.mode === "narration"}
      exitLabel="回到阿布 LAB"
      homeLineageKey={homeLineageKey}
      media={media}
      onContextChange={onContextChange}
      onExit={() => navigate(overviewRoute)}
      onNarrationStateChange={(open) => navigate({
        ...overviewRoute,
        mode: open ? "narration" : "current",
      }, "replace")}
      onOpenSyntheticLab={() =>
        navigate({ ...overviewRoute, mode: "catalog" })
      }
      onSurfaceChange={onSurfaceChange}
      surface="LAB"
    />
  );
}
