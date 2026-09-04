import type { MingliSyntheticLabRoute } from "./mingliSyntheticLabNavigation";
import type {
  MingliSyntheticExperimentCatalog,
  MingliSyntheticExperimentCatalogEntry,
  MingliSyntheticOutcome,
} from "./mingliSyntheticLabTypes";
import {
  latestSyntheticSuiteRunSelection,
} from "./mingliSyntheticSuiteSelection";
import type { MingliSyntheticSuiteCatalog } from "./mingliSyntheticSuiteTypes";

export interface MingliResearchProjection {
  experimentCount: number;
  sealedExperimentCount: number;
  archivedRunCount: number;
  latestSuiteTitle: string | null;
  latestSuiteSealed: number;
  latestSuiteTotal: number;
  reviewRequiredCount: number;
  runnerErrorCount: number;
  errorClusterCount: number;
}

export function projectMingliResearchStatus(
  experiments: MingliSyntheticExperimentCatalog,
  suites: MingliSyntheticSuiteCatalog,
): MingliResearchProjection {
  const latest = latestSyntheticSuiteRunSelection(suites);
  return {
    experimentCount: experiments.experiments.length,
    sealedExperimentCount: experiments.experiments.filter(
      (experiment) => experiment.run_status === "SEALED",
    ).length,
    archivedRunCount: experiments.experiments.reduce(
      (count, experiment) => count + experiment.runs.length,
      0,
    ),
    latestSuiteTitle: latest?.suite.title ?? null,
    latestSuiteSealed: latest?.review.counts.sealed ?? 0,
    latestSuiteTotal: latest?.review.counts.experiments ?? 0,
    reviewRequiredCount: latest?.review.counts.review_required ?? 0,
    runnerErrorCount: latest?.review.counts.runner_errors ?? 0,
    errorClusterCount: latest?.review.error_clusters.length ?? 0,
  };
}

export function routeToSyntheticExperiment(
  experiment: MingliSyntheticExperimentCatalogEntry,
  suites: MingliSyntheticSuiteCatalog,
): MingliSyntheticLabRoute {
  const latest = latestSyntheticSuiteRunSelection(suites);
  const suiteItem = latest?.review.items.find(
    (item) => item.experiment_ref === experiment.experiment_ref
      && item.execution_status === "SEALED"
      && item.experiment_run_ref,
  );
  return {
    mode: "synthetic",
    suiteRunRef: suiteItem ? latest?.run.suite_run_ref ?? null : null,
    experimentRef: experiment.experiment_ref,
    runRef: suiteItem?.experiment_run_ref ?? experiment.latest_run_ref,
    variant: "A",
  };
}

export function syntheticFamilyLabel(
  family: MingliSyntheticExperimentCatalogEntry["family"],
): string {
  switch (family) {
    case "CONTROLLED_LEGAL_HOUR_PAIR":
      return "合法时柱响应";
    case "CONTROLLED_ROOT_IDENTITY_PAIR":
      return "同字与同元素";
    case "CONTROLLED_HIDDEN_RANK_PRIMARY_SECONDARY_PAIR":
      return "第一至第二藏干";
    case "CONTROLLED_HIDDEN_RANK_SECONDARY_TERTIARY_PAIR":
      return "第二至第三藏干";
    case "CONTROLLED_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_PAIR":
      return "跨日主泛化";
    case "CONTROLLED_REGIME_WORK_PATH_GENERALIZATION_PAIR":
      return "判型与主路径";
    case "CONTROLLED_DECISION_DISCIPLINE_GENERALIZATION_PAIR":
      return "候选闭合与反证";
    case "CONTROLLED_MONTH_COMMAND_REGIME_GENERALIZATION_PAIR":
      return "月令坐标与判型";
  }
}

export function syntheticOutcomeLabel(
  outcome: MingliSyntheticOutcome | null,
): string {
  switch (outcome) {
    case "PASS":
      return "模型独立通过";
    case "PRODUCT_SAFE_MODEL_FAIL":
      return "产品已收稳 · 模型待复核";
    case "MODEL_FAIL":
      return "模型未通过";
    case "INVALID_EXPERIMENT":
      return "实验结构无效";
    default:
      return "等待离线运行";
  }
}
