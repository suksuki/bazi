import type { ExperienceUnit } from "../experienceUnits";
import type { HomeSnapshot } from "../homeApi";
import { HomeCompanionRail } from "./HomeCompanionRail";
import { MingliCanonicalDrawer } from "./MingliCanonicalDrawer";

export function HomeSceneCompanion({
  activeUnit,
  busy,
  home,
  mingliSceneActive,
  onCompareMechanisms,
  onEnterDream,
  onHomeRefresh,
}: {
  activeUnit: ExperienceUnit;
  busy: boolean;
  home: HomeSnapshot;
  mingliSceneActive: boolean;
  onCompareMechanisms: () => void;
  onEnterDream: () => void;
  onHomeRefresh: () => Promise<void>;
}) {
  if (mingliSceneActive) {
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
