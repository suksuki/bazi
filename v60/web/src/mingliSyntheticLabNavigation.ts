import type { MingliSyntheticVariant } from "./mingliSyntheticLabTypes";

export interface MingliSyntheticLabRoute {
  mode: "overview" | "catalog" | "current" | "narration" | "synthetic";
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
  const modeValue = parameters.get("lab_mode");
  const mode = modeValue === "synthetic"
    || modeValue === "catalog"
    || modeValue === "current"
    || modeValue === "narration"
    ? modeValue
    : "overview";
  return {
    mode,
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
    url.searchParams.set("lab_mode", route.mode);
    url.searchParams.set("lab_variant", route.variant);
    setOptional(url, "lab_suite", route.suiteRunRef);
    setOptional(url, "lab_experiment", route.experimentRef);
    setOptional(url, "lab_run", route.runRef);
  } else if (route.mode === "overview") {
    LAB_ROUTE_KEYS.forEach((key) => url.searchParams.delete(key));
  } else {
    url.searchParams.set("lab_mode", route.mode);
    ["lab_suite", "lab_experiment", "lab_run", "lab_variant"].forEach(
      (key) => url.searchParams.delete(key),
    );
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
