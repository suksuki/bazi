import { AbuCompanionMotion } from "../AbuCompanionMotion";
import type {
  DreamSnapshot,
  RuntimeMediaManifest,
} from "../api";
import {
  type ExperienceUnit,
  unitSubtitle,
  unitTitle,
} from "../experienceUnits";
import type {
  FocusSourcesHandler,
  SemanticFocus,
} from "../semanticFocus";
import { AbuSaysUnit } from "../units/AbuSaysUnit";
import { DreamUnit } from "../units/DreamUnit";
import { LabUnit } from "../units/LabUnit";
import { MingliUnit } from "../units/MingliUnit";
import { SemanticFocusThread } from "../units/SemanticFocusThread";
import { TheaterUnit } from "../units/TheaterUnit";

interface CompanionRailProps {
  focus: SemanticFocus | null;
  activeUnit: ExperienceUnit;
  media: RuntimeMediaManifest;
  onFocusSources: FocusSourcesHandler;
  snapshot: DreamSnapshot;
}

export function CompanionRail({
  focus,
  activeUnit,
  media,
  onFocusSources,
  snapshot,
}: CompanionRailProps) {
  const guideLeft =
    activeUnit === "dream" &&
    snapshot.question === null &&
    snapshot.encounter.state.observed_organs.length === 0 &&
    snapshot.tree.organs.some(
      (organ) => organ.visible && organ.status === "AVAILABLE",
    );

  return (
    <aside className="companion-rail" data-perspective={activeUnit}>
      <header className="companion-header">
        <span className="companion-actor">
          <AbuCompanionMotion
            className="companion-actor-media"
            cueKey={snapshot.encounter.encounter_ref}
            guideLeft={guideLeft}
            guideLeftCue={media.cues.abu_guide_left}
            idleCue={media.cues.abu_idle}
            label={
              guideLeft
                ? "阿布转向左侧生命树，轻轻抬起前爪邀请你观察"
                : "阿布安静陪在生命树旁"
            }
          />
        </span>
        <span>
          <strong>{unitTitle(activeUnit)}</strong>
          <small>{unitSubtitle(activeUnit)}</small>
        </span>
      </header>

      <div className="companion-content">
        {focus && <SemanticFocusThread focus={focus} unit={activeUnit} />}
        {activeUnit === "dream" && <DreamUnit snapshot={snapshot} />}
        {activeUnit === "mingli" && (
          <MingliUnit
            focus={focus}
            onFocusSources={onFocusSources}
            snapshot={snapshot}
          />
        )}
        {activeUnit === "abu" && (
          <AbuSaysUnit focus={focus} snapshot={snapshot} />
        )}
        {activeUnit === "theater" && (
          <TheaterUnit
            focus={focus}
            onFocusSources={onFocusSources}
            snapshot={snapshot}
          />
        )}
        {activeUnit === "lab" && (
          <LabUnit
            focus={focus}
            onFocusSources={onFocusSources}
            snapshot={snapshot}
          />
        )}
      </div>

      <footer className="companion-footer">
        <span className="status-seed" aria-hidden="true" />
        <p>{snapshot.projections.dream.journey_status}</p>
      </footer>
    </aside>
  );
}
