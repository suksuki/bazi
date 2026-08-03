import type { MingliSyntheticLabRoute } from "./mingliSyntheticLabNavigation";
import type {
  MingliSyntheticSuiteCatalog,
  MingliSyntheticSuiteErrorCluster,
  MingliSyntheticSuiteRun,
  MingliSyntheticSuiteRunItem,
  MingliSyntheticSuiteRunSelection,
} from "./mingliSyntheticSuiteTypes";

export interface MingliSyntheticSuiteMetricSnapshot {
  modelIndependent: number;
  reviewRequired: number;
  sealed: number;
  total: number;
  suiteIndependent: boolean;
}

export interface MingliSyntheticSuiteClusterChange {
  key: string;
  label: string;
  previous: number;
  current: number;
}

export interface MingliSyntheticSuiteRunComparison {
  status: "COMPARABLE" | "INCOMPARABLE";
  reason: string;
  current: MingliSyntheticSuiteRunSelection;
  previous: MingliSyntheticSuiteRunSelection;
  currentMetrics: MingliSyntheticSuiteMetricSnapshot;
  previousMetrics: MingliSyntheticSuiteMetricSnapshot;
  clusterChanges: MingliSyntheticSuiteClusterChange[];
}

export function findSyntheticSuiteRun(
  catalog: MingliSyntheticSuiteCatalog,
  suiteRunRef: string,
): MingliSyntheticSuiteRunSelection | null {
  for (const suite of catalog.suites) {
    const run = suite.runs.find((item) => item.suite_run_ref === suiteRunRef);
    if (run) return { suite, run, review: run.current_review_projection };
  }
  return null;
}

export function latestSyntheticSuiteRunSelection(
  catalog: MingliSyntheticSuiteCatalog,
): MingliSyntheticSuiteRunSelection | null {
  let latest: MingliSyntheticSuiteRunSelection | null = null;
  for (const suite of catalog.suites) {
    const run = suite.runs[0];
    if (run && (!latest || run.created_at > latest.run.created_at)) {
      latest = { suite, run, review: run.current_review_projection };
    }
  }
  return latest;
}

export function compareWithPreviousSyntheticSuiteRun(
  history: MingliSyntheticSuiteCatalog,
  current: MingliSyntheticSuiteRunSelection,
): MingliSyntheticSuiteRunComparison | null {
  const historicalSuite = history.suites.find(
    (suite) => suite.suite_ref === current.suite.suite_ref,
  );
  if (!historicalSuite) return null;
  const currentIndex = historicalSuite.runs.findIndex(
    (run) => run.suite_run_ref === current.run.suite_run_ref,
  );
  const previousRun = currentIndex >= 0
    ? historicalSuite.runs[currentIndex + 1]
    : undefined;
  if (!previousRun) return null;
  const previous: MingliSyntheticSuiteRunSelection = {
    suite: historicalSuite,
    run: previousRun,
    review: previousRun.current_review_projection,
  };
  const reason = comparisonBlockReason(current, previous);
  return {
    status: reason ? "INCOMPARABLE" : "COMPARABLE",
    reason: reason ?? "同一 Suite、Evaluator 与 Gold，可直接比较候选表现。",
    current,
    previous,
    currentMetrics: suiteMetricSnapshot(current.run),
    previousMetrics: suiteMetricSnapshot(previous.run),
    clusterChanges: reason
      ? []
      : changedClusters(
          previous.review.error_clusters,
          current.review.error_clusters,
        ),
  };
}

function comparisonBlockReason(
  current: MingliSyntheticSuiteRunSelection,
  previous: MingliSyntheticSuiteRunSelection,
): string | null {
  if (
    current.run.suite_definition_hash !== previous.run.suite_definition_hash
    || current.review.items.length !== previous.review.items.length
  ) {
    return "Suite 定义已经变化，本轮与上轮不可直接比较。";
  }
  for (let index = 0; index < current.review.items.length; index += 1) {
    const currentItem = current.review.items[index];
    const previousItem = previous.review.items[index];
    if (
      !currentItem
      || !previousItem
      || currentItem.experiment_ref !== previousItem.experiment_ref
      || currentItem.definition_hash !== previousItem.definition_hash
    ) {
      return "合成课题或定义已经变化，本轮与上轮不可直接比较。";
    }
    if (
      currentItem.execution_status !== "SEALED"
      || previousItem.execution_status !== "SEALED"
    ) {
      return "至少一轮没有完整封存，不能计算模型能力变化。";
    }
    if (
      currentItem.evaluator_version !== previousItem.evaluator_version
      || currentItem.dev_gold_version !== previousItem.dev_gold_version
      || currentItem.dev_gold_hash !== previousItem.dev_gold_hash
    ) {
      return "Evaluator 或 Gold 已变化，只能并列查看，不能声称错误减少。";
    }
    if (
      currentItem.review_contract_status !== "CURRENT"
      || previousItem.review_contract_status !== "CURRENT"
    ) {
      return "至少一轮已被当前审查口径替代，只能并列查看。";
    }
  }
  return null;
}

