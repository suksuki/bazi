export type SemanticTreeOrganId =
  | "leafBasic01"
  | "leafBasic02"
  | "trunkBackbone01"
  | "flower";

export type SemanticTreeVisualState = "INITIAL" | "FLOWER_OPEN" | "FRUIT_WHITE";

interface SemanticTreeAssetRef {
  source: string;
  sha256: string;
  width: number;
  height: number;
  alpha: boolean;
  hitMask?: string;
  hitMaskSha256?: string;
}

interface SemanticTreeAnchor {
  x: number;
  y: number;
  displayWidth?: number;
  displayHeight?: number;
}

interface SemanticTreeOrganLayout {
  desktop: SemanticTreeAnchor;
  mobile: SemanticTreeAnchor;
}

const ROOT = "/assets/dream/semantic-tree-visible-v1";

export const SEMANTIC_TREE_SCENE_BUNDLE = {
  bundleId: "SEMANTIC_TREE_VISIBLE_V1",
  schemaVersion: "deepbazi.semantic_tree_asset_bundle.v1",
  ownerAcceptedOuterSha256:
    "2bd3f4d277462eec9200622315e2124ddd8e9ed417f12603500dfc9adf777efc",
  publicRoot: ROOT,
  legacyFallbackAllowed: false,
  characterPolicy: "PRESERVE_EXISTING_RUNTIME_ABU",
  canvas: {
    nativeWidth: 1280,
    nativeHeight: 720,
    fit: "cover",
    cameraMotionAfterEntry: false,
  },
  assets: {
    treeBase: asset(
      "assets/tree_base_clean.png",
      "dfd661d7e1b171a77afdf75224c453de2d7984ddfe2531df06f2ae11dd187be9",
      1280,
      720,
      false,
    ),
    leafBasic01: asset(
      "assets/leaf_basic_01.png",
      "e13b7640c3cbed3be6a185a550e0f4df39df7dedc37dbc5468d0c1b93a9288b8",
      320,
      249,
      true,
      "masks/leaf_basic_01_hit_mask.png",
      "10f6d4c0dde6aafd99b972592aa2a097f6abfc7785830da1c8f03c827bc6be8d",
    ),
    leafBasic02: asset(
      "assets/leaf_basic_02.png",
      "f13312a1b25fd117208ea0cb67c932ed2af9b68d7f8a53cee7a218690a3837f8",
      208,
      280,
      true,
      "masks/leaf_basic_02_hit_mask.png",
      "542b76f1190afc0c841e1be3e435a3f2789d479cfbc7e0b558deaad99e38ebc4",
    ),
    trunkBackbone01: asset(
      "assets/trunk_backbone_01.png",
      "cc594091d7ae29c91b54813817570d9aac2c49c531447e7d717604f7eb450837",
      107,
      460,
      true,
      "masks/trunk_backbone_01_hit_mask.png",
      "72abef1ed2321e5f10228eb30e9e19fe9f4539188cbe4efae08256a296147b53",
    ),
    energyFlow: asset(
      "assets/energy_flow_mask.png",
      "f8c1a9f8453f29896cbbd170b48308a2a1f1a84df24badd2b7f2948e465b6e4f",
      1280,
      720,
      true,
    ),
    flowerBudClosed: asset(
      "assets/flower_bud_closed.png",
      "2e96823d2cb5ed3956db70afcda82800f65e0ba9f6c33a79f3f82c5e00a6b713",
      112,
      280,
      true,
      "masks/flower_bud_closed_hit_mask.png",
      "8516603bde01a8d5fa44bb617e595adefe1615648bcd74d953527cc4228b8f60",
    ),
    flowerOpen: asset(
      "assets/flower_open.png",
      "14a7d4f92b317542dbfb4e2036021b7225c730dafe0ed7aeff8bf3d2270b2f86",
      290,
      320,
      true,
      "masks/flower_open_hit_mask.png",
      "2dbce319ffd6be5686bf10f1f10218de8a505aebd60883124df2a820f96e6451",
    ),
    fruitWhite: asset(
      "assets/fruit_white.png",
      "7619465b06110857dff001edb31b3a00de11326765f8a7fe0d4b7721cac08452",
      240,
      222,
      true,
      "masks/fruit_white_hit_mask.png",
      "fe31f0057077864452b5b982a1e8a7aef9c5dc67eb5fdc97d65a6b7931318c11",
    ),
    foregroundOcclusion: asset(
      "assets/foreground_occlusion.png",
      "8fbce9ff56d7c2a107c3b04df87aa950031a7a8a6547ece9c6addabe6a3b59d2",
      318,
      340,
      true,
    ),
  },
  layouts: {
    leafBasic01: layout(
      { x: 620, y: 245, displayWidth: 104 },
      { x: 138, y: 210, displayWidth: 76 },
    ),
    leafBasic02: layout(
      { x: 950, y: 340, displayWidth: 78 },
      { x: 260, y: 370, displayWidth: 56 },
    ),
    trunkBackbone01: layout(
      { x: 674, y: 280, displayWidth: 92 },
      { x: 168, y: 280, displayWidth: 52 },
    ),
    flowerBudClosed: layout(
      { x: 1050, y: 240, displayHeight: 110 },
      { x: 286, y: 230, displayHeight: 95 },
    ),
    flowerOpen: layout(
      { x: 1008, y: 200, displayHeight: 145 },
      { x: 250, y: 210, displayHeight: 120 },
    ),
    fruitWhite: layout(
      { x: 1030, y: 250, displayHeight: 95 },
      { x: 270, y: 250, displayHeight: 80 },
    ),
    foregroundOcclusion: layout(
      { x: 1060, y: 270, displayWidth: 105 },
      { x: 280, y: 280, displayWidth: 90 },
    ),
  },
  integrityFiles: {
    "ASSET_PROVENANCE.md": "0223c298d8f2fa6d9281221b01247913b49c0aa064dcfe8c6142ca301bd3ed52",
    "LAYOUT_CONTRACT.json": "aae176a9a7ecc6338a1a853c8794a19adc4196451d8801540a5f7866d1c114e2",
    "MANIFEST.json": "904dfe13c7483444aecb4a7d2beac1ee0699c4e7779450bf24f4493efcacb9bb",
    "README.md": "9f18d75eb4a18ae118ff917a22b212bd7da8d63a3590f6252eeb516e8ef80e31",
    "assets/abu_character_v1.webm": "a63cfd680f27eae5f8fcbb317231d1a0e15ec37db52b854d9163777f769d2ec7",
    "assets/abu_character_v1_poster.png": "6aa0b95c6b7f325286087eb665c943f2aa49c2d43a0615b64102a3027b128702",
    "assets/energy_flow_mask.png": "f8c1a9f8453f29896cbbd170b48308a2a1f1a84df24badd2b7f2948e465b6e4f",
    "assets/energy_flow_mask.svg": "88926f9b927feb8a1ab09022d6d3302b6d8123150036db3b69a3b6fb190f7061",
    "assets/flower_bud_closed.png": "2e96823d2cb5ed3956db70afcda82800f65e0ba9f6c33a79f3f82c5e00a6b713",
    "assets/flower_open.png": "14a7d4f92b317542dbfb4e2036021b7225c730dafe0ed7aeff8bf3d2270b2f86",
    "assets/foreground_occlusion.png": "8fbce9ff56d7c2a107c3b04df87aa950031a7a8a6547ece9c6addabe6a3b59d2",
    "assets/fruit_white.png": "7619465b06110857dff001edb31b3a00de11326765f8a7fe0d4b7721cac08452",
    "assets/leaf_basic_01.png": "e13b7640c3cbed3be6a185a550e0f4df39df7dedc37dbc5468d0c1b93a9288b8",
    "assets/leaf_basic_02.png": "f13312a1b25fd117208ea0cb67c932ed2af9b68d7f8a53cee7a218690a3837f8",
    "assets/tree_base_clean.png": "dfd661d7e1b171a77afdf75224c453de2d7984ddfe2531df06f2ae11dd187be9",
    "assets/trunk_backbone_01.png": "cc594091d7ae29c91b54813817570d9aac2c49c531447e7d717604f7eb450837",
    "masks/flower_bud_closed_hit_mask.png": "8516603bde01a8d5fa44bb617e595adefe1615648bcd74d953527cc4228b8f60",
    "masks/flower_open_hit_mask.png": "2dbce319ffd6be5686bf10f1f10218de8a505aebd60883124df2a820f96e6451",
    "masks/fruit_white_hit_mask.png": "fe31f0057077864452b5b982a1e8a7aef9c5dc67eb5fdc97d65a6b7931318c11",
    "masks/leaf_basic_01_hit_mask.png": "10f6d4c0dde6aafd99b972592aa2a097f6abfc7785830da1c8f03c827bc6be8d",
    "masks/leaf_basic_02_hit_mask.png": "542b76f1190afc0c841e1be3e435a3f2789d479cfbc7e0b558deaad99e38ebc4",
    "masks/trunk_backbone_01_hit_mask.png": "72abef1ed2321e5f10228eb30e9e19fe9f4539188cbe4efae08256a296147b53",
    "previews/semantic_tree_desktop_three_states.png": "8bce863a6a11821b5d8f5299b6049132edb5b25fbd8bb24523bf314756d447f7",
    "previews/semantic_tree_mobile_stage2.png": "ecc8a0b40a063e6068b7576957093c6f242efaa9a1ec97ee5bc78bf432beceb8",
    "previews/semantic_tree_organ_contact_sheet.png": "5aabfc5a74ca7cd78aec58111edf8efd4219417d3cdae3779722d4518aaa55c7",
  },
} as const;

