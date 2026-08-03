import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = (...parts) => path.resolve(here, "../src", ...parts);
const read = (...parts) => readFile(source(...parts), "utf8");
const failures = [];
const expect = (condition, message) => {
  if (!condition) failures.push(message);
};
const occurrences = (value, pattern) => value.match(pattern)?.length ?? 0;

const [
  api,
  navigation,
  experienceNavigation,
  workspace,
  scene,
  sceneFeedback,
  toolbar,
  inspector,
  suiteApi,
  suiteSelection,
  suiteSummary,
  suiteValidation,
  stageValidation,
  syntheticValidation,
  overview,
  catalogScene,
  researchProjection,
  homeScene,
  homeCompanion,
] = await Promise.all([
  read("mingliSyntheticLabApi.ts"),
  read("mingliSyntheticLabNavigation.ts"),
  read("experienceNavigation.ts"),
  read("components", "MingliLabWorkspaceHost.tsx"),
  read("components", "MingliSyntheticExperimentScene.tsx"),
  read("components", "MingliSyntheticExperimentFeedback.tsx"),
  read("components", "MingliSyntheticExperimentToolbar.tsx"),
  read("components", "MingliSyntheticExperimentInspector.tsx"),
  read("mingliSyntheticSuiteApi.ts"),
  read("mingliSyntheticSuiteSelection.ts"),
  read("components", "MingliSyntheticSuiteSummary.tsx"),
  read("mingliSyntheticSuiteValidation.ts"),
  read("mingliStageValidation.ts"),
  read("mingliSyntheticLabValidation.ts"),
  read("components", "MingliResearchOverview.tsx"),
  read("components", "MingliSyntheticCatalogScene.tsx"),
  read("mingliResearchProjection.ts"),
  read("components", "HomeLifeTreeScene.tsx"),
  read("components", "HomeSceneCompanion.tsx"),
]);
const ordinarySubjectValidator =
  stageValidation.match(/function isStageSubjectId[\s\S]*?\n}/)?.[0] ?? "";
const sceneSurface = `${scene}\n${sceneFeedback}`;
const { compareWithPreviousSyntheticSuiteRun } = await import(
  source("mingliSyntheticSuiteSelection.ts")
);

