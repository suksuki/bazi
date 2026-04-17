/** 机房「保存到系统基准」等场景触发与 StreamBoard 同构的静默 analyze-seed。 */
export const SILENT_PHYSICS_RECALC_EVENT = "qiazhi:silent-physics-recalc";

export function dispatchSilentPhysicsRecalc(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(SILENT_PHYSICS_RECALC_EVENT));
}
