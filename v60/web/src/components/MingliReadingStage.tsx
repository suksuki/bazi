import { useCallback, useEffect, useState } from "react";

import { loadMingliStage, loadMingliStageSubjects } from "../mingliStageApi";
import {
  readMingliStageRoute,
  type MingliStageRoute,
  writeMingliStageRoute,
} from "../mingliStageNavigation";
import type {
  MingliNarrationVisualClock,
  MingliStageProjection,
  MingliStageSubject,
  MingliStageSubjectId,
  MingliStageViewContext,
} from "../mingliStageTypes";
import { MingliNarrationPlayer } from "./MingliNarrationPlayer";
import { MingliPillarStage } from "./MingliPillarStage";

const INITIAL_CLOCK: MingliNarrationVisualClock = {
  phase: null,
  currentTimeMs: 0,
  activeCueId: null,
};

export function MingliReadingStage({
  homeLineageKey,
  onContextChange,
}: {
  homeLineageKey: string;
  onContextChange: (context: MingliStageViewContext) => void;
}) {
  const [route, setRoute] = useState<MingliStageRoute>(readMingliStageRoute);
  const [subjects, setSubjects] = useState<MingliStageSubject[]>([]);
  const [stage, setStage] = useState<MingliStageProjection | null>(null);
  const [clock, setClock] = useState<MingliNarrationVisualClock>(INITIAL_CLOCK);
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
    setStage(null);
    setClock(INITIAL_CLOCK);
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
        onContextChange({
          subjectId: route.subjectId,
          status: "READY",
          projection,
        });
        if (route.mode === "NATAL_DAYUN_YEAR_6" && route.year === null) {
          const restored = { ...route, year: projection.selected_year };
          setRoute(restored);
          writeMingliStageRoute(restored, "replace");
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
    writeMingliStageRoute(next);
  };

  return (
    <div
      className="mingli-reading-stage"
      data-active-cue-id={clock.activeCueId ?? "NONE"}
      data-audio-time-ms={clock.currentTimeMs}
      data-narration-phase={clock.phase ?? "IDLE"}
      data-projection-hash={stage?.projection_hash ?? ""}
      data-projection-ref={stage?.projection_ref ?? ""}
      data-stage-mode={stage?.stage_mode ?? route.mode}
    >
      <header className="mingli-stage-header">
        <div>
          <p>档案叶 · 命理枝</p>
          <h1>{stage ? `${stage.display_name}的命理舞台` : "命理舞台正在生长"}</h1>
          <span className="mingli-identity-badge">
            {stage?.identity_badge ?? "读取档案身份"}
          </span>
        </div>
        <div className="mingli-stage-controls" aria-label="命理舞台选择">
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
                navigate({
                  ...route,
                  mode: "NATAL_DAYUN_YEAR_6",
                  year: null,
                })
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
      </header>

      {stageLoading && (
        <div className="mingli-stage-loading" role="status">
          <span aria-hidden="true" />
          正在从当前 Case 生长命理枝……
        </div>
      )}
      {stageError && (
        <div className="mingli-stage-error" role="alert">
          <p>命理舞台暂时没有完成接线：{stageError}</p>
          <button onClick={() => setStageRetry((value) => value + 1)} type="button">
            重新读取
          </button>
        </div>
      )}
      {stage && (
        <>
          <MingliPillarStage clock={clock} stage={stage} />
          <MingliNarrationPlayer
            key={stage.projection_ref}
            onClock={onClock}
            stage={stage}
          />
          <footer className="mingli-stage-boundary">
            <span>
              系统目前只证明坐标与六冲／六合成员关系
              {stage.stage_mode === "NATAL_DAYUN_YEAR_6" &&
                ` · 当前大运区间 ${stage.current_dayun_start_date}—${stage.current_dayun_end_date}，交运当日不声明“当前”`}
            </span>
            <small>
              关系作用、来源可用性、旺衰、概率、有效做功与吉凶均保持未决
            </small>
          </footer>
        </>
      )}
    </div>
  );
}
