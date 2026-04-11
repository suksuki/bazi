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
  L0_HIDDEN_ENERGY_SCALE: { min: 0.25, max: 2.5, step: 0.05, label: "藏干能量总标度" },
  L0_ROOT_BOOST_FACTOR: { min: 0.25, max: 2.5, step: 0.05, label: "通根反哺乘子" },
  L0_YM_DH_WEIGHT_RATIO: { min: 0.35, max: 2.8, step: 0.05, label: "年月相对日时权重比" },
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
  L1_SUB_BRANCH_OP_ENABLE: { min: 0, max: 1, step: 1, label: "地支深度算子总开关" },
  SUB_BRANCH_BANHE_PHI: { min: 0, max: 1, step: 0.01, label: "半合 Phi" },
  SUB_BRANCH_BANHE_ABS_BOOST: { min: 0, max: 0.12, step: 0.002, label: "半合 Abs 增益" },
  SUB_BRANCH_BANHE_VECTOR_BOOST: { min: 0, max: 0.08, step: 0.002, label: "半合向量补丁" },
  SUB_BRANCH_SANHE_ABS_BOOST: { min: 0, max: 0.2, step: 0.005, label: "三合 Abs 爆发" },
  SUB_BRANCH_LIUHE_ABS_BOOST: { min: 0, max: 0.15, step: 0.005, label: "六合 Abs 增益" },
  SUB_BRANCH_SANXING_ABS_DAMP: { min: 0.85, max: 1, step: 0.005, label: "三刑 Abs 阻尼" },
  SUB_BRANCH_LIUCHONG_ABS_DAMP: { min: 0.85, max: 1, step: 0.005, label: "六冲 Abs 阻尼" },
  SUB_BRANCH_LIUHAI_ABS_DAMP: { min: 0.9995, max: 1, step: 0.00005, label: "六害 Abs 阻尼" },
  SUB_BRANCH_LIUPO_ABS_DAMP: { min: 0.9995, max: 1, step: 0.00005, label: "六破 Abs 阻尼" },
  SUB_BRANCH_LIUHAI_ENABLE: { min: 0, max: 1, step: 1, label: "六害协议开关" },
  SUB_BRANCH_LIUPO_ENABLE: { min: 0, max: 1, step: 1, label: "六破协议开关" },
  L1_STEM_FUSION_ENABLE: { min: 0, max: 1, step: 1, label: "天干五合总开关" },
  STEM_FUSION_VECTOR_LEAK_RATIO: { min: 0.02, max: 0.45, step: 0.01, label: "化气向量泄漏" },
  STEM_FUSION_BRANCH_SUPPORT_RATIO: { min: 0.15, max: 0.85, step: 0.01, label: "化神支承阈值" },
  WEIGHT_LUCK: { min: 0, max: 1, step: 0.01, label: "岁运通道权重" },
  WEIGHT_YEAR: { min: 0, max: 1, step: 0.01, label: "年柱通道权重" },
  BASE_BACKFIRE_RISK: { min: 0, max: 1, step: 0.01, label: "反噬风险" },
  HIGH_IMBALANCE_RISK: { min: 0, max: 1, step: 0.01, label: "高失衡风险" },
  TOMB_LOCK_RATE: { min: 0, max: 1, step: 0.01, label: "墓库闭锁率" },
  CLIMATE_INTENSITY: { min: 0, max: 1.5, step: 0.01, label: "气候强度" },
  STEM_RESONANCE_BOOST: { min: 1, max: 3, step: 0.05, label: "干谐振增强" },
  TRANSFER_DISTANCE_DECAY: { min: 0, max: 0.5, step: 0.01, label: "跨柱距离衰减" },
  WORK_MIN_THRESHOLD: { min: 0, max: 3, step: 0.1, label: "做功可见阈值" },
  SHOW_WEAK_WORK_PATHS: { min: 0, max: 1, step: 1, label: "显示微弱路径" },
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
