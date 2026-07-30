import type {
  DreamGrove,
  DreamSnapshot,
  RuntimeMediaManifest,
  TreeOrgan,
} from "../api";
import { DreamGroveScene } from "../DreamGroveScene";
import type { ExperienceScope } from "../experienceNavigation";
import type { HomeSnapshot } from "../homeApi";
import { buildDreamReadingObservationLens } from "../homeDreamObservationLens";
import { LifeTreeScene } from "../LifeTreeScene";
import { DreamReadingObservationLens } from "./DreamReadingObservationLens";
import { HomeLifeTreeScene as HomeTree } from "./HomeLifeTreeScene";

interface ExperienceStoryCanvasProps {
  scope: ExperienceScope;
  home: HomeSnapshot;
  grove: DreamGrove | null;
  snapshot: DreamSnapshot | null;
  media: RuntimeMediaManifest;
  busy: boolean;
  focusedOrganRef: string | null;
  onEnterDream: () => void;
  onSelectTree: (candidateRef: string) => void;
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
  home,
  grove,
  snapshot,
  media,
  busy,
  focusedOrganRef,
  onEnterDream,
  onSelectTree,
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

  return (
    <section className="story-canvas" aria-label="生命树故事现场">
      {scope === "home" ? (
        <HomeTree
          background={media.assets.life_world_background}
          busy={busy}
          home={home}
          media={media}
          onEnterDream={onEnterDream}
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
        <p>{sceneLineage(scope, grove)}</p>
      </div>
    </section>
  );
}

function sceneLineage(scope: ExperienceScope, grove: DreamGrove | null) {
  if (scope === "home") {
    return "这是你的私密生命树；梦境中的生命不会被写进这里。";
  }
  if (grove) {
    return "三棵树来自三条独立、持续运行的合成人生线。";
  }
  return "这棵树只记得已经发生、已经封存和已经被世界回应的事。";
}
