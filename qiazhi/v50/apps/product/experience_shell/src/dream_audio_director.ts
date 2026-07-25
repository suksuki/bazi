import { DREAM_RUNTIME_ASSETS } from "./dream_asset_registry";
import type { DreamAudioCue } from "./dream_story_contracts";


export interface DreamAudioIntent {
  cue: DreamAudioCue;
  source: string;
  fallback: string;
  volume: number;
  loop: boolean;
  required: boolean;
}


export function audioIntentFor(cue: DreamAudioCue): DreamAudioIntent {
  if (cue === "opening_theme") {
    return {
      cue,
      source: DREAM_RUNTIME_ASSETS.openingTheme.source,
      fallback: DREAM_RUNTIME_ASSETS.openingTheme.fallback || "",
      volume: 0.12,
      loop: true,
      required: false,
    };
  }
  return {
    cue,
    source: "",
    fallback: "",
    volume: 0,
    loop: false,
    required: false,
  };
}
