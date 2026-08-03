import type { MingliSyntheticVariant } from "./mingliSyntheticLabTypes";

export interface MingliSyntheticLabRoute {
  mode: "current" | "synthetic";
  suiteRunRef: string | null;
  experimentRef: string | null;
  runRef: string | null;
  variant: MingliSyntheticVariant;
}

const LAB_ROUTE_KEYS = [
  "lab_mode",
  "lab_suite",
  "lab_experiment",
  "lab_run",
  "lab_variant",
];

export function readMingliSyntheticLabRoute(): MingliSyntheticLabRoute {
  const parameters = new URL(window.location.href).searchParams;
  const synthetic = parameters.get("lab_mode") === "synthetic";
  return {
    mode: synthetic ? "synthetic" : "current",
    suiteRunRef: nonempty(parameters.get("lab_suite")),
    experimentRef: nonempty(parameters.get("lab_experiment")),
    runRef: nonempty(parameters.get("lab_run")),
    variant: parameters.get("lab_variant") === "B" ? "B" : "A",
  };
}

export function writeMingliSyntheticLabRoute(
  route: MingliSyntheticLabRoute,
  mode: "push" | "replace" = "push",
): void {
  const url = new URL(window.location.href);
  url.searchParams.set("view", "lab");
  if (route.mode === "synthetic") {
    url.searchParams.set("lab_mode", "synthetic");
    url.searchParams.set("lab_variant", route.variant);
    setOptional(url, "lab_suite", route.suiteRunRef);
    setOptional(url, "lab_experiment", route.experimentRef);
    setOptional(url, "lab_run", route.runRef);
  } else {
    LAB_ROUTE_KEYS.forEach((key) => url.searchParams.delete(key));
  }
  window.history[mode === "push" ? "pushState" : "replaceState"](null, "", url);
}

function setOptional(url: URL, key: string, value: string | null): void {
  if (value) url.searchParams.set(key, value);
  else url.searchParams.delete(key);
}

function nonempty(value: string | null): string | null {
  return value && value.trim() ? value : null;
}
