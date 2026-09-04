import { useCallback, useEffect, useState } from "react";
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
import type { RuntimeMediaManifest } from "../publicRuntimeTypes";
import { MingliSceneHost } from "./MingliSceneHost";
import { MingliResearchOverview } from "./MingliResearchOverview";

const LAB_OVERVIEW_ROUTE: MingliSyntheticLabRoute = {
  mode: "overview",
  suiteRunRef: null,
  experimentRef: null,
  runRef: null,
  variant: "A",
};

function isDemoLabMode(
  mode: MingliSyntheticLabRoute["mode"],
): mode is "overview" | "current" | "narration" {
  return mode === "overview" || mode === "current" || mode === "narration";
}

function readDemoLabRoute(): MingliSyntheticLabRoute {
  const route = readMingliSyntheticLabRoute();
  return isDemoLabMode(route.mode) ? route : LAB_OVERVIEW_ROUTE;
}

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
    readDemoLabRoute,
  );

  useEffect(() => {
    const restore = () => {
      const requested = readMingliSyntheticLabRoute();
      if (!isDemoLabMode(requested.mode)) {
        writeMingliSyntheticLabRoute(LAB_OVERVIEW_ROUTE, "replace");
      }
      setRoute(isDemoLabMode(requested.mode) ? requested : LAB_OVERVIEW_ROUTE);
    };
    restore();
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
    if (route.mode === "overview") {
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

  if (route.mode === "overview") {
    return (
      <MingliResearchOverview
        media={media}
        onExit={onExit}
        onOpenNarration={() => enterCurrentRoom("narration")}
        onOpenSixPillar={() => enterCurrentRoom("current")}
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
      onExit={() => navigate(LAB_OVERVIEW_ROUTE)}
      onNarrationStateChange={(open) => navigate({
        ...LAB_OVERVIEW_ROUTE,
        mode: open ? "narration" : "current",
      }, "replace")}
      onSurfaceChange={onSurfaceChange}
      surface="LAB"
    />
  );
}
