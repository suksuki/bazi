import type { MingliSyntheticLabRoute } from "./mingliSyntheticLabNavigation";
import type {
  MingliSyntheticSuiteCatalog,
  MingliSyntheticSuiteRunItem,
  MingliSyntheticSuiteRunSelection,
} from "./mingliSyntheticSuiteTypes";

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
