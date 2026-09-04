import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { RuntimeMediaManifest } from "../publicRuntimeTypes";
import {
  loadMingliReadingSummary,
  loadMingliStage,
  loadMingliStageSubjects,
} from "../mingliStageApi";
import {
  readMingliStageEntryMode,
  readMingliStageRoute,
  type MingliReadingLayer,
  type MingliStageRoute,
  writeMingliStageExperience,
  writeMingliStageRoute,
} from "../mingliStageNavigation";
import {
  hasMingliSummaryLayerNarration,
  projectMingliSummaryLayerNarration,
} from "../mingliLayerNarrationProjection";
import {
  directMingliScene,
  INITIAL_MINGLI_CLOCK,
  type MingliSceneSurface,
} from "../mingliSceneDirector";
import { buildMingliSceneHostStyle } from "../mingliSceneVisualStyle";
import type {
  MingliNarrationVisualClock,
  MingliReadingSummaryProjection,
  MingliStageProjection,
  MingliStageSubject,
  MingliStageViewContext,
} from "../mingliStageTypes";
import {
  selectMingliRehearsalSpeechRecords,
  useMingliFocusedPassGeneration,
  usePublicMingliAutoGeneration,
} from "../useMingliFocusedPassGeneration";
import { MingliLabSceneInspector } from "./MingliLabSceneInspector";
import { MingliLayerRehearsal } from "./MingliLayerRehearsal";
import { MingliNarrationDirector } from "./MingliNarrationDirector";
import { MingliReadingJourney, summaryMatchesStage } from "./MingliReadingJourney";
import { MingliSceneBoundary } from "./MingliSceneBoundary";
import { MingliSceneControls } from "./MingliSceneControls";
import { MingliScenePlayer } from "./MingliScenePlayer";
export function MingliSceneHost({
  autoOpenNarration = false,
  exitLabel,
  homeLineageKey,
  media,
  onContextChange,
  onExit,
  onNarrationStateChange,
  onReturnToBranch,
  onSurfaceChange,
  publicMode = false,
  surface,
}: {
  autoOpenNarration?: boolean;
  exitLabel?: string;
  homeLineageKey: string;
  media: RuntimeMediaManifest;
  onContextChange: (context: MingliStageViewContext) => void;
  onExit: () => void;
  onNarrationStateChange?: (open: boolean) => void;
  onReturnToBranch?: () => void;
  onSurfaceChange: (surface: MingliSceneSurface) => void;
  publicMode?: boolean;
  surface: MingliSceneSurface;
}) {
  const [route, setRoute] = useState<MingliStageRoute>(() =>
    readMingliSceneRoute(publicMode),
  );
  const [subjects, setSubjects] = useState<MingliStageSubject[]>([]);
  const [stage, setStage] = useState<MingliStageProjection | null>(null);
  const [readingSummary, setReadingSummary] =
    useState<MingliReadingSummaryProjection | null>(null);
  const {
    agentError,
    agentGenerating,
    generateAgentReading,
    resetAgentGeneration,
  } = useMingliFocusedPassGeneration({
    onSummary: setReadingSummary,
    stage,
  });
  const [clock, setClock] = useState<MingliNarrationVisualClock>(
    INITIAL_MINGLI_CLOCK,
  );
  const [selectedRelationRef, setSelectedRelationRef] = useState<string | null>(null);
  const [narrationOpen, setNarrationOpen] = useState(false);
  const [rehearsalOpen, setRehearsalOpen] = useState(
    () => readMingliStageEntryMode() === "rehearsal",
  );
  const [subjectsLoading, setSubjectsLoading] = useState(true);
  const [subjectsError, setSubjectsError] = useState<string | null>(null);
  const [subjectsRetry, setSubjectsRetry] = useState(0);
  const [stageLoading, setStageLoading] = useState(true);
  const [stageError, setStageError] = useState<string | null>(null);
  const [stageRetry, setStageRetry] = useState(0);
  const currentHomeLineageKey =
    route.subjectId === "current" ? homeLineageKey : "SYNTHETIC";
  const onClock = useCallback((next: MingliNarrationVisualClock) => {
    setClock(next);
  }, []);

  useEffect(() => {
    if (autoOpenNarration) setNarrationOpen(true);
  }, [autoOpenNarration]);

  useEffect(() => {
    if (publicMode) {
      setSubjects([]);
      setSubjectsLoading(false);
      setSubjectsError(null);
      return;
    }
    const controller = new AbortController();
    setSubjects([]);
    setSubjectsLoading(true);
    setSubjectsError(null);
    void loadMingliStageSubjects(controller.signal)
      .then((nextSubjects) => {
        if (!controller.signal.aborted) setSubjects(nextSubjects);
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setSubjectsError(caught instanceof Error ? caught.message : String(caught));
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setSubjectsLoading(false);
      });
    return () => controller.abort();
  }, [publicMode, subjectsRetry]);

  useEffect(() => {
    const restore = () => {
      const restored = readMingliSceneRoute(publicMode);
      onContextChange({
        subjectId: restored.subjectId,
        status: "LOADING",
        projection: null,
      });
      setStage(null);
      resetAgentGeneration();
      setReadingSummary(null);
      setNarrationOpen(autoOpenNarration);
      setRehearsalOpen(readMingliStageEntryMode() === "rehearsal");
      setRoute(restored);
    };
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [autoOpenNarration, onContextChange, publicMode, resetAgentGeneration]);

  useEffect(() => {
    const controller = new AbortController();
    const requestedYear =
      route.mode === "NATAL_DAYUN_YEAR_6" ? route.year : null;
    resetAgentGeneration();
    setStageLoading(true);
    setStageError(null);
    setReadingSummary(null);
    setNarrationOpen(autoOpenNarration);
    setRehearsalOpen(readMingliStageEntryMode() === "rehearsal");
    setClock(INITIAL_MINGLI_CLOCK);
    onContextChange({
      subjectId: route.subjectId,
      status: "LOADING",
      projection: null,
    });
    void loadMingliStage(
      route.subjectId,
      route.mode,
      requestedYear,
      controller.signal,
    )
      .then(async (projection) => ({
        projection,
        summary:
          projection.reading_ref === null
            ? null
            : await loadMingliReadingSummary(projection, controller.signal),
      }))
      .then(({ projection, summary }) => {
        if (controller.signal.aborted) return;
        setStage(projection);
        setReadingSummary(summary);
        const canOpenRehearsal = summary !== null
          && hasMingliSummaryLayerNarration(summary, route.layer);
        setRehearsalOpen(
          readMingliStageEntryMode() === "rehearsal"
          && canOpenRehearsal,
        );
        if (readMingliStageEntryMode() === "rehearsal" && !canOpenRehearsal) {
          writeMingliStageExperience("stage", "observe", "replace");
        }
        setStageLoading(false);
        setSelectedRelationRef((current) =>
          projection.relations.some(
            (relation) => relation.relation_ref === current,
          )
            ? current
            : null,
        );
        onContextChange({
          subjectId: route.subjectId,
          status: "READY",
          projection,
        });
        if (route.mode === "NATAL_DAYUN_YEAR_6" && route.year === null) {
          const restored = { ...route, year: projection.selected_year };
          setRoute(restored);
          const currentView = new URL(window.location.href).searchParams.get("view");
          writeMingliStageRoute(
            restored,
            "replace",
            currentView === "lab" ? "lab" : "mingli",
          );
        }
      })
      .catch((caught) => {
        if (!controller.signal.aborted) {
          setStage(null);
          setReadingSummary(null);
          setNarrationOpen(false);
          setRehearsalOpen(false);
          setStageLoading(false);
          setStageError(caught instanceof Error ? caught.message : String(caught));
          onContextChange({
            subjectId: route.subjectId,
            status: "ERROR",
            projection: null,
          });
        }
      });
    return () => controller.abort();
  }, [
    currentHomeLineageKey,
    onContextChange,
    route.mode,
    route.subjectId,
    route.year,
    resetAgentGeneration,
    stageRetry,
  ]);

  const navigate = (next: MingliStageRoute) => {
    resetAgentGeneration();
    onContextChange({
      subjectId: next.subjectId,
      status: "LOADING",
      projection: null,
    });
    setStage(null);
    setReadingSummary(null);
    setNarrationOpen(autoOpenNarration);
    setRehearsalOpen(false);
    setRoute(next);
    writeMingliStageRoute(
      next,
      "push",
      surface === "LAB" ? "lab" : "mingli",
    );
    writeMingliStageExperience("stage", "observe", "replace");
  };
  const navigateLayer = (layer: MingliReadingLayer) => {
    const next = { ...route, layer };
    setRoute(next);
    writeMingliStageRoute(
      next,
      "push",
      surface === "LAB" ? "lab" : "mingli",
    );
  };
  const currentSummary = stage !== null && summaryMatchesStage(readingSummary, stage)
    ? readingSummary : null;
  usePublicMingliAutoGeneration({
    agentGenerating,
    currentSummary,
    generateAgentReading,
    layer: route.layer,
    publicMode,
    rehearsalOpen,
    stage,
  });
  const currentClaimGraph = currentSummary?.claim_graph ?? null;
  const currentWholeClaim = currentClaimGraph?.claims.find(
    (item) => item.semantic_key === "WHOLE_CHART",
  );
  const wholeChartNeedsReconciliation = currentWholeClaim?.status === "NEEDS_RECONCILIATION";
  useEffect(() => {
    if (
      !rehearsalOpen
      || currentSummary === null
      || hasMingliSummaryLayerNarration(currentSummary, route.layer)
    ) return;
    setRehearsalOpen(false);
    writeMingliStageExperience("stage", "observe", "replace");
  }, [currentSummary, rehearsalOpen, route.layer]);
  const layerNarration = useMemo(
    () => stage !== null && currentSummary !== null
      ? projectMingliSummaryLayerNarration(currentSummary, route.layer)
      : null,
    [currentSummary, route.layer, stage],
  );
  const rehearsalSpeechRecords = useMemo(
    () => selectMingliRehearsalSpeechRecords(currentSummary, layerNarration),
    [currentSummary, layerNarration],
  );
  const rehearsalVisible = rehearsalOpen
    && layerNarration !== null
    && layerNarration.chapters.length > 0;
  const worldLight = new URL(window.location.href).searchParams.get("mingli_light") === "night"
    ? "night"
    : "day";
  const rehearsalPoster = worldLight === "night"
    ? media.assets.mingli_growth_night_poster
    : media.assets.mingli_growth_day_poster;
  const labStagePoster = worldLight === "night"
    ? media.assets.mingli_lab_night_background
    : media.assets.mingli_lab_day_background;
  const rehearsalActorRef = publicMode
    ? "ABU_NARRATOR_V1" as const
    : worldLight === "day"
    ? "DUODUO_NARRATOR_V1" as const
    : "ABU_NARRATOR_V1" as const;
  const hostStyle = buildMingliSceneHostStyle({
    labStageUrl: labStagePoster.url,
    rehearsalArtUrl: rehearsalPoster.url,
    rehearsalVisible,
    surface,
  });
  const frame = useMemo(
    () =>
      stage
        ? directMingliScene({
            clock,
            narrationOpen: narrationOpen || rehearsalVisible,
            selectedRelationRef,
            stage,
            surface,
          })
        : null,
    [clock, narrationOpen, rehearsalVisible, selectedRelationRef, stage, surface],
  );
  const openStageNarration = () => {
    setRehearsalOpen(false);
    writeMingliStageExperience("stage", "observe", "replace");
    setNarrationOpen(true);
    onNarrationStateChange?.(true);
  };
  const closeRehearsal = () => {
    setRehearsalOpen(false);
    setClock(INITIAL_MINGLI_CLOCK);
    writeMingliStageExperience("stage", "observe", "replace");
    if (surface === "READING") onReturnToBranch?.();
  };

  return (
    <div
      className="mingli-scene-host"
      data-narration-open={narrationOpen}
      data-rehearsal-open={rehearsalVisible}
      data-scene-surface={surface}
      data-stage-loading={stageLoading}
      data-world-light={worldLight}
      style={hostStyle}
    >
      <MingliSceneControls
        exitLabel={exitLabel}
        onExit={onExit}
        onNavigate={navigate}
        onRetrySubjects={() => setSubjectsRetry((value) => value + 1)}
        onSurfaceChange={onSurfaceChange}
        publicMode={publicMode}
        route={route}
        stage={stage}
        subjects={subjects}
        subjectsError={subjectsError}
        subjectsLoading={subjectsLoading}
        surface={surface}
      />

      {stageLoading && (
        <div className="mingli-stage-loading" role="status">
          <span aria-hidden="true" />
          {stage ? "正在展开新的时间位置；当前舞台会留在原处……" : "正在从当前档案生长命理枝……"}
        </div>
      )}
      {stageError && (
        <div className="mingli-stage-error" role="alert">
          <p>新的命盘位置暂时没有展开，请重新读取；当前档案不会受到影响。</p>
          <button onClick={() => setStageRetry((value) => value + 1)} type="button">
            重新读取
          </button>
        </div>
      )}

      {stage && frame && (
        <div
          className="mingli-scene-composition"
          data-overlay={rehearsalVisible ? "REHEARSAL" : narrationOpen ? "NARRATION" : surface}
        >
          <MingliScenePlayer
            daylight={rehearsalVisible && worldLight === "day"}
            fallbackClock={clock}
            frame={frame}
            stage={stage}
          />
          {rehearsalVisible && layerNarration ? (
            <MingliLayerRehearsal
              actorCue={rehearsalActorRef === "DUODUO_NARRATOR_V1"
                ? media.cues.dodo_idle
                : media.cues.abu_idle}
              actorRef={rehearsalActorRef}
              onClock={onClock}
              onClose={closeRehearsal}
              projection={layerNarration}
              returnLabel={surface === "READING" ? "回到命理枝" : "回到 Lab 观察"}
              speechRecords={rehearsalSpeechRecords}
              stage={stage}
            />
          ) : narrationOpen ? (
            <MingliNarrationDirector
              actorCue={
                stage.narrator_actor_id === "DUODUO_NARRATOR_V1"
                  ? media.cues.dodo_idle
                  : media.cues.abu_idle
              }
              key={stage.projection_ref}
              onClock={onClock}
              onClose={() => {
                setNarrationOpen(false);
                onNarrationStateChange?.(false);
                setClock(INITIAL_MINGLI_CLOCK);
              }}
              returnLabel={surface === "LAB" ? "回到 Lab 观察" : "回到命理阅读"}
              stage={stage}
            />
          ) : surface === "LAB" ? (
            <MingliLabSceneInspector
              agentReading={currentSummary?.agent_reading ?? null}
              claimGraph={currentClaimGraph}
              onAskGuide={openStageNarration}
              onSelectRelation={setSelectedRelationRef}
              selectedRelationRef={selectedRelationRef}
              stage={stage}
            />
          ) : (
            <MingliReadingJourney
              agentError={agentError}
              agentGenerating={agentGenerating}
              layer={route.layer}
              onAskGuide={openStageNarration}
              onExpandTime={() =>
                navigate({ ...route, mode: "NATAL_DAYUN_YEAR_6", year: null })
              }
              onGenerateAgent={generateAgentReading}
              onLayerChange={navigateLayer}
              stage={stage}
              summary={currentSummary}
            />
          )}
        </div>
      )}
      {stage && (
        <MingliSceneBoundary
          claimGraphReady={currentClaimGraph !== null}
          focusedReadingReady={Boolean(currentSummary?.focused_reading
            || currentSummary?.focused_pass_records.length)}
          stage={stage}
          surface={surface}
          wholeChartNeedsReconciliation={wholeChartNeedsReconciliation}
        />
      )}
    </div>
  );
}

function readMingliSceneRoute(publicMode: boolean): MingliStageRoute {
  const route = readMingliStageRoute();
  if (!publicMode || readMingliStageEntryMode() !== "rehearsal") return route;
  return {
    ...route,
    mode: "NATAL_DAYUN_YEAR_6",
    year: route.mode === "NATAL_DAYUN_YEAR_6" ? route.year : null,
  };
}