expect(
  occurrences(api, /request<unknown>/g) === 2 &&
    !/method:\s*["']POST/.test(api) &&
    !/generateMingliAgentReading|agent-reading/.test(api),
  "synthetic-api:browser-must-only-read-two-get-endpoints",
);
expect(
  occurrences(suiteApi, /request<unknown>/g) === 1 &&
    suiteApi.includes("synthetic-suite-runs/${encodeURIComponent(suiteRunRef)}") &&
    !/method:\s*["']POST/.test(suiteApi),
  "synthetic-suite-api:catalog-and-exact-run-must-remain-read-only",
);
expect(
  navigation.includes('modeValue === "synthetic"') &&
    navigation.includes('modeValue === "catalog"') &&
    navigation.includes('modeValue === "current"') &&
    navigation.includes('modeValue === "narration"') &&
    navigation.includes(': "overview"') &&
    navigation.includes('parameters.get("lab_suite")') &&
    navigation.includes('url.searchParams.set("lab_variant"') &&
    navigation.includes('setOptional(url, "lab_suite"') &&
    navigation.includes('setOptional(url, "lab_experiment"') &&
    navigation.includes('setOptional(url, "lab_run"'),
  "synthetic-navigation:route-must-restore-mode-run-and-variant",
);
expect(
  ["lab_mode", "lab_suite", "lab_experiment", "lab_run", "lab_variant"].every((key) =>
    experienceNavigation.includes(`url.searchParams.delete("${key}")`),
  ),
  "experience-navigation:must-clear-synthetic-route-outside-lab",
);
expect(
  workspace.includes('route.mode === "overview"') &&
    workspace.includes('route.mode === "catalog"') &&
    workspace.includes('route.mode === "synthetic"') &&
    workspace.includes('mode: "NATAL_DAYUN_YEAR_6"') &&
    workspace.includes('autoOpenNarration={route.mode === "narration"}') &&
    occurrences(workspace, /<MingliSyntheticExperimentScene/g) === 1 &&
    occurrences(workspace, /<MingliSceneHost/g) === 1 &&
    occurrences(workspace, /<MingliResearchOverview/g) === 1 &&
    occurrences(workspace, /<MingliSyntheticCatalogScene/g) === 1,
  "synthetic-workspace:overview-catalog-current-and-replay-modes-must-be-exclusive",
);
expect(
  overview.includes("把命理变成可以观察、比较和验证的东西") &&
    overview.includes("这里研究方法，不存放案例") &&
    overview.includes("八字合成验证") &&
    overview.includes("四柱／六柱共享舞台") &&
    overview.includes("当前接入六冲／六合成员事实") &&
    overview.includes("同一个 Scene Player") &&
    overview.includes("media.assets.mingli_lab_day_background") &&
    overview.includes("media.cues.dodo_idle") &&
    !/MingliScenePlayer|Canvas/.test(overview),
  "v131-lab-overview:must-preserve-three-instruments-with-real-boundaries-and-no-webgl",
);
expect(
  catalogScene.includes("命局流正在经过这里") &&
    catalogScene.includes("已揭晓封存复盘") &&
    catalogScene.includes("不借用其他命盘冒充复盘") &&
    catalogScene.includes("routeToSyntheticExperiment") &&
    catalogScene.includes("catalog.suites.modes.map") &&
    catalogScene.includes("页面只读 GET") &&
    catalogScene.includes("上次刷新失败，保留当前现场") &&
    !catalogScene.includes("catalog.error || !catalog.experiments") &&
    !/MingliScenePlayer|Canvas/.test(catalogScene),
  "v131-synthetic-catalog:must-project-real-topics-before-the-shared-player",
);
expect(
  researchProjection.includes("experiment.runs.length") &&
    researchProjection.includes('experiment.run_status === "SEALED"') &&
    researchProjection.includes("review.counts.review_required") &&
    researchProjection.includes("review.error_clusters.length") &&
    researchProjection.includes("experiment.latest_run_ref"),
  "v131-lab-projection:all-visible-counts-and-routes-must-come-from-real-catalogs",
);
expect(
  homeScene.includes("循着水光，进入阿布 LAB") &&
    !homeScene.includes('passage === "dream" ? "穿过树洞，进入阿布梦境" : "沿着生命光，进入命理枝"'),
  "v131-lab-entry:home-flower-must-enter-the-research-realm-not-a-mingli-branch",
);
expect(
  homeCompanion.includes('activeUnit === "lab"') &&
    homeCompanion.includes('labRoom === "overview" || labRoom === "catalog"') &&
    homeCompanion.includes("return null"),
  "v131-lab-shell:overview-and-catalog-must-not-be-covered-by-the-old-stage-boundary",
);
expect(
  occurrences(scene, /<MingliScenePlayer/g) === 1 &&
    !scene.includes("key={snapshot.stage.projection_ref}") &&
    sceneSurface.includes("尚无封存实验结果，请通过离线 Lab runner 生成") &&
    sceneSurface.includes("当前仍显示 {displayedVariant} 组") &&
    sceneSurface.includes("当前链接的封存结果不可用") &&
    occurrences(sceneSurface, /改读最新封存结果/g) === 2 &&
    scene.includes("canRestoreLatest={Boolean(experiment && latestRunRef)}") &&
    sceneFeedback.includes("activeError && canRestoreLatest") &&
    scene.includes("<MingliSyntheticExperimentToolbar") &&
    scene.includes("<MingliSyntheticSuiteSummary") &&
    scene.includes("setSnapshot(null)") &&
    /route\.experimentRef\s*\?/.test(scene) &&
    scene.includes("const committedSnapshot = snapshot") &&
    scene.includes("snapshot.experiment_ref === route.experimentRef") &&
    scene.includes("stage={committedSnapshot.stage}") &&
    scene.includes('selected.run_status !== "SEALED"'),
  "synthetic-scene:must-have-one-persistent-player-and-no-browser-run-control",
);
expect(
  toolbar.includes('aria-label="选择合成实验"') &&
    toolbar.includes('aria-label="选择封存运行"') &&
    toolbar.includes("experiment.runs") &&
    toolbar.includes("run.review_contract_status") &&
    toolbar.includes("onSelectVariant"),
  "synthetic-toolbar:must-own-topic-run-and-variant-controls",
);
expect(
  suiteSelection.includes("exactSyntheticSuiteItem") &&
    suiteSelection.includes("compareWithPreviousSyntheticSuiteRun") &&
    suiteSelection.includes("Evaluator 或 Gold 已变化") &&
    suiteSelection.includes("mingli_synthetic_suite_item_binding_mismatch") &&
    suiteSelection.includes("candidate.experiment_ref === route.experimentRef") &&
    suiteSelection.includes("candidate.experiment_run_ref === route.runRef"),
  "synthetic-suite-selection:must-resolve-only-exact-suite-members",
);
expect(
  suiteSummary.includes("review.counts.sealed") &&
    suiteSummary.includes("review.counts.runner_errors") &&
    suiteSummary.includes("review.counts.review_required") &&
    suiteSummary.includes("review.error_clusters") &&
    !/MingliScenePlayer|Canvas/.test(suiteSummary),
  "synthetic-suite-summary:must-show-counts-topics-and-clusters-without-owning-scene",
);

const definitionHash = "d".repeat(64);
const goldHash = "a".repeat(64);
const evaluator = "v60.mingli-synthetic-experiment-evaluator.006";
const goldVersion = "v60.mingli-synthetic-experiment-dev-gold.004";
const cluster = (key, label, occurrence_count) => ({ key, label, occurrence_count });
const reviewItem = (experiment_ref, itemDefinitionHash = definitionHash) => ({
  experiment_ref,
  definition_hash: itemDefinitionHash,
  execution_status: "SEALED",
  evaluator_version: evaluator,
  dev_gold_version: goldVersion,
  dev_gold_hash: goldHash,
  review_contract_status: "CURRENT",
  model_independence: "FAIL",
});
const suiteRun = (suite_run_ref, error_clusters) => ({
  suite_run_ref,
  suite_definition_hash: definitionHash,
  current_review_projection: {
    items: [reviewItem("first"), reviewItem("second")],
    counts: { experiments: 2, sealed: 2, runner_errors: 0, review_required: 2 },
    error_clusters,
  },
});
const currentRun = suiteRun("current", [
  cluster("SERVER_REPAIR:DAY_MASTER_REGIME", "日主判型", 2),
  cluster("SERVER_REPAIR:WORK_PATH", "主路径", 2),
]);
const previousRun = suiteRun("previous", [
  cluster("SERVER_REPAIR:DAY_MASTER_REGIME", "日主判型", 4),
  cluster("SERVER_REPAIR:WORK_PATH", "主路径", 2),
  cluster("CHECK_FAIL:HIDDEN_RANK_PROSE_WITHIN_SCOPE", "藏干正文位阶", 1),
  cluster("SERVER_REPAIR:DAY_MASTER_CAPACITY_H1", "日主承载", 1),
]);
const suiteEntry = {
  suite_ref: "hidden-rank-training",
  suite_definition_hash: definitionHash,
  runs: [currentRun, previousRun],
};
const historyCatalog = { suites: [suiteEntry] };
const currentSelection = {
  suite: suiteEntry,
  run: currentRun,
  review: currentRun.current_review_projection,
};
const comparison = compareWithPreviousSyntheticSuiteRun(
  historyCatalog,
  currentSelection,
);
const deltas = new Map(comparison?.clusterChanges.map((item) => [item.key, item]));
expect(
  comparison?.status === "COMPARABLE" &&
    comparison.currentMetrics.modelIndependent === 0 &&
    comparison.previousMetrics.modelIndependent === 0 &&
    comparison.currentMetrics.reviewRequired === 2 &&
    comparison.previousMetrics.reviewRequired === 2 &&
    deltas.get("SERVER_REPAIR:DAY_MASTER_REGIME")?.previous === 4 &&
    deltas.get("SERVER_REPAIR:DAY_MASTER_REGIME")?.current === 2 &&
    deltas.get("CHECK_FAIL:HIDDEN_RANK_PROSE_WITHIN_SCOPE")?.current === 0 &&
    deltas.get("SERVER_REPAIR:DAY_MASTER_CAPACITY_H1")?.current === 0 &&
    !deltas.has("SERVER_REPAIR:WORK_PATH"),
  "synthetic-suite-comparison:must-show-only-real-deltas-under-the-same-ruler",
);

const comparisonWith = (mutatePrevious) => {
  const altered = structuredClone(previousRun);
  mutatePrevious(altered);
  const entry = { ...suiteEntry, runs: [currentRun, altered] };
  return compareWithPreviousSyntheticSuiteRun(
    { suites: [entry] },
    { ...currentSelection, suite: entry },
  );
};
expect(
  comparisonWith((run) => {
    run.current_review_projection.items[0].evaluator_version =
      "v60.mingli-synthetic-experiment-evaluator.005";
  })?.status === "INCOMPARABLE" &&
    comparisonWith((run) => {
      run.current_review_projection.items[0].dev_gold_hash = "b".repeat(64);
    })?.status === "INCOMPARABLE" &&
    comparisonWith((run) => {
      run.suite_definition_hash = "c".repeat(64);
    })?.status === "INCOMPARABLE" &&
    comparisonWith((run) => {
      run.current_review_projection.items[0].execution_status = "ERROR";
    })?.status === "INCOMPARABLE" &&
    compareWithPreviousSyntheticSuiteRun(
      { suites: [{ ...suiteEntry, runs: [currentRun] }] },
      currentSelection,
    ) === null,
  "synthetic-suite-comparison:must-block-changed-rulers-incomplete-runs-and-missing-history",
);
expect(
  suiteValidation.includes("run.items.length !== suite.experiment_refs.length") &&
    suiteValidation.includes("validateCurrentReviewProjection") &&
    suiteValidation.includes("projection.source_suite_run_hash !== run.suite_run_hash") &&
    suiteValidation.includes("EXECUTION_STATUSES.includes") &&
    suiteValidation.includes("mingli_synthetic_suite_error_item_invalid") &&
    suiteValidation.includes("REVIEW_CONTRACTS.includes") &&
    suiteValidation.includes("validateClusters"),
  "synthetic-suite-validation:must-close-members-enums-errors-and-derived-clusters",
);
expect(
  inspector.includes("开发证据，不等于方法取得资格") &&
    inspector.includes("Gold 未进入 Agent 输入") &&
    inspector.includes("TrainingTracks") &&
    inspector.includes("ModelNormalizationTrace") &&
    inspector.includes("模型原断 → 系统校正") &&
    inspector.includes("关键字段") &&
    inspector.includes("三条结果轨道") &&
    !/MingliScenePlayer|Canvas/.test(inspector),
  "synthetic-inspector:must-separate-three-tracks-and-trace-without-owning-scene",
);
expect(
  stageValidation.includes('stage.subject_id.startsWith("research:")') &&
    stageValidation.includes('stage.identity_badge === "研究合成命盘"') &&
    stageValidation.includes('stage.privacy_scope === "SYNTHETIC_RESEARCH"') &&
    !ordinarySubjectValidator.includes("research:"),
  "stage-validation:research-projection-must-pass-without-entering-subject-list",
);
expect(
  syntheticValidation.includes(
    "snapshot.definition.experiment_ref !== snapshot.experiment_ref",
  ) &&
    syntheticValidation.includes(
      'item.group === "EXPERIMENT_VALIDITY" || item.group === "MUST_HOLD"',
    ) &&
    syntheticValidation.includes(
      "value.changed_pass_count !== changedPassCount",
    ) &&
    syntheticValidation.includes("value.outcome !== expectedOutcome") &&
    syntheticValidation.includes("TRACE_STAGES.includes") &&
    syntheticValidation.includes("value.stage_counts.reduce") &&
    syntheticValidation.includes("sameStrings(value.server_issue_keys, expectedIssues)") &&
    syntheticValidation.includes("mingli_synthetic_catalog_experiment_duplicate") &&
    syntheticValidation.includes("item.experiment_ref !== entry.experiment_ref") &&
    syntheticValidation.includes("runs[0]?.run_ref !== entry.latest_run_ref") &&
    syntheticValidation.includes("item.review_contract_status"),
  "synthetic-validation:must-recompute-outcomes-and-close-trace-invariants",
);

if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify({
  syntheticLabContract: "PASS",
  browserModelCalls: 0,
  runtimeScenePlayers: 1,
  resultTracks: 3,
  normalizationTrace: "FIELD_LEVEL_OR_HONEST_LEGACY",
  experimentDiscovery: "MULTI_EXPERIMENT_AND_RUN_HISTORY",
  routeRecovery: ["suite", "experiment", "run", "variant"],
  labRooms: ["overview", "catalog", "current", "narration", "synthetic"],
  v131ExperienceCommit: "ea2db274ba55b8f9d323881c096d3a3a1ceba66c",
  ordinarySubjectLeakage: false,
  failures,
}, null, 2));
