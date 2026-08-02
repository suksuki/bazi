import type {
  DreamGrove,
  DreamSnapshot,
  RuntimeMediaManifest,
  TreeOrgan,
} from "../api";
import type { CSSProperties } from "react";
import { DreamGroveScene } from "../DreamGroveScene";
import type { DreamLifeDomain } from "../dreamPersonalJourneyTypes";
import type { ExperienceScope } from "../experienceNavigation";
import type { ExperienceUnit } from "../experienceUnits";
import type { HomeSnapshot } from "../homeApi";
import { buildDreamReadingObservationLens } from "../homeDreamObservationLens";
import type { MingliStageViewContext } from "../mingliStageTypes";
import { readMingliLeafEntry } from "../mingliStageNavigation";
import { LifeTreeScene } from "../LifeTreeScene";
import { DreamReadingObservationLens } from "./DreamReadingObservationLens";
import { HomeLifeTreeScene as HomeTree } from "./HomeLifeTreeScene";
import { MingliBranchSceneHost } from "./MingliBranchSceneHost";
import { MingliLabWorkspaceHost } from "./MingliLabWorkspaceHost";

interface ExperienceStoryCanvasProps {
  scope: ExperienceScope;
  activeUnit: ExperienceUnit;
  home: HomeSnapshot;
  grove: DreamGrove | null;
  snapshot: DreamSnapshot | null;
  media: RuntimeMediaManifest;
  busy: boolean;
  focusedOrganRef: string | null;
  onEnterDream: () => void;
  onHomeRefresh: () => Promise<void>;
  onMingliContext: (context: MingliStageViewContext) => void;
  onSelectUnit: (unit: ExperienceUnit, mode?: "push" | "replace") => void;
  onSelectTree: (candidateRef: string) => void;
  onStartPersonalJourney: (
    candidateRef: string,
    domain: DreamLifeDomain,
    question: string,
  ) => void;
  onSelectDreamAttention: (observationRef: string) => void;
  onFocus: (organ: TreeOrgan) => void;
  onOrgan: (organ: TreeOrgan) => void;
  onAnswer: (choiceId: string) => void;
  onReveal: () => void;
  onReconcile: () => void;
  onContinue: () => void;
  onReturnToGrove: () => void;
}

export function ExperienceStoryCanvas({
  scope,
  activeUnit,
  home,
  grove,
  snapshot,
  media,
  busy,
  focusedOrganRef,
  onEnterDream,
  onHomeRefresh,
  onMingliContext,
  onSelectUnit,
  onSelectTree,
  onStartPersonalJourney,
  onSelectDreamAttention,
  onFocus,
  onOrgan,
  onAnswer,
  onReveal,
  onReconcile,
  onContinue,
  onReturnToGrove,
}: ExperienceStoryCanvasProps) {
  const observationLens = buildDreamReadingObservationLens({
    reading_brief: home.mingli.reading_brief,
    mechanism_comparison: home.lab.mechanism_comparison,
  });
  const growthEntry = scope === "home" && activeUnit === "mingli"
    ? readMingliLeafEntry()
    : null;
  const growthStyle = growthEntry
    ? ({
        "--mingli-entry-x": `${growthEntry.viewportX}%`,
        "--mingli-entry-y": `${growthEntry.viewportY}%`,
        "--mingli-scene-entry-x": `${growthEntry.sceneX}%`,
        "--mingli-scene-entry-y": `${growthEntry.sceneY}%`,
      } as CSSProperties)
    : undefined;

  return (
    <section className="story-canvas" aria-label="生命树故事现场">
      {scope === "home" && activeUnit === "mingli" ? (
        <div className="mingli-growth-composition" style={growthStyle}>
          <div aria-hidden="true" className="mingli-growth-home-underlay" inert>
            <HomeTree
              busy
              home={home}
              media={media}
              onEnterDream={onEnterDream}
              onHomeRefresh={onHomeRefresh}
              onOpenLab={() => onSelectUnit("lab")}
              onOpenMingli={() => undefined}
            />
          </div>
          <MingliBranchSceneHost
            media={media}
            onContextChange={onMingliContext}
            onExit={() => onSelectUnit("dream", "replace")}
            onOpenStage={() => onSelectUnit("lab")}
          />
        </div>
      ) : scope === "home" && activeUnit === "lab" ? (
        <MingliLabWorkspaceHost
          homeLineageKey={[
            home.case.case_ref,
            home.chart.chart_version_ref,
            home.life_case.life_case_revision_ref,
            home.mingli.reading.reading_ref,
          ].join("|")}
          media={media}
          onContextChange={onMingliContext}
          onExit={() => onSelectUnit("dream", "replace")}
          onSurfaceChange={(surface) =>
            onSelectUnit(surface === "LAB" ? "lab" : "mingli")
          }
        />
      ) : scope === "home" ? (
        <HomeTree
          busy={busy}
          home={home}
          media={media}
          onEnterDream={onEnterDream}
          onHomeRefresh={onHomeRefresh}
          onOpenLab={() => onSelectUnit("lab")}
          onOpenMingli={() => onSelectUnit("mingli")}
        />
      ) : grove ? (
        <DreamGroveScene
          background={media.assets.grove_background}
          busy={busy}
          grove={grove}
          lens={observationLens}
          media={media}
          onSelect={onSelectTree}
          onSelectAttention={onSelectDreamAttention}
          onStartPersonalJourney={onStartPersonalJourney}
        />
      ) : (
        snapshot && (
          <>
            <LifeTreeScene
              background={media.assets.life_world_background}
              snapshot={snapshot}
              busy={busy}
              focusedOrganRef={focusedOrganRef}
              onFocus={onFocus}
              onOrgan={onOrgan}
              onAnswer={onAnswer}
              onReveal={onReveal}
              onReconcile={onReconcile}
              onContinue={onContinue}
              onReturnToGrove={onReturnToGrove}
            />
            <DreamReadingObservationLens
              lens={observationLens}
              mode="encounter"
            />
          </>
        )
      )}
      <div className="scene-lineage">
        <span aria-hidden="true" />
        <p>{sceneLineage(scope, grove, activeUnit)}</p>
      </div>
    </section>
  );
}

function sceneLineage(
  scope: ExperienceScope,
  grove: DreamGrove | null,
  activeUnit: ExperienceUnit,
) {
  if (scope === "home" && (activeUnit === "mingli" || activeUnit === "lab")) {
    return "命理阅读、Lab 与角色讲述共用同一个可复算舞台；未被证明的作用不会被补写。";
  }
  if (scope === "home") {
    return "这是你的私密生命树；梦境中的生命不会被写进这里。";
  }
  if (grove) {
    return "三棵树来自三条独立、持续运行的合成人生线。";
  }
  return "这棵树只记得已经发生、已经封存和已经被世界回应的事。";
}
