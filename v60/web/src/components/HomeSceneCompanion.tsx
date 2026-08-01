import type { ExperienceUnit } from "../experienceUnits";
import type { HomeSnapshot } from "../homeApi";
import { readMingliStageRoute } from "../mingliStageNavigation";
import { mingliStageMatchesHome } from "../mingliStageContext";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { HomeCompanionRail } from "./HomeCompanionRail";
import { MingliCanonicalDrawer } from "./MingliCanonicalDrawer";

export function HomeSceneCompanion({
  activeUnit,
  busy,
  home,
  mingliContext,
  mingliSceneActive,
  onCompareMechanisms,
  onEnterDream,
  onHomeRefresh,
}: {
  activeUnit: ExperienceUnit;
  busy: boolean;
  home: HomeSnapshot;
  mingliContext: MingliStageViewContext;
  mingliSceneActive: boolean;
  onCompareMechanisms: () => void;
  onEnterDream: () => void;
  onHomeRefresh: () => Promise<void>;
}) {
  if (mingliSceneActive) {
    const routeMatchesContext = (
      readMingliStageRoute().subjectId === mingliContext.subjectId
    );
    if (!routeMatchesContext || !mingliStageMatchesHome(mingliContext, home)) {
      const stage = mingliContext.projection;
      return (
        <aside className="mingli-case-evidence-boundary" role="status">
          <small>CASE-BOUND EVIDENCE</small>
          <strong>
            {stage ? `${stage.display_name}的证据抽屉尚未接线` : "正在核对这份档案的证据边界"}
          </strong>
          <p>
            {stage
              ? `主舞台与命理枝已经绑定 ${stage.identity_badge}；为避免混入${home.profile.display_name}的 Reading，这里不会显示或提交当前生命树的证据。`
              : "Case、命盘、LifeCase 与 Reading 完全一致后，证据入口才会开放。"}
          </p>
        </aside>
      );
    }
    return (
      <MingliCanonicalDrawer
        activeUnit={activeUnit}
        busy={busy}
        home={home}
        key={activeUnit}
        onCompareMechanisms={onCompareMechanisms}
        onEnterDream={onEnterDream}
        onHomeRefresh={onHomeRefresh}
      />
    );
  }
  return (
    <HomeCompanionRail
      activeUnit={activeUnit}
      busy={busy}
      home={home}
      onCompareMechanisms={onCompareMechanisms}
      onEnterDream={onEnterDream}
      onHomeRefresh={onHomeRefresh}
    />
  );
}
