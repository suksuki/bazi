export const SLOT_ORDER = ["year", "month", "day", "hour", "luck", "annual"];

export const SLOT_LABELS = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
  luck: "大运",
  annual: "流年",
};

export const GENDER_LABELS = Object.freeze({
  male: "乾造",
  female: "坤造",
  unknown: "命造未定",
});

export const ELEMENT_LABELS = {
  wood: "木",
  fire: "火",
  earth: "土",
  metal: "金",
  water: "水",
};

export const TEN_GOD_LABELS = {
  day_master: "日主",
  bi_jian: "比肩",
  jie_cai: "劫财",
  shi_shen: "食神",
  shang_guan: "伤官",
  pian_cai: "偏财",
  zheng_cai: "正财",
  qi_sha: "七杀",
  zheng_guan: "正官",
  pian_yin: "偏印",
  zheng_yin: "正印",
};

export const RELATION_LABELS = {
  generates: "相生",
  controls: "相克",
  same_element_support: "同气",
  stores: "藏干",
  roots: "通根",
  forms_half_combination: "半合",
  forms_triple_combination: "三合",
  clashes: "相冲",
  harmonizes: "相合",
  activates: "引动",
  bridges: "通关",
  position_link: "同柱",
};

export const RECOMPUTE_LABELS = Object.freeze({
  recalculating: Object.freeze({
    tone: "pending",
    title: "正在重新排盘与重算大运",
  }),
  recalculated_changed: Object.freeze({
    tone: "changed",
    title: "已重算，大运发生变化",
  }),
  recalculated_unchanged: Object.freeze({
    tone: "unchanged",
    title: "已重算，大运没有变化",
  }),
  recalculation_unavailable: Object.freeze({
    tone: "unavailable",
    title: "当前输入不足，无法可靠重算",
  }),
});

export function recomputeViewModel(timing = {}) {
  const status = RECOMPUTE_LABELS[timing.status]
    ? timing.status
    : "recalculation_unavailable";
  const definition = RECOMPUTE_LABELS[status];
  const reference = timing.formal_reference || {};
  const changed = status === "recalculated_changed";
  const structuralOnly = timing.exact_timing_status === "unavailable"
    || timing.calculation_mode === "structural_sequence_only";
  const birthYearMismatch = timing.exact_timing_status === "birth_year_no_consistent_match";
  const genderMissing = (timing.missing_inputs || []).includes("gender_required_for_luck_direction")
    || timing.calculation_mode === "gender_required";
  return {
    status,
    tone: definition.tone,
    title: genderMissing
      ? "请选择乾造或坤造"
      : birthYearMismatch
      ? "出生年份与四柱尚未对齐"
      : structuralOnly
      ? `${changed ? "大运序列已改变" : "大运序列保持"}，当前大运待定位`
      : definition.title,
    current_pillar: timing.luck_pillar || "",
    current_year_range: timing.luck_year_range || [],
    reference_pillar: reference.luck_pillar || "",
    reference_year_range: reference.luck_year_range || [],
    missing_inputs: timing.missing_inputs || [],
    detail: genderMissing
      ? "命造未确认时，大运顺逆与序列均不计算"
      : birthYearMismatch
      ? (timing.failure_reason || "请继续调整四柱，系统会实时重新反查")
      : structuralOnly
      ? `${timing.direction === "forward" ? "顺排" : timing.direction === "reverse" ? "逆排" : "顺逆待定"} · 四柱只能确定序列；需真实出生年份、日期或已确认档案才能定位当前大运`
      : status === "recalculation_unavailable"
      ? (timing.failure_reason || (timing.missing_inputs || []).join(" · ") || "缺少可验证的起运输入")
      : status === "recalculating"
        ? (timing.detail || "候选尚未提交，正式盘保持不变")
      : changed
        ? `${reference.luck_pillar || "—"} → ${timing.luck_pillar || "—"}`
        : `${timing.luck_pillar || reference.luck_pillar || "—"} · 结果保持`,
  };
}

