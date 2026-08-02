import type { MingliSceneSurface } from "../mingliSceneDirector";
import type { MingliStageProjection } from "../mingliStageTypes";

export function MingliSceneBoundary({
  claimGraphReady,
  stage,
  surface,
  wholeChartNeedsReconciliation,
}: {
  claimGraphReady: boolean;
  stage: MingliStageProjection;
  surface: MingliSceneSurface;
  wholeChartNeedsReconciliation: boolean;
}) {
  if (surface === "LAB") {
    return (
      <footer className="mingli-stage-boundary">
        <span>
          {claimGraphReady
            ? "Lab 正在展开命理枝上的同一次整盘初断；这里不会另起一套结论。"
            : "整盘初断生成后，Lab 会在这里展开主解释、竞争解释和证据引用。"}
          {stage.stage_mode === "NATAL_DAYUN_YEAR_6" &&
            ` · 当前大运区间 ${stage.current_dayun_start_date}—${stage.current_dayun_end_date}，交运当日不声明“当前”`}
        </span>
        <small>单条判断可以继续校准；局部争议不会让整份命盘停止判断。</small>
      </footer>
    );
  }

  return (
    <footer className="mingli-stage-boundary">
      <span>
        {claimGraphReady
          ? wholeChartNeedsReconciliation
            ? "这份整盘初断已经保存；主解释仍在专业校准，不是定论。"
            : "这份整盘初断已经保存；刷新或切回档案后仍会回到同一结果。"
          : "四柱已经排定，等待阿布完成一次整盘研判。"}
      </span>
      <small>阿布会把原局、结构竞争与岁运放在同一条判断链里。</small>
    </footer>
  );
}
