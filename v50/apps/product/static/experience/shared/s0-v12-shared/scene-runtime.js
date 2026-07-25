const MODULE_BASE = new URL("./", import.meta.url);

export const SHARED_BASE = MODULE_BASE.href.replace(/\/$/, "");

const REQUIRED_PATH = "path-observed-jia-ding-geng";
const REQUIRED_RELATIONS = new Set([
  "relation-jia-generates-ding",
  "relation-ding-controls-geng",
  "relation-year-chen-clashes-day-xu",
  "relation-hour-chen-clashes-day-xu",
  "relation-luck-geng-controls-jia",
  "relation-luck-yin-roots-jia",
  "relation-year-bing-supports-ding",
]);

export async function loadScene() {
  const [manifestResponse, sourceResponse, narrationResponse] = await Promise.all([
    fetch(new URL("manifest.json", MODULE_BASE), {cache: "no-store"}),
    fetch(new URL("scene-source.json", MODULE_BASE), {cache: "no-store"}),
    fetch(new URL("narration.json", MODULE_BASE), {cache: "no-store"}),
  ]);
  if (!manifestResponse.ok || !sourceResponse.ok || !narrationResponse.ok) {
    throw new Error("s0_v11_scene_source_unavailable");
  }
  const manifest = await manifestResponse.json();
  const source = await sourceResponse.json();
  const narration = await narrationResponse.json();
  validateScene(manifest, source);
  return {manifest, source, narration};
}

function validateScene(manifest, source) {
  if (manifest.manifest_status !== "INTERNAL_CREATIVE_PROTOTYPE") throw new Error("s0_v11_manifest_status_invalid");
  if (manifest.identity_disclosed_to_client !== false) throw new Error("s0_v11_identity_boundary_invalid");
  if (source.source_mode !== manifest.source_mode) throw new Error("s0_v11_source_mode_mismatch");
  if (source.observed_natal_path.path_ref !== REQUIRED_PATH) throw new Error("s0_v11_path_ref_mismatch");
  const allowed = new Set(manifest.allowed_relation_refs || []);
  for (const ref of REQUIRED_RELATIONS) if (!allowed.has(ref)) throw new Error(`s0_v11_relation_missing:${ref}`);
  const serialized = JSON.stringify(source);
  for (const forbiddenKey of ["public_figure_name", "birth_date", "birth_time", "birth_location", "reality_feedback"]) {
    if (serialized.includes(`\"${forbiddenKey}\"`)) throw new Error(`s0_v11_identity_field_present:${forbiddenKey}`);
  }
}

export function stageFor(source, stageId) {
  if (stageId === "original") {
    return {
      id: "original",
      label: "原局",
      shortLabel: source.presentation_copy.original,
      pathRef: source.observed_natal_path.path_ref,
      explanation: source.observed_natal_path.professional_expression,
      relationRefs: source.observed_natal_path.relation_refs,
    };
  }
  const index = stageId === "luck" ? 0 : 1;
  const stage = source.temporal_stages[index];
  if (!stage) throw new Error(`s0_v11_stage_missing:${stageId}`);
  return {
    id: stageId,
    label: stage.pillar,
    shortLabel: source.presentation_copy[stageId],
    pathRef: stage.path_ref,
    explanation: stage.explanation,
    relationRefs: stage.relation_refs,
    discreteChange: stage.discrete_change,
  };
}

export function scenePillars(source) {
  const natal = source.chart.semantic_slots.map((slot) => ({...slot, temporal: false}));
  const temporal = source.temporal_stages.map((stage, index) => ({
    slot_ref: stage.pillar_slot_ref,
    label: index === 0 ? "大运" : "流年",
    pillar: stage.pillar,
    temporal: true,
  }));
  return [...natal, ...temporal];
}

export const ELEMENT_META = {
  甲:{element:"wood",polarity:"yang"},乙:{element:"wood",polarity:"yin"},
  丙:{element:"fire",polarity:"yang"},丁:{element:"fire",polarity:"yin"},
  戊:{element:"earth",polarity:"yang"},己:{element:"earth",polarity:"yin"},
  庚:{element:"metal",polarity:"yang"},辛:{element:"metal",polarity:"yin"},
  壬:{element:"water",polarity:"yang"},癸:{element:"water",polarity:"yin"},
  子:{element:"water",polarity:"yang"},丑:{element:"earth",polarity:"yin"},
  寅:{element:"wood",polarity:"yang"},卯:{element:"wood",polarity:"yin"},
  辰:{element:"earth",polarity:"yang"},巳:{element:"fire",polarity:"yin"},
  午:{element:"fire",polarity:"yang"},未:{element:"earth",polarity:"yin"},
  申:{element:"metal",polarity:"yang"},酉:{element:"metal",polarity:"yin"},
  戌:{element:"earth",polarity:"yang"},亥:{element:"water",polarity:"yin"},
};