export function selectionContextViewModel(candidate = {}) {
  const context = candidate.selection_context || {};
  return {
    disclosure_mode: context.disclosure_mode || "structural_source_not_disclosed",
    primary: context.selected_pillar
      || candidate.display_label
      || "六十甲子候选",
    linked_slot: context.linked_slot || "",
    linked_pillar: context.linked_pillar || "",
    dependency_rule: context.dependency_rule || "",
    maps_to_real_birth_datetime: Boolean(context.maps_to_real_birth_datetime),
    raw_birth_datetime_in_fixture: Boolean(context.raw_birth_datetime_in_fixture),
  };
}

export const MOTIF_BINDINGS = Object.freeze({
  wood: Object.freeze({
    motif: "木影",
    binding_type: "tradition_supported",
    mapping_explanation: "以生长的木影表现木性节点，不增加事件判断。",
    source_ref: "metaphor-binding:five-element:wood:v1",
  }),
  fire: Object.freeze({
    motif: "灯火",
    binding_type: "tradition_supported",
    mapping_explanation: "以灯火表现火性节点，不增加事件判断。",
    source_ref: "metaphor-binding:five-element:fire:v1",
  }),
  earth: Object.freeze({
    motif: "山台",
    binding_type: "tradition_supported",
    mapping_explanation: "以山台表现土性节点及承载关系，不增加事件判断。",
    source_ref: "metaphor-binding:five-element:earth:v1",
  }),
  metal: Object.freeze({
    motif: "金石",
    binding_type: "tradition_supported",
    mapping_explanation: "以金石表现金性节点及结构位置，不增加事件判断。",
    source_ref: "metaphor-binding:five-element:metal:v1",
  }),
  water: Object.freeze({
    motif: "水路",
    binding_type: "tradition_supported",
    mapping_explanation: "以水路表现水性节点及传递关系，不增加事件判断。",
    source_ref: "metaphor-binding:five-element:water:v1",
  }),
});

export function metaphorBindingFor(node) {
  const binding = MOTIF_BINDINGS[node?.element] || Object.freeze({
    motif: "结构标记",
    binding_type: "illustrative_only",
    mapping_explanation: "仅用于保持对象在象法表达中的可追踪性。",
    source_ref: "metaphor-binding:structural-marker:v1",
  });
  return {
    semantic_ref: node?.semantic_ref || `node:${node?.node_key || "unknown"}`,
    visual_asset_ref: `motif:${node?.element || "structural"}`,
    author: "deepbazi_curated",
    disclosure_level: "member",
    ...binding,
  };
}

export function compileOneCanvasCues(path, availability = {}) {
  const luckAvailable = availability.luckAvailable !== false;
  const annualAvailable = availability.annualAvailable !== false;
  const cues = [
    {
      cue_id: "scene:natal",
      action: "show_natal",
      temporal_stage: 0,
      node_keys: [],
      label: "原局先成立，时间节点暂未进入",
    },
    ...(luckAvailable ? [{
      cue_id: "scene:luck",
      action: "enter_luck",
      temporal_stage: 1,
      node_keys: ["luck_stem", "luck_branch"],
      label: "大运进入当前命局",
    }] : []),
    ...(annualAvailable ? [{
      cue_id: "scene:annual",
      action: "enter_annual",
      temporal_stage: 2,
      node_keys: ["annual_stem", "annual_branch"],
      label: "流年作为已披露的时间材料进入",
    }] : []),
  ];
  const nodeKeys = path?.node_keys || [];
  const segments = path?.segments || [];
  for (let index = 0; index < nodeKeys.length; index += 1) {
    cues.push({
      cue_id: `scene:${path?.epistemic_status || "path"}:focus:${index}`,
      action: "focus_node",
      temporal_stage: 2,
      node_keys: [nodeKeys[index]],
      label: `聚焦路径节点 ${index + 1}`,
    });
    const segment = segments[index];
    if (!segment) continue;
    const status = segment.status || (segment.relation_type === "missing" ? "missing" : "available");
    const blocked = status === "missing" || segment.epistemic_status === "blocked";
    cues.push({
      cue_id: `scene:${path?.epistemic_status || "path"}:${blocked ? "block" : "trace"}:${index}`,
      action: blocked ? "block_path" : "trace_path",
      temporal_stage: 2,
      node_keys: [segment.from_key || segment.from_anchor, segment.to_key || segment.to_anchor],
      segment_index: index,
      label: blocked ? "关系缺失，演时在此停止" : segment.label || "路径继续",
    });
    if (blocked) break;
  }
  return cues;
}

