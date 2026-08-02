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
          <small>独立研究命盘</small>
          <strong>
            {stage ? `${stage.display_name}正在独立展示` : "正在切换研究命盘"}
          </strong>
          <p>
            {stage
              ? `当前舞台只呈现${stage.identity_badge}；${home.profile.display_name}的生命树内容仍留在自己的档案里。`
              : "研究命盘准备完成后再展开；当前生命树不会被改动。"}
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
