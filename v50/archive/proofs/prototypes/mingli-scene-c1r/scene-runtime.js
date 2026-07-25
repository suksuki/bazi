export const RENDER_PROFILES = Object.freeze(["lab", "xiangfa", "theater"]);

const MOTIFS = Object.freeze({
  wood: { motif: "木影", bindingType: "tradition_supported", explanation: "以生长的木影表现木性节点。" },
  fire: { motif: "灯火", bindingType: "tradition_supported", explanation: "以灯火表现火性节点，不增加事件判断。" },
  earth: { motif: "山台", bindingType: "tradition_supported", explanation: "以山台表现土性节点及承载关系。" },
  metal: { motif: "金石", bindingType: "tradition_supported", explanation: "以金石表现金性节点及其结构位置。" },
  water: { motif: "水路", bindingType: "tradition_supported", explanation: "以水路表现水性节点及其传递关系。" },
});

const SLOT_LABELS = Object.freeze({
  year_stem: "年干", year_branch: "年支",
  month_stem: "月干", month_branch: "月支",
  day_stem: "日干", day_branch: "日支",
  hour_stem: "时干", hour_branch: "时支",
});

export function compileSceneState(fixture, input) {
  assertFixture(fixture);
  const variant = fixture.variants[input.variantIndex];
  const year = fixture.year_dial[input.yearIndex];
  if (!variant || !year) throw new Error("scene_state_input_out_of_range");

  const visualObjects = variant.nodes.map((node) => visualNode(node));
  visualObjects.push(temporalObject(
    "luck",
    fixture.formal.luck_pillar,
    "official",
    "source:formal:luck-pillar",
  ));
  visualObjects.push(temporalObject(
    "year",
    year.pillar,
    year.source_mode,
    year.source_mode === "official"
      ? "source:formal:annual-pillar"
      : `source:sandbox:year-dial:${year.year}`,
  ));

  const formalPath = compileFormalReference(fixture.formal.path, variant);
  const candidatePath = compileCandidatePath(variant.graph_candidate);
  const draftPath = compileDraftPath(input.draftNodes || [], variant);
  const paths = { formal: formalPath, candidate: candidatePath, draft: draftPath };
  const activePath = paths[input.pathLens] || formalPath;
  const objectRefs = new Set(visualObjects.map((item) => item.semantic_ref));
  const selected = objectRefs.has(input.selectedSemanticRef)
    ? input.selectedSemanticRef
    : activePath.node_refs[0] || visualObjects[0]?.semantic_ref || "";

  return {
    schema_version: "deepbazi.mingli_scene_state.prototype.v1",
    scene_state_id: `scene:${variant.variant_id}:${year.year}`,
    render_profile: RENDER_PROFILES.includes(input.renderProfile) ? input.renderProfile : "lab",
    variant_ref: variant.variant_id,
    source_mode: input.mode === "formal" ? "canonical" : "hypothetical",
    temporal_stage: {
      luck_pillar: fixture.formal.luck_pillar,
      year: year.year,
      year_pillar: year.pillar,
      year_source_mode: year.source_mode,
      formal_temporal_effect_available: year.formal_temporal_effect_available,
    },
    visual_objects: visualObjects,
    active_path: activePath,
    available_paths: paths,
    user_path_draft: draftPath,
    selected_semantic_ref: selected,
    diff_focus: {
      continuity_status: variant.formal_path_reference.continuity_status,
      preserved_segments: variant.formal_path_reference.preserved_segments,
      total_segments: variant.formal_path_reference.total_segments,
      added_relations: variant.diff.added_relations.length,
      removed_relations: variant.diff.removed_relations.length,
      changed_pillars: variant.diff.changed_pillars,
    },
    camera_state: { framing: input.renderProfile === "xiangfa" ? "scene" : "path" },
    metaphor_bindings: visualObjects
      .filter((item) => item.object_type === "stem" || item.object_type === "branch")
      .map((item) => metaphorBinding(item)),
    cues: compileSceneCues(activePath),
    boundaries: fixture.boundaries,
  };
}

export function compileSceneCues(path) {
  const cues = [];
  for (let index = 0; index < path.node_refs.length; index += 1) {
    const semanticRef = path.node_refs[index];
    cues.push({
      cue_id: `cue:${path.path_ref}:focus:${index}`,
      action: "focus",
      semantic_refs: [semanticRef],
      at_step: cues.length,
      label: `聚焦 ${path.node_labels[index]}`,
    });
    const segment = path.segments[index];
    if (!segment) continue;
    cues.push({
      cue_id: `cue:${path.path_ref}:${segment.status}:${index}`,
      action: segment.status === "missing" ? "block_path" : "trace_path",
      semantic_refs: [segment.from_ref, segment.to_ref],
      at_step: cues.length,
      label: segment.status === "missing" ? `在 ${segment.label} 处停止` : segment.label,
    });
    if (segment.status === "missing") break;
  }
  return cues;
}

export function objectByRef(sceneState, semanticRef) {
  return sceneState.visual_objects.find((item) => item.semantic_ref === semanticRef) || null;
}

function visualNode(node) {
  return {
    visual_object_id: `visual:${node.node_key}`,
    semantic_ref: `node:${node.node_key}`,
    object_type: node.node_type,
    slot: node.position,
    slot_label: SLOT_LABELS[node.position] || node.position,
    label: node.label,
    element: node.element,
    polarity: node.polarity,
    ten_god: node.ten_god,
    hidden_stems: node.hidden_stems || [],
    epistemic_status: "canonical",
    source_refs: node.source_refs || [],
    interaction_capabilities: ["select", "inspect", "draft_path"],
    disclosure_profile: "member",
  };
}

