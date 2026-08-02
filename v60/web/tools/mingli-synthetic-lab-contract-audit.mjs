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
    scene.includes("snapshotError && experiment && latestRunRef") &&
    scene.includes("displayedVariant === variant"),
  "synthetic-scene:must-have-one-persistent-player-and-no-browser-run-control",
);
expect(
  inspector.includes("开发证据，不等于方法取得资格") &&
    inspector.includes("Gold 未进入 Agent 输入") &&
    !/MingliScenePlayer|Canvas/.test(inspector),
  "synthetic-inspector:must-show-qualification-boundary-without-owning-scene",
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
    syntheticValidation.includes("value.outcome !== expectedOutcome"),
  "synthetic-validation:must-recompute-identity-counts-drift-and-outcome",
);

if (failures.length) throw new Error(failures.join("\n"));
console.log(JSON.stringify({
  syntheticLabContract: "PASS",
  browserModelCalls: 0,
  runtimeScenePlayers: 1,
  routeRecovery: ["experiment", "run", "variant"],
  ordinarySubjectLeakage: false,
  failures,
}, null, 2));
