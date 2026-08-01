import type {
  MingliStageMode,
  MingliStageSubjectId,
} from "./mingliStageTypes";
import type { HomeWorldLight } from "./homeWorldLight";

export interface MingliStageRoute {
  subjectId: MingliStageSubjectId;
  mode: MingliStageMode;
  year: number | null;
  layer: MingliReadingLayer;
}

export type MingliReadingLayer = "principle" | "image" | "themes" | "timing";

export interface MingliLeafEntry {
  light: HomeWorldLight;
  viewportX: number;
  viewportY: number;
  sceneX: number;
  sceneY: number;
}

export function readMingliStageRoute(): MingliStageRoute {
  const url = new URL(window.location.href);
  const subjectValue = url.searchParams.get("mingli_subject");
  const modeValue = url.searchParams.get("mingli_mode");
  const yearValue = Number(url.searchParams.get("mingli_year"));
  const layerValue = url.searchParams.get("mingli_layer");
  const subjectId: MingliStageSubjectId = isStageSubjectId(subjectValue)
    ? subjectValue
    : "current";
  const mode: MingliStageMode =
    modeValue === "NATAL_DAYUN_YEAR_6" ? modeValue : "NATAL_4";
  return {
    subjectId,
    mode,
    year:
      mode === "NATAL_DAYUN_YEAR_6" && Number.isInteger(yearValue) && yearValue > 0
        ? yearValue
        : null,
    layer: ["principle", "image", "themes", "timing"].includes(layerValue ?? "")
      ? (layerValue as MingliReadingLayer)
      : "principle",
  };
}

export function readMingliLeafEntry(): MingliLeafEntry | null {
  const url = new URL(window.location.href);
  if (url.searchParams.get("mingli_entry") !== "leaf") return null;
  const rawValues = ["x", "y", "scene_x", "scene_y"].map((key) =>
    url.searchParams.get(`mingli_entry_${key}`),
  );
  if (rawValues.some((value) => value === null || value.trim() === "")) return null;
  const values = rawValues.map(Number);
  if (values.some((value) => !Number.isFinite(value) || value < 0 || value > 100)) {
    return null;
  }
  return {
    light: url.searchParams.get("mingli_light") === "night" ? "night" : "day",
    viewportX: values[0],
    viewportY: values[1],
    sceneX: values[2],
    sceneY: values[3],
  };
}

export function clearMingliLeafEntry() {
  const url = new URL(window.location.href);
  for (const key of [
    "mingli_entry",
    "mingli_entry_x",
    "mingli_entry_y",
    "mingli_entry_scene_x",
    "mingli_entry_scene_y",
  ]) {
    url.searchParams.delete(key);
  }
  window.history.replaceState(null, "", url);
}

export function writeMingliLeafRoute(
  subjectId: MingliStageSubjectId,
  entry: MingliLeafEntry,
) {
  const url = new URL(window.location.href);
  url.searchParams.set("view", "mingli");
  url.searchParams.set("mingli_subject", subjectId);
  url.searchParams.set("mingli_mode", "NATAL_4");
  url.searchParams.delete("mingli_year");
  url.searchParams.delete("mingli_layer");
  url.searchParams.set("mingli_entry", "leaf");
  url.searchParams.set("mingli_entry_x", entry.viewportX.toFixed(3));
  url.searchParams.set("mingli_entry_y", entry.viewportY.toFixed(3));
  url.searchParams.set("mingli_entry_scene_x", entry.sceneX.toFixed(3));
  url.searchParams.set("mingli_entry_scene_y", entry.sceneY.toFixed(3));
  url.searchParams.set("mingli_light", entry.light);
  window.history.pushState(null, "", url);
}

export function writeMingliStageRoute(
  route: MingliStageRoute,
  mode: "push" | "replace" = "push",
  view: "mingli" | "lab" = "mingli",
) {
  const url = new URL(window.location.href);
  url.searchParams.set("view", view);
  url.searchParams.set("mingli_subject", route.subjectId);
  url.searchParams.set("mingli_mode", route.mode);
  if (route.mode === "NATAL_DAYUN_YEAR_6" && route.year !== null) {
    url.searchParams.set("mingli_year", String(route.year));
  } else {
    url.searchParams.delete("mingli_year");
  }
  if (route.layer === "principle") url.searchParams.delete("mingli_layer");
  else url.searchParams.set("mingli_layer", route.layer);
  window.history[mode === "push" ? "pushState" : "replaceState"](null, "", url);
}

function isStageSubjectId(value: string | null): value is string {
  return value !== null && (
    ["current", "abu", "duoduo"].includes(value) ||
    (value.startsWith("case:") && value.length > "case:".length)
  );
}
