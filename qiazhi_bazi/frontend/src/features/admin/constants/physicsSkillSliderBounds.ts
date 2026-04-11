import type { PhysicsLabConfig } from "@/features/stream-board/models";

/** 实验交互滑块：范围 + 可选中文标签（与 skill_manifest.physics_setting_key 对齐） */
export type PhysicsSliderBinding = {
  min: number;
  max: number;
  step: number;
  label?: string;
};

/**
 * L1 算子卡片内 `physics_setting_key` 白名单，与后端 DEFAULT_PHYSICS_SETTINGS / 算子 clamp 语义对齐。
 */
export const PHYSICS_SKILL_SLIDER_BINDINGS: Partial<
  Record<keyof PhysicsLabConfig, PhysicsSliderBinding>
> = {
  L1_OP_PROD_ETA: { min: 0, max: 3, step: 0.05 },
  L1_OP_DEST_ETA: { min: 0, max: 3, step: 0.05 },
  L1_OP_CONN_ETA: { min: 0, max: 3, step: 0.05 },
  INTERDIMENSIONAL_CONDUCTIVITY: { min: 0, max: 2, step: 0.05 },
  INTERDIMENSIONAL_BARRIER_STRENGTH: { min: 0, max: 2, step: 0.05 },
  CONDUCTIVITY_DECAY_RATE: { min: 0, max: 1, step: 0.05 },
  GHOST_ENERGY_DAMPING: { min: 0, max: 1, step: 0.05 },
  MANGPAI_ETA_DIMENSIONAL_CRUSH: { min: 0, max: 2, step: 0.05 },
  MANGPAI_ROOT_RESONANCE: { min: 0, max: 3, step: 0.05 },
  SGJG_COORDINATE_DISTORTION_DECAY: {
    min: 0,
    max: 1,
    step: 0.01,
    label: "坐标畸变衰减",
  },
  L1_OWL_FOOD_DAMPING: { min: 0, max: 0.95, step: 0.01 },
  L1_WEALTH_SEAL_COLLAPSE: { min: 0, max: 0.95, step: 0.01 },
  L1_BLADE_CLASH_INSTABILITY: { min: 0, max: 2, step: 0.05 },
  L1_ROBBER_WEALTH_ALLOC_LOSS: { min: 0, max: 0.95, step: 0.01 },
  L1_GOV_KILL_EFFICIENCY_LOSS: { min: 0, max: 1, step: 0.01 },
  GRAVE_BURST_MULTIPLIER: { min: 0.5, max: 3, step: 0.05 },
  L1_SANHE_PHI_CLAMP: { min: 0, max: 1, step: 0.05 },
  STATUS_BOOST_MULTIPLIER: { min: 0.5, max: 2, step: 0.05 },
};

export function physicsSliderBindingForKey(
  key: string | undefined | null,
): PhysicsSliderBinding | undefined {
  if (!key) return undefined;
  return PHYSICS_SKILL_SLIDER_BINDINGS[key as keyof PhysicsLabConfig];
}

export function boundsForPhysicsSettingKey(
  key: string | undefined | null,
): [number, number, number] | undefined {
  const b = physicsSliderBindingForKey(key);
  if (!b) return undefined;
  return [b.min, b.max, b.step];
}
