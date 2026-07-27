import type { DreamAssetIntent } from "./dream_story_contracts";


export interface DreamRuntimeAsset {
  assetId: string;
  intent: DreamAssetIntent;
  kind: "video" | "image" | "actor" | "audio";
  source: string;
  poster?: string;
  fallback?: string;
  sourceSha256?: string;
  sourceMaster?: string;
  sourceTimeRange?: [number, number];
  reducedMotionSafe: boolean;
  mobileSafe: boolean;
  status:
    | "LIBRARY_READY"
    | "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW"
    | "TRANSITIONAL_FALLBACK";
}


export const DREAM_ENCOUNTER_ASSET_ROOT = "/assets/dream/encounter-01-v1";
const DIRECTOR_ROOT = `${DREAM_ENCOUNTER_ASSET_ROOT}/director-v2`;
const ABU_V12 = "/assets/abu/v12-actor-pass";


export const DREAM_RUNTIME_ASSETS = {
  homeTree: {
    assetId: "semantic_tree_base_clean_v1",
    intent: "home_tree",
    kind: "image",
    source: "/assets/dream/semantic-tree-visible-v1/assets/tree_base_clean.png",
    sourceMaster: "SEMANTIC_TREE_VISIBLE_V1",
    sourceSha256: "dfd661d7e1b171a77afdf75224c453de2d7984ddfe2531df06f2ae11dd187be9",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  abuSleep: {
    assetId: "abu_sleep_breathe_v6_transitional",
    intent: "abu_sleep_breath",
    kind: "actor",
    source: "/assets/abu/v6-designer-sleep/web/abu_sleep_breathe_v6.webp",
    poster: "/assets/abu/v6-designer-sleep/posters/abu_sleep_breathe_v6.png",
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "TRANSITIONAL_FALLBACK",
  },
  abuSeated: {
    assetId: "ABU_01_SEATED_IDLE_LOOP_V3",
    intent: "ghost_orbit",
    kind: "actor",
    source: `${ABU_V12}/abu-01-seated-idle-loop-v3/web/abu_01_seated_idle_loop_v3.webm`,
    poster: `${ABU_V12}/abu-01-seated-idle-loop-v3/posters/abu_01_seated_idle_loop_v3.png`,
    fallback: `${ABU_V12}/abu-01-seated-idle-loop-v3/web/abu_01_seated_idle_loop_v3.webp`,
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  abuWalk: {
    assetId: "ABU_02_CALM_FOLLOW_WALK_LOOP_V1",
    intent: "abu_tree_leap",
    kind: "actor",
    source: `${ABU_V12}/abu-02-calm-follow-walk-loop-v1/web/abu_02_calm_follow_walk_loop_v1.webm`,
    poster: `${ABU_V12}/abu-02-calm-follow-walk-loop-v1/posters/abu_02_calm_follow_walk_loop_v1.png`,
    fallback: `${ABU_V12}/abu-02-calm-follow-walk-loop-v1/web/abu_02_calm_follow_walk_loop_v1.webp`,
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "TRANSITIONAL_FALLBACK",
  },
  dreamEntry: {
    assetId: "ABU_03_DREAM_ENTRY_TRANSITION_V1",
    intent: "fog_gate",
    kind: "video",
    source: "/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_runtime_1080p.mp4",
    poster: "/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_first_frame.png",
    fallback: "/assets/dream/entry-transition-v1/abu_03_dream_entry_transition_v1_last_frame.png",
    sourceMaster: "Create_an_second_cinematic_d.mp4",
    sourceSha256: "ca42b6e7c7ad1236cb3c35676471302d26401ae07fb2fc3550cf15fa2243e7f7",
    sourceTimeRange: [0, 7.75],
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW",
  },
  porchBlue: {
    assetId: "dream_porch_blue_tree_actor_v5",
    intent: "ghost_orbit",
    kind: "actor",
    source: "/assets/dream/porch-v5/tree-blue-actor-v5-08170159.png",
    sourceSha256: "081701597f2f4dfaf422215204f7a607d27fcb9ec05c473a7edf52180923dd85",
    sourceMaster: "blue single-tree scene + background extraction",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW",
  },
  porchJade: {
    assetId: "dream_porch_jade_tree_actor_v5",
    intent: "ghost_orbit",
    kind: "actor",
    source: "/assets/dream/porch-v5/tree-jade-actor-v5-9541d056.png",
    sourceSha256: "9541d056857df81b6f753e99ee68e4113808c47a060bef77b65d9714f69ec6c2",
    sourceMaster: "jade single-tree scene + background extraction",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW",
  },
  porchAmber: {
    assetId: "dream_porch_amber_tree_actor_v5",
    intent: "ghost_orbit",
    kind: "actor",
    source: "/assets/dream/porch-v5/tree-amber-actor-v5-1f98142a.png",
    sourceSha256: "1f98142ad58c8f9b207c780844ab04bd0733d91a01a8c15465359910e1e7c11e",
    sourceMaster: "amber single-tree scene + background extraction",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "POSTPROCESS_COMPLETE_AWAITING_OWNER_REVIEW",
  },
  porchCleanBackdrop: {
    assetId: "DREAM_PORCH_CLEAN_BACKGROUND_V5",
    intent: "ghost_orbit",
    kind: "image",
    source: "/assets/dream/porch-v5/grove-clean-approved-v5-e97ec6b5.png",
    sourceMaster: "owner-approved forest object-removal edit",
    sourceSha256: "e97ec6b5f856e15371cad08c91609b4585d55eea112ec9b1176ebfb5bd6eca54",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  fixedTreeBud: {
    assetId: "dream_fixed_tree_bud_preseal_v1",
    intent: "fixed_tree",
    kind: "image",
    source: `${DIRECTOR_ROOT}/tree-question-map-full-preseal.png`,
    fallback: `${DIRECTOR_ROOT}/tree-observe-bud-mobile-preseal.jpg`,
    sourceMaster: "1000056879.mp4",
    sourceSha256: "3d2d7e5beeb6705d79ed48178a0deb89b42525beb172a545d5eefe77440b089d",
    sourceTimeRange: [5, 5],
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  fixedTreeFlower: {
    assetId: "dream_fixed_tree_flower_preseal_v1",
    intent: "question_bud",
    kind: "image",
    source: `${DIRECTOR_ROOT}/tree-flower-open-preseal.png`,
    fallback: `${DIRECTOR_ROOT}/tree-flower-open-mobile-preseal.jpg`,
    sourceMaster: "1000056885.mp4",
    sourceSha256: "feb7faf1f08910894e944ebd8ae288afc5f6526b1cd677d4e4f8ade916fde137",
    sourceTimeRange: [5, 7.5],
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  treeEnter: {
    assetId: "dream_tree_entry_transition_v1",
    intent: "fixed_tree",
    kind: "video",
    source: `${DIRECTOR_ROOT}/tree-enter-clean.mp4`,
    fallback: `${DIRECTOR_ROOT}/tree-observe-bud-preseal.png`,
    sourceMaster: "1000056879.mp4",
    sourceSha256: "3d2d7e5beeb6705d79ed48178a0deb89b42525beb172a545d5eefe77440b089d",
    sourceTimeRange: [2.5, 5],
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  fruitForm: {
    assetId: "dream_fog_white_fruit_form_reference_v1",
    intent: "fruit_form",
    kind: "video",
    source: `${DIRECTOR_ROOT}/fruit-reveal-reference-clean.mp4`,
    sourceMaster: "1000056885.mp4",
    sourceSha256: "feb7faf1f08910894e944ebd8ae288afc5f6526b1cd677d4e4f8ade916fde137",
    sourceTimeRange: [7.5, 10],
    reducedMotionSafe: false,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
  openingTheme: {
    assetId: "abu_mingli_opening_theme_morning_glints_v1",
    intent: "fog_gate",
    kind: "audio",
    source: "/assets/audio/abu/morning-glints-in-the-grove-v1/morning-glints-in-the-grove-opening-v1.opus",
    fallback: "/assets/audio/abu/morning-glints-in-the-grove-v1/morning-glints-in-the-grove-opening-v1.mp3",
    reducedMotionSafe: true,
    mobileSafe: true,
    status: "LIBRARY_READY",
  },
} as const satisfies Record<string, DreamRuntimeAsset>;


export async function preloadDreamPorchScenes(): Promise<void> {
  const sources = [
    DREAM_RUNTIME_ASSETS.porchCleanBackdrop.source,
    DREAM_RUNTIME_ASSETS.porchBlue.source,
    DREAM_RUNTIME_ASSETS.porchJade.source,
    DREAM_RUNTIME_ASSETS.porchAmber.source,
  ];
  await Promise.all(sources.map((source) => preloadImage(source)));
}


function preloadImage(source: string): Promise<void> {
  return new Promise((resolve) => {
    const image = new Image();
    const complete = () => resolve();
    image.addEventListener("load", complete, { once: true });
    image.addEventListener("error", complete, { once: true });
    image.src = source;
    if (image.complete) {
      void image.decode().catch(() => undefined).finally(complete);
    }
  });
}


export function assetForIntent(intent: DreamAssetIntent): DreamRuntimeAsset[] {
  return Object.values(DREAM_RUNTIME_ASSETS).filter((asset) => asset.intent === intent);
}
