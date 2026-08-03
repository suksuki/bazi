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
  inspector,
  stageValidation,
  syntheticValidation,
] = await Promise.all([
  read("mingliSyntheticLabApi.ts"),
  read("mingliSyntheticLabNavigation.ts"),
  read("experienceNavigation.ts"),
  read("components", "MingliLabWorkspaceHost.tsx"),
  read("components", "MingliSyntheticExperimentScene.tsx"),
  read("components", "MingliSyntheticExperimentInspector.tsx"),
  read("mingliStageValidation.ts"),
  read("mingliSyntheticLabValidation.ts"),
]);
const ordinarySubjectValidator =
  stageValidation.match(/function isStageSubjectId[\s\S]*?\n}/)?.[0] ?? "";

expect(
  occurrences(api, /request<unknown>/g) === 2 &&
    !/method:\s*["']POST/.test(api) &&
    !/generateMingliAgentReading|agent-reading/.test(api),
  "synthetic-api:browser-must-only-read-two-get-endpoints",
);
expect(
  navigation.includes('parameters.get("lab_mode") === "synthetic"') &&
    navigation.includes('url.searchParams.set("lab_variant"') &&
    navigation.includes('setOptional(url, "lab_experiment"') &&
    navigation.includes('setOptional(url, "lab_run"'),
  "synthetic-navigation:route-must-restore-mode-run-and-variant",
);
expect(
  ["lab_mode", "lab_experiment", "lab_run", "lab_variant"].every((key) =>
    experienceNavigation.includes(`url.searchParams.delete("${key}")`),
  ),
  "experience-navigation:must-clear-synthetic-route-outside-lab",
);
expect(
  workspace.includes('route.mode === "synthetic"') &&
    occurrences(workspace, /<MingliSyntheticExperimentScene/g) === 1 &&
    occurrences(workspace, /<MingliSceneHost/g) === 1,
  "synthetic-workspace:current-and-paired-modes-must-be-exclusive",
);
expect(
  occurrences(scene, /<MingliScenePlayer/g) === 1 &&
    !scene.includes("key={snapshot.stage.projection_ref}") &&
    scene.includes("尚无封存实验结果，请通过离线 Lab runner 生成") &&
    scene.includes("当前仍显示 {displayedVariant} 组") &&
    scene.includes("当前链接的封存结果不可用") &&
    occurrences(scene, /改读最新封存结果/g) === 2 &&
    scene.includes("activeSnapshotError && experiment && latestRunRef") &&
    scene.includes("displayedVariant === variant") &&
    scene.includes('aria-label="选择合成实验"') &&
    scene.includes('aria-label="选择封存运行"') &&
    scene.includes("experiment.runs") &&
    scene.includes("run.review_contract_status") &&
    scene.includes("setSnapshot(null)") &&
    /route\.experimentRef\s*\?/.test(scene) &&
    scene.includes("const committedSnapshot = snapshot") &&
    scene.includes("snapshot.experiment_ref === route.experimentRef") &&
    scene.includes("stage={committedSnapshot.stage}") &&
    scene.includes('selected.run_status !== "SEALED"'),
  "synthetic-scene:must-have-one-persistent-player-and-no-browser-run-control",
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
  routeRecovery: ["experiment", "run", "variant"],
  ordinarySubjectLeakage: false,
  failures,
}, null, 2));
