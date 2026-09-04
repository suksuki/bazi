export const PUBLIC_PRODUCT_EXPOSURE_VERSION =
  "v60.public-product-exposure.003" as const;

export const PUBLIC_PRODUCT_EXPOSURE = {
  policyVersion: PUBLIC_PRODUCT_EXPOSURE_VERSION,
  publicUnits: ["MINGLI_READING", "ABU_SAYS"],
  lab: {
    status: "INTERNAL_ONLY",
    publicEntryAllowed: false,
    publicRouteAllowed: false,
  },
} as const;

const OBSOLETE_ROUTE_KEYS = [
  "scope",
  "focus",
  "unit",
  "lab_mode",
  "lab_suite",
  "lab_experiment",
  "lab_run",
  "lab_variant",
] as const;

const MINGLI_ROUTE_KEYS = [
  "mingli_subject",
  "mingli_mode",
  "mingli_year",
  "mingli_layer",
  "mingli_entry",
  "mingli_entry_x",
  "mingli_entry_y",
  "mingli_entry_scene_x",
  "mingli_entry_scene_y",
  "mingli_light",
  "mingli_stage",
  "mingli_rehearsal",
] as const;

export function normalizePublicExperienceUrl(input: URL): URL {
  const url = new URL(input.href);
  OBSOLETE_ROUTE_KEYS.forEach((key) => url.searchParams.delete(key));
  if (url.searchParams.get("view") !== "mingli") {
    url.searchParams.delete("view");
    MINGLI_ROUTE_KEYS.forEach((key) => url.searchParams.delete(key));
  }
  return url;
}

export function enforcePublicExperienceLocation(): boolean {
  if (typeof window === "undefined") return false;
  const current = new URL(window.location.href);
  const normalized = normalizePublicExperienceUrl(current);
  if (normalized.href === current.href) return false;
  window.history.replaceState(null, "", normalized);
  return true;
}