export function createOneCanvasModel(fixture) {
  assertFixture(fixture);
  const baseline = fixture.candidate_families.day[fixture.baseline_candidate_index.day];
  const officialYearIndex = Math.max(0, fixture.year_dial.findIndex((item) => item.source_mode === "official"));
  let selectionCatalog = null;

  function setSelectionCatalog(catalog) {
    if (!catalog?.year?.length || !catalog?.day?.length) {
      throw new Error("onecanvas_selection_catalog_invalid");
    }
    const stems = catalog.stems?.length
      ? [...catalog.stems]
      : [...new Set(catalog.year.map((pillar) => pillar[0]))];
    const branches = catalog.branches?.length
      ? [...catalog.branches]
      : [...new Set(catalog.year.map((pillar) => pillar[1]))];
    selectionCatalog = {
      ...catalog,
      stems,
      branches,
      branches_by_stem: catalog.branches_by_stem || Object.fromEntries(
        stems.map((stem) => [stem, catalog.year.filter((pillar) => pillar[0] === stem).map((pillar) => pillar[1])]),
      ),
      stems_by_branch: catalog.stems_by_branch || Object.fromEntries(
        branches.map((branch) => [branch, catalog.year.filter((pillar) => pillar[1] === branch).map((pillar) => pillar[0])]),
      ),
      cycle_year_anchor_by_year_pillar: catalog.cycle_year_anchor_by_year_pillar
        || catalog.birth_year_by_year_pillar
        || {},
      annual_observations: catalog.annual_observations || fixture.year_dial.map((item) => ({
        year: item.year,
        pillar: item.pillar,
      })),
    };
    Object.assign(fixture.r1_contract.slot_capabilities, {
      year: { editable_in_experiment: true, switchable: false, derived: false, independent_cycle_choice: true, option_count: 60 },
      month: { editable_in_experiment: true, switchable: false, derived: false, depends_on: "year", option_count: 12 },
      day: { editable_in_experiment: true, switchable: false, derived: false, independent_cycle_choice: true, option_count: 60 },
      hour: { editable_in_experiment: true, switchable: false, derived: false, depends_on: "day", option_count: 12 },
    });
    Object.assign(fixture.constraint_profiles, {
      year: { locked_slots: ["day"], linked_slots: ["month"], option_count: 60, explanation: "年柱从六十甲子中选择；月柱候选随年干更新。" },
      month: { locked_slots: ["year", "day"], linked_slots: [], option_count: 12, depends_on: "year", explanation: "月柱从当前年干对应的十二个合法整柱中选择。" },
      day: { locked_slots: ["year", "month"], linked_slots: ["hour"], option_count: 60, explanation: "日柱从六十甲子中选择；时柱候选随日干更新。" },
      hour: { locked_slots: ["year", "month", "day"], linked_slots: [], option_count: 12, depends_on: "day", explanation: "时柱从当前日干对应的十二个合法整柱中选择。" },
    });
  }

  if (fixture.selection_catalogs) setSelectionCatalog(fixture.selection_catalogs);

  function formalVariant() {
    return {
      variant_id: "formal",
      source_mode: "canonical",
      pillars: [...fixture.formal.pillars],
      nodes: fixture.formal.nodes,
      relations: fixture.formal.relations,
      graph_candidate: null,
      formal_path_reference: baseline.formal_path_reference,
      diff: {
        changed_pillars: [],
        added_relation_count: 0,
        removed_relation_count: 0,
        added_relations: [],
        removed_relations: [],
      },
      timing_recalculation: fixture.formal.timing_recalculation,
    };
  }

  function variantFor(snapshot) {
    if (!snapshot || snapshot.mode === "formal") return formalVariant();
    if (snapshot.variant) return snapshot.variant;
    const family = fixture.candidate_families[snapshot.axis] || fixture.candidate_families.day;
    const baselineIndex = fixture.baseline_candidate_index[snapshot.axis];
    return family[snapshot.index] || family[Number.isInteger(baselineIndex) ? baselineIndex : 0];
  }

  function nodesFor(snapshot) {
    const variant = variantFor(snapshot);
    const selectedLuck = luckObservationFor(snapshot);
    const replacement = new Map([
      ...(selectedLuck?.nodes || []),
    ].map((node) => [node.node_key, node]));
    const nodes = new Map((variant.nodes || []).map((node) => [node.node_key, node]));
    for (const [key, node] of replacement) nodes.set(key, node);
    return SLOT_ORDER.flatMap((slot) => [`${slot}_stem`, `${slot}_branch`])
      .map((key) => nodes.get(key))
      .filter(Boolean);
  }

  function currentLuckIndex(snapshot) {
    const timing = variantFor(snapshot).timing_recalculation || {};
    const sequence = timing.luck_sequence || [];
    const exact = sequence.findIndex((item) => (
      item.pillar === timing.luck_pillar
      && item.start_year === (timing.luck_year_range || [])[0]
    ));
    return exact >= 0 ? exact : -1;
  }

  function luckObservationFor(snapshot) {
    const timing = variantFor(snapshot).timing_recalculation || {};
    const sequence = timing.luck_sequence || [];
    if (Number.isInteger(snapshot?.luckIndex) && snapshot.luckIndex >= 0) {
      return sequence[snapshot.luckIndex] || null;
    }
    const current = currentLuckIndex(snapshot);
    return current >= 0 ? sequence[current] || null : null;
  }

  function beginPillarEditSession(snapshot, nodeKey, direction) {
    if (!selectionCatalog) throw new Error("onecanvas_selection_catalog_not_loaded");
    const match = /^(year|day)_(stem|branch)$/.exec(nodeKey || "");
    if (!match || ![-1, 1].includes(direction)) {
      throw new Error("onecanvas_pillar_edit_target_invalid");
    }
    const slot = match[1];
    const anchorComponent = match[2];
    const counterpartComponent = anchorComponent === "stem" ? "branch" : "stem";
    const sourcePillar = variantFor(snapshot).pillars[slot === "year" ? 0 : 2];
    const anchorUniverse = anchorComponent === "stem"
      ? selectionCatalog.stems
      : selectionCatalog.branches;
    const anchorValue = cycleValue(
      anchorUniverse,
      sourcePillar[anchorComponent === "stem" ? 0 : 1],
      direction,
    );
    return pillarEditSessionState({
      slot,
      sourcePillar,
      anchorComponent,
      anchorValue,
      counterpartComponent,
      counterpartValue: sourcePillar[counterpartComponent === "stem" ? 0 : 1],
      direction,
    });
  }

  function stepPillarEditSession(session, nodeKey, direction) {
    if (!session || ![-1, 1].includes(direction)) {
      throw new Error("onecanvas_pillar_edit_session_invalid");
    }
    const match = /^(year|day)_(stem|branch)$/.exec(nodeKey || "");
    if (!match || match[1] !== session.slot) {
      throw new Error("onecanvas_pillar_edit_target_mismatch");
    }
    const component = match[2];
    if (component === session.anchorComponent) {
      const anchorUniverse = component === "stem"
        ? selectionCatalog.stems
        : selectionCatalog.branches;
      return pillarEditSessionState({
        ...session,
        anchorValue: cycleValue(anchorUniverse, session.anchorValue, direction),
        direction,
      });
    }
    const counterpartValue = cycleValue(
      session.legalCounterparts,
      session.counterpartValue,
      direction,
    );
    return pillarEditSessionState({ ...session, counterpartValue, direction });
  }

  function pillarEditSessionState(value) {
    const legalCounterparts = value.anchorComponent === "stem"
      ? selectionCatalog.branches_by_stem[value.anchorValue] || []
      : selectionCatalog.stems_by_branch[value.anchorValue] || [];
    const counterpartValue = legalCounterparts.includes(value.counterpartValue)
      ? value.counterpartValue
      : nearestLegalCounterpart(value.counterpartValue, legalCounterparts, value.direction);
    const stem = value.anchorComponent === "stem" ? value.anchorValue : counterpartValue;
    const branch = value.anchorComponent === "branch" ? value.anchorValue : counterpartValue;
    const pillar = `${stem}${branch}`;
    if (!(selectionCatalog.year || []).includes(pillar)) {
      throw new Error("onecanvas_pillar_edit_not_in_server_catalog");
    }
    return {
      ...value,
      counterpartComponent: value.anchorComponent === "stem" ? "branch" : "stem",
      counterpartValue,
      legalCounterparts: [...legalCounterparts],
      previewPillar: pillar,
      complete: true,
    };
  }

  function nearestLegalCounterpart(current, legal, direction) {
    const universe = selectionCatalog.branches.includes(current)
      ? selectionCatalog.branches
      : selectionCatalog.stems;
    if (!universe.length || !legal.length) return legal[0] || "";
    let index = universe.indexOf(current);
    for (let offset = 0; offset < universe.length; offset += 1) {
      index = (index + direction + universe.length) % universe.length;
      if (legal.includes(universe[index])) return universe[index];
    }
    return legal[0];
  }

  function cycleValue(values, current, direction) {
    if (!values?.length) throw new Error("onecanvas_candidate_set_empty");
    const index = Math.max(0, values.indexOf(current));
    return values[(index + direction + values.length) % values.length];
  }

  function dependentPillarOptions(slot, snapshot) {
    const pillars = variantFor(snapshot).pillars;
    if (slot === "month") return selectionCatalog.month_by_year?.[pillars[0]] || [];
    if (slot === "hour") return selectionCatalog.hour_by_day?.[pillars[2]] || [];
    return [];
  }

  function cycleYearChoicesForPillar(pillar, analysisYear) {
    if (!selectionCatalog?.cycle_year_anchor_by_year_pillar || !pillar) return [];
    return [...(selectionCatalog.cycle_year_anchor_by_year_pillar[pillar] || [])]
      .filter((year) => Number.isInteger(year) && year <= analysisYear)
      .sort((left, right) => right - left);
  }

  function annualObservations() {
    return [...(selectionCatalog?.annual_observations || [])];
  }

  function targetCompileRequest(selectedPillars, snapshot, overrides = {}) {
    const gender = overrides.gender || snapshot.gender || "unknown";
    if (!Object.hasOwn(GENDER_LABELS, gender)) {
      throw new Error("onecanvas_gender_invalid");
    }
    const request = {
      target_draft_id: overrides.targetDraftId || `target:${Date.now()}`,
      baseline_pillars: [...fixture.formal.pillars],
      baseline_relations: fixture.formal.relations,
      formal_path: fixture.formal.path,
      baseline_timing: fixture.formal.timing_recalculation,
      analysis_year: Number.isInteger(overrides.analysisYear)
        ? overrides.analysisYear
        : Number.isInteger(snapshot.analysisYear)
          ? snapshot.analysisYear
          : fixture.formal.analysis_year,
      gender,
      cycle_year_anchor: Number.isInteger(overrides.cycleYearAnchor)
        ? overrides.cycleYearAnchor
        : Number.isInteger(snapshot.birthYearHint)
          ? snapshot.birthYearHint
          : null,
    };
    if (overrides.targetDraft) {
      request.target_draft = targetDraftInput(overrides.targetDraft);
    } else {
      if (!Array.isArray(selectedPillars) || selectedPillars.length !== 4) {
        throw new Error("onecanvas_complete_target_required");
      }
      request.desired = {
        year: selectedPillars[0],
        month: selectedPillars[1],
        day: selectedPillars[2],
        hour: selectedPillars[3],
      };
    }
    if (overrides.selectedVariantId) request.selected_variant_id = overrides.selectedVariantId;
    return request;
  }

  function targetDraftInput(value = {}) {
    return Object.fromEntries(["year", "month", "day", "hour"].map((slot) => {
      const constraint = value[slot] || {};
      return [slot, {
        pillar: String(constraint.pillar || ""),
        stem: String(constraint.stem || ""),
        branch: String(constraint.branch || ""),
      }];
    }));
  }

  function pathFor(snapshot) {
    if (!snapshot || snapshot.mode === "formal") {
      return {
        authority: "committed_life_case",
        epistemic_status: "committed",
        warning: "LifeCase 已提交主路径",
        node_keys: fixture.formal.path.ordered_nodes.map((item) => item.anchor),
        segments: fixture.formal.path.segments.map((item) => ({
          ...item,
          from_key: item.from_anchor,
          to_key: item.to_anchor,
          label: item.relation_label,
        })),
      };
    }
    const candidate = variantFor(snapshot).graph_candidate;
    return candidate || {
      authority: "experimental_graph_candidate",
      epistemic_status: "candidate",
      warning: "当前实验没有可闭合的 Graph 候选路径",
      node_keys: [],
      segments: [],
    };
  }

  function relationBetween(snapshot, fromKey, toKey) {
    const relations = variantFor(snapshot).relations;
    const direct = relations.find((item) => item.from_key === fromKey && item.to_key === toKey);
    if (direct) return { status: "available", direction: "direct", relation: direct };
    const reverse = relations.find((item) => item.from_key === toKey && item.to_key === fromKey);
    if (reverse) return { status: "reverse", direction: "reverse", relation: reverse };
    return { status: "missing", direction: "none", relation: null };
  }

  function draftSegments(snapshot, keys) {
    return keys.slice(0, -1).map((key, index) => ({
      from_key: key,
      to_key: keys[index + 1],
      ...relationBetween(snapshot, key, keys[index + 1]),
    }));
  }

  function changedNodeKeys(a, b) {
    const left = new Map(nodesFor(a).map((node) => [node.node_key, node.label]));
    const right = new Map(nodesFor(b).map((node) => [node.node_key, node.label]));
    return SLOT_ORDER.flatMap((slot) => [`${slot}_stem`, `${slot}_branch`])
      .filter((key) => left.get(key) !== right.get(key));
  }

  return {
    fixture,
    officialYearIndex,
    formalVariant,
    variantFor,
    nodesFor,
    pathFor,
    relationBetween,
    draftSegments,
    changedNodeKeys,
    currentLuckIndex,
    luckObservationFor,
    beginPillarEditSession,
    stepPillarEditSession,
    dependentPillarOptions,
    cycleYearChoicesForPillar,
    annualObservations,
    setSelectionCatalog,
    targetCompileRequest,
  };
}

