import type {
  MingliStageMode,
  MingliStageSubjectId,
} from "./mingliStageTypes";

export interface MingliStageRoute {
  subjectId: MingliStageSubjectId;
  mode: MingliStageMode;
  year: number | null;
}

export function readMingliStageRoute(): MingliStageRoute {
  const url = new URL(window.location.href);
  const subjectValue = url.searchParams.get("mingli_subject");
  const modeValue = url.searchParams.get("mingli_mode");
  const yearValue = Number(url.searchParams.get("mingli_year"));
  const subjectId: MingliStageSubjectId = ["current", "abu", "duoduo"].includes(
    subjectValue ?? "",
  )
    ? (subjectValue as MingliStageSubjectId)
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
  };
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
  window.history[mode === "push" ? "pushState" : "replaceState"](null, "", url);
}
