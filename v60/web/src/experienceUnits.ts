export type ExperienceUnit = "dream" | "mingli" | "abu" | "theater" | "lab";

export interface ExperienceUnitDefinition {
  key: ExperienceUnit;
  glyph: string;
  label: string;
  contentKey: string;
}

export const EXPERIENCE_UNITS: readonly ExperienceUnitDefinition[] = [
  {
    key: "dream",
    glyph: "界",
    label: "梦境世界",
    contentKey: "navigation.unit.dream",
  },
  {
    key: "mingli",
    glyph: "命",
    label: "命理测算",
    contentKey: "navigation.unit.mingli",
  },
  {
    key: "theater",
    glyph: "故",
    label: "阿布小剧场",
    contentKey: "navigation.unit.theater",
  },
  {
    key: "lab",
    glyph: "研",
    label: "命理 Lab",
    contentKey: "navigation.unit.lab",
  },
] as const;

export function isExperienceUnit(value: string | null): value is ExperienceUnit {
  return ["dream", "mingli", "abu", "theater", "lab"].includes(value ?? "");
}

export function unitTitle(unit: ExperienceUnit): string {
  if (unit === "mingli") return "阿布知命";
  if (unit === "abu") return "问问阿布";
  if (unit === "theater") return "阿布小剧场";
  if (unit === "lab") return "命理 Lab";
  return "阿布梦境";
}

export function unitSubtitle(unit: ExperienceUnit): string {
  if (unit === "mingli") return "查看正式命盘与事实来源";
  if (unit === "abu") return "陪你把问题说清楚";
  if (unit === "theater") return "看见已经发生的一幕";
  if (unit === "lab") return "检查证据、候选与未决边界";
  return "在持续世界中观察与判断";
}
