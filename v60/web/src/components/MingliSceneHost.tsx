import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { RuntimeMediaManifest } from "../api";
import {
  generateMingliAgentReading,
  loadMingliReadingSummary,
  loadMingliStage,
  loadMingliStageSubjects,
} from "../mingliStageApi";
import {
  readMingliStageRoute,
  type MingliReadingLayer,
  type MingliStageRoute,
  writeMingliStageRoute,
} from "../mingliStageNavigation";
import {
  directMingliScene,
  INITIAL_MINGLI_CLOCK,
  type MingliSceneSurface,
} from "../mingliSceneDirector";
import type {
  MingliNarrationVisualClock,
  MingliReadingSummaryProjection,
  MingliStageProjection,
  MingliStageSubject,
  MingliStageSubjectId,
  MingliStageViewContext,
} from "../mingliStageTypes";
import { MingliLabSceneInspector } from "./MingliLabSceneInspector";
import { MingliNarrationDirector } from "./MingliNarrationDirector";
import {
  MingliReadingJourney,
  summaryMatchesStage,
} from "./MingliReadingJourney";
import { MingliScenePlayer } from "./MingliScenePlayer";

export function MingliSceneHost({
  homeLineageKey,
  media,
  onContextChange,
  onExit,
  onSurfaceChange,
  surface,
}: {
  homeLineageKey: string;
  media: RuntimeMediaManifest;
  onContextChange: (context: MingliStageViewContext) => void;
  onExit: () => void;
  onSurfaceChange: (surface: MingliSceneSurface) => void;
  surface: MingliSceneSurface;
}) {
  const [route, setRoute] = useState<MingliStageRoute>(readMingliStageRoute);
  const [subjects, setSubjects] = useState<MingliStageSubject[]>([]);
  const [stage, setStage] = useState<MingliStageProjection | null>(null);
  const stageRef = useRef<MingliStageProjection | null>(null);
  const generationRequestRef = useRef(0);
  const generationControllerRef = useRef<AbortController | null>(null);
  const [readingSummary, setReadingSummary] =
    useState<MingliReadingSummaryProjection | null>(null);
  const [agentGenerating, setAgentGenerating] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);
  const [clock, setClock] = useState<MingliNarrationVisualClock>(
    INITIAL_MINGLI_CLOCK,
  );
  const [selectedRelationRef, setSelectedRelationRef] = useState<string | null>(null);
  const [narrationOpen, setNarrationOpen] = useState(false);
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

  useEffect(() => () => {
    generationRequestRef.current += 1;
    generationControllerRef.current?.abort();
  }, []);

  useEffect(() => {
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
  }, [subjectsRetry]);

  useEffect(() => {
    const restore = () => {
      const restored = readMingliStageRoute();
      onContextChange({
        subjectId: restored.subjectId,
        status: "LOADING",
        projection: null,
      });
      setStage(null);
      stageRef.current = null;
      generationRequestRef.current += 1;
      generationControllerRef.current?.abort();
      setReadingSummary(null);
      setAgentGenerating(false);
      setAgentError(null);
      setNarrationOpen(false);
      setRoute(restored);
    };
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [onContextChange]);

  useEffect(() => {
    const controller = new AbortController();
    const requestedYear =
      route.mode === "NATAL_DAYUN_YEAR_6" ? route.year : null;
    generationRequestRef.current += 1;
    generationControllerRef.current?.abort();
    generationControllerRef.current = null;
    stageRef.current = null;
    setStageLoading(true);
    setStageError(null);
    setReadingSummary(null);
    setAgentGenerating(false);
    setAgentError(null);
    setNarrationOpen(false);
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
        stageRef.current = projection;
        setStage(projection);
        setReadingSummary(summary);
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
          stageRef.current = null;
          setReadingSummary(null);
          setNarrationOpen(false);
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
    stageRetry,
  ]);

  const navigate = (next: MingliStageRoute) => {
    generationRequestRef.current += 1;
    generationControllerRef.current?.abort();
    generationControllerRef.current = null;
    stageRef.current = null;
    onContextChange({
      subjectId: next.subjectId,
      status: "LOADING",
      projection: null,
    });
    setStage(null);
    setReadingSummary(null);
    setNarrationOpen(false);
    setRoute(next);
    writeMingliStageRoute(
      next,
      "push",
      surface === "LAB" ? "lab" : "mingli",
    );
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
  const generateAgentReading = () => {
    if (stage === null || agentGenerating) return;
    const requestedStage = stage;
    const requestId = generationRequestRef.current + 1;
    generationRequestRef.current = requestId;
    generationControllerRef.current?.abort();
    const controller = new AbortController();
    generationControllerRef.current = controller;
    setAgentGenerating(true);
    setAgentError(null);
    void generateMingliAgentReading(requestedStage, controller.signal)
      .then(() => loadMingliReadingSummary(requestedStage, controller.signal))
      .then((summary) => {
        const activeStage = stageRef.current;
        if (
          !controller.signal.aborted
          && generationRequestRef.current === requestId
          && activeStage !== null
          && summaryMatchesStage(summary, activeStage)
        ) {
          setReadingSummary(summary);
        }
      })
      .catch((caught) => {
        if (!controller.signal.aborted && generationRequestRef.current === requestId) {
          setAgentError(caught instanceof Error ? caught.message : String(caught));
        }
      })
      .finally(() => {
        if (generationRequestRef.current === requestId) {
          setAgentGenerating(false);
          generationControllerRef.current = null;
        }
      });
  };
  const currentSummary = stage !== null && summaryMatchesStage(readingSummary, stage)
    ? readingSummary
    : null;
  const currentClaimGraph = currentSummary?.claim_graph ?? null;
  const currentWholeClaim = currentClaimGraph?.claims.find(
    (item) => item.semantic_key === "WHOLE_CHART",
  );
  const wholeChartNeedsReconciliation =
    currentWholeClaim?.status === "NEEDS_RECONCILIATION";
  const frame = useMemo(
    () =>
      stage
        ? directMingliScene({
            clock,
            narrationOpen,
            selectedRelationRef,
            stage,
            surface,
          })
        : null,
    [clock, narrationOpen, selectedRelationRef, stage, surface],
  );

  return (
    <div
      className="mingli-scene-host"
      data-narration-open={narrationOpen}
      data-scene-surface={surface}
      data-stage-loading={stageLoading}
    >
      <header className="mingli-scene-host-header">
        <button className="mingli-scene-exit" onClick={onExit} type="button">
          <span aria-hidden="true">←</span>
          回到生命树
        </button>
        <div className="mingli-scene-title">
          <p>档案叶 · 同一命理舞台</p>
          <h1>{stage ? `${stage.display_name}的命理枝` : "命理枝正在生长"}</h1>
          <span>{stage?.identity_badge ?? "读取档案身份"}</span>
        </div>
        <div className="mingli-scene-surfaces" role="group" aria-label="命理阅读与 Lab">
          <button
            aria-pressed={surface === "READING"}
            onClick={() => onSurfaceChange("READING")}
            type="button"
          >
            命理阅读
          </button>
          <button
            aria-pressed={surface === "LAB"}
            onClick={() => onSurfaceChange("LAB")}
            type="button"
          >
            Lab 观察
          </button>
        </div>
      </header>

      <div className="mingli-scene-toolbar" aria-label="命理舞台坐标选择">
        <label>
          <span>档案</span>
          <select
            aria-label="选择命理档案"
            disabled={subjectsLoading || Boolean(subjectsError) || !subjects.length}
            onChange={(event) =>
              navigate({
                ...route,
                subjectId: event.target.value as MingliStageSubjectId,
                year: null,
              })
            }
            value={route.subjectId}
          >
            {!subjects.length && (
              <option value={route.subjectId}>
                {subjectsLoading ? "正在读取档案…" : "档案列表暂不可用"}
              </option>
            )}
            {subjects.map((subject) => (
              <option key={subject.subject_id} value={subject.subject_id}>
                {route.subjectId !== "current" && subject.subject_id === "current"
                  ? "我的档案 · 私密真实档案"
                  : `${subject.display_name} · ${subject.identity_badge}`}
              </option>
            ))}
          </select>
        </label>
        {subjectsError && (
          <button
            className="mingli-subject-retry"
            onClick={() => setSubjectsRetry((value) => value + 1)}
            type="button"
          >
            重试档案列表
          </button>
        )}
        <div className="mingli-stage-mode" role="group" aria-label="选择四柱或六柱">
          <button
            aria-pressed={route.mode === "NATAL_4"}
            onClick={() => navigate({ ...route, mode: "NATAL_4", year: null })}
            type="button"
          >
            本命四柱
          </button>
          <button
            aria-pressed={route.mode === "NATAL_DAYUN_YEAR_6"}
            onClick={() =>
              navigate({ ...route, mode: "NATAL_DAYUN_YEAR_6", year: null })
            }
            type="button"
          >
            展开时间层
          </button>
        </div>
        {stage?.stage_mode === "NATAL_DAYUN_YEAR_6" && (
          <label>
            <span>所选流年</span>
            <select
              aria-label="选择流年"
              onChange={(event) =>
                navigate({ ...route, year: Number(event.target.value) })
              }
              value={stage.selected_year ?? ""}
            >
              {stage.available_years.map((year) => (
                <option key={year} value={year}>
                  {year} 年
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

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
          data-overlay={narrationOpen ? "NARRATION" : surface}
        >
          <MingliScenePlayer fallbackClock={clock} frame={frame} stage={stage} />
          {narrationOpen ? (
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
                setClock(INITIAL_MINGLI_CLOCK);
              }}
              returnLabel={surface === "LAB" ? "回到 Lab 观察" : "回到命理阅读"}
              stage={stage}
            />
          ) : surface === "LAB" ? (
            <MingliLabSceneInspector
              agentReading={currentSummary?.agent_reading ?? null}
              claimGraph={currentClaimGraph}
              onAskGuide={() => setNarrationOpen(true)}
              onSelectRelation={setSelectedRelationRef}
              selectedRelationRef={selectedRelationRef}
              stage={stage}
            />
          ) : (
            <MingliReadingJourney
              agentError={agentError}
              agentGenerating={agentGenerating}
              layer={route.layer}
              onAskGuide={() => setNarrationOpen(true)}
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

      {stage && surface === "LAB" && (
        <footer className="mingli-stage-boundary">
          <span>
            {currentClaimGraph
              ? "Lab 正在展开命理枝上的同一次整盘初断；这里不会另起一套结论。"
              : "整盘初断生成后，Lab 会在这里展开主解释、竞争解释和证据引用。"}
            {stage.stage_mode === "NATAL_DAYUN_YEAR_6" &&
              ` · 当前大运区间 ${stage.current_dayun_start_date}—${stage.current_dayun_end_date}，交运当日不声明“当前”`}
          </span>
          <small>单条判断可以继续校准；局部争议不会让整份命盘停止判断。</small>
        </footer>
      )}
      {stage && surface === "READING" && (
        <footer className="mingli-stage-boundary">
          <span>
            {currentClaimGraph
              ? wholeChartNeedsReconciliation
                ? "这份整盘初断已经保存；主解释仍在专业校准，不是定论。"
                : "这份整盘初断已经保存；刷新或切回档案后仍会回到同一结果。"
              : "四柱已经排定，等待阿布完成一次整盘研判。"}
          </span>
          <small>阿布会把原局、结构竞争与岁运放在同一条判断链里。</small>
        </footer>
      )}
    </div>
  );
}
