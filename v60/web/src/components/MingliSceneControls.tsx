import type {
  MingliStageRoute,
} from "../mingliStageNavigation";
import type { MingliSceneSurface } from "../mingliSceneDirector";
import type {
  MingliStageProjection,
  MingliStageSubject,
  MingliStageSubjectId,
} from "../mingliStageTypes";

export function MingliSceneControls({
  onExit,
  onNavigate,
  onOpenSyntheticLab,
  onRetrySubjects,
  onSurfaceChange,
  route,
  stage,
  subjects,
  subjectsError,
  subjectsLoading,
  surface,
}: {
  onExit: () => void;
  onNavigate: (route: MingliStageRoute) => void;
  onOpenSyntheticLab?: () => void;
  onRetrySubjects: () => void;
  onSurfaceChange: (surface: MingliSceneSurface) => void;
  route: MingliStageRoute;
  stage: MingliStageProjection | null;
  subjects: MingliStageSubject[];
  subjectsError: string | null;
  subjectsLoading: boolean;
  surface: MingliSceneSurface;
}) {
  return (
    <>
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
          {surface === "LAB" && onOpenSyntheticLab && (
            <button
              aria-pressed="false"
              onClick={onOpenSyntheticLab}
              type="button"
            >
              合成验证
            </button>
          )}
        </div>
      </header>

      <div className="mingli-scene-toolbar" aria-label="命理舞台坐标选择">
        <label>
          <span>档案</span>
          <select
            aria-label="选择命理档案"
            disabled={subjectsLoading || Boolean(subjectsError) || !subjects.length}
            onChange={(event) =>
              onNavigate({
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
          <button className="mingli-subject-retry" onClick={onRetrySubjects} type="button">
            重试档案列表
          </button>
        )}
        <div className="mingli-stage-mode" role="group" aria-label="选择四柱或六柱">
          <button
            aria-pressed={route.mode === "NATAL_4"}
            onClick={() => onNavigate({ ...route, mode: "NATAL_4", year: null })}
            type="button"
          >
            本命四柱
          </button>
          <button
            aria-pressed={route.mode === "NATAL_DAYUN_YEAR_6"}
            onClick={() =>
              onNavigate({ ...route, mode: "NATAL_DAYUN_YEAR_6", year: null })
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
                onNavigate({ ...route, year: Number(event.target.value) })
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
    </>
  );
}
