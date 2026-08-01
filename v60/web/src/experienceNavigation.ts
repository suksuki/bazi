import {
  isExperienceUnit,
  type ExperienceUnit,
} from "./experienceUnits";

export type ExperienceScope = "home" | "dream";

export function readScope(): ExperienceScope {
  return new URL(window.location.href).searchParams.get("scope") === "dream"
    ? "dream"
    : "home";
}

export function readUnit(): ExperienceUnit {
  const value = new URL(window.location.href).searchParams.get("view");
  if (value === "abu") return readScope() === "dream" ? "dream" : "mingli";
  return isExperienceUnit(value) ? value : "dream";
}

export function readFocusRef(): string | null {
  return new URL(window.location.href).searchParams.get("focus");
}

export function writeNavigation(
  scope: ExperienceScope,
  unit: ExperienceUnit,
  focusRef: string | null,
  mode: "push" | "replace",
) {
  const url = new URL(window.location.href);
  if (scope === "home") url.searchParams.delete("scope");
  else url.searchParams.set("scope", "dream");
  if (unit === "dream") url.searchParams.delete("view");
  else url.searchParams.set("view", unit);
  if (scope !== "home" || (unit !== "mingli" && unit !== "lab")) {
    url.searchParams.delete("mingli_subject");
    url.searchParams.delete("mingli_mode");
    url.searchParams.delete("mingli_year");
    url.searchParams.delete("mingli_layer");
    url.searchParams.delete("mingli_entry");
    url.searchParams.delete("mingli_entry_x");
    url.searchParams.delete("mingli_entry_y");
    url.searchParams.delete("mingli_entry_scene_x");
    url.searchParams.delete("mingli_entry_scene_y");
    url.searchParams.delete("mingli_light");
  }
  if (scope === "dream" && focusRef) url.searchParams.set("focus", focusRef);
  else url.searchParams.delete("focus");
  window.history[mode === "push" ? "pushState" : "replaceState"](
    null,
    "",
    url,
  );
}