function suiteMetricSnapshot(
  run: MingliSyntheticSuiteRun,
): MingliSyntheticSuiteMetricSnapshot {
  const review = run.current_review_projection;
  const allCurrent = review.items.every(
    (item) => item.review_contract_status === "CURRENT",
  );
  const modelIndependent = review.items.filter(
    (item) => item.model_independence === "PASS",
  ).length;
  return {
    modelIndependent,
    reviewRequired: review.counts.review_required,
    sealed: review.counts.sealed,
    total: review.counts.experiments,
    suiteIndependent:
      review.counts.sealed === review.counts.experiments
      && review.counts.runner_errors === 0
      && allCurrent
      && modelIndependent === review.counts.experiments
      && review.error_clusters.length === 0,
  };
}

function changedClusters(
  previous: MingliSyntheticSuiteErrorCluster[],
  current: MingliSyntheticSuiteErrorCluster[],
): MingliSyntheticSuiteClusterChange[] {
  const previousByKey = new Map(previous.map((cluster) => [cluster.key, cluster]));
  const currentByKey = new Map(current.map((cluster) => [cluster.key, cluster]));
  return [...new Set([...previousByKey.keys(), ...currentByKey.keys()])]
    .map((key) => {
      const previousCluster = previousByKey.get(key);
      const currentCluster = currentByKey.get(key);
      return {
        key,
        label: currentCluster?.label ?? previousCluster?.label ?? key,
        previous: previousCluster?.occurrence_count ?? 0,
        current: currentCluster?.occurrence_count ?? 0,
      };
    })
    .filter((change) => change.previous !== change.current)
    .sort((left, right) =>
      (right.previous - right.current) - (left.previous - left.current)
      || left.key.localeCompare(right.key)
    );
}

export function exactSyntheticSuiteItem(
  selection: MingliSyntheticSuiteRunSelection | null,
  route: MingliSyntheticLabRoute,
): MingliSyntheticSuiteRunItem | null {
  if (!selection || !route.experimentRef || !route.runRef) return null;
  return selection.review.items.find(
    (item) => item.execution_status === "SEALED"
      && item.experiment_ref === route.experimentRef
      && item.experiment_run_ref === route.runRef,
  ) ?? null;
}

export function firstSyntheticSuiteRoute(
  selection: MingliSyntheticSuiteRunSelection,
): MingliSyntheticLabRoute | null {
  const first = selection.review.items.find(
    (item) => item.execution_status === "SEALED" && item.experiment_run_ref,
  );
  if (!first?.experiment_run_ref) return null;
  return {
    mode: "synthetic",
    suiteRunRef: selection.run.suite_run_ref,
    experimentRef: first.experiment_ref,
    runRef: first.experiment_run_ref,
    variant: "A",
  };
}

export function firstReviewRequiredSyntheticSuiteRoute(
  selection: MingliSyntheticSuiteRunSelection,
): MingliSyntheticLabRoute | null {
  const first = selection.review.items.find(
    (item) => item.execution_status === "SEALED"
      && item.review_required
      && item.experiment_run_ref,
  );
  if (!first?.experiment_run_ref) return null;
  return {
    mode: "synthetic",
    suiteRunRef: selection.run.suite_run_ref,
    experimentRef: first.experiment_ref,
    runRef: first.experiment_run_ref,
    variant: "A",
  };
}

export type SyntheticSuiteRouteResolution =
  | { status: "BOUND" }
  | { status: "PATCH"; experimentRef: string; runRef: string }
  | { status: "ERROR"; error: string };

export function resolveSyntheticSuiteRoute(
  selection: MingliSyntheticSuiteRunSelection,
  route: MingliSyntheticLabRoute,
): SyntheticSuiteRouteResolution {
  if (route.experimentRef && route.runRef) {
    return exactSyntheticSuiteItem(selection, route)
      ? { status: "BOUND" }
      : { status: "ERROR", error: "mingli_synthetic_suite_item_binding_mismatch" };
  }
  const item = selection.review.items.find((candidate) =>
    candidate.execution_status === "SEALED"
      && candidate.experiment_run_ref
      && (!route.experimentRef || candidate.experiment_ref === route.experimentRef)
      && (!route.runRef || candidate.experiment_run_ref === route.runRef)
  );
  if (!item?.experiment_run_ref) {
    return {
      status: "ERROR",
      error: route.experimentRef || route.runRef
        ? "mingli_synthetic_suite_item_binding_mismatch"
        : "mingli_synthetic_suite_has_no_sealed_item",
    };
  }
  return {
    status: "PATCH",
    experimentRef: item.experiment_ref,
    runRef: item.experiment_run_ref,
  };
}

export function formatSyntheticRunLabel(
  createdAt: string,
  model: "PASS" | "FAIL" | "NOT_EVALUABLE",
  contract: "CURRENT" | "SUPERSEDED",
): string {
  const date = createdAt.replace("T", " ").slice(0, 16);
  const status = model === "PASS"
    ? "模型独立"
    : model === "FAIL"
      ? "仍需校正"
      : "实验不可评价";
  return `${date} · ${status} · ${contract === "CURRENT" ? "当前口径" : "旧口径"}`;
}
