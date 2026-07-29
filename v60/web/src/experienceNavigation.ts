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
  if (scope === "dream" && focusRef) url.searchParams.set("focus", focusRef);
  else url.searchParams.delete("focus");
  window.history[mode === "push" ? "pushState" : "replaceState"](
    null,
    "",
    url,
  );
}
