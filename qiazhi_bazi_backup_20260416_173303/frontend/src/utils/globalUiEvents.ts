/** 供音效 / 触觉预埋：相变锁定瞬间 */
export const PHASE_LOCK_SHIMMER = "phase-lock-shimmer";

/** `PhaseTransitionAura`：半幅中控 Flash */
export const PHASE_TRANSITION_FLASH = "qiazhi:phase-transition-flash";

/** 极坐标格局仪表盘：金色扩散涟漪（与 Flash / Shimmer 同步） */
export const PHASE_POLAR_RIPPLE = "qiazhi:phase-polar-ripple";

export type PhaseTransitionFlashDetail = {
  message: string;
};

export function dispatchGlobalEvent(name: string, detail?: unknown): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(name, { detail: detail ?? null }));
}

/** 触发底部 `PhaseTransitionAura` Flash（与 SSE / 组件解耦） */
export function flashPhaseTransitionToast(message: string): void {
  dispatchGlobalEvent(PHASE_TRANSITION_FLASH, { message } satisfies PhaseTransitionFlashDetail);
}
