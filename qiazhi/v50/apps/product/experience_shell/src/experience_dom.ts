import type { UiState } from "./state";


export function applyActiveAnchor(anchor: string): void {
  document.querySelectorAll(".narration-active").forEach((element) => element.classList.remove("narration-active"));
  document.querySelectorAll<HTMLElement>(`[data-anchor="${CSS.escape(anchor)}"], [data-select-anchor="${CSS.escape(anchor)}"]`).forEach((element) => element.classList.add("narration-active"));
}


export function updateExperienceLocation(activeCaseId: string, ui: UiState): void {
  const params = new URLSearchParams({ case: activeCaseId });
  if (ui.productArea !== "world") params.set("area", ui.productArea);
  if (ui.productArea === "workbench" && ui.workspaceSurface !== "overview") {
    params.set("surface", ui.workspaceSurface);
  }
  history.replaceState({}, "", `/experience?${params.toString()}`);
}


export function humanizeError(message: string): string {
  return message
    .replace(/^formal_life_case_not_available$/, "四柱已经就绪，整盘主线还在整理中。")
    .replace(/^experience_case_not_found$/, "没有找到这份案例，或它不属于当前账户。")
    .replace(/^canvas_official_timing_required$/, "这份案例还没有完整的大运与流年计算。")
    .replace(/_/g, " ");
}