export function semanticTreeOrganStyle(
  layoutKey: keyof typeof SEMANTIC_TREE_SCENE_BUNDLE.layouts,
): string {
  const selected = SEMANTIC_TREE_SCENE_BUNDLE.layouts[layoutKey];
  return [
    anchorStyle("desktop", selected.desktop, 1440, 900),
    anchorStyle("mobile", selected.mobile, 390, 844),
  ].join(";");
}

function asset(
  path: string,
  sha256: string,
  width: number,
  height: number,
  alpha: boolean,
  hitMaskPath?: string,
  hitMaskSha256?: string,
): SemanticTreeAssetRef {
  return {
    source: `${ROOT}/${path}`,
    sha256,
    width,
    height,
    alpha,
    ...(hitMaskPath ? { hitMask: `${ROOT}/${hitMaskPath}` } : {}),
    ...(hitMaskSha256 ? { hitMaskSha256 } : {}),
  };
}

function layout(
  desktop: SemanticTreeAnchor,
  mobile: SemanticTreeAnchor,
): SemanticTreeOrganLayout {
  return { desktop, mobile };
}

function anchorStyle(
  profile: "desktop" | "mobile",
  anchor: SemanticTreeAnchor,
  viewportWidth: number,
  viewportHeight: number,
): string {
  const values = [
    `--semantic-${profile}-left:${percentage(anchor.x, viewportWidth)}`,
    `--semantic-${profile}-top:${percentage(anchor.y, viewportHeight)}`,
  ];
  if (anchor.displayWidth) {
    values.push(`--semantic-${profile}-width:${percentage(anchor.displayWidth, viewportWidth)}`);
  }
  if (anchor.displayHeight) {
    values.push(`--semantic-${profile}-height:${percentage(anchor.displayHeight, viewportHeight)}`);
  }
  return values.join(";");
}

function percentage(value: number, total: number): string {
  return `${((value / total) * 100).toFixed(5)}%`;
}
