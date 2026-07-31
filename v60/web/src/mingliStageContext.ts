import type { HomeSnapshot } from "./homeApi";
import { readMingliStageRoute } from "./mingliStageNavigation";
import type { MingliStageViewContext } from "./mingliStageTypes";

export function initialMingliStageContext(): MingliStageViewContext {
  return {
    subjectId: readMingliStageRoute().subjectId,
    status: "LOADING",
    projection: null,
  };
}

export function mingliStageMatchesHome(
  context: MingliStageViewContext,
  home: HomeSnapshot,
): boolean {
  const stage = context.projection;
  return (
    context.status === "READY" &&
    context.subjectId === "current" &&
    stage?.subject_id === "current" &&
    stage.subject_kind === "HUMAN_OWNER" &&
    stage.privacy_scope === "PRIVATE_OWNER" &&
    stage.case_ref === home.case.case_ref &&
    stage.chart_version_ref === home.chart.chart_version_ref &&
    stage.life_case_revision_ref === home.life_case.life_case_revision_ref &&
    stage.reading_ref === home.mingli.reading.reading_ref
  );
}
