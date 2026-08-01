import type { ExperienceUnit } from "../experienceUnits";
import type { HomeSnapshot } from "../homeApi";
import { HomeCompanionRail } from "./HomeCompanionRail";

export function MingliCanonicalDrawer({
  activeUnit,
  busy,
  home,
  onCompareMechanisms,
  onEnterDream,
  onHomeRefresh,
}: {
  activeUnit: ExperienceUnit;
  busy: boolean;
  home: HomeSnapshot;
  onCompareMechanisms: () => void;
  onEnterDream: () => void;
  onHomeRefresh: () => Promise<void>;
}) {
  return (
    <details
      className="mingli-canonical-drawer"
      data-perspective={activeUnit}
    >
      <summary>
        <span>
          {activeUnit === "lab" ? "Lab 证据与候选" : "命盘依据"}
        </span>
        <small>展开排盘与推演依据</small>
      </summary>
      <div className="mingli-canonical-drawer-panel">
        <HomeCompanionRail
          activeUnit={activeUnit}
          busy={busy}
          home={home}
          onCompareMechanisms={onCompareMechanisms}
          onHomeRefresh={onHomeRefresh}
          onEnterDream={onEnterDream}
        />
      </div>
    </details>
  );
}