function temporalObject(kind, pillar, sourceMode, sourceRef) {
  return {
    visual_object_id: `visual:temporal:${kind}`,
    semantic_ref: `temporal:${kind}`,
    object_type: "temporal_signal",
    slot: kind,
    slot_label: kind === "luck" ? "大运" : "流年",
    label: pillar,
    element: "temporal",
    polarity: "mixed",
    epistemic_status: sourceMode === "official" ? "canonical" : "hypothetical",
    source_refs: [sourceRef],
    interaction_capabilities: ["select", "inspect"],
    disclosure_profile: "member",
  };
}

function compileFormalReference(formalPath, variant) {
  const orderedAnchors = formalPath.ordered_nodes.map((item) => item.anchor);
  const nodes = orderedAnchors.map((anchor) => variant.nodes.find((item) => item.node_key === anchor));
  const continuity = variant.formal_path_reference.segments;
  const segments = [];
  for (let index = 0; index < orderedAnchors.length - 1; index += 1) {
    const fromAnchor = orderedAnchors[index];
    const toAnchor = orderedAnchors[index + 1];
    const item = continuity.find((candidate) => {
      const base = candidate.baseline;
      return base.from_anchor === fromAnchor && base.to_anchor === toAnchor;
    });
    const replacement = item?.variant_relation || null;
    const baselineLabel = item?.baseline?.relation_label || "原关系";
    segments.push({
      semantic_ref: `relation:${fromAnchor}:${item?.baseline?.relation_type || "unknown"}:${toAnchor}`,
      from_ref: `node:${fromAnchor}`,
      to_ref: `node:${toAnchor}`,
      label: item?.status === "preserved"
        ? replacement?.label || baselineLabel
        : `原关系「${baselineLabel}」未保留`,
      relation_type: item?.baseline?.relation_type || "unknown",
      status: item?.status || "missing",
      epistemic_status: item?.status === "preserved" ? "derived" : "blocked",
      source_refs: replacement?.source_refs || [],
    });
  }
  return {
    path_ref: formalPath.path_ref,
    label: "LifeCase 正式路径参考",
    authority: "committed_reference",
    epistemic_status: "committed",
    continuity_status: variant.formal_path_reference.continuity_status,
    node_refs: orderedAnchors.map((item) => `node:${item}`),
    node_labels: nodes.map((item) => item?.label || "?"),
    segments,
  };
}

function compileCandidatePath(candidate) {
  return {
    path_ref: candidate.path_ref,
    label: "Graph 结构候选",
    authority: candidate.authority,
    epistemic_status: "candidate",
    continuity_status: "candidate",
    node_refs: candidate.node_keys.map((item) => `node:${item}`),
    node_labels: candidate.node_labels,
    segments: candidate.segments.map((item) => ({
      semantic_ref: `relation:${item.from_anchor}:${item.relation_type}:${item.to_anchor}`,
      from_ref: `node:${item.from_anchor}`,
      to_ref: `node:${item.to_anchor}`,
      label: item.label,
      relation_type: item.relation_type,
      status: "candidate",
      epistemic_status: "candidate",
      source_refs: item.source_refs || [],
    })),
  };
}

function compileDraftPath(nodeKeys, variant) {
  const nodeMap = new Map(variant.nodes.map((item) => [item.node_key, item]));
  const relations = variant.relations || [];
  const segments = [];
  for (let index = 0; index < nodeKeys.length - 1; index += 1) {
    const fromKey = nodeKeys[index];
    const toKey = nodeKeys[index + 1];
    const exact = relations.find((item) => item.from_key === fromKey && item.to_key === toKey);
    const reverse = relations.find((item) => item.from_key === toKey && item.to_key === fromKey);
    const relation = exact || reverse || null;
    segments.push({
      semantic_ref: `draft-relation:${fromKey}:${toKey}`,
      from_ref: `node:${fromKey}`,
      to_ref: `node:${toKey}`,
      label: exact?.label || (reverse ? `方向相反：${reverse.label}` : "此处没有可用关系"),
      relation_type: relation?.relation_type || "missing",
      status: exact ? "draft_available" : reverse ? "draft_reverse" : "missing",
      epistemic_status: "user_draft",
      source_refs: relation?.source_refs || [],
    });
  }
  return {
    path_ref: "path:user-draft",
    label: "用户路径草稿",
    authority: "user_draft",
    epistemic_status: "user_draft",
    continuity_status: segments.some((item) => item.status === "missing") ? "open" : nodeKeys.length > 1 ? "complete" : "empty",
    node_refs: nodeKeys.map((item) => `node:${item}`),
    node_labels: nodeKeys.map((item) => nodeMap.get(item)?.label || "?"),
    segments,
  };
}

function metaphorBinding(item) {
  const motif = MOTIFS[item.element] || {
    motif: "结构标记",
    bindingType: "illustrative_only",
    explanation: "用于保持对象在象法场景中的可追踪性。",
  };
  return {
    semantic_ref: item.semantic_ref,
    motif: motif.motif,
    binding_type: motif.bindingType,
    visual_asset_ref: `motif:${item.element}`,
    mapping_explanation: motif.explanation,
    source_ref: `metaphor-binding:five-element:${item.element}:v1`,
    author: "deepbazi_curated",
    disclosure_level: item.disclosure_profile,
  };
}

function assertFixture(fixture) {
  if (!fixture?.variants?.length || !fixture?.formal?.path) {
    throw new Error("mingli_scene_fixture_invalid");
  }
}