export function cloneSnapshot(snapshot) {
  return {
    mode: snapshot.mode,
    axis: snapshot.axis,
    index: snapshot.index,
    variant: snapshot.variant || null,
    yearIndex: snapshot.yearIndex,
    analysisYear: Number.isInteger(snapshot.analysisYear) ? snapshot.analysisYear : null,
    luckIndex: Number.isInteger(snapshot.luckIndex) ? snapshot.luckIndex : null,
    gender: snapshot.gender || "unknown",
    birthYearHint: Number.isInteger(snapshot.birthYearHint) ? snapshot.birthYearHint : null,
    targetDraftId: snapshot.targetDraftId || "",
    constraintResolution: snapshot.constraintResolution || null,
    draftNodes: [...(snapshot.draftNodes || [])],
  };
}

function samePillars(a, b) {
  return Array.isArray(a) && Array.isArray(b) && a.length === b.length && a.every((item, index) => item === b[index]);
}

function assertFixture(fixture) {
  if (!fixture || fixture.schema_version !== "deepbazi.mingli_onecanvas_c2ar_fixture.v1") {
    throw new Error("onecanvas_fixture_schema_invalid");
  }
  const gender = fixture.structural_context?.gender || "unknown";
  const expectedNodeCount = gender === "unknown" ? 10 : 12;
  if ((fixture.formal.nodes || []).length !== expectedNodeCount) {
    throw new Error(`onecanvas_requires_${expectedNodeCount}_nodes_for_${gender}`);
  }
  if (gender === "unknown" && (fixture.formal.nodes || []).some((node) => node.node_key?.startsWith("luck_"))) {
    throw new Error("onecanvas_unknown_gender_must_not_disclose_luck_nodes");
  }
  if (fixture.r1_contract?.selection_mode !== "sexagenary_cycle_structural") {
    throw new Error("onecanvas_r1_pillar_dependency_authority_missing");
  }
  if (fixture.source.contains_personal_identity || fixture.source.contains_raw_birth_datetime) {
    throw new Error("onecanvas_fixture_privacy_boundary_failed");
  }
}
