import { useCallback, useEffect, useMemo, useState } from "react";

import type { RuntimeMediaManifest } from "../api";
import { loadMingliStage, loadMingliStageSubjects } from "../mingliStageApi";
import {
  readMingliStageRoute,
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
  MingliStageProjection,
  MingliStageSubject,
  MingliStageSubjectId,
  MingliStageViewContext,
} from "../mingliStageTypes";
import { MingliLabSceneInspector } from "./MingliLabSceneInspector";
import { MingliNarrationDirector } from "./MingliNarrationDirector";
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
      setRoute(restored);
    };
    window.addEventListener("popstate", restore);
    return () => window.removeEventListener("popstate", restore);
  }, [onContextChange]);

  useEffect(() => {
    const controller = new AbortController();
    const requestedYear =
      route.mode === "NATAL_DAYUN_YEAR_6" ? route.year : null;
    setStageLoading(true);
    setStageError(null);
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
      .then((projection) => {
        if (controller.signal.aborted) return;
        setStage(projection);
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
    onContextChange({
      subjectId: next.subjectId,
      status: "LOADING",
      projection: null,
    });
    setRoute(next);
    writeMingliStageRoute(
      next,
      "push",
      surface === "LAB" ? "lab" : "mingli",
    );
  };
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
          {stage ? "正在锁定新的坐标；当前场景保持不拆除……" : "正在从当前 Case 生长命理枝……"}
        </div>
      )}
      {stageError && (
        <div className="mingli-stage-error" role="alert">
          <p>新坐标暂时没有完成接线：{stageError}</p>
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
              onAskGuide={() => setNarrationOpen(true)}
              onSelectRelation={setSelectedRelationRef}
              selectedRelationRef={selectedRelationRef}
              stage={stage}
            />
          ) : (
            <ReadingSceneGuide
              onAskGuide={() => setNarrationOpen(true)}
              stage={stage}
            />
          )}
        </div>
      )}

      {stage && (
        <footer className="mingli-stage-boundary">
          <span>
            系统目前只证明坐标与六冲／六合成员关系
            {stage.stage_mode === "NATAL_DAYUN_YEAR_6" &&
              ` · 当前大运区间 ${stage.current_dayun_start_date}—${stage.current_dayun_end_date}，交运当日不声明“当前”`}
          </span>
          <small>关系作用、来源可用性、旺衰、概率、有效做功与吉凶均保持未决</small>
        </footer>
      )}
    </div>
  );
}

function ReadingSceneGuide({
  onAskGuide,
  stage,
}: {
  onAskGuide: () => void;
  stage: MingliStageProjection;
}) {
  return (
    <aside className="mingli-reading-guide" aria-label="命理阅读层">
      <p>同一份 Reading · 同一个舞台</p>
      <h2>{stage.stage_mode === "NATAL_4" ? "先看本命四柱" : "时间层已展开为完整六柱"}</h2>
      <div className="mingli-reading-layer-list" aria-label="命理四层">
        <span><strong>命局原理</strong><small>坐标与成员事实已锁定</small></span>
        <span><strong>生命意象</strong><small>不由本舞台自行推导</small></span>
        <span><strong>人生主题</strong><small>等待可验证的应事证据</small></span>
        <span><strong>时间趋势</strong><small>{stage.stage_mode === "NATAL_4" ? "展开大运与所选流年后查看" : "大运与流年共同在场"}</small></span>
      </div>
      <button className="mingli-reading-ask-guide" onClick={onAskGuide} type="button">
        请{stage.narrator_actor_id === "DUODUO_NARRATOR_V1" ? "多多" : "阿布"}讲当前舞台
        <span aria-hidden="true">声音、字幕与粒子一起开始 →</span>
      </button>
    </aside>
  );
}
