export const SHARED_BASE = "/experience-static/prototypes/s0-shared";

const REQUIRED_RELATIONS = new Set([
  "relation-yi-generates-ding",
  "relation-ding-acts-on-metal",
  "relation-luck-geng-controls-yi",
  "relation-year-bing-supports-ding",
]);

const REQUIRED_PATH = "path-committed-output-pressure";

export async function loadApprovedScene() {
  const [manifestResponse, sourceResponse, narrationResponse] = await Promise.all([
    fetch(`${SHARED_BASE}/manifest.json`, { cache: "no-store" }),
    fetch(`${SHARED_BASE}/scene-source.json`, { cache: "no-store" }),
    fetch(`${SHARED_BASE}/narration.json`, { cache: "no-store" }),
  ]);
  if (!manifestResponse.ok || !sourceResponse.ok || !narrationResponse.ok) {
    throw new Error("s0_shared_source_unavailable");
  }
  const manifest = await manifestResponse.json();
  const source = await sourceResponse.json();
  const narration = await narrationResponse.json();
  validateApprovedScene(manifest, source);
  return { manifest, source, narration };
}

function validateApprovedScene(manifest, source) {
  if (manifest.manifest_status !== "LOCKED_FOR_INTERNAL_G2") {
    throw new Error("s0_manifest_not_locked");
  }
  if (manifest.source_mode !== "approved_anonymous_teaching_fixture") {
    throw new Error("s0_manifest_source_mode_invalid");
  }
  if (source.source_mode !== manifest.source_mode) {
    throw new Error("s0_source_mode_mismatch");
  }
  if (source.approved_natal_path.path_ref !== REQUIRED_PATH) {
    throw new Error("s0_path_ref_mismatch");
  }
  const manifestRelations = new Set(manifest.approved_relation_refs || []);
  if (manifestRelations.size !== REQUIRED_RELATIONS.size) {
    throw new Error("s0_relation_count_mismatch");
  }
  for (const relationRef of REQUIRED_RELATIONS) {
    if (!manifestRelations.has(relationRef)) throw new Error(`s0_relation_missing:${relationRef}`);
  }
  if (manifest.s0_g2_authorized !== true || manifest.s0_g3_authorized !== false) {
    throw new Error("s0_gate_mismatch");
  }
}

export function approvedStage(source, stageId) {
  if (stageId === "original") {
    return {
      id: "original",
      label: "原局",
      shortLabel: source.presentation_copy.original,
      pathState: "active",
      pathRef: source.approved_natal_path.path_ref,
      relationRefs: source.approved_natal_path.relation_refs,
      explanation: "乙木生丁火，丁火进一步作用于金结构。",
      temporalRef: null,
    };
  }
  const target = stageId === "luck" ? "snapshot-luck-gengzi-v1" : "snapshot-year-bingwu-v1";
  const stage = source.approved_temporal_stages.find((item) => item.temporal_ref === target);
  if (!stage) throw new Error(`s0_stage_missing:${stageId}`);
  return {
    id: stageId,
    label: stage.pillar,
    shortLabel: source.presentation_copy[stageId],
    pathState: stage.approved_discrete_change,
    pathRef: stage.path_ref,
    relationRefs: stage.approved_relation_refs,
    explanation: stage.approved_explanation,
    temporalRef: stage.temporal_ref,
    affectedObjectRefs: stage.affected_object_refs,
  };
}

export function scenePillars(source) {
  const natal = source.chart.semantic_slots.map((slot) => ({
    slotRef: slot.slot_ref,
    label: slot.label,
    pillar: slot.pillar,
    temporal: false,
  }));
  const temporal = source.approved_temporal_stages.map((stage, index) => ({
    slotRef: stage.pillar_slot_ref,
    label: index === 0 ? "大运" : "流年",
    pillar: stage.pillar,
    temporal: true,
  }));
  return [...natal, ...temporal];
}

export const ELEMENT_META = {
  甲: { element: "wood", polarity: "yang" },
  乙: { element: "wood", polarity: "yin" },
  丙: { element: "fire", polarity: "yang" },
  丁: { element: "fire", polarity: "yin" },
  戊: { element: "earth", polarity: "yang" },
  己: { element: "earth", polarity: "yin" },
  庚: { element: "metal", polarity: "yang" },
  辛: { element: "metal", polarity: "yin" },
  壬: { element: "water", polarity: "yang" },
  癸: { element: "water", polarity: "yin" },
  子: { element: "water", polarity: "yang" },
  丑: { element: "earth", polarity: "yin" },
  寅: { element: "wood", polarity: "yang" },
  卯: { element: "wood", polarity: "yin" },
  辰: { element: "earth", polarity: "yang" },
  巳: { element: "fire", polarity: "yin" },
  午: { element: "fire", polarity: "yang" },
  未: { element: "earth", polarity: "yin" },
  申: { element: "metal", polarity: "yang" },
  酉: { element: "metal", polarity: "yin" },
  戌: { element: "earth", polarity: "yang" },
  亥: { element: "water", polarity: "yin" },
};
