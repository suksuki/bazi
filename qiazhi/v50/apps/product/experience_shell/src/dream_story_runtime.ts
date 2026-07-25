import type { DreamGameState } from "./dream_game_api";
import type { DreamVisitView } from "./dream_api";
import { sceneForStory } from "./dream_scene_director";
import {
  initialDreamStorySnapshot,
  reduceDreamStory,
} from "./dream_story_reducer";
import type {
  DreamSceneContract,
  DreamStoryEvent,
  DreamStorySnapshot,
} from "./dream_story_contracts";

const DREAM_RETURN_PRESENTATION_KEY = "deepbazi.dream.returned-with-seed.v1";


export interface DreamStorySyncInput {
  dreamAvailable?: boolean;
  resumable?: boolean;
  visit?: DreamVisitView | null;
  gameState?: DreamGameState | "";
  hasAttempt?: boolean;
  hasResult?: boolean;
  foundationComplete?: boolean;
  returnedWithSeed?: boolean;
}


export class DreamStoryRuntime {
  private snapshotValue = initialDreamStorySnapshot();

  get snapshot(): DreamStorySnapshot {
    return this.snapshotValue;
  }

  get scene(): DreamSceneContract {
    return sceneForStory(this.snapshotValue);
  }

  dispatch(event: DreamStoryEvent): DreamStorySnapshot {
    this.snapshotValue = reduceDreamStory(this.snapshotValue, event);
    return this.snapshotValue;
  }

  sync(input: DreamStorySyncInput): DreamStorySnapshot {
    return this.dispatch({
      type: "SYNC_SERVER",
      context: {
        dreamAvailable: Boolean(input.dreamAvailable),
        resumable: Boolean(input.resumable),
        visit: input.visit || null,
        gameState: input.gameState || "",
        hasAttempt: Boolean(input.hasAttempt),
        hasResult: Boolean(input.hasResult),
        foundationComplete: Boolean(input.foundationComplete),
        returnedWithSeed: Boolean(input.returnedWithSeed),
      },
    });
  }

  can(command: DreamSceneContract["allowedCommands"][number]): boolean {
    return this.scene.allowedCommands.includes(command);
  }
}


export function markDreamReturnedWithSeed(hasKnowledgeSeed: boolean): void {
  sessionStorage.setItem(DREAM_RETURN_PRESENTATION_KEY, JSON.stringify({
    hasKnowledgeSeed,
    recordedAt: Date.now(),
  }));
}


export function consumeDreamReturnedWithSeed(): boolean {
  try {
    const raw = sessionStorage.getItem(DREAM_RETURN_PRESENTATION_KEY);
    sessionStorage.removeItem(DREAM_RETURN_PRESENTATION_KEY);
    if (!raw) return false;
    const value = JSON.parse(raw) as { hasKnowledgeSeed?: boolean; recordedAt?: number };
    return Boolean(
      value.hasKnowledgeSeed
      && Number.isFinite(value.recordedAt)
      && Date.now() - Number(value.recordedAt) < 5 * 60 * 1000,
    );
  } catch {
    sessionStorage.removeItem(DREAM_RETURN_PRESENTATION_KEY);
    return false;
  }
}
